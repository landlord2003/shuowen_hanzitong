# -*- coding: utf-8 -*-
"""B 管线公共工具：下载、SVG->PNG、许可证元数据、署名收集。"""
import os
import json
import shutil
import subprocess

# 本机代理（老吴本机梯子，端口 18081）。Wikimedia/IA 等境外源需走此代理才能出海。
# 设为 None 表示直连（适用海外机器）；设 "http://127.0.0.1:18081" 走本机梯子。
LOCAL_PROXY = os.environ.get("RUBBING_PROXY", "http://127.0.0.1:18081")
if LOCAL_PROXY.lower() in ("", "none", "direct", "off"):
    LOCAL_PROXY = None

LICENSES = {
    "pd": "Public Domain / 公版（可自由商用）",
    "cc_by_sa_2_1_jp": "CC BY-SA 2.1 JP（须署名 + 衍生同授权）",
    "cc_by_sa_2_5_tw": "CC BY-SA 2.5 TW（须署名 + 衍生同授权）",
    "unknown": "未知（请人工确认授权后再商用）",
}


def make_session():
    """建一个走本机梯子（或直连）的 requests.Session。"""
    import requests
    s = requests.Session()
    if LOCAL_PROXY:
        s.proxies = {"http": LOCAL_PROXY, "https": LOCAL_PROXY}
        s.trust_env = False  # 用显式代理，忽略环境变量（沙箱会注入 127.0.0.1:64928）
    else:
        s.trust_env = False  # 海外机器直连
    return s


def download_file(url, dest, timeout=60, retries=3, session=None):
    """下载文件，带重试。失败返回 False（不抛异常，便于逐字容错）。
    若传入 session（requests.Session），则复用连接池以加速批量抓取。"""
    if session is not None:
        http = session
    else:
        http = make_session()
    for attempt in range(1, retries + 1):
        try:
            r = http.get(url, timeout=timeout, headers={"User-Agent": "rubbing-pipeline/1.0"}, allow_redirects=True)
            if r.status_code == 200 and r.content:
                os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(r.content)
                return True
            if r.status_code == 404:
                return False  # 404 不重试（该字无此字形），避免批量抓取浪费
        except Exception:
            pass
    return False


def normalize_png(png_path, size=160, keep_alpha=True):
    """把任意模式的 PNG 统一为 size×size 灰度图，存回原文件。
    keep_alpha=True（默认）保留透明背景，输出 LA 模式；
    keep_alpha=False 输出 RGB 白底图。
    失败返回 False（如非 PNG/无法读取）。"""
    from PIL import Image
    try:
        im = Image.open(png_path)
    except Exception:
        return False
    if im.mode not in ("L", "LA", "RGBA", "RGB"):
        im = im.convert("RGBA")
    # 缩放到 size×size
    if im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    if keep_alpha:
        # 统一合成到白底后转灰度（L 模式）。
        # 关键：SVG 栅格化常为「透明背景 + 黑字形」，直接 convert("L") 会把透明像素
        # 转成黑(0)，导致整图全黑。必须先 alpha_composite 到白底，再转 L。
        if im.mode in ("RGBA", "LA"):
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
            im = Image.alpha_composite(bg, im.convert("RGBA"))
            im = im.convert("L")
        elif im.mode == "RGB":
            im = im.convert("L")
        elif im.mode == "L":
            pass
        # im 已是 L（白底黑字灰度图）
    else:
        # 白底 RGB
        if im.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, (0, 0), im if im.mode == "RGBA" else im.split()[-1] if im.mode == "LA" else None)
            im = bg
        elif im.mode == "L":
            im = im.convert("RGB")
    im.save(png_path, "PNG", optimize=True)
    return True


def svg_to_png(svg_path, png_path, size=160):
    """把 SVG 栅格化为 size×size 白底 PNG。优先 resvg（自包含，无需系统 cairo），回退 cairosvg / rsvg-convert / inkscape。"""
    os.makedirs(os.path.dirname(os.path.abspath(png_path)), exist_ok=True)
    svg_bytes = open(svg_path, "rb").read()
    # 1) resvg-py（自带原生库，Windows 无需 GTK/cairo）
    try:
        import resvg_py
        png = resvg_py.svg_to_bytes(svg_bytes.decode("utf-8"), width=size, height=size)
        with open(png_path, "wb") as f:
            f.write(png)
        if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
            return True
    except Exception:
        pass
    # 2) cairosvg
    try:
        import cairosvg
        cairosvg.svg2png(
            url=svg_path, write_to=png_path,
            output_width=size, output_height=size, background_color="white",
        )
        if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
            return True
    except Exception:
        pass
    # 3) rsvg-convert
    if shutil.which("rsvg-convert"):
        rc = subprocess.run(
            ["rsvg-convert", "-w", str(size), "-h", str(size), "-b", "white", svg_path, "-o", png_path],
            check=False,
        )
        if rc.returncode == 0 and os.path.exists(png_path):
            return True
    # 4) inkscape
    if shutil.which("inkscape"):
        rc = subprocess.run(
            ["inkscape", svg_path, "--export-filename", png_path, "-w", str(size), "-h", str(size), "-b", "white"],
            check=False,
        )
        if rc.returncode == 0 and os.path.exists(png_path):
            return True
    return False


class Attribution:
    """收集各字形的来源与许可证，输出 dataset.attribution.json 便于合规署名。"""

    def __init__(self):
        self.entries = {}

    def add(self, key, source, license_name):
        e = self.entries.setdefault(
            key, {"source": source, "license": license_name, "count": 0}
        )
        e["count"] += 1

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)
