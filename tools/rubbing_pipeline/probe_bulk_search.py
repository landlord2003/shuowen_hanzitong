# -*- coding: utf-8 -*-
"""决定性测试：能否用 Special:Search 按文件名**批量枚举**全 Commons 的古文字形文件。

若可行，扩量成本从「逐字 8105 次查询」降到「几十次分页查询」。
"""
import os, re, sys, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
S = make_session()
S.headers.update({"User-Agent": UA})

BASE = ("https://commons.wikimedia.org/w/index.php?title=Special:Search"
        "&ns6=1&fulltext=1&limit={lim}&offset={off}&search={q}")


def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = S.get(url, timeout=40)
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 503):
                time.sleep(4 * (i + 1)); continue
            return ""
        except Exception:
            time.sleep(1)
    return None


def total_count(html):
    """从 'Results 1 – 50 of 12,345' 里取总数"""
    m = re.search(r"of\s+([\d,]+)\s*</", html) or \
        re.search(r"of\s+([\d,]+)", html)
    return int(m.group(1).replace(",", "")) if m else None


def files(html):
    return {urllib.parse.unquote(x).replace("_", " ")
            for x in re.findall(r'File:([^"#/?]+?\.(?:svg|png))', html, re.I)}


QUERIES = [
    ("intitle:bronze", "-金文"),
    ("intitle:oracle", "-甲骨"),
    ("intitle:seal", "-篆（含小篆/大篆）"),
    ("intitle:bigseal", "-大篆"),
    ("intitle:hanjian", "-汗簡"),
    ("intitle:clerical", "-隸書"),
    ("intitle:ACC-", "ACC 编号系列"),
    ("intitle:silk", "-簡帛"),
]

for q, label in QUERIES:
    html = fetch(BASE.format(lim=500, off=0, q=urllib.parse.quote(q)))
    if html is None:
        print(f"  {q:<22} 请求失败"); continue
    n = total_count(html)
    fs = files(html)
    print(f"  {q:<22} 全站命中 {str(n):>7} 个｜本页取到 {len(fs):>4}"
          f"｜样例 {sorted(fs)[:3]}")
    time.sleep(2)

print()
print("=" * 72)
print("分页验证：bronze 前 3 页是否稳定返回不同结果（可否大规模枚举）")
print("=" * 72)
seen = set()
for off in (0, 50, 100):
    html = fetch(BASE.format(lim=50, off=off, q=urllib.parse.quote("intitle:bronze")))
    fs = files(html or "")
    new = fs - seen
    seen |= fs
    print(f"  offset={off:<4} 本页 {len(fs):>3} 个｜新增 {len(new):>3}｜累计 {len(seen)}")
    print(f"      {sorted(new)[:5]}")
    time.sleep(2)
