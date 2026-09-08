# -*- coding: utf-8 -*-
"""Wikimedia Commons 小篆 SVG 适配器（公版优先）。

走 Commons API 搜索每个字对应的「小篆」SVG 并栅格化。覆盖面取决于 Commons 实际类目，
属于 best-effort：取不到的字留空（由其它适配器或 A 路线字体渲染补齐）。
"""
import os
import json
import time

from sources import download_file, svg_to_png, normalize_png, LICENSES, make_session

API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia Commons「Ancient Chinese characters project」(ACC) 命名规范：
#   小篆 = {汉字}-seal.svg（如 口-seal.svg / 說-seal.svg / 書-seal.svg）
# 公版 (Public Domain)，直接按文件名构造直链，无需搜索。
#
# 关键：upload.wikimedia.org（图片 CDN）对代理/梯子出口 IP 永久 429（拉黑），
# 但 commons.wikimedia.org 的 thumb.php 缩略图服务可正常访问，且对 SVG 直接返回
# 栅格化后的 PNG（512px），绕开 upload 域名限流 + 省掉本地 svg_to_png。
FILE_URL = "https://commons.wikimedia.org/w/thumb.php?f={char}-seal.svg&w=512"

# Wikimedia 对无 UA / 高频请求限流（429 + Retry-After），必须：
#   1) 规范 UA（Wikimedia 要求含联系方式）
#   2) 字间延迟
#   3) 429 时等 Retry-After 再重试
USER_AGENT = "rubbing-pipeline/1.0 (local research; no contact)"
REQUEST_DELAY = 1.2  # 秒，每字之间的间隔，降低触发限流概率


def _search_svg(char, limit=1):
    """返回该字的小篆图片直链（thumb.php，直接给 PNG）。"""
    from urllib.parse import quote
    direct = FILE_URL.format(char=quote(char))
    return [direct]


def fetch(chars, out_dir, attribution=None, limit=None, **kw):
    """chars: list of dict(id,char,trad)。返回 manifest 列表。"""
    os.makedirs(out_dir, exist_ok=True)
    results = []
    items = chars if limit is None else chars[:limit]
    session = make_session()
    session.headers.update({"User-Agent": USER_AGENT})
    delay = float(kw.get("delay", REQUEST_DELAY))
    n = len(items)
    for idx, c in enumerate(items, 1):
        ch = c.get("trad") or c.get("char")
        ch = _strip(ch)
        if not ch:
            continue
        urls = _search_svg(ch, limit=3)
        got = False
        for url in urls:
            # thumb.php 直接返回栅格化后的 PNG（512px 白底），无需 svg_to_png
            png_path = os.path.join(out_dir, f"wm_{c['id']}.png")
            if download_file(url, png_path, session=session) and normalize_png(png_path, size=160, keep_alpha=True):
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
        if idx % 20 == 0:
            print(f"  [wikimedia_seal] 已处理 {idx}/{n}，命中 {len(results)}")
        time.sleep(delay)
    return results


def _strip(v):
    if v is None:
        return ""
    return str(v).strip().strip("'\"")
