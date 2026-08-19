# -*- coding: utf-8 -*-
"""部首彻底清理：统一到康熙 214 部（繁体正体）。
1. 简化偏旁/变体 → 繁体正体
2. 部首=字本身（非部首字）→ 重新猜测
"""
import json

BASE = r"D:\WorkBuddy\projects\说文解字"
CHARS = BASE + r"\data\characters.json"

# 康熙 214 部首（繁体正体）
KANGXI_214 = set(
    "一丨丶丿乙亅二亠人儿入八冂冖冫几凵刀力勹匕匚匸十卜卩厂厶又"
    "口囗土士夂夊夕大女子宀寸小尢尸屮山巛工己巾干幺广廴廾弋弓彐彡彳"
    "心戈戶手支攴文斗斤方无日曰月木欠止歹殳毋比毛氏气水火爪父爻爿片牙牛犬"
    "玄玉瓜瓦甘生用田疋疒癶白皮皿目矛矢石示禸禾穴立"
    "竹米糸缶网羊羽老而耒耳聿肉臣自至臼舌舛舟艮色艸虍虫血行衣襾"
    "見角言谷豆豕豸貝赤走足身車辛辰辵邑酉釆里"
    "金長門阜隶隹雨青非面革韋韭音頁風飛食首香"
    "馬骨高髟鬥鬯鬲鬼魚鳥鹵鹿麥麻黃黍黑黹黽鼎鼓鼠"
    "鼻齊齒龍龜龠"
)

# 简化偏旁/变体 → 繁体正体
MAP = {
    "氵": "水", "扌": "手", "艹": "艸", "亻": "人", "讠": "言",
    "纟": "糸", "辶": "辵", "忄": "心", "钅": "金", "犭": "犬",
    "灬": "火", "刂": "刀", "饣": "食",
    "门": "門", "马": "馬", "鸟": "鳥", "鱼": "魚", "车": "車",
    "见": "見", "贝": "貝", "页": "頁", "龙": "龍", "风": "風",
    "飞": "飛", "齿": "齒", "齐": "齊", "麦": "麥", "韦": "韋",
    "卤": "鹵", "龟": "龜", "黄": "黃", "黾": "黽", "长": "長",
    "礻": "示", "攵": "攴", "牜": "牛", "衤": "衣", "罒": "网",
    "丷": "八", "爫": "爪", "覀": "襾", "乛": "乙", "乚": "乙",
    "王": "玉", "月": "月", "疋": "疋",
}

# 重新猜测的偏旁优先级
GUESS_ORDER = [
    "钅", "氵", "艹", "扌", "讠", "纟", "亻", "忄", "犭", "灬",
    "刂", "辶", "饣", "礻", "衤", "牜", "罒", "攵", "女", "口",
    "木", "土", "山", "火", "石", "日", "目", "虫", "竹", "禾",
    "米", "言", "宀", "广", "疒", "酉", "足", "耳", "马", "鸟",
    "鱼", "车", "贝", "页", "见", "门", "风", "龙", "雨", "田",
]


def guess(ch):
    for bp in GUESS_ORDER:
        if bp in ch:
            return MAP.get(bp, bp)
    # 阝 特殊
    if "阝" in ch:
        idx = ch.find("阝")
        return "邑" if (idx > 0 and idx >= len(ch) // 2) else "阜"
    return ch[0]


data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]
n_map = 0
n_guess = 0
for c in chars:
    rad = c.get("radical", "")
    ch = c["char"]
    new_rad = None
    # 1. 简化偏旁/变体 → 正体
    if rad in MAP:
        new_rad = MAP[rad]
        n_map += 1
    # 2. 部首=字本身 且 非部首字 → 重新猜测
    elif rad == ch and ch not in KANGXI_214:
        new_rad = guess(ch)
        n_guess += 1
    if new_rad:
        c["radical"] = new_rad
        c["radical_name"] = new_rad + "部"

json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
rads = Counter(c.get("radical", "") for c in chars)
illegal = sum(v for k, v in rads.items() if k not in KANGXI_214)
print(f"简化偏旁映射: {n_map}, 重新猜测: {n_guess}")
print(f"部首种类: {len(rads)}, 非法部首剩: {illegal} 字")
print("高频部首:", rads.most_common(15))
