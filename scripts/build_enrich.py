#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""任务34：从 shuowen 数据库补全字段（反切/段玉裁注/异体重文）到 characters.json

注意：seal_character（小篆字形）字段已确认损坏（错位数据），不提取。
小篆字形改用 EVOBC 的 seal 书体图（已在页面"字形演变"中）。
"""
import json
import glob
import os

BASE = r"D:\WorkBuddy\projects\说文解字"
DATA_DIR = os.path.join(BASE, ".workbuddy", "charlist", "shuowen", "data")
MATCH = os.path.join(BASE, ".workbuddy", "charlist", "shuowen_match.json")
CHARS = os.path.join(BASE, "data", "characters.json")

# 1. 加载 shuowen 数据库，建立 wordhead -> entry
wordhead_map = {}
for f in glob.glob(os.path.join(DATA_DIR, "*.json")):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    wh = d.get("wordhead", "")
    wordhead_map[wh] = d

# 2. 加载匹配结果（char -> trad/wordhead）
match = json.load(open(MATCH, encoding="utf-8"))
match_by_char = {m["char"]: m for m in match}

# 3. 加载 characters.json
data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]

def format_duan_notes(entry):
    """段玉裁注：合并成可读文本"""
    notes = entry.get("duan_notes", [])
    if not notes:
        return ""
    parts = []
    for n in notes:
        expl = n.get("explanation", "").strip()
        note = n.get("note", "").strip()
        if expl and note:
            parts.append(f"〔{expl}〕{note}")
        elif note:
            parts.append(note)
        elif expl:
            parts.append(f"〔{expl}〕")
    return "／".join(parts)

def format_variants(entry):
    """异体重文：合并成可读文本"""
    variants = entry.get("variants", [])
    if not variants:
        return ""
    parts = []
    for v in variants:
        wh = v.get("wordhead", "").strip()
        expl = v.get("explanation", "").strip()
        if wh and expl:
            parts.append(f"{wh}（{expl}）")
        elif wh:
            parts.append(wh)
    return "；".join(parts)

# 4. 补全字段
n_fanqie = 0
n_duan = 0
n_variant = 0
for c in chars:
    m = match_by_char.get(c["char"])
    if not m or not m.get("matched"):
        continue
    wh = m.get("trad", "")
    entry = wordhead_map.get(wh)
    if not entry:
        continue
    fanqie = entry.get("pronunciation", "").strip()
    if fanqie:
        c["fanqie"] = fanqie
        n_fanqie += 1
    duan = format_duan_notes(entry)
    if duan:
        c["duan_note"] = duan
        n_duan += 1
    variant = format_variants(entry)
    if variant:
        c["variant"] = variant
        n_variant += 1

# 5. 写回
json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"补全完成：反切 {n_fanqie} 字，段玉裁注 {n_duan} 字，异体重文 {n_variant} 字")
print(f"总字数: {len(chars)}")

for ch in ["帝", "一", "龙", "妈"]:
    c = next((x for x in chars if x["char"] == ch), None)
    if c:
        print(f"\n=== {ch} ===")
        print(f"  反切: {c.get('fanqie','（无）')}")
        print(f"  段注: {c.get('duan_note','（无）')[:80]}")
        print(f"  异体: {c.get('variant','（无）')[:80]}")
