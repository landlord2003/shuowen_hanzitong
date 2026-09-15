#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""六书交叉校验修正：
1. 47 个"从X声"形声字误标为会意/象形 → 改回形声（据说文构形）
2. 排除"象形兼声"有争议字（龙/求/秃/要/腰/禽/主）
"""
import json

BASE = r"D:\WorkBuddy\projects\说文解字"
CHARS = BASE + r"\data\characters.json"

# 明确的形声字（说文构形"从X聲/X亦聲/X省聲"，无"象形"异说）
XINGSHENG_FIX = [
    "化", "功", "去", "可", "皮", "发", "有", "成", "同", "年",
    "舌", "向", "次", "字", "阳", "阴", "形", "更", "体", "饮",
    "良", "者", "事", "到", "岩", "单", "春", "城", "思", "秋",
    "重", "复", "食", "将", "帝", "哭", "酒", "家", "黄", "野",
    "商", "朝", "暑", "量", "然", "福", "舞",
]

data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]

n_fix = 0
for c in chars:
    if c["char"] in XINGSHENG_FIX and c.get("liushu") in ("会意", "象形"):
        c["liushu"] = "形声"
        c["liushu_source"] = "《说文》构形（从X声）"
        n_fix += 1

json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
c = Counter(x["liushu"] for x in chars if x.get("liushu"))
print(f"形声修正: {n_fix} 字")
print("六书分布(修正后):", dict(c))

for ch in ["有", "帝", "家", "酒", "龙", "求"]:
    x = next((y for y in chars if y["char"] == ch), None)
    if x:
        print(f"{ch}: {x['liushu']}")
