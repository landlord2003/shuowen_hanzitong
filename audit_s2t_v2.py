# -*- coding: utf-8 -*-
"""精算 331 处 trad 错配的连带影响：新旧《说文》归属条目是否变化。
输出 _s2t_detail.txt：char | oldTrad | newTrad | oldWH | newWH | 条目是否变化 | 显示用旧/新shuowen
"""
import json, os, glob, re
BASE = r"D:\WorkBuddy\projects\说文解字"
SW = os.path.join(BASE, ".workbuddy", "charlist", "shuowen", "data")

wordheadSet, entryByWH, varParent, indexToWH = set(), {}, {}, {}
for f in glob.glob(os.path.join(SW, "*.json")):
    try:
        e = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    wh = e.get("wordhead")
    if not wh:
        continue
    wordheadSet.add(wh); entryByWH[wh] = e
    for v in (e.get("variants") or []):
        vw = v.get("wordhead")
        if vw:
            varParent[vw] = wh
    for ix in (e.get("indexes") or []):
        indexToWH.setdefault(ix, wh)

bad = json.load(open(BASE + r"\_s2t_bad.json", encoding="utf-8"))
cj = json.load(open(BASE + r"\data\characters.json", encoding="utf-8"))
byChar = {c["char"]: c for c in cj["characters"]}

lines, same_entry, diff_entry, no_entry = [], 0, 0, 0
recs = []
for m in bad:
    ch, old = m["char"], m["cur"]
    new = m["hant"]
    oldWH = indexToWH.get(old) or (old if old in wordheadSet else None)
    newWH = new if new in wordheadSet else indexToWH.get(new)
    c = byChar.get(ch, {})
    oldSW = (c.get("shuowen") or "")[:26]
    if newWH is None:
        newSW = "(无《说文》条目)"
        cat = "no_entry"; no_entry += 1
    elif newWH == oldWH:
        newSW = "(同条目，shuowen不变)"
        cat = "same"; same_entry += 1
    else:
        newSW = (entryByWH.get(newWH, {}).get("explanation") or "")[:26]
        cat = "diff"; diff_entry += 1
    recs.append({"char": ch, "old": old, "new": new, "oldWH": oldWH, "newWH": newWH, "cat": cat})
    lines.append("%s\t%s→%s\t旧WH=%s\t新WH=%s\t%s\t旧:%s\t新:%s" % (ch, old, new, oldWH, newWH, cat, oldSW, newSW))

print("总数", len(bad), " 同条目:", same_entry, " 换条目:", diff_entry, " 无条目:", no_entry)
open(BASE + r"\_s2t_detail.txt", "w", encoding="utf-8").write("\n".join(lines))
json.dump(recs, open(BASE + r"\_s2t_recs.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
