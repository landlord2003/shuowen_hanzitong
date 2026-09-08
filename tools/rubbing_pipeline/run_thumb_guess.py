# -*- coding: utf-8 -*-
"""阶段1：thumb.php 盲猜直连（不受 api.php 限流）。

对每个字盲猜 {char}-oracle/-bronze/-seal/-silk/-slip/-bigseal 等直接命名，
用 commons thumb.php 拿栅格化 PNG。thumb.php 不触发 api.php 的 429 限流，
可高并发稳定跑完全部 8105 字。

命中率低（约 15-20%，仅 ACC 项目「已映射到汉字」的直接命名文件），
但稳定快速，作为分类反查（api.php，高命中但限流严重）的互补。
"""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import make_session, download_file, normalize_png, LICENSES
import opencc

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS_PATH = r"E:\Workbuddy\说文解字\data\characters.json"
OUT_DIR = os.path.join(HERE, "_glyph_tmp")
THUMB = "https://commons.wikimedia.org/w/thumb.php?f={name}&w=512"

# 盲猜后缀 -> 脚本类型（含变体）
SUFFIXES = [
    ("-oracle.svg", "oracle-bone"),
    ("-oracle-western.svg", "oracle-bone"),
    ("-oracle-zhouyuan.svg", "oracle-bone"),
    ("-bronze.svg", "bronze"),
    ("-bronze-shang.svg", "bronze"),
    ("-bronze-spring.svg", "bronze"),
    ("-bronze-warring.svg", "bronze"),
    ("-seal.svg", "seal"),
    ("-bigseal.svg", "seal"),
    ("-silk.svg", "bamboo-silk"),
    ("-slip.svg", "bamboo-silk"),
]

def _strip(v):
    if v is None:
        return ""
    return str(v).strip().strip("'\"")

def main():
    d = json.load(open(CHARS_PATH, encoding="utf-8"))
    chars = d["characters"] if isinstance(d, dict) else d
    cc = opencc.OpenCC("s2t")

    session = make_session()
    session.headers.update({"User-Agent": "rubbing-pipeline/1.0 (research; contact none)"})

    results = []
    def process_one(c):
        ch = _strip(c.get("trad")) or _strip(c.get("char"))
        if not ch or len(ch) != 1:
            return []
        # 候选名：简体 + 繁体
        names = [ch]
        try:
            t = cc.convert(ch)
            if t and t != ch:
                names.append(t)
        except Exception:
            pass
        out = []
        seen = set()
        for base in names:
            for suf, script in SUFFIXES:
                if script in seen:
                    continue
                fname = base + suf
                png_path = os.path.join(OUT_DIR, f"wb_{c['id']}_{script}.png")
                if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
                    out.append({"id": str(c["id"]), "char": ch, "script": script, "img": png_path})
                    seen.add(script)
                    continue
                url = THUMB.format(name=fname)
                if download_file(url, png_path, session=session, retries=1) and \
                        normalize_png(png_path, size=160, keep_alpha=True):
                    out.append({"id": str(c["id"]), "char": ch, "script": script, "img": png_path})
                    seen.add(script)
        return out

    print(f"[thumb-guess] 开始，共 {len(chars)} 字", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = [ex.submit(process_one, c) for c in chars]
        for f in as_completed(futs):
            results.extend(f.result())
            done += 1
            if done % 1000 == 0:
                print(f"  [thumb-guess] 已处理 {done}/{len(chars)}，字形 {len(results)}", flush=True)

    from collections import Counter
    dist = Counter(r["script"] for r in results)
    covered = len(set(r["id"] for r in results))
    print(f"[thumb-guess] 完成：字形 {len(results)}，覆盖 {covered}/{len(chars)} 字", flush=True)
    print(f"[thumb-guess] 分布: {dict(dist)}", flush=True)

    # 写 manifest
    with open(os.path.join(OUT_DIR, "wb_manifest.jsonl"), "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
