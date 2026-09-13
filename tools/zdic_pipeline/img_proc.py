# -*- coding: utf-8 -*-
"""健壮的字形图预处理：Otsu 阈值 + 背景方向判定 + alpha 遮罩兜底。"""
import io
from PIL import Image

def _otsu(hist, total):
    """Otsu 二值化阈值。"""
    sum_total = sum(i * hist[i] for i in range(256))
    sum_bg = w_bg = 0
    best_t = 0
    best_var = -1.0
    for t in range(256):
        w_bg += hist[t]
        if w_bg == 0:
            continue
        w_fg = total - w_bg
        if w_fg == 0:
            break
        sum_bg += t * hist[t]
        mean_bg = sum_bg / w_bg
        mean_fg = (sum_total - sum_bg) / w_fg
        var_between = w_bg * w_fg * (mean_bg - mean_fg) ** 2
        if var_between > best_var:
            best_var = var_between
            best_t = t
    return best_t

def load_image_as_gray(png_bytes):
    """PNG bytes -> (w, h, px_bytes)。墨迹统一为 255, 背景为 0。"""
    im = Image.open(io.BytesIO(png_bytes))
    w, h = im.size
    has_alpha = (im.mode in ("RGBA", "LA")
                 or (im.mode == "P" and "transparency" in im.info))
    if has_alpha:
        rgba = im.convert("RGBA")
        alpha = rgba.split()[3]
        apx = alpha.tobytes()
        n_opaque = sum(1 for v in apx if v > 128)
        # 只有 alpha 真正有区分度时才拿它当遮罩。白底渲染出来的 PNG 虽然带 alpha，
        # 但全画布不透明（alpha 恒 255），此时必须回退到亮度阈值，否则整幅图被当成墨迹。
        if 0 < n_opaque < w * h * 0.995:
            return w, h, bytes(255 if v > 128 else 0 for v in apx)
        data = rgba.convert("L").tobytes()
    else:
        data = im.convert("L").tobytes()

    corners = [data[0], data[w - 1], data[(h - 1) * w], data[h * w - 1]]

    # 已是二值图（灰度级 <= 2）：Otsu 会退化到阈值 0，必须单独处理。
    # 场景：_plan2_cache/*.png 本身就是 0/255 的掩码，再走 Otsu 会全变 0。
    uniq = sorted(set(data))
    if len(uniq) <= 2:
        lo, hi = uniq[0], uniq[-1]
        if lo == hi:
            return w, h, bytes(w * h)  # 纯色：无墨迹
        bg_is_hi = (sum(corners) / 4.0) > (lo + hi) / 2.0
        ink_val = lo if bg_is_hi else hi  # 四角是背景 → 墨迹取另一侧
        return w, h, bytes(255 if v == ink_val else 0 for v in data)

    hist = [0] * 256
    for v in data:
        hist[v] += 1
    total = w * h
    t = _otsu(hist, total)

    # 四角背景值，判断墨迹方向
    bg_val = sum(corners) / 4
    ink_is_light = bg_val < t  # 背景比阈值暗 → 墨迹在亮侧

    if ink_is_light:
        return w, h, bytes(255 if v > t else 0 for v in data)
    return w, h, bytes(255 if v < t else 0 for v in data)


if __name__ == "__main__":
    import os
    import base64, re
    HTML = r"E:\Workbuddy\说文解字\output\金文缺口1083字总表\金文缺口1083字_总表.html"
    OUT = r"E:\Workbuddy\说文解字\_diag_out"
    def html_png(ch):
        html = open(HTML, "r", encoding="utf-8").read()
        cjk = re.compile(r"^[一-鿿]$")
        for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.S):
            row = m.group(1)
            img_m = re.search(r'<img[^>]+src="(data:image/[^;]+;base64,[^"]+)"', row)
            if not img_m:
                continue
            c = None
            for cm in re.finditer(r"<td[^>]*>\s*([^<>]+?)\s*</td>", row):
                if cjk.match(cm.group(1).strip()):
                    c = cm.group(1).strip()
                    break
            if c == ch:
                return base64.b64decode(img_m.group(1).split(",", 1)[1])
        return None

    for ch in ["为", "乞"]:
        png = html_png(ch)
        if png:
            w, h, px = load_image_as_gray(png)
            nz = sum(1 for v in px if v > 0)
            print(ch, "w=", w, "h=", h, "nonzero=", nz, "ratio=", nz / (w * h))
            Image.frombytes("L", (w, h), px).save(os.path.join(OUT, f"{ch}_otsu_test.png"))
