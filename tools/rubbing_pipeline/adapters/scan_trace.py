# -*- coding: utf-8 -*-
"""Internet Archive 公版书影裁剪适配器（甲骨 / 金文 / 篆文）。

伙伴从 IA 下载公版书（如罗振玉《殷虚书契》、說文篆書本、金文集古录等）并按页渲染为 PNG，
再用 `bbox_map.json`（字 -> 书 + 页码 + 包围盒）自动裁剪对应区域、灰度化，作为该字的古文字位图。
这是用户最初设想的「自绘公版拓片」自动化落地：真迹来源、公版授权、可批量。
"""
import os
import json
import glob

from PIL import Image
from sources import LICENSES

PAGE_NAMING = "{book}_page_{page:04d}.png"  # 0 基页码；伙伴可按实际命名调整


def _find_page(scan_root, book, page):
    book_dir = os.path.join(scan_root, book)
    cand = os.path.join(book_dir, PAGE_NAMING.format(book=book, page=page))
    if os.path.exists(cand):
        return cand
    # 宽松回退：扫描该目录下包含页码标记的文件
    pat = os.path.join(book_dir, f"*page*{page:0>2d}*")
    hits = sorted(glob.glob(pat))
    if hits:
        return hits[0]
    # 再退一步：按页码序号（目录字母序）
    all_png = sorted(glob.glob(os.path.join(book_dir, "*.png")))
    if 0 <= page < len(all_png):
        return all_png[page]
    return None


def _binarize(im, size=160):
    im = im.convert("L")
    w, h = im.size
    scale = min(1.0, size / max(w, h))
    if scale < 1.0:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    return im


def fetch(chars, out_dir, attribution=None, scan_root=None, bbox_map=None, limit=None, **kw):
    if not scan_root or not bbox_map:
        raise ValueError("scan_trace 需要 scan_root 与 bbox_map")
    with open(bbox_map, encoding="utf-8") as f:
        bmap = json.load(f)
    os.makedirs(out_dir, exist_ok=True)
    results = []
    items = chars if limit is None else chars[:limit]
    for c in items:
        ch = _strip(c.get("char"))
        if ch not in bmap:
            continue
        entry = bmap[ch]
        book = entry["book"]
        page = int(entry["page"])
        bbox = entry["bbox"]
        script = entry.get("script", "oracle-bone")
        page_path = _find_page(scan_root, book, page)
        if not page_path:
            continue
        try:
            im = Image.open(page_path)
            crop = im.crop((int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])))
            crop = _binarize(crop, size=160)
            png_path = os.path.join(out_dir, f"scan_{c['id']}.png")
            crop.save(png_path)
        except Exception:
            continue
        results.append({
            "id": str(c["id"]), "char": ch,
            "script": script, "img": png_path,
        })
        if attribution:
            attribution.add(script, f"Internet Archive 公版书影 ({book})", LICENSES["pd"])
    return results


def _strip(v):
    if v is None:
        return ""
    return str(v).strip().strip("'\"")
