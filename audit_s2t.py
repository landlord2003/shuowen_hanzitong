# -*- coding: utf-8 -*-
"""全量简繁映射审计：以 zhconv(zh-hant) 为权威基准核查 characters.json 的 trad 字段。
判定当前 trad 合法当且仅当满足其一：
  A. cur == hant(char)                      —— 权威繁体
  B. convert(cur, zh-hans) == char           —— cur 是本字的合法繁体（多对一/异体）
  C. cur == char                             —— 本字即繁体（无需转换）
不满足者列为可疑，另行分类。
"""
import json, re
import zhconv

BASE = r"D:\WorkBuddy\projects\说文解字"
cj = json.load(open(BASE + r"\data\characters.json", encoding="utf-8"))
chars = cj["characters"]

BAD = []      # 可疑：cur 既非权威繁体，也非本字，且回简化也对不上
KEEP = []     # trad==char 但本字其实有繁体（漏转换，低优先）
for c in chars:
    ch = c["char"]
    cur = (c.get("trad") or "").strip()
    hant = zhconv.convert(ch, "zh-hant")
    try:
        back = zhconv.convert(cur, "zh-hans") if cur else ""
    except Exception:
        back = ""
    ok = (cur == hant) or (back == ch) or (cur == ch)
    if not ok:
        BAD.append({"char": ch, "cur": cur, "hant": hant, "back": back, "liushu": c.get("liushu", "")})
    elif cur == ch and hant != ch:
        KEEP.append({"char": ch, "hant": hant})

print("总字数:", len(chars))
print("可疑(需订正) trad:", len(BAD))
print("trad==char 但存在繁体(低优先):", len(KEEP))
json.dump(BAD, open(BASE + r"\_s2t_bad.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(KEEP, open(BASE + r"\_s2t_keep.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

lines = ["===== A. 可疑 trad（应订正） %d =====" % len(BAD)]
for m in BAD:
    lines.append("%s\t%s\t->\t%s" % (m["char"], m["cur"], m["hant"]))
lines.append("")
lines.append("===== B. trad==char 但本字有繁体（低优先） %d =====" % len(KEEP))
for m in KEEP:
    lines.append("%s\t%s" % (m["char"], m["hant"]))
open(BASE + r"\_s2t_report.txt", "w", encoding="utf-8").write("\n".join(lines))
print("已写 _s2t_report.txt")
