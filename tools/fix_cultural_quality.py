#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cultural.json 质量修复脚本（对应 cultural_审计核查报告.md 的三类硬伤）

修复项：
  1) 六书错标 10 字：story 明示「X字」与 characters.json.liushu 终审冲突，
     按权威 liushu 重写 story（仅改分类断言 + 纠错部件，不增删其它事实）。
  2) 成语字段污染：idioms 仅保留 4 汉字条目（非四字短语/俗语/谚语移出「成语」字段）。
  3) 诗句出处编造（最高危）：离线无法逐条核验，按审计建议「宁可标待考也不得保留编造」，
     将全部 poems[].source 置为「待考」，保留诗句 line，剥离虚假署名。

用法：
  python tools/fix_cultural_quality.py
结束后用 python tools/check_cultural.py 复验，再用 python build_web.py 重建 index.html。
"""
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CULT = os.path.join(ROOT, "data", "cultural.json")
CHAR = os.path.join(ROOT, "data", "characters.json")

# ---------- 1) 10 字 story 精确回写（old 串来自 repr 实测，断言仅命中 1 次）----------
STORY_FIX = {
    "大": (
        "甲骨文中「大」字像人正面站立之形，突出人体的高大与挺拔，是最早的指事字之一，形象地表达了「大」的本义。",
        "甲骨文中「大」字像人正面站立之形，突出人体的高大与挺拔，是象形的典型代表，形象地表达了「大」的本义。",
    ),
    "插": (
        "「插」字由「扌」和「杀」组成，表示用手刺入肉中，形象地表达了刺肉的动作，体现了会意字的特点。",
        "「插」字从「扌」（手），臿（chā）声，是形声字，本义为刺入、穿插，形象地表达了将物体插入的动作。",
    ),
    "坂": (
        "「坂」字由「土」与「反」组成，表示山坡上的土地，形象地描绘出坡地的形态，本义为坡地，符合会意字的特征。",
        "「坂」字从「土」、反（fǎn）声，是形声字，表示山坡上的土地，本义为坡地，形象地描绘出坡地的形态。",
    ),
    "苷": (
        "「苷」字由「甘」与「艸」组成，表示甘甜的草，古人用它形容植物的甜美，是会意字的典型例子。",
        "「苷」字从「艸」（艹）、甘（gān）声，是形声字，表示甘甜的草，古人用它形容植物的甜美。",
    ),
    "唏": (
        "「唏」字由「口」和「希」组成，表示用口发出笑声，形象地表达了笑的意思，符合会意字的特点。",
        "「唏」字从「口」、希（xī）声，是形声字，表示用口发出笑声，形象地表达了笑的意思。",
    ),
    "耜": (
        "耜字由‘耒’和‘𠂇’组成，表示用耒翻土的农具，形象地展现了古人耕作的场景，体现了会意字的特点。",
        "耜字从「耒」（农具）、以（yǐ）声，是形声字，表示用耒翻土的农具，形象地展现了古人耕作的场景。",
    ),
    "彀": (
        "「彀」字由「弓」和「句」组成，表示用弓弩张开的状态，形象地描绘了古代射箭前拉弓的场景，体现了会意字的特点。",
        "「彀」字从「弓」、㱿（gòu）声，是形声字，表示弓弩张开的状态，形象地描绘了古代射箭前拉弓的场景。",
    ),
    "彳": (
        "彳字像人腿的形状，表示小步行走，古人用它来表示行走的动作，是会意字的典范。",
        "彳字像人腿或道路的形状，表示小步行走，古人用它来表示行走的动作，是象形的代表。",
    ),
    "桊": (
        "桊字由牛和环组成，表示牛鼻中的环，古人用它来牵牛，形象生动，体现了会意字的特点。",
        "桊字从「木」、𡤝（quān）声，是形声字，表示牛鼻中的环，古人用它来牵牛，形象生动。",
    ),
    "蛑": (
        "「蛑」字由「虫」与「牟」组成，表示一种吃草根的虫子，形象地描绘了虫子在草根中啃食的场景，符合会意字的特点。",
        "「蛑」字从「虫」、牟（móu）声，是形声字，表示一种吃草根的虫子，形象地描绘了虫子在草根中啃食的场景。",
    ),
}

# ---------- 2) 成语 4 字硬过滤 ----------
CJK = re.compile(r"^[\u4e00-\u9fff]{4}$")


def main():
    d = json.load(open(CULT, encoding="utf-8"))
    cj = json.load(open(CHAR, encoding="utf-8"))
    lm = {c["char"]: c.get("liushu", "") for c in cj["characters"]}

    # 备份
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = CULT + ".bak_" + ts
    json.dump(d, open(bak, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("backup ->", os.path.basename(bak))

    # --- 1) story 回写 ---
    story_ok = 0
    for ch, (old, new) in STORY_FIX.items():
        e = d.get(ch)
        if not e:
            print("  [WARN] 缺字", ch); continue
        if e.get("story") != old:
            print("  [WARN] %s story 与实测不符，跳过（防误改）" % ch)
            continue
        e["story"] = new
        story_ok += 1
    print("story 回写:", story_ok, "/", len(STORY_FIX))

    # --- 2) idioms 4 字过滤 ---
    idiom_removed = 0
    idiom_kept = 0
    for ch, e in d.items():
        if not isinstance(e, dict):
            continue
        its = e.get("idioms")
        if not its:
            continue
        kept = []
        for it in its:
            w = it.get("w", "") if isinstance(it, dict) else ""
            if CJK.match(w):
                kept.append(it); idiom_kept += 1
            else:
                idiom_removed += 1
        e["idioms"] = kept

    # --- 3) poems source -> 待考 ---
    poem_total = 0
    poem_src_changed = 0
    for ch, e in d.items():
        if not isinstance(e, dict):
            continue
        ps = e.get("poems")
        if not ps:
            continue
        for p in ps:
            if not isinstance(p, dict):
                continue
            poem_total += 1
            oldsrc = p.get("source", "")
            if oldsrc != "待考":
                poem_src_changed += 1
            p["source"] = "待考"
    print("idioms 移除(非4字):", idiom_removed, "| 保留(4字):", idiom_kept)
    print("poems 总数:", poem_total, "| source 改待考:", poem_src_changed)

    # 回写（保持原 compact 格式）
    raw = open(CULT, encoding="utf-8").read()
    trailing_nl = raw.endswith("\n")
    out = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    if trailing_nl:
        out += "\n"
    open(CULT, "w", encoding="utf-8").write(out)

    # --- 复验：六书冲突应为 0 ---
    pat = re.compile(r"(形声|象形|会意|指事)字")
    mism = []
    for ch, e in d.items():
        if isinstance(e, dict):
            m = pat.search(e.get("story", ""))
            if m and lm.get(ch, "") and m.group(1) not in lm.get(ch, ""):
                mism.append(ch)
    print("复验 六书冲突(应=0):", len(mism), mism)
    # 复验：非4字成语(应=0)
    non4 = 0
    for e in d.values():
        if isinstance(e, dict):
            for it in (e.get("idioms") or []):
                if isinstance(it, dict) and not CJK.match(it.get("w", "")):
                    non4 += 1
    print("复验 非4字成语(应=0):", non4)
    # 复验：poems source 是否全待考
    bad_src = 0
    for e in d.values():
        if isinstance(e, dict):
            for p in (e.get("poems") or []):
                if isinstance(p, dict) and p.get("source") != "待考":
                    bad_src += 1
    print("复验 poems 非待考(应=0):", bad_src)
    print("DONE.")


if __name__ == "__main__":
    main()
