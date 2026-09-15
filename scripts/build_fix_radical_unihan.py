# -*- coding: utf-8 -*-
"""用 Unihan kRSUnicode 权威数据修正非法部首。
kRSUnicode 格式："167'.1" = 部首编号167(金) + 剩余1画
康熙214部首编号顺序映射到部首字。
"""
import json, re

BASE = r"D:\WorkBuddy\projects\说文解字"
CHARS = BASE + r"\data\characters.json"
UNIHAN = r"C:\Users\吴自强\AppData\Local\Temp\Unihan_IRGSources.txt"

# 康熙 214 部首编号顺序（1-214）
KANGXI_ORDER = list(
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
assert len(KANGXI_ORDER) == 214, f"部首表长度错误: {len(KANGXI_ORDER)}"
KANGXI_214 = set(KANGXI_ORDER)

# 解析 kRSUnicode：char -> 部首编号
def parse_unicode_hex(ch):
    return f"U+{ord(ch):04X}"

rad_index = {}  # char -> 部首字
with open(UNIHAN, encoding="utf-8") as f:
    for ln in f:
        if "kRSUnicode" not in ln:
            continue
        parts = ln.split("\t")
        if len(parts) < 3:
            continue
        cp = parts[0]  # U+XXXX
        val = parts[2].strip()
        m = re.match(r"(\d+)", val)  # 取部首编号（忽略 ' 变体标记 和 .剩余画）
        if not m:
            continue
        idx = int(m.group(1))
        if 1 <= idx <= 214:
            try:
                ch = chr(int(cp[2:], 16))
            except Exception:
                continue
            rad_index[ch] = KANGXI_ORDER[idx - 1]

print(f"解析 kRSUnicode: {len(rad_index)} 字")

data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]
n_fix = 0
n_miss = 0
miss_chars = []
for c in chars:
    rad = c.get("radical", "")
    ch = c["char"]
    if rad in KANGXI_214 and rad != ch:
        continue  # 已是合法部首
    # 用 Unihan 修正
    if ch in rad_index:
        new_rad = rad_index[ch]
        if new_rad != rad:
            c["radical"] = new_rad
            c["radical_name"] = new_rad + "部"
            n_fix += 1
    else:
        # Unihan 也没有，且部首非法
        if rad not in KANGXI_214:
            n_miss += 1
            miss_chars.append(ch)

json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
rads = Counter(c.get("radical", "") for c in chars)
illegal = sum(v for k, v in rads.items() if k not in KANGXI_214)
print(f"Unihan 修正: {n_fix} 字")
print(f"Unihan 也没有且非法: {n_miss} 字: {''.join(miss_chars[:50])}")
print(f"部首种类: {len(rads)}, 非法部首剩: {illegal} 字")
