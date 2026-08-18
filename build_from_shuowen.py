# -*- coding: utf-8 -*-
"""从说文数据库匹配结果，程序化推导字段：
- trad / shuowen / pinyin：直接取自说文（权威）
- liushu（六书）：从说文原文构形句式推导
- original（本义）：从说文原文第一句释义提取
输出 3500 字的「权威字段」中间结果 authoritative_fields.json
"""
import json
import os
import re

BASE = r"D:\WorkBuddy\projects\说文解字"
MATCH = os.path.join(BASE, ".workbuddy", "charlist", "shuowen_match.json")
OUT = os.path.join(BASE, ".workbuddy", "charlist", "authoritative_fields.json")

def clean_pinyin(p):
    """清洗拼音：IPA ɡ→g，去空格"""
    return p.replace("ɡ", "g").replace(" ", "").strip()

def derive_liushu(exp):
    """从说文构形句式推导六书"""
    if "象形" in exp or ("象" in exp and "形" in exp):
        return "象形"
    if "指事" in exp:
        return "指事"
    if "聲" in exp or "声" in exp:
        return "形声"
    if "从" in exp:
        return "会意"
    return ""

def extract_original(exp):
    """提取本义：说文第一句释义（去掉构形'从X'部分）"""
    # 找 '从' 构形起始位置
    m = re.search(r"[，,。]\s*从", exp)
    end = m.start() + 1 if m else len(exp)
    first = exp[:end]
    # 去掉末尾句号
    first = first.rstrip("。，,")
    # 去掉 '凡X之屬' 之类
    first = re.sub(r"凡[^。]*屬[^。]*。?", "", first)
    first = first.strip("。，, ").strip()
    if not first:
        first = exp.split("。")[0]
    return first

r = json.load(open(MATCH, encoding="utf-8"))
out = {}
for x in r:
    ch = x["char"]
    if x["matched"]:
        shuowen = x["shuowen"].strip()
        out[ch] = {
            "trad": x["trad"],
            "shuowen": shuowen,
            "pinyin": clean_pinyin(x["pinyin"]),
            "fanqie": x["fanqie"],
            "liushu": derive_liushu(shuowen),
            "original": extract_original(shuowen),
            "shuowen_radical": x["shuowen_radical"],
            "matched": True,
        }
    else:
        out[ch] = {"trad": ch, "shuowen": "", "pinyin": "", "liushu": "", "original": "", "matched": False}

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
matched = sum(1 for v in out.values() if v["matched"])
with_liushu = sum(1 for v in out.values() if v["liushu"])
with_original = sum(1 for v in out.values() if v["original"])
print(f"总字数: {len(out)}")
print(f"有说文: {matched}")
print(f"六书推导成功: {with_liushu}")
print(f"本义提取成功: {with_original}")

# 六书分布
from collections import Counter
c = Counter(v["liushu"] for v in out.values() if v["liushu"])
print("六书分布:", dict(c))
print("已保存:", OUT)
