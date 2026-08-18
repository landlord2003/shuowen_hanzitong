# -*- coding: utf-8 -*-
"""扩展 8105 字：为 4605 新增字生成权威字段（说文+康熙+玉篇+广韵+opencc）。

输出 .workbuddy/charlist/extend_authoritative.json，含每字的：
  trad/shuowen/pinyin/fanqie/duan_note/variant/liushu/original（说文匹配的字）
  radical/radical_name（康熙【X字部】提取）
  trace_kangxi/trace_yupian/trace_guangyun（后起字溯源）

剩余字段（modern/evolution/category/stroke）留待模型生成。
"""
import json, os, re, glob, csv
from opencc import OpenCC

BASE = r"D:\WorkBuddy\projects\说文解字"
DATA_DIR = os.path.join(BASE, ".workbuddy", "charlist", "shuowen", "data")
DICT = os.path.join(BASE, ".workbuddy", "dict")
TO_ADD = os.path.join(BASE, ".workbuddy", "charlist", "to_add_4605.txt")
OUT = os.path.join(BASE, ".workbuddy", "charlist", "extend_authoritative.json")

# ============ 1. 说文数据库 ============
index_map = {}
wordhead_map = {}
for f in glob.glob(os.path.join(DATA_DIR, "*.json")):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    wh = d.get("wordhead", "")
    wordhead_map[wh] = d
    for idx in d.get("indexes", []):
        index_map.setdefault(idx, d)
    index_map.setdefault(wh, d)

cc_s2t = OpenCC("s2t")
cc_s2twp = OpenCC("s2twp")

def lookup(ch):
    if ch in index_map:
        return index_map[ch], ch
    for c in (cc_s2t, cc_s2twp):
        t = c.convert(ch)
        if t in index_map:
            return index_map[t], t
    return None, ch

# ============ 2. 康熙字典 ============
kangxi = {}
for fn in ["康熙字典_p1.txt", "康熙字典_p2.txt"]:
    for ln in open(os.path.join(DICT, fn), encoding="utf-8"):
        if "\t" in ln:
            h, c = ln.split("\t", 1)
            h, c = h.strip(), c.strip()
            if h and c and not h.startswith("#"):
                kangxi[h] = c

# ============ 3. 玉篇 ============
yupian = {}
for ln in open(os.path.join(DICT, "玉篇.txt"), encoding="utf-8"):
    if "\t" in ln:
        h, c = ln.split("\t", 1)
        h, c = h.strip(), c.strip()
        if h and c:
            yupian[h] = c

# ============ 4. 广韵 ============
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

# ============ 5. 工具函数 ============
def clean_pinyin(p):
    # 清洗 IPA：ɡ→g 及常见 IPA 字符
    ipa_map = {"ɡ": "g", "ɢ": "g", "ʁ": "r", "ŋ": "ng", "ɳ": "n", "ɲ": "n",
               "ɸ": "f", "β": "b", "θ": "th", "ð": "d", "ʃ": "sh", "ʒ": "zh",
               "ɕ": "x", "ʑ": "z", "ʂ": "sh", "ʐ": "r", "ɻ": "r", "ɥ": "y",
               "ɬ": "l", "ɮ": "l", "ʋ": "v", "ɹ": "r", "ɰ": "w"}
    for k, v in ipa_map.items():
        p = p.replace(k, v)
    return p.replace(" ", "").strip()

def derive_liushu(exp):
    if "指事" in exp:
        return "指事"
    if "象形" in exp or re.search(r"象[一-龥]*之形", exp):
        return "象形"
    if re.search(r"从[一-龥]+[声聲]", exp):
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

def format_duan(entry):
    parts = []
    for n in entry.get("duan_notes", []):
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
    parts = []
    for v in entry.get("variants", []):
        wh = v.get("wordhead", "").strip()
        expl = v.get("explanation", "").strip()
        if wh and expl:
            parts.append(f"{wh}（{expl}）")
        elif wh:
            parts.append(wh)
    return "；".join(parts)

def kangxi_trim(content, maxlen=130):
    content = re.sub(r"^【[^】]+】【[^】]+】\s*", "", content)
    content = re.sub(r"^·康熙筆画：[^·]+·部外筆画：[^·]+·", "", content)
    content = content.strip()
    if len(content) > maxlen:
        content = content[:maxlen] + "…"
    return content

def extract_radical(kx_content):
    """从康熙条目【X字部】提取部首和部首名"""
    m = re.search(r"【([一-龥]+)字部】", kx_content)
    if m:
        rad = m.group(1)
        return rad, rad + "部"
    return "", ""

# ============ 6. 主循环 ============
to_add = open(TO_ADD, encoding="utf-8").read().split()
result = []
for ch in to_add:
    entry, trad = lookup(ch)
    rec = {"char": ch, "trad": trad, "matched_shuowen": False}

    if entry:
        rec["matched_shuowen"] = True
        rec["trad"] = entry.get("wordhead", trad)
        rec["shuowen"] = entry.get("explanation", "").strip()
        pinyin = clean_pinyin(entry.get("pinyin_full", ""))
        rec["pinyin"] = pinyin
        fanqie = entry.get("pronunciation", "").strip()
        if fanqie:
            rec["fanqie"] = fanqie
        duan = format_duan(entry)
        if duan:
            rec["duan_note"] = duan
        var = format_variants(entry)
        if var:
            rec["variant"] = var
        rec["liushu"] = derive_liushu(rec["shuowen"])
        rec["original"] = extract_original(rec["shuowen"])
    else:
        # 说文未匹配：拼音用 opencc 繁体查康熙/玉篇
        rec["trad"] = cc_s2t.convert(ch)
        rec["shuowen"] = ""
        rec["pinyin"] = ""
        rec["liushu"] = ""
        rec["original"] = ""

    # 康熙：部首 + 溯源
    kx_key = None
    for k in (ch, rec["trad"]):
        if k in kangxi:
            kx_key = k
            break
    if kx_key:
        kx_content = kangxi[kx_key]
        rad, rad_name = extract_radical(kx_content)
        if rad:
            rec["radical"] = rad
            rec["radical_name"] = rad_name
        rec["trace_kangxi"] = kangxi_trim(kx_content)

    # 玉篇
    for k in (ch, rec["trad"]):
        if k in yupian:
            rec["trace_yupian"] = yupian[k]
            break
    # 广韵
    for k in (ch, rec["trad"]):
        if k in guangyun:
            fq, me = guangyun[k]
            rec["trace_guangyun"] = f"{fq}，{me}".strip("，") if fq or me else ""
            break

    result.append(rec)

json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 统计
n = len(result)
n_sw = sum(1 for r in result if r["matched_shuowen"])
n_kx = sum(1 for r in result if r.get("trace_kangxi"))
n_yp = sum(1 for r in result if r.get("trace_yupian"))
n_gy = sum(1 for r in result if r.get("trace_guangyun"))
n_rad = sum(1 for r in result if r.get("radical"))
n_liushu = sum(1 for r in result if r.get("liushu"))
print(f"总字数: {n}")
print(f"  说文匹配: {n_sw} ({n_sw/n*100:.1f}%)")
print(f"  六书推导: {n_liushu}")
print(f"  康熙溯源: {n_kx}")
print(f"  玉篇溯源: {n_yp}")
print(f"  广韵溯源: {n_gy}")
print(f"  部首提取: {n_rad} ({n_rad/n*100:.1f}%)")

from collections import Counter
c = Counter(r["liushu"] for r in result if r["liushu"])
print("  六书分布:", dict(c))
print("已保存:", OUT)
