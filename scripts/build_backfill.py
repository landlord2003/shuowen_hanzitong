#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""权威数据回填：
1. 后起字本义（original）：用玉篇首义 > 康熙首义 回填，替代"（后起字，无古本义）"
2. 六书（liushu）：修正指事字（说文不直接写"指事"，靠构形特征判断）
"""
import json
import re

BASE = r"D:\WorkBuddy\projects\说文解字"
CHARS = BASE + r"\data\characters.json"

data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]

# ========== 1. 后起字本义回填 ==========
HOUQI_KW = ["未收", "后起", "後起", "新造", "近代"]
n_backfill = 0
for c in chars:
    # 只处理后起字（shuowen 含后起关键词）
    if not any(k in c.get("shuowen", "") for k in HOUQI_KW):
        continue
    # 已回填过的（含"出《"来源标注）跳过
    if "出《" in c.get("original", ""):
        continue
    # 同名异义/新造字：古义≠今义，不能直接回填，保持现状（trace_note 已说明）
    if c.get("trace_note"):
        continue
    # 优先玉篇首义
    yp = c.get("trace_yupian", "")
    if yp and "。" in yp:
        meaning = yp.split("。", 1)[1].split("。")[0].strip()
        if meaning:
            c["original"] = meaning + "（出《玉篇》）"
            c["original_source"] = "《玉篇》(543年)"
            n_backfill += 1
            continue
    # 次选康熙首义
    kx = c.get("trace_kangxi", "")
    if kx:
        m = re.search(r"【[^】]+】\s*([^。，,；;【]+)", kx)
        if m:
            meaning = m.group(1).strip()
            if meaning and len(meaning) > 1:
                c["original"] = meaning + "（出《康熙字典》）"
                c["original_source"] = "《康熙字典》(1716年)"
                n_backfill += 1

print(f"后起字本义回填: {n_backfill} 字")

# ========== 2. 六书指事字修正 ==========
# 指事字清单（《说文》不直书"指事"，据构形特征判定）
ZHISHI = "一二三上下本末刃寸甘曰中天旦夕才之了于乎太小少大王玉示只亦立并凹凸丫卡卅卌四五六七八九十廿卅"
n_zhishi = 0
for c in chars:
    ch = c["char"]
    if ch in ZHISHI and c.get("liushu") in ("象形", "会意", ""):
        c["liushu"] = "指事"
        n_zhishi += 1

print(f"六书指事字修正: {n_zhishi} 字")

json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 验证
from collections import Counter
c = Counter(x["liushu"] for x in chars if x.get("liushu"))
print("六书分布(修正后):", dict(c))

for ch in ["妈", "爷", "他", "氧", "啡", "一", "上", "本"]:
    x = next((y for y in chars if y["char"] == ch), None)
    if x:
        print(f"{ch}: 六书={x['liushu']} 本义={x.get('original','')[:35]}")
