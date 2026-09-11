# -*- coding: utf-8 -*-
"""找「零噪声」的搜索式：目标是直接枚举全 Commons 的古文字形文件。"""
import os, re, sys, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
S = make_session()
S.headers.update({"User-Agent": UA})
BASE = ("https://commons.wikimedia.org/w/index.php?title=Special:Search"
        "&ns6=1&fulltext=1&limit=500&search={q}")


def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = S.get(url, timeout=45)
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 503):
                time.sleep(4 * (i + 1)); continue
            return ""
        except Exception:
            time.sleep(1)
    return None


def files(html):
    return {urllib.parse.unquote(x).replace("_", " ")
            for x in re.findall(r'File:([^"#/?]+?\.(?:svg|png))', html, re.I)}


def total(html):
    m = re.search(r"of\s+([\d,]+)", html)
    return int(m.group(1).replace(",", "")) if m else None


# 古文字形文件的特征：文件名以「汉字-后缀.svg」结尾。
# 试多种查询式，看哪种既高召回又低噪声。
QFORMS = [
    ('intitle:"-bigseal.svg"', "大篆 短语式"),
    ('intitle:"-hanjian.svg"', "汗簡 短语式"),
    ('intitle:"-oracle.svg"', "甲骨 短语式"),
    ('intitle:"-bronze.svg"', "金文 短语式"),
    ('intitle:"-seal.svg"', "篆 短语式"),
    ('intitle:"-silk.svg"', "簡帛 短语式"),
    ('deepcat:"Ancient Chinese characters"', "深度分类树"),
    ('deepcat:"Oracle bone script"', "深度分类·甲骨"),
    ('deepcat:"Seal script"', "深度分类·篆"),
]

SUF = re.compile(r"[-_](oracle|bronze|seal|bigseal|silk|slip|hanjian|clerical|ancient)[-.]", re.I)

print("=" * 78)
print("查询式对比（ns6=文件命名空间，limit=500）")
print("=" * 78)
for q, label in QFORMS:
    html = fetch(BASE.format(q=urllib.parse.quote(q)))
    if html is None:
        print(f"  {label:<16} 请求失败"); continue
    fs = files(html)
    good = {f for f in fs if SUF.search(f.replace(" ", "_"))}
    print(f"  {label:<16} 全站命中 {str(total(html)):>7}｜本页 {len(fs):>4}｜"
          f"其中古文字形 {len(good):>4}｜纯度 {len(good)/max(1,len(fs))*100:>5.1f}%")
    if good:
        print(f"      样例: {sorted(good)[:5]}")
    time.sleep(2)
