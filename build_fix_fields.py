#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""质量核验修复：
问题1：78字 original/modern/shuowen 三字段错位（510字原始数据 bug）→ 循环移位
问题2：212字 original 被回填成反切"XX切" → 重新提取玉篇/康熙正确首义
"""
import json
import re

BASE = r"D:\WorkBuddy\projects\说文解字"
CHARS = BASE + r"\data\characters.json"

data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]

# ========== 问题1：字段错位（modern 存了说文原文） ==========
MISPLACED = set(
    "厂了与个么已无比计以正世旧们用外主市出动有同因件向合设那如她远把报时利体作位近应这没社现表者其事些制和的所性实建织要战种重前觉院样根钱特部展通眼做着最就意数"
)

def extract_first_meaning(sw):
    """从说文原文提取首义（第一个'也'前，含'也'）"""
    idx = sw.find("也")
    if idx > 0:
        return sw[: idx + 1]
    return sw.split("。")[0]

n_fix1 = 0
for c in chars:
    if c["char"] in MISPLACED and c.get("modern"):
        old_orig = c.get("original", "")
        old_modern = c.get("modern", "")
        # 循环移位：modern←orig(今义), shuowen←modern(说文原文), original←说文首义
        c["modern"] = old_orig
        c["shuowen"] = old_modern
        c["original"] = extract_first_meaning(old_modern)
        n_fix1 += 1

print(f"问题1修复（字段错位）: {n_fix1} 字")

# ========== 问题2：反切当本义 → 重新提取 ==========
def extract_yupian_meaning(yp):
    """玉篇首义：最后一个非反切段"""
    if not yp:
        return ""
    parts = [p.strip() for p in yp.rstrip("。").split("。") if p.strip()]
    for p in reversed(parts):
        if "切" not in p and "音" not in p:
            return p
    return ""

def extract_kangxi_meaning(kx):
    """康熙首义：'音X。'后的释义"""
    if not kx:
        return ""
    m = re.search(r"音[一-龥]。([^。【]+)", kx)
    if m:
        return m.group(1).strip()
    # 无'音X'时，找'切。'或'切，'后的释义
    m = re.search(r"切[。，]\s*([^。【，]+)", kx)
    if m and "切" not in m.group(1):
        return m.group(1).strip()
    return ""

n_fix2 = 0
n_fix2_empty = 0
for c in chars:
    if "切（出" not in c.get("original", ""):
        continue
    yp = c.get("trace_yupian", "")
    kx = c.get("trace_kangxi", "")
    meaning = extract_yupian_meaning(yp) or extract_kangxi_meaning(kx)
    if meaning and len(meaning) > 1:
        # 判断来源
        src = "《玉篇》" if extract_yupian_meaning(yp) == meaning else "《康熙字典》"
        c["original"] = meaning + f"（出{src}）"
        n_fix2 += 1
    else:
        c["original"] = "（后起字，无古本义）"
        n_fix2_empty += 1

print(f"问题2修复（反切当本义）: 重新提取 {n_fix2} 字，改回无本义 {n_fix2_empty} 字")

json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 验证
for ch in ["了", "比", "有", "刁", "丫", "叭", "凹", "忙", "盹"]:
    c = next((x for x in chars if x["char"] == ch), None)
    if c:
        print(f"\n{ch}: 本义={c.get('original','')[:25]}")
        print(f"   今义={c.get('modern','')[:25]}")
        print(f"   说文={c.get('shuowen','')[:25]}")
