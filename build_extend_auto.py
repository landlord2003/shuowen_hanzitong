# -*- coding: utf-8 -*-
"""在 extend_authoritative.json 基础上，自动补全：
1. 拼音（pypinyin，说文未匹配的 1989 字）
2. 后起字本义（康熙/玉篇首义）
3. 后起字六书（默认形声 + 指事字清单）
输出 extend_full.json（剩余 modern/evolution/category/stroke 待模型生成）
"""
import json, re
from pypinyin import pinyin, Style

BASE = r"D:\WorkBuddy\projects\说文解字"
AUTH = BASE + r"\.workbuddy\charlist\extend_authoritative.json"
OUT = BASE + r"\.workbuddy\charlist\extend_full.json"

recs = json.load(open(AUTH, encoding="utf-8"))

# 指事字清单（说文不直书"指事"，据构形判定）
ZHISHI = "一二三上下本末刃寸甘曰中天旦夕才之了于乎太小少大王玉示只亦立并凹凸丫卡卅卌四五六七八九十廿卅"

n_pinyin = 0
n_orig = 0
n_liushu = 0

for r in recs:
    ch = r["char"]
    # 1. 拼音补全
    if not r.get("pinyin"):
        try:
            py = pinyin(ch, style=Style.TONE)[0][0]
            r["pinyin"] = py
            n_pinyin += 1
        except Exception:
            pass

    # 2. 后起字（说文未匹配）本义 + 六书
    if not r.get("matched_shuowen"):
        # 本义：玉篇首义 > 康熙首义（跳过反切"XX切"）
        if not r.get("original"):
            meaning = ""
            yp = r.get("trace_yupian", "")
            if yp:
                for seg in yp.split("。"):
                    seg = seg.strip()
                    if seg and "切" not in seg and "音" not in seg:
                        meaning = seg
                        break
                if meaning:
                    r["original"] = meaning + "（出《玉篇》）"
                    r["original_source"] = "《玉篇》(543年)"
                    n_orig += 1
            if not meaning:
                kx = r.get("trace_kangxi", "")
                if kx:
                    # 找"音X"后的"XX也"
                    m = re.search(r"音[一-龥]+[。，]?\s*([^。；【】]{1,20}也)", kx)
                    if m:
                        meaning = m.group(1).strip()
                    else:
                        m2 = re.search(r"([^。；【】]{1,15}也)", kx)
                        if m2 and "切" not in m2.group(1):
                            meaning = m2.group(1).strip()
                    if meaning and len(meaning) > 1:
                        r["original"] = meaning + "（出《康熙字典》）"
                        r["original_source"] = "《康熙字典》(1716年)"
                        n_orig += 1
        # 六书：指事清单 > 默认形声
        if not r.get("liushu"):
            if ch in ZHISHI:
                r["liushu"] = "指事"
            else:
                r["liushu"] = "形声"  # 现代新造字/后起字多形声
            n_liushu += 1

json.dump(recs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 统计
n = len(recs)
print(f"总字数: {n}")
print(f"  拼音补全: {n_pinyin}")
print(f"  后起字本义: {n_orig}")
print(f"  后起字六书: {n_liushu}")

# 剩余待模型生成的字段
missing_modern = sum(1 for r in recs if not r.get("modern"))
missing_evolution = sum(1 for r in recs if not r.get("evolution"))
missing_category = sum(1 for r in recs if not r.get("category"))
missing_stroke = sum(1 for r in recs if not r.get("stroke"))
missing_radical = sum(1 for r in recs if not r.get("radical"))
print(f"  待生成: modern={missing_modern}, evolution={missing_evolution}, category={missing_category}, stroke={missing_stroke}, radical={missing_radical}")

# 抽查
for r in recs[:3]:
    print(f"  示例 {r['char']}: trad={r['trad']} pinyin={r.get('pinyin','')} liushu={r.get('liushu','')} original={r.get('original','')[:20]} radical={r.get('radical','')}")
print("已保存:", OUT)
