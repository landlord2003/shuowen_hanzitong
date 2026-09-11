# -*- coding: utf-8 -*-
"""深挖两条扩量路径：
   ① ACC 编号系列（j/b/s/L）——枚举空间与汉字映射方式
   ② 书体级/文献级分类（說文篆文字表 等）
"""
import os, re, sys, json, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
IDX = "https://commons.wikimedia.org/w/index.php?title={t}&action=render"
RAW = "https://commons.wikimedia.org/w/index.php?title={t}&action=raw"
S = make_session()
S.headers.update({"User-Agent": UA})


def fetch(url, retries=3):
    for i in range(retries):
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
    html = fetch(IDX.format(t=urllib.parse.quote("Category:" + name)))
    if html is None:
        return None
    raw = set(re.findall(r'File:([^"#/?]+?\.(?:svg|png))', html, re.I))
    return sorted({urllib.parse.unquote(x).replace("_", " ") for x in raw})


def report_cat(name):
    fs = files_in(name)
    if fs is None:
        print(f"\n【{name}】取页失败\n"); return None
    print(f"\n【{name}】共 {len(fs)} 文件")
    print("  前 14:", fs[:14])
    return fs


print("=" * 74)
print("① 书体级 / 文献级分类（按书体直抓，不依赖单字分类）")
print("=" * 74)
for c in ["Oracle bone script characters", "Bronze script characters",
          "Shuowen script characters", "Shuowen seal script radicals",
          "Shuowen Jiezi", "Oracle script characters",
          "Shang oracle script characters", "Western Zhou oracle script characters"]:
    report_cat(c)
    time.sleep(2)

print()
print("=" * 74)
print("② ACC 编号系列：文件页 action=raw 的映射内容")
print("=" * 74)
for t in ["File:ACC-B00001.svg", "File:ACC-b00001.svg", "File:ACC-j00001.svg",
          "File:ACC-s00001.svg", "File:ACC-L00001.svg"]:
    txt = fetch(RAW.format(t=urllib.parse.quote(t)))
    print(f"  {t:<26} -> {repr((txt or '')[:160])}")
    time.sleep(2)

print()
print("=" * 74)
print("③ 看「一」分类里 ACC 系列的完整清单（判断每字变体数量级）")
print("=" * 74)
fs = files_in("一") or []
acc = [f for f in fs if f.upper().startswith("ACC-") or re.search(r"ACC-", f, re.I)]
letters = {}
for f in acc:
    m = re.search(r"ACC-([a-zA-Z])", f)
    if m:
        letters[m.group(1)] = letters.get(m.group(1), 0) + 1
print(f"  「一」分类内 ACC 文件 {len(acc)} 个，按字母: {letters}")
print("  样例:", acc[:14])
