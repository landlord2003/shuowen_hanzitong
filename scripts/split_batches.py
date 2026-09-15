# -*- coding: utf-8 -*-
"""把 extend_full.json 的 4605 字分割成 N 批，供并行 Agent 生成 modern/evolution/stroke。
每批输出 extend_batch_N.json，含 char + 权威字段 + 空 modern/evolution/stroke。
"""
import json

BASE = r"D:\WorkBuddy\projects\说文解字"
FULL = BASE + r"\.workbuddy\charlist\extend_full.json"

recs = json.load(open(FULL, encoding="utf-8"))
N_BATCH = 6
size = len(recs)
per = (size + N_BATCH - 1) // N_BATCH

for i in range(N_BATCH):
    chunk = recs[i*per:(i+1)*per]
    # 只保留 char + 权威参考字段 + 空目标字段
    out = []
    for r in chunk:
        out.append({
            "char": r["char"],
            "pinyin": r.get("pinyin", ""),
            "liushu": r.get("liushu", ""),
            "original": r.get("original", ""),
            "shuowen": r.get("shuowen", ""),
            "modern": "",
            "evolution": "",
            "stroke": 0,
        })
    json.dump(out, open(f"{BASE}\\.workbuddy\\charlist\\extend_batch_{i+1}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"batch_{i+1}: {len(out)} 字 ({out[0]['char']}...{out[-1]['char']})")
