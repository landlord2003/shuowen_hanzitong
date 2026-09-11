# -*- coding: utf-8 -*-
"""决定性测试：挑「当前没有某书体字形」的字，看其 Commons 分类里是否藏着被漏掉的 ACC 文件。

这直接回答「修 ACC 大小写能提升多少覆盖率」。
"""
import os, re, sys, json, time, random, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
IDX = "https://commons.wikimedia.org/w/index.php?title={t}&action=render"
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_glyph_tmp")
CHARS = r"E:\Workbuddy\说文解字\data\characters.json"

S = make_session()
S.headers.update({"User-Agent": UA})


def have_map():
    """id -> set(script)，来自 _glyph_tmp 现有产物 + dataset 已知内容"""
    have = {}
    for fn in os.listdir(TMP):
        m = re.match(r"(?:wa|wb|wm)_(\d+)_(\S+)\.png$", fn)
        if m:
            have.setdefault(m.group(1), set()).add(m.group(2))
        m2 = re.match(r"(?:gw)_(\d+)\.png$", fn)
        if m2:
            have.setdefault(m2.group(1), set()).add("glyphwiki")
    return have


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


def main(target_script="bronze", n=60, seed=7):
    chars = json.load(open(CHARS, encoding="utf-8"))["characters"]
    have = have_map()
    gap = [c for c in chars if target_script not in have.get(str(c["id"]), set())]
    print(f"[{target_script}] 缺失该字形的字：{len(gap)} / {len(chars)}"
          f"（覆盖率 {(len(chars)-len(gap))/len(chars)*100:.1f}%）")
    random.seed(seed)
    sample = random.sample(gap, min(n, len(gap)))

    acc_letter = {}
    rescuable = 0          # 分类页里有 ACC 但当前被丢弃
    rescuable_by_letter = {}
    tot = 0
    t0 = time.time()
    for i, c in enumerate(sample, 1):
        html = page(c["char"])
        if html is None:
            continue
        tot += 1
        letters = set(re.findall(r"ACC-([a-zA-Z])(\d{3,6})\.svg", html))
        for L in letters:
            acc_letter[L] = acc_letter.get(L, 0) + 1
        # 大写 B / 小写 b 都算金文来源
        if {"B", "b"} & letters:
            rescuable += 1
            for L in letters & {"B", "b"}:
                rescuable_by_letter[L] = rescuable_by_letter.get(L, 0) + 1
        if i % 20 == 0:
            print(f"  …{i}/{len(sample)}  {(time.time()-t0):.0f}s  可救 {rescuable}", flush=True)
    print()
    print("=" * 70)
    print(f"抽样 {tot} 个「无 {target_script}」的字")
    print("=" * 70)
    print(f"  分类页 ACC 字母频次: {dict(sorted(acc_letter.items(), key=lambda x:-x[1]))}")
    print(f"  含 ACC 金文(大小写)的字: {rescuable}  ({rescuable/max(1,tot)*100:.1f}%)"
          f"  按字母 {rescuable_by_letter}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bronze",
         int(sys.argv[2]) if len(sys.argv) > 2 else 60)
