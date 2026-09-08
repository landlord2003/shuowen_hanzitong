# -*- coding: utf-8 -*-
"""全量抓取 Wikimedia ACC 字形（甲骨文/金文/小篆/简帛）—— 8105 字。

断点续传：已存在且非空的 png 自动跳过（见 wikimedia_ancient.fetch）。
进度：每 100 字打印一次，结束写 summary。
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters.wikimedia_ancient import fetch
from sources import Attribution

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS_PATH = r"E:\Workbuddy\说文解字\data\characters.json"
OUT_DIR = os.path.join(HERE, "_glyph_tmp")

def main():
    d = json.load(open(CHARS_PATH, encoding="utf-8"))
    chars = d["characters"] if isinstance(d, dict) else d
    print(f"[full-run] 开始全量抓取，共 {len(chars)} 字", flush=True)
    t0 = time.time()

    attr = Attribution()
    recs = fetch(chars, OUT_DIR, attribution=attr, workers=3)

    dt = time.time() - t0
    from collections import Counter
    dist = Counter(r["script"] for r in recs)
    covered = len(set(r["id"] for r in recs))
    print(f"\n[full-run] 完成：耗时 {dt/60:.1f} 分钟，字形 {len(recs)} 条，覆盖 {covered}/{len(chars)} 字", flush=True)
    print(f"[full-run] 脚本分布: {dict(dist)}", flush=True)

    # 存 manifest 供打包
    manifest_path = os.path.join(HERE, "_glyph_tmp", "wa_manifest.jsonl")
    with open(manifest_path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[full-run] manifest 已写: {manifest_path}", flush=True)

if __name__ == "__main__":
    main()
