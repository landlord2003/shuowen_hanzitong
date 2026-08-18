# -*- coding: utf-8 -*-
"""合并说文数据库：把《说文解字》精确数据（说文原文/繁体/拼音）匹配到 3500 常用字表。
输出 shuowen_match.json，含每字的 trad/shuowen/pinyin/fanqie 及匹配状态。
"""
import json
import os
import glob

BASE = r"D:\WorkBuddy\projects\说文解字"
DATA_DIR = os.path.join(BASE, ".workbuddy", "charlist", "shuowen", "data")
LEVEL1 = os.path.join(BASE, ".workbuddy", "charlist", "level1_txwdzxq.txt")
OUT = os.path.join(BASE, ".workbuddy", "charlist", "shuowen_match.json")

# 1. 加载说文数据库 -> index -> entry
files = glob.glob(os.path.join(DATA_DIR, "*.json"))
index_map = {}
for f in files:
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    wh = d.get("wordhead", "")
    for idx in d.get("indexes", []):
        index_map.setdefault(idx, d)
    index_map.setdefault(wh, d)
print("说文 index 总数:", len(index_map))

# 2. 加载 3500 字表
level1 = [x.strip() for x in open(LEVEL1, encoding="utf-8").read().split() if x.strip()]
print("3500 字表:", len(level1))

# 3. opencc 简繁转换
converters = []
try:
    from opencc import OpenCC
    converters = [OpenCC("s2t"), OpenCC("s2twp")]
    print("opencc 可用")
except Exception as e:
    print("opencc 不可用，跳过简繁补充:", e)

def lookup(ch):
    """返回 (entry, trad) 或 (None, ch)"""
    if ch in index_map:
        return index_map[ch], ch
    for cc in converters:
        try:
            t = cc.convert(ch)
            if t in index_map:
                return index_map[t], t
        except Exception:
            pass
    return None, ch

# 4. 匹配
result = []
hit = 0
for ch in level1:
    entry, trad = lookup(ch)
    if entry:
        hit += 1
        result.append({
            "char": ch,
            "trad": entry.get("wordhead", trad),
            "shuowen": entry.get("explanation", ""),
            "pinyin": entry.get("pinyin_full", ""),
            "fanqie": entry.get("pronunciation", ""),
            "shuowen_radical": entry.get("radical", ""),
            "matched": True,
        })
    else:
        result.append({"char": ch, "trad": ch, "shuowen": "", "pinyin": "", "matched": False})

print("匹配成功:", hit, "/", len(level1), f"({hit/len(level1)*100:.1f}%)")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False)
print("已保存:", OUT)
