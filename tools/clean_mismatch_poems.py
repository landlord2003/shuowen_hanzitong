# -*- coding: utf-8 -*-
"""
clean_mismatch_poems.py — cultural.json 诗词「不含本字」错配清洗

契约（不靠猜、不编造）：
- 诗词引用挂在某字 X 下，前提是诗句中确实含有字符 X（否则属语义弱关联冒充，误导用户）。
- 对本产品 8105 字库而言，诗句不含 X 即视为错配，从 X 的 poems 中移除。
- 已核实出处（source 非待考）的条目同样受此契约约束——出处对，但字不对，仍移除。
- 移除后若某字 poems 变空，属诚实空（不强行塞句）。
- 不改写任何 source；如需把被移除的诗句重新正确挂到「含该字」的其它字下，
  属 P1 权威古诗库全量重索引任务，不在此脚本范围（避免引入新错配）。

写回后 bump cultural-ui.js 的 fetch 缓存版本，强制刷新。

用法：python tools/clean_mismatch_poems.py
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CULT = os.path.join(BASE, "data", "cultural.json")
REMOVED_LOG = os.path.join(BASE, "data", "poems_removed_mismatch.json")

def main():
    d = json.load(open(CULT, encoding="utf-8"))
    before = 0
    removed = []
    for ch, v in d.items():
        if not isinstance(v, dict):
            continue
        poems = v.get("poems") or []
        kept = []
        for pm in poems:
            if not isinstance(pm, dict):
                kept.append(pm)
                continue
            before += 1
            line = pm.get("line", "")
            if ch in line:
                kept.append(pm)
            else:
                removed.append({"char": ch, "line": line, "source": pm.get("source", "")})
        v["poems"] = kept
    after = before - len(removed)
    json.dump(d, open(CULT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(removed, open(REMOVED_LOG, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"poems before: {before}")
    print(f"removed (不含本字错配): {len(removed)}")
    print(f"poems after: {after}")
    print(f"removed log -> {REMOVED_LOG}")
    print("--- sample removed (前 20) ---")
    for r in removed[:20]:
        print(f"  {r['char']} | {r['line']}")

if __name__ == "__main__":
    main()
