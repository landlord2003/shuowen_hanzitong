# -*- coding: utf-8 -*-
"""诊断：验证 Wikimedia Commons 的 {汉字}-seal.svg 直链在你本机是否有效。
跑法：受管 python diag_wikimedia.py
走本机梯子 127.0.0.1:18081（sources.make_session 自动处理）。
"""
import sys, requests, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sources import make_session

# 用几个有代表性、且大概率有 ACC 小篆的字（含繁体）
TEST_CHARS = ["口", "日", "月", "水", "木", "人", "一", "說", "書", "龍", "山", "火"]

def probe(char):
    url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{char}-seal.svg"
    s = make_session()
    try:
        r = s.get(url, timeout=20, headers={"User-Agent": "rubbing-pipeline/1.0"}, allow_redirects=True)
        return r.status_code, len(r.content)
    except Exception as e:
        return "ERR", str(e)[:60]

if __name__ == "__main__":
    print("=== Wikimedia Commons {汉字}-seal.svg 直链诊断（走本机梯子）===")
    ok = 0
    for ch in TEST_CHARS:
        code, size = probe(ch)
        tag = "✅" if code == 200 else "❌"
        print(f"  {tag} {ch}-seal.svg  ->  HTTP {code}  {size}B")
        if code == 200:
            ok += 1
    print(f"\n命中 {ok}/{len(TEST_CHARS)}")
    if ok == 0:
        print("全部失败：可能是网络被墙，或 ACC 命名不是 {汉字}-seal.svg")
    else:
        print("有命中：说明直链有效，可以全量跑 wikimedia_seal 源")
