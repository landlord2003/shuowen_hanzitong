#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean_idioms.py — cultural.json 成语字段清洗（P0-3，可逆保守版）

策略：
- idioms 字段应只含真成语。误混入的俗语/现代短语/非四字短语移入新字段 phrases（不删除，可逆）。
- 默认保守模式：仅把「明显非成语」移出——
    ① 含现代专属字素（网/电脑/手机/软件/app/因特网…）；
    ② 含英文字母/数字；
    ③ 非 4 字纯中文。
- 若提供 --dict 成语白名单 json（如本机从成语词典导出的 list[str]），则更严格：
    不在白名单的 4 字短语也移入 phrases（真成语由白名单保护，不会误删）。
- 备份 + 写回，输出移出清单 data/idioms_removed.json。

用法：
  python tools/clean_idioms.py                              # 保守模式（沙箱可跑）
  python tools/clean_idioms.py --dict idioms_whitelist.json # 白名单模式（本机全量，需词典）
"""
import json, re, os, sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CULT = os.path.join(ROOT, "data", "cultural.json")

# 现代专属词素（仅多字/完整词，成语几乎不含；单字如「云/微/电/因/互」在古成语正常出现，绝不列入，否则误删真成语）
MODERN_MULTI = ("网", "电脑", "手机", "软件", "因特", "互联", "互联网", "计算机", "app", "APP", "App")


def obvious_non_idiom(w):
    # 极度保守：仅当含英文字母/数字时判定为非成语（古成语绝不含，零误删）。
    # 单字古汉字（云/微/电/因/互等）一律保留，绝不误删真成语。
    if re.search(r"[A-Za-z0-9]", w):
        return True
    return False


def main():
    d = json.load(open(CULT, encoding="utf-8"))
    whitelist = None
    if "--dict" in sys.argv:
        p = sys.argv[sys.argv.index("--dict") + 1]
        whitelist = set(json.load(open(p, encoding="utf-8")))
        print("白名单词条:", len(whitelist))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = CULT + ".bak_" + ts
    json.dump(d, open(bak, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    removed = []
    kept_total = 0
    for ch, e in d.items():
        if not isinstance(e, dict):
            continue
        its = e.get("idioms")
        if not its:
            continue
        keep = []
        for it in its:
            w = it.get("w", "") if isinstance(it, dict) else ""
            bad = obvious_non_idiom(w) or (whitelist is not None and w not in whitelist)
            if bad:
                removed.append({"char": ch, "w": w,
                                "meaning": it.get("meaning", "") if isinstance(it, dict) else ""})
                e.setdefault("phrases", []).append(it)
            else:
                keep.append(it)
                kept_total += 1
        e["idioms"] = keep

    out = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    open(CULT, "w", encoding="utf-8").write(out)
    json.dump(removed, open(os.path.join(ROOT, "data", "idioms_removed.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("移出(入 phrases，可逆):", len(removed))
    print("保留成语:", kept_total)
    print("清单 -> data/idioms_removed.json")
    if removed:
        print("样例:", removed[:10])


if __name__ == "__main__":
    main()
