# -*- coding: utf-8 -*-
"""测两条「能扩覆盖」的新通道：
   A) Commons Special:Search（按文件名全文搜索）—— 能找到未被归入「Category:字」的文件
   B) zh.wiktionary 字条目 —— 中文维基词典的古文字形图
"""
import os, re, sys, json, time, random, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
S = make_session()
S.headers.update({"User-Agent": UA})

SEARCH = ("https://commons.wikimedia.org/w/index.php?title=Special:Search"
          "&ns6=1&fulltext=1&limit=50&search={q}")
ZHWIKT = "https://zh.wiktionary.org/w/index.php?title={t}&action=render"
ENWIKT = "https://en.wiktionary.org/w/index.php?title={t}&action=render"
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_glyph_tmp")
CHARS = r"E:\Workbuddy\说文解字\data\characters.json"


def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 503):
                time.sleep(3 * (i + 1)); continue
            return ""
        except Exception:
            time.sleep(1)
    return None


def have_map():
    have = {}
    for fn in os.listdir(TMP):
        m = re.match(r"(?:wa|wb|wm)_(\d+)_(\S+)\.png$", fn)
        if m:
            have.setdefault(m.group(1), set()).add(m.group(2))
    return have


print("=" * 72)
print("A) Commons Special:Search 可达性与产出")
print("=" * 72)
for q in ["馬-bronze", "intitle:馬-oracle", "馬 seal script"]:
    html = fetch(SEARCH.format(q=urllib.parse.quote(q)))
    if html is None:
        print(f"  [{q}] 请求失败"); continue
    files = set(re.findall(r'File:([^"#/?]+?\.(?:svg|png))', html, re.I))
    print(f"  [{q}] bytes={len(html)}  命中文件 {len(files)}")
    print(f"      {sorted({urllib.parse.unquote(x) for x in files})[:8]}")
    time.sleep(2)

print()
print("=" * 72)
print("B) 抽样：对「无金文」的字，Search 能否找到 Category 里没有的文件")
print("=" * 72)
chars = json.load(open(CHARS, encoding="utf-8"))["characters"]
have = have_map()
gap = [c for c in chars if "bronze" not in have.get(str(c["id"]), set())]
random.seed(3)
sample = random.sample(gap, 15)
extra = 0
t0 = time.time()
for i, c in enumerate(sample, 1):
    q = f"{c['char']}-bronze"
    html = fetch(SEARCH.format(q=urllib.parse.quote(q)))
    if not html:
        continue
    files = {urllib.parse.unquote(x) for x in re.findall(r'File:([^"#/?]+?\.(?:svg|png))', html, re.I)}
    hits = [f for f in files if "bronze" in f.lower()]
    if hits:
        extra += 1
        print(f"  {c['char']}: {hits[:3]}")
    time.sleep(2)
print(f"  -> 15 字中 {extra} 字找到 bronze 文件（{(time.time()-t0):.0f}s）")

print()
print("=" * 72)
print("C) zh.wiktionary vs Commons：同字古文字形文件对比")
print("=" * 72)
PAT = re.compile(r"([^\"/#?]*?(?:-oracle|-bronze|-seal|-bigseal|-silk|-slip|-hanjian|-clerical)[^\"/#?]*?\.(?:svg|png))", re.I)
for ch in ["馬", "水", "一", "車"]:
    zw = fetch(ZHWIKT.format(t=urllib.parse.quote(ch)))
    ew = fetch(ENWIKT.format(t=urllib.parse.quote(ch)))
    zf = {urllib.parse.unquote(x).replace("_", " ") for x in PAT.findall(zw or "")}
    ef = {urllib.parse.unquote(x).replace("_", " ") for x in PAT.findall(ew or "")}
    print(f"\n【{ch}】zh.wiktionary {len(zf)} 个 | en.wiktionary {len(ef)} 个")
    print("  zh:", sorted(zf)[:10])
    print("  en:", sorted(ef)[:10])
    time.sleep(2)
