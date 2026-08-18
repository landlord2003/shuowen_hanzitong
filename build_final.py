# -*- coding: utf-8 -*-
"""合并所有数据源 → 3500 字 characters.json
数据源优先级（字段级）：
- trad/pinyin/shuowen/liushu/original: 说文数据库(authoritative) > 现有510 > 模型202 > 后起字fallback
- radical/radical_name/stroke/modern/evolution/category: gen_part(2818) > 现有510 > 模型202
"""
import json
import os

BASE = r"D:\WorkBuddy\projects\说文解字"
CHARS_DIR = os.path.join(BASE, ".workbuddy", "charlist")

# 1. 加载数据源
level1 = [x.strip() for x in open(os.path.join(CHARS_DIR, "level1_txwdzxq.txt"), encoding="utf-8").read().split() if x.strip()]

auth = json.load(open(os.path.join(CHARS_DIR, "authoritative_fields.json"), encoding="utf-8"))  # char -> {trad,shuowen,pinyin,liushu,original,...}
existing = {c["char"]: c for c in json.load(open(os.path.join(CHARS_DIR, "characters_510.json"), encoding="utf-8"))}

part = {}
for i in (1, 2):
    for c in json.load(open(os.path.join(CHARS_DIR, f"chars_part{i}.json"), encoding="utf-8")):
        part[c["char"]] = c

gen = {}
for i in range(1, 15):
    for c in json.load(open(os.path.join(CHARS_DIR, f"gen_part{i}.json"), encoding="utf-8")):
        gen[c["char"]] = c

# 2. opencc（后起字繁体）
cc = None
try:
    from opencc import OpenCC
    cc = OpenCC("s2t")
except Exception:
    pass

# 3. 合并
def pick(field, *sources):
    for src in sources:
        if not isinstance(src, dict):
            continue
        v = src.get(field)
        if v:
            return v
    return ""

result = []
for idx, ch in enumerate(level1, start=1):
    a = auth.get(ch, {})
    e = existing.get(ch, {})
    p = part.get(ch, {})
    g = gen.get(ch, {})

    trad = pick("trad", e, a, p)
    if not trad or trad == ch:  # 未匹配到繁体（后起字/字形差异），用 opencc 转换
        trad = (cc.convert(ch) if cc else ch) or ch
    shuowen = pick("shuowen", e, a, p)
    pinyin = pick("pinyin", e, a, p)
    liushu = pick("liushu", e, a, p)
    original = pick("original", e, a, p)

    result.append({
        "id": idx,
        "char": ch,
        "trad": trad,
        "pinyin": pinyin,
        "radical": pick("radical", e, g, p),
        "radical_name": pick("radical_name", e, g, p),
        "stroke": pick("stroke", e, g, p),
        "liushu": liushu,
        "original": original,
        "modern": pick("modern", e, g, p),
        "shuowen": shuowen if shuowen else "（后起字，《说文》未收）",
        "evolution": pick("evolution", e, g, p),
        "category": pick("category", e, g, p) or "其他",
    })

# 4. 统计
n_shuowen = sum(1 for c in result if c["shuowen"] and "（后起字" not in c["shuowen"])
n_pinyin = sum(1 for c in result if c["pinyin"])
n_liushu = sum(1 for c in result if c["liushu"])
n_radical = sum(1 for c in result if c["radical"])
n_stroke = sum(1 for c in result if c["stroke"])
n_modern = sum(1 for c in result if c["modern"])
n_evol = sum(1 for c in result if c["evolution"])

print(f"总字数: {len(result)}")
print(f"有说文原文: {n_shuowen}")
print(f"有拼音: {n_pinyin}")
print(f"有六书: {n_liushu}")
print(f"有部首: {n_radical}")
print(f"有笔画: {n_stroke}")
print(f"有今义: {n_modern}")
print(f"有演变: {n_evol}")

# 5. 写入 characters.json
out = {
    "meta": {
        "name": "说文解字 · 汉字知识库",
        "version": "2.0",
        "total_chars": len(result),
        "description": "3500 常用字，说文原文来自《说文解字》数据库（CC BY-NC-SA），六书/本义/今义/演变含模型生成，需核验",
        "fields": ["char", "trad", "pinyin", "radical", "radical_name", "stroke", "liushu", "original", "modern", "shuowen", "evolution", "category"],
    },
    "characters": result,
}

out_path = os.path.join(BASE, "data", "characters.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("已写入:", out_path)
