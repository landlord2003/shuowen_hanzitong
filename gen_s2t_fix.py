# -*- coding: utf-8 -*-
"""生成简繁映射修复清单。
- 基准：zhconv(zh-hant)；允许 cur 能回简化到本字（异体合法）。
- index 构建采用 wordhead 优先（修正原 merge_shuowen.py 的 setdefault 覆盖问题）。
- overrides：卤→鹵（鹵 有《说文》字头，滷 无）、征→征（征为 𨒌 之或体，保持同条目）
- excludes：着（App 既有策略保留 著）
输出 _s2t_fix.json
"""
import json, os, glob, re
import zhconv

BASE = r"D:\WorkBuddy\projects\说文解字"
SW = os.path.join(BASE, ".workbuddy", "charlist", "shuowen", "data")

OVER = {"卤": "鹵", "征": "征"}
EXCL = {"着"}

wordheadSet, entryByWH, varParent = set(), {}, {}
rawIndex = {}
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
        if v.get("wordhead"):
            varParent[v["wordhead"]] = wh
    for ix in (e.get("indexes") or []):
        rawIndex.setdefault(ix, wh)
# wordhead 优先
indexToWH = dict(rawIndex)
for w in wordheadSet:
    indexToWH[w] = w


def clean_pinyin(p):
    return (p or "").replace("ɡ", "g").replace(" ", "").strip()


def derive_liushu(exp):
    if "象形" in exp or ("象" in exp and "形" in exp):
        return "象形"
    if "指事" in exp:
        return "指事"
    if "聲" in exp or "声" in exp:
        return "形声"
    if "从" in exp:
        return "会意"
    return ""


def extract_original(exp):
    m = re.search(r"[，,。]\s*从", exp)
    end = m.start() + 1 if m else len(exp)
    first = exp[:end].rstrip("。，,")
    first = re.sub(r"凡[^。]*屬[^。]*。?", "", first)
    first = first.strip("。，, ").strip()
    if not first:
        first = exp.split("。")[0]
    return first


cj = json.load(open(BASE + r"\data\characters.json", encoding="utf-8"))
fixes = []
manual = []
for c in cj["characters"]:
    ch = c["char"]
    if ch in EXCL:
        continue
    cur = (c.get("trad") or "").strip()
    hant = OVER.get(ch) or zhconv.convert(ch, "zh-hant")
    try:
        back = zhconv.convert(cur, "zh-hans") if cur else ""
    except Exception:
        back = ""
    if (cur == hant) or (back == ch) or (cur == ch and ch not in OVER):
        continue
    # 需修
    oldWH = indexToWH.get(cur) or (cur if cur in wordheadSet else None)
    newWH = hant if hant in wordheadSet else indexToWH.get(hant)
    if newWH is None:
        fixes.append({"char": ch, "old": cur, "new": hant, "mode": "trad_only", "newWH": None})
        manual.append(ch)
    elif newWH == oldWH:
        fixes.append({"char": ch, "old": cur, "new": hant, "mode": "trad_only", "newWH": newWH})
    else:
        e = entryByWH[newWH]
        exp = e.get("explanation", "")
        fixes.append({
            "char": ch, "old": cur, "new": hant, "mode": "full", "newWH": newWH,
            "shuowen": exp,
            "original": extract_original(exp),
            "liushu": derive_liushu(exp),
            "pinyin": clean_pinyin(e.get("pinyin_full", "")),
            "fanqie": e.get("pronunciation", ""),
            "radical": e.get("radical", ""),
        })

json.dump(fixes, open(BASE + r"\_s2t_fix.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
full = [f for f in fixes if f["mode"] == "full"]
print("需修总数:", len(fixes), " trad_only:", len(fixes) - len(full), " full:", len(full), " 无条目(手工):", len(manual))
print("full 明细:")
for f in full:
    print("  %s %s→%s  wh=%s  sw=%s" % (f["char"], f["old"], f["new"], f["newWH"], (f.get("shuowen") or "")[:30]))
print("无条目(需手工):", " ".join(manual))
