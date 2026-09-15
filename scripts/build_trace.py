#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""任务35：给 683 个"未收"字补后起字溯源（玉篇/广韵/康熙字典）

三个关键发现（要在工具里说明）：
1. 康熙字典是集大成字书（整合玉篇/广韵/集韵/唐韵反切+释义）
2. 玉篇(543年)/广韵(1008年)提供更早字义
3. 音译字陷阱：啡=唾声、吨=气相冲、她=姐古文，不能直接套用
"""
import json
import csv
import os

BASE = r"D:\WorkBuddy\projects\说文解字"
DICT = os.path.join(BASE, ".workbuddy", "dict")
CHARS = os.path.join(BASE, "data", "characters.json")

# 1. 玉篇：字头 -> 内容
yupian = {}
for ln in open(os.path.join(DICT, "玉篇.txt"), encoding="utf-8"):
    if "\t" in ln:
        h, c = ln.split("\t", 1)
        h, c = h.strip(), c.strip()
        if h and c:
            yupian[h] = c

# 2. 广韵 CSV：字头 -> (反切, 释义)
guangyun = {}
with open(os.path.join(DICT, "廣韻全字表.csv"), encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    header = next(reader)
    i_head = header.index("廣韻字頭(覈校後)")
    i_fanqie = header.index("廣韻反切(覈校後)")
    i_meaning = header.index("廣韻釋義")
    for r in reader:
        if len(r) <= i_head:
            continue
        h = r[i_head].strip()
        if not h or h in guangyun:
            continue
        fq = r[i_fanqie].strip() if len(r) > i_fanqie else ""
        me = r[i_meaning].strip() if len(r) > i_meaning else ""
        guangyun[h] = (fq, me)

# 3. 康熙字典：字头 -> 内容
kangxi = {}
for fn in ["康熙字典_p1.txt", "康熙字典_p2.txt"]:
    for ln in open(os.path.join(DICT, fn), encoding="utf-8"):
        if "\t" in ln:
            h, c = ln.split("\t", 1)
            h, c = h.strip(), c.strip()
            if h and c and not h.startswith("#"):
                kangxi[h] = c

def kangxi_trim(content, maxlen=130):
    """康熙字典条目截取精华：去掉部首/笔画头，保留反切+首义"""
    # 去掉开头的【...集...】【...字部】和笔画信息，从反切【X韻】开始
    import re
    # 去掉 【子集上】【一字部】 一 ·康熙筆画：1 ·部外筆画：0 这类头部
    content = re.sub(r'^【[^】]+】【[^】]+】\s*', '', content)
    content = re.sub(r'^·康熙筆画：[^·]+·部外筆画：[^·]+·', '', content)
    content = content.strip()
    if len(content) > maxlen:
        content = content[:maxlen] + "…"
    return content

# 4. 加载 characters.json
data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]
# 后起字判定：统一覆盖各种格式（未收/后起/新造/近代）
HOUQI_KW = ["未收", "后起", "後起", "新造", "近代"]
houqi = [c for c in chars if any(k in c.get("shuowen", "") for k in HOUQI_KW)]

# 5. 补溯源
n_hit = 0
n_yupian = 0
n_guangyun = 0
n_kangxi = 0
for c in houqi:
    keys = [c["char"], c.get("trad", "")]
    # 玉篇
    yp = None
    for k in keys:
        if k in yupian:
            yp = yupian[k]
            break
    # 广韵
    gy = None
    for k in keys:
        if k in guangyun:
            gy = guangyun[k]
            break
    # 康熙
    kx = None
    for k in keys:
        if k in kangxi:
            kx = kangxi_trim(kangxi[k])
            break

    if yp or gy or kx:
        n_hit += 1
    if yp:
        c["trace_yupian"] = yp
        n_yupian += 1
    if gy:
        fq, me = gy
        c["trace_guangyun"] = f"{fq}，{me}".strip("，") if fq or me else ""
        if c.get("trace_guangyun"):
            n_guangyun += 1
        else:
            c.pop("trace_guangyun", None)
    if kx:
        c["trace_kangxi"] = kx
        n_kangxi += 1

# 6. 写回
json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"溯源补全：命中 {n_hit}/{len(houqi)} 字")
print(f"  玉篇 {n_yupian} 字，广韵 {n_guangyun} 字，康熙字典 {n_kangxi} 字")

# 抽查
for ch in ["妈", "爷", "他", "啡", "吨", "氧", "们"]:
    c = next((x for x in chars if x["char"] == ch), None)
    if c:
        print(f"\n=== {ch}（trad={c.get('trad','')}）===")
        print(f"  玉篇: {c.get('trace_yupian','（无）')[:60]}")
        print(f"  广韵: {c.get('trace_guangyun','（无）')[:60]}")
        print(f"  康熙: {c.get('trace_kangxi','（无）')[:60]}")
