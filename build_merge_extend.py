# -*- coding: utf-8 -*-
"""合并 4605 新增字到 characters.json，形成 8105 字。
1. 把 6 个批次的 modern/evolution/stroke 合并回 extend_full.json
2. 补后起字 shuowen 标注、缺部首/本义兜底
3. 追加到 characters.json（id 从 3501 起）
"""
import json

BASE = r"D:\WorkBuddy\projects\说文解字"
FULL = BASE + r"\.workbuddy\charlist\extend_full.json"
CHARS = BASE + r"\data\characters.json"

# 1. 读 extend_full + 6 批次
recs = json.load(open(FULL, encoding="utf-8"))
batch_map = {}
for i in range(1, 7):
    for r in json.load(open(f"{BASE}\\.workbuddy\\charlist\\extend_batch_{i}.json", encoding="utf-8")):
        batch_map[r["char"]] = r

# 2. 合并 modern/evolution/stroke
n_modern = 0
for r in recs:
    b = batch_map.get(r["char"])
    if b:
        r["modern"] = b.get("modern", "")
        r["evolution"] = b.get("evolution", "")
        r["stroke"] = b.get("stroke", 0)
        if r["modern"]:
            n_modern += 1

# 3. 兜底处理
RADICAL_GUESS = "钅氵艹扌讠纟亻女口木土山火王石日忄目虫竹禾米言辶阝宀广门马鸟鱼犭"
def guess_radical(ch):
    for r in RADICAL_GUESS:
        if r in ch:
            return r, r + "旁"
    return ch[0], ch[0] + "部"

n_shuowen = 0
n_orig = 0
n_rad = 0
for r in recs:
    # 后起字 shuowen 标注
    if not r.get("shuowen"):
        r["shuowen"] = "（后起字，《说文》未收）"
        n_shuowen += 1
    # 后起字本义兜底（用今义第一义项）
    if not r.get("original"):
        modern = r.get("modern", "")
        if modern:
            first = modern.split("；")[0].split(";")[0]
            r["original"] = first + "（后起字，无古本义）"
        else:
            r["original"] = "（后起字，无古本义）"
        n_orig += 1
    # 缺部首兜底
    if not r.get("radical"):
        rad, rad_name = guess_radical(r["char"])
        r["radical"] = rad
        r["radical_name"] = rad_name
        n_rad += 1

json.dump(recs, open(FULL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"合并 modern: {n_modern}")
print(f"后起字 shuowen 标注: {n_shuowen}")
print(f"后起字本义兜底: {n_orig}")
print(f"缺部首兜底: {n_rad}")

# 4. 合并到 characters.json
data = json.load(open(CHARS, encoding="utf-8"))
existing = data["characters"]
existing_chars = set(c["char"] for c in existing)

# 字段顺序（与现有 3500 字对齐）
FIELDS = ["id", "char", "trad", "pinyin", "radical", "radical_name", "stroke",
          "liushu", "original", "modern", "shuowen", "evolution", "category",
          "fanqie", "duan_note", "variant",
          "trace_kangxi", "trace_yupian", "trace_guangyun", "trace_note"]

n_add = 0
for idx, r in enumerate(recs, start=len(existing) + 1):
    if r["char"] in existing_chars:
        continue
    entry = {"id": idx, "char": r["char"], "trad": r.get("trad", r["char"]),
             "pinyin": r.get("pinyin", ""), "radical": r.get("radical", ""),
             "radical_name": r.get("radical_name", ""), "stroke": r.get("stroke", 0),
             "liushu": r.get("liushu", ""), "original": r.get("original", ""),
             "modern": r.get("modern", ""), "shuowen": r.get("shuowen", ""),
             "evolution": r.get("evolution", ""), "category": r.get("category", "抽象"),
             "fanqie": r.get("fanqie", ""), "duan_note": r.get("duan_note", ""),
             "variant": r.get("variant", ""),
             "trace_kangxi": r.get("trace_kangxi", ""),
             "trace_yupian": r.get("trace_yupian", ""),
             "trace_guangyun": r.get("trace_guangyun", "")}
    if r.get("original_source"):
        entry["original_source"] = r["original_source"]
    existing.append(entry)
    n_add += 1

data["characters"] = existing
data["meta"]["total_chars"] = len(existing)
json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"追加 {n_add} 字，总字数: {len(existing)}")
