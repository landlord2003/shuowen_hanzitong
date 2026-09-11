# -*- coding: utf-8 -*-
"""调研：除「汉字分类反查」外，Wikimedia 上还有哪些古文字形入口可扩量。

只做只读探测，全部走 index.php（不受 api.php 限流）。
"""
import os, re, sys, json, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
IDX = "https://commons.wikimedia.org/w/index.php?title={t}&action=render"
ZL_IDX = "https://zh.wikisource.org/w/index.php?title={t}&action=render"
EN_WIKT = "https://en.wiktionary.org/w/index.php?title={t}&action=render"

S = make_session()
S.headers.update({"User-Agent": UA})


def get(url, retries=2):
    for i in range(retries):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 503):
                time.sleep(5 * (i + 1))
                continue
            return ""
        except Exception as e:
            time.sleep(2)
    return None


def _tpl(host):
    return {"zhws": ZL_IDX, "wikt": EN_WIKT}.get(host, IDX)


def probe_cat(name, host="commons"):
    """取分类页，统计文件数与子分类数。"""
    tpl = _tpl(host)
    html = get(tpl.format(t=urllib.parse.quote("Category:" + name)))
    if html is None:
        return {"cat": name, "host": host, "status": "ERROR"}
    imgs = set(re.findall(r'File:([^"#/?]+?\.(?:svg|png|jpg|jpeg|gif))', html, re.I))
    subs = set(re.findall(r'Category:([^"#/?]+)"', html))
    return {"cat": name, "host": host, "bytes": len(html),
            "files": len(imgs), "subcats": len(subs),
            "sample": sorted(imgs)[:6], "some_subcats": sorted(subs)[:10]}


def probe_page(title, host="zhws"):
    tpl = _tpl(host)
    html = get(tpl.format(t=urllib.parse.quote(title)))
    if html is None:
        return {"title": title, "host": host, "status": "ERROR"}
    imgs = set(re.findall(r'(?:File:|src="[^"]*?/(?:commons|zh\.wikisource)/[^"]*?)([Aa]?[^"/]*?\.(?:svg|png|jpg))', html, re.I))
    return {"title": title, "host": host, "bytes": len(html), "imgs": len(imgs),
            "sample": sorted(imgs)[:8]}


CATS = [
    # 顶层与书体级（按书体抓，而不是按字抓）
    "Ancient Chinese characters",
    "Oracle bone script",
    "Oracle bone script characters",
    "Chinese bronze inscriptions",
    "Bronze script",
    "Seal script",
    "Shuowen Jiezi",
    "Chinese characters by ancient script",
    # 具体器物/文献
    "Oracle bones",
    "Chinese ritual bronzes",
]

print("=" * 70)
print("A) Commons 书体级 / 文献级分类探测")
print("=" * 70)
for c in CATS:
    r = probe_cat(c)
    print(json.dumps(r, ensure_ascii=False))
    time.sleep(2)

print()
print("=" * 70)
print("B) zh.wikisource 說文解字 / 康熙字典")
print("=" * 70)
for t in ["說文解字", "康熙字典", "說文解字/卷一"]:
    r = probe_page(t, host="zhws")
    print(json.dumps(r, ensure_ascii=False))
    time.sleep(2)

print()
print("=" * 70)
print("C) en.wiktionary 单字条目是否含古文字图")
print("=" * 70)
for t in ["一", "水", "馬"]:
    r = probe_page(t, host="wikt")
    print(json.dumps(r, ensure_ascii=False))
    time.sleep(2)
