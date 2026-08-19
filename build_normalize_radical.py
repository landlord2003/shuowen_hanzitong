# -*- coding: utf-8 -*-
"""部首规范化：把简化偏旁统一映射到康熙正体部首（214部体系）。
消除"氵/水""扌/手"等同部首不同写法的问题，同步更新部首名。
"""
import json

BASE = r"D:\WorkBuddy\projects\说文解字"
CHARS = BASE + r"\data\characters.json"

# 简化偏旁 → 康熙正体部首
RADICAL_MAP = {
    "亻": "人", "刂": "刀", "忄": "心", "扌": "手", "氵": "水",
    "灬": "火", "犭": "犬", "纟": "糸", "艹": "艸", "讠": "言",
    "辶": "辵", "钅": "金", "饣": "食",
    # 简化字正体部首（部分现代部首在康熙里是繁体）
    "门": "門", "马": "馬", "鸟": "鳥", "鱼": "魚", "车": "車",
    "见": "見", "贝": "貝", "页": "頁", "龙": "龍", "龟": "龜",
    "冈": "岡", "长": "長", "韦": "韋", "风": "風", "飞": "飛",
    "齿": "齒", "齐": "齊", "麦": "麥", "卤": "鹵", "黾": "黽",
    "龀": "齒",
}

def normalize_radical(ch, rad):
    """返回 (正体部首, 部首名)"""
    if rad == "阝":
        # 左耳刀=阜，右耳刀=邑
        idx = ch.find("阝")
        if idx > 0 and idx >= len(ch) // 2:
            return "邑", "邑部"
        return "阜", "阜部"
    if rad in RADICAL_MAP:
        norm = RADICAL_MAP[rad]
        return norm, norm + "部"
    # 已是正体，直接用
    return rad, rad + "部"

data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]
n = 0
for c in chars:
    rad = c.get("radical", "")
    if rad in RADICAL_MAP or rad == "阝":
        new_rad, new_name = normalize_radical(c["char"], rad)
        c["radical"] = new_rad
        c["radical_name"] = new_name
        n += 1

json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
rads = Counter(c.get("radical", "") for c in chars)
print(f"规范化 {n} 字部首")
print(f"部首种类: {len(rads)}")
print("高频部首:", rads.most_common(15))
