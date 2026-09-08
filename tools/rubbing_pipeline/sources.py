# -*- coding: utf-8 -*-
"""B 管线公共工具：下载、SVG->PNG、许可证元数据、署名收集。"""
import os
import json
import shutil
import subprocess

LICENSES = {
    "pd": "Public Domain / 公版（可自由商用）",
    "cc_by_sa_2_1_jp": "CC BY-SA 2.1 JP（须署名 + 衍生同授权）",
    "cc_by_sa_2_5_tw": "CC BY-SA 2.5 TW（须署名 + 衍生同授权）",
    "unknown": "未知（请人工确认授权后再商用）",
}


def download_file(url, dest, timeout=60, retries=3, session=None):
    """下载文件，带重试。失败返回 False（不抛异常，便于逐字容错）。
    若传入 session（requests.Session），则复用连接池以加速批量抓取。"""
    import requests
    http = session if session is not None else requests
    for attempt in range(1, retries + 1):
        try:
            r = http.get(url, timeout=timeout, headers={"User-Agent": "rubbing-pipeline/1.0"})
            if r.status_code == 200 and r.content:
                os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(r.content)
                return True
        except Exception:
            pass
    return False


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
