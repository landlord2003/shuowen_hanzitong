# -*- coding: utf-8 -*-
"""Wikimedia Commons 小篆 SVG 适配器（公版优先）。

走 Commons API 搜索每个字对应的「小篆」SVG 并栅格化。覆盖面取决于 Commons 实际类目，
属于 best-effort：取不到的字留空（由其它适配器或 A 路线字体渲染补齐）。
"""
import os
import json

from sources import download_file, svg_to_png, LICENSES

API = "https://commons.wikimedia.org/w/api.php"
SEARCH_QUERY = "{char} seal script"  # 伙伴可按 Commons 实际命名调整


def _search_svg(char, limit=1):
    """返回该字匹配的 SVG 文件直链（Special:FilePath）。"""
    import requests
    q = SEARCH_QUERY.format(char=char)
    params = {
        "action": "query", "format": "json", "list": "search",
        "srsearch": q, "srnamespace": "6", "srlimit": str(limit),
    }
    try:
        r = requests.get(API, params=params, timeout=30,
                         headers={"User-Agent": "rubbing-pipeline/1.0"})
        data = r.json()
    except Exception:
        return []
    out = []
    for item in data.get("query", {}).get("search", []):
        title = item["title"]  # 形如 File:xxx.svg
        if not title.lower().endswith(".svg"):
            continue
        fname = title.split(":", 1)[-1]
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + fname
        out.append(url)
    return out


def fetch(chars, out_dir, attribution=None, limit=None, **kw):
    """chars: list of dict(id,char,trad)。返回 manifest 列表。"""
    os.makedirs(out_dir, exist_ok=True)
    results = []
    items = chars if limit is None else chars[:limit]
    for c in items:
        ch = c.get("trad") or c.get("char")
        ch = _strip(ch)
        if not ch:
            continue
        urls = _search_svg(ch, limit=3)
        got = False
        for url in urls:
            svg_path = os.path.join(out_dir, f"wm_{c['id']}.svg")
            png_path = os.path.join(out_dir, f"wm_{c['id']}.png")
            if download_file(url, svg_path) and svg_to_png(svg_path, png_path, size=160):
                results.append({
                    "id": str(c["id"]), "char": _strip(c["char"]),
                    "script": "seal", "img": png_path,
                })
                if attribution:
                    attribution.add("seal", "Wikimedia Commons (Seal Script SVG)", LICENSES["pd"])
                got = True
                break
        if not got:
            pass  # 留空，交给其它源 / A 路线
    return results


def _strip(v):
    if v is None:
        return ""
    return str(v).strip().strip("'\"")
