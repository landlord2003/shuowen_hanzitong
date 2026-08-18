# -*- coding: utf-8 -*-
"""修正 3500 字中扫描出的错误：字段错位、六书误判、本义问题。"""
import json

CHARS = r"D:\WorkBuddy\projects\说文解字\data\characters.json"

# 精确修复映射
FIX = {
    # A. 字段错位（前：三字段错位；其：modern 存了本义+演变）
    "前": {
        "original": "不行而進（前进）",
        "modern": "前面；从前",
        "shuowen": "不行而進謂之歬。从止在舟上。",
    },
    "其": {
        "modern": "代词；语气词",
    },
    # B. 六书误判
    "无": {"liushu": "形声"},
    "尤": {"liushu": "形声"},
    "少": {"liushu": "形声"},
    "斥": {"liushu": "形声"},
    "雪": {"liushu": "形声"},
    "康": {"liushu": "形声"},
    "向": {"liushu": "会意"},
    "路": {"liushu": "会意"},
    "为": {"liushu": "象形"},
    "凸": {"liushu": "象形"},
    "凹": {"liushu": "象形"},
    # C. 本义==今义（本义用说文首义）
    "军": {"original": "圜圍也（围圈驻扎，四千人一军）"},
    "绿": {"original": "帛青黃色也（青黄色丝帛）"},
    "静": {"original": "審也（明审）"},
    # D. 本义存引文（提取实质释义）
    "乏": {"original": "反正（不正）"},
    "武": {"original": "武力（止戈为武）"},
    "畜": {"original": "田畜（畜养）"},
    # E. 轻微重复
    "就": {"original": "高也"},
    "切": {"modern": "切割；迫切"},
}

data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]
applied = []
for c in chars:
    if c["char"] in FIX:
        for k, v in FIX[c["char"]].items():
            c[k] = v
        applied.append(c["char"])

json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"已修复 {len(applied)} 字:", "".join(applied))

# 验证
for ch in applied:
    c = next(x for x in chars if x["char"] == ch)
    print(f"  {ch}: 六书={c.get('liushu','')} 本义={c.get('original','')[:20]} 今义={c.get('modern','')[:20]}")
