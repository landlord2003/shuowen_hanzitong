# -*- coding: utf-8 -*-
"""量化：Commons 每字分类里，我们当前抓取规则漏掉了多少字形变体。

当前规则只认后缀 -oracle/-bronze/-seal/-bigseal/-silk/-slip，
且每个 script 只留 1 张（最短文件名）。本脚本列出各字分类下**全部**疑似古文字形文件，
统计被丢弃的变体种类。
"""
import os, re, sys, json, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
IDX = "https://commons.wikimedia.org/w/index.php?title={t}&action=render"
S = make_session()
S.headers.update({"User-Agent": UA})

CURRENT = ("-oracle", "-bronze", "-seal", "-bigseal", "-silk", "-slip")
# 疑似"书体/时期"后缀关键词（含未接入的）
ANY = re.compile(r"-([a-z][a-z0-9-]{2,24})\.(?:svg|png)$", re.I)


def cat_html(name):
    url = IDX.format(t=urllib.parse.quote("Category:" + name))
    for i in range(3):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 503):
                time.sleep(4 * (i + 1)); continue
            return ""
        except Exception:
            time.sleep(2)
    return None


def files_in(name):
    html = cat_html(name)
    if html is None:
        return None
    raw = set(re.findall(r'File:([^"#/?]+?\.(?:svg|png))', html, re.I))
    return sorted({urllib.parse.unquote(x).replace("_", " ") for x in raw})


SAMPLES = ["馬", "水", "一", "車", "貝", "女", "魚", "鳥", "龍", "門"]

print("=" * 74)
print("A) 抽样：每个字分类下的全部文件 -> 当前规则能认 vs 漏掉")
print("=" * 74)
all_suffix = {}
total_files = 0
total_cur = 0
for ch in SAMPLES:
    fs = files_in(ch)
    if fs is None:
        print(f"{ch}: 取页失败"); continue
    cur = [f for f in fs if any(s in f.lower() for s in CURRENT)]
    others = [f for f in fs if f not in cur]
    total_files += len(fs); total_cur += len(cur)
    print(f"\n【{ch}】分类内共 {len(fs)} 文件｜当前规则可认 {len(cur)}｜其它 {len(others)}")
    print("  当前可认:", cur[:8])
    print("  其它文件:", others[:12])
    for f in others:
        m = ANY.search(f.replace(" ", "_"))
        if m:
            all_suffix[m.group(1).lower()] = all_suffix.get(m.group(1).lower(), 0) + 1
    time.sleep(2)

print()
print("=" * 74)
print("B) 非当前规则文件的「后缀词」频次（= 潜在可接入的新书体/变体）")
print("=" * 74)
for k, v in sorted(all_suffix.items(), key=lambda x: -x[1])[:40]:
    print(f"  {k:<26} {v}")

print()
print("=" * 74)
print("C) 书体级 / 文献级分类：按书体直接抓（不依赖单字分类）")
print("=" * 74)
for c in ["Oracle bone script characters", "Bronze script characters",
          "Shuowen script characters", "Shuowen seal script radicals",
          "Oracle script radicals (SVG)", "Jiaguwen heji",
          "Inscriptions on Chinese bronzes"]:
    fs = files_in(c)
    if fs is None:
        print(f"\n【{c}】取页失败"); time.sleep(2); continue
    print(f"\n【{c}】共 {len(fs)} 文件")
    print("  样例:", fs[:10])
    time.sleep(2)
