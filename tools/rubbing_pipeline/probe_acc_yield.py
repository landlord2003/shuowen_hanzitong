# -*- coding: utf-8 -*-
"""抽样估算：修正 ACC 大小写 + 扩展后缀词后，能多覆盖多少字 / 多少字形。

抽 N 个字，走 index.php 取分类页，按「当前规则」与「放宽规则」分别统计，
得出覆盖率增幅估计。
"""
import os, re, sys, json, time, random, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
IDX = "https://commons.wikimedia.org/w/index.php?title={t}&action=render"
CHARS = r"E:\Workbuddy\说文解字\data\characters.json"

S = make_session()
S.headers.update({"User-Agent": UA})

# —— 当前规则 ——
CUR_ACC = {"j": "oracle-bone", "b": "bronze", "s": "seal", "L": "seal"}
CUR_NAMES = [("-oracle", "oracle-bone"), ("-bronze", "bronze"), ("-seal", "seal"),
             ("-bigseal", "seal"), ("-silk", "bamboo-silk"), ("-slip", "bamboo-silk")]

# —— 放宽规则（拟议）——
NEW_ACC = {"j": "oracle-bone", "J": "oracle-bone",
           "b": "bronze", "B": "bronze",
           "s": "seal", "S": "seal",
           "L": "bigseal", "l": "bigseal"}
NEW_NAMES = [("-oracle", "oracle-bone"), ("-bronze", "bronze"),
             ("-seal", "seal"), ("-bigseal", "bigseal"),
             ("-silk", "bamboo-silk"), ("-slip", "bamboo-silk"),
             ("-hanjian", "hanjian"), ("-zhou", "bronze")]

NAMEPAT = re.compile(r"File:([^\"#/]*?(?:-oracle|-bronze|-seal|-bigseal|-silk|-slip|-hanjian|-zhou)[^\"#/]*)\.svg", re.I)


def page(ch):
    url = IDX.format(t=urllib.parse.quote("Category:" + ch))
    for i in range(3):
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


def analyze(html):
    """返回 (当前script集合, 放宽后script集合, ACC字母集合)"""
    cur, new = set(), set()
    for letter, num in re.findall(r"ACC-([a-zA-Z])(\d{3,6})\.svg", html):
        if letter in CUR_ACC:
            cur.add(CUR_ACC[letter])
        if letter in NEW_ACC:
            new.add(NEW_ACC[letter])
    for base in NAMEPAT.findall(html):
        base = urllib.parse.unquote(base)
        low = base.lower()
        for suf, sc in CUR_NAMES:
            if suf in low:
                cur.add(sc); break
        for suf, sc in NEW_NAMES:
            if suf in low:
                new.add(sc); break
    return cur, new, set(re.findall(r"ACC-([a-zA-Z])\d{3,6}\.svg", html))


def main(n=80, seed=11):
    chars = json.load(open(CHARS, encoding="utf-8"))["characters"]
    random.seed(seed)
    sample = random.sample(chars, min(n, len(chars)))
    tot_cur = tot_new = 0
    hit_cur = hit_new = 0
    letters = {}
    gain_detail = {}
    t0 = time.time()
    for i, c in enumerate(sample, 1):
        html = page(c["char"])
        if html is None:
            continue
        cur, new, ls = analyze(html)
        for L in ls:
            letters[L] = letters.get(L, 0) + 1
        tot_cur += len(cur); tot_new += len(new)
        if cur: hit_cur += 1
        if new: hit_new += 1
        for s in (new - cur):
            gain_detail[s] = gain_detail.get(s, 0) + 1
        if i % 20 == 0:
            print(f"  …{i}/{len(sample)}  {(time.time()-t0):.0f}s", flush=True)

    N = len(sample)
    print()
    print("=" * 70)
    print(f"抽样 {N} 字（随机种子 {seed}）")
    print("=" * 70)
    print(f"  命中字(当前规则): {hit_cur}  ({hit_cur/N*100:.1f}%)")
    print(f"  命中字(放宽规则): {hit_new}  ({hit_new/N*100:.1f}%)")
    print(f"  字形总数(当前):   {tot_cur}")
    print(f"  字形总数(放宽):   {tot_new}   (+{tot_new-tot_cur}, +{(tot_new-tot_cur)/max(1,tot_cur)*100:.1f}%)")
    print(f"  ACC 字母出现频次: {dict(sorted(letters.items(), key=lambda x:-x[1]))}")
    print(f"  新增字形按书体:   {dict(sorted(gain_detail.items(), key=lambda x:-x[1]))}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    main(n)
