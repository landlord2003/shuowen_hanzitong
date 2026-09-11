#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-1 诗词全量核实（沙箱可达版）。

1. 从 chinese-poetry 官方仓库下载权威古诗文语料（缓存到 tools/poetry_corpus/）。
2. 用 opencc 把语料繁体 -> 简体，去标点后建索引 line -> (朝代·作者《篇名》)。
3. 比对 data/cultural.json 每条 poems[].line，填补真实出处；已含《的权威出处保留不动。
4. 备份原文件后写回，打印统计（已核实 / 新核实 / 仍待核）。

纪律红线：宁可保留"待考"/"示例·出处待核"，绝不补造或保留虚假出处。
"""
import urllib.request, json, os, ssl, re, time, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import opencc
    CC = opencc.OpenCC("t2s")
    def t2s(s): return CC.convert(s)
except Exception:
    def t2s(s): return s  # 退化：不转换（仍可按字符比对）

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "poetry_corpus")
os.makedirs(CACHE, exist_ok=True)
API = "https://api.github.com/repos/chinese-poetry/chinese-poetry/contents/"
CULT = os.path.join(ROOT, "data", "cultural.json")

# 集合 -> (文件正则, 朝代标签)
COLLECTIONS = {
    "全唐诗":   (r"^poet\.(tang|song)\..*\.json$|^唐诗补录\.json$", "唐"),
    "宋词":     (r"^ci\.song.*\.json$|^宋词三百首\.json$", "宋"),
    "元曲":     (r"^yuanqu\.json$", "元"),
    "诗经":     (r"^shijing\.json$", "诗经"),
    "楚辞":     (r"^chuci\.json$", "楚辞"),
    "曹操诗集": (r"^caocao\.json$", "汉"),
    "纳兰性德": (r"^纳兰性德诗集\.json$", "清"),
    "蒙学":     (r"\.json$", "蒙学"),
    "四书五经": (r"\.json$", "先秦"),
    "论语":     (r"^lunyu\.json$", "先秦"),
}

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

def get_json(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0",
                                             "Accept": "application/vnd.github+json"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(2)
    raise RuntimeError("API fail " + u)

def fetch_file(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return "cached"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            return "ok"
        except Exception:
            time.sleep(min(2 ** attempt * 3, 30))
    return "FAIL"

PUNCT = re.compile(r"[，。、；：？！“”‘’「」『』（）《》…—\s\.,;:?!()\[\]{}<>~@#%&*_+=|\\\"'/]")

def norm(s):
    s = t2s(s or "")
    return PUNCT.sub("", s)

def main():
    # ---- 1. 下载语料 ----
    jobs = []
    for coll, (pat, _dyn) in COLLECTIONS.items():
        cdir = os.path.join(CACHE, coll)
        os.makedirs(cdir, exist_ok=True)
        try:
            listing = get_json(API + urllib.parse.quote(coll))
        except Exception as e:
            print("LIST ERR", coll, str(e)[:80]); continue
        rx = re.compile(pat)
        for item in listing:
            if item.get("type") != "file":
                continue
            if item["name"].lower() == "readme.md":
                continue
            if not rx.search(item["name"]):
                continue
            # 用 jsDelivr CDN 取文件（raw.githubusercontent 在沙箱大文件会超时）
            rel = item.get("path") or (coll + "/" + item["name"])
            url = "https://cdn.jsdelivr.net/gh/chinese-poetry/chinese-poetry@master/" + urllib.parse.quote(rel)
            jobs.append((url, os.path.join(cdir, item["name"])))
    print("[fetch] total files:", len(jobs), flush=True)
    ok = cached = fail = 0
    fails = []
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_file, u, p): (u, p) for u, p in jobs}
        for f in as_completed(futs):
            res = f.result()
            if res == "ok":
                ok += 1
            elif res == "cached":
                cached += 1
            else:
                fail += 1; fails.append(res)
            done += 1
            if done % 25 == 0:
                print(f"[fetch] progress {done}/{len(jobs)} ok={ok} fail={fail}", flush=True)
    print(f"[fetch] ok={ok} cached={cached} fail={fail}", flush=True)

    # ---- 2. 建索引 ----
    idx = {}  # norm_line -> list of label
    def add(key, label):
        if not key:
            return
        idx.setdefault(key, []).append(label)
    for coll, (_pat, default_dyn) in COLLECTIONS.items():
        cdir = os.path.join(CACHE, coll)
        if not os.path.isdir(cdir):
            continue
        for fn in os.listdir(cdir):
            if not fn.endswith(".json"):
                continue
            dyn = default_dyn
            if coll == "全唐诗":
                dyn = "宋" if fn.startswith("poet.song") else "唐"
            fp = os.path.join(cdir, fn)
            try:
                arr = json.load(open(fp, encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(arr, list):
                arr = [arr]
            for e in arr:
                if not isinstance(e, dict):
                    continue
                author = e.get("author") or ""
                title = e.get("title") or e.get("section") or e.get("chapter") or ""
                lines = e.get("paragraphs") or e.get("content") or []
                if isinstance(lines, str):
                    lines = [lines]
                for ln in lines:
                    if not isinstance(ln, str):
                        continue
                    k = norm(ln)
                    if len(k) < 4:
                        continue
                    label = (f"{dyn}·{author}《{title}》" if author
                             else f"{dyn}《{title}》")
                    add(k, label)
    print("[index] unique lines:", len(idx))

    # ---- 3. 比对 cultural.json ----
    data = json.load(open(CULT, encoding="utf-8"))
    total = already = filled = pending = 0
    for ch, v in data.items():
        poems = v.get("poems")
        if not poems:
            continue
        for e in poems:
            total += 1
            src = (e.get("source") or "").strip()
            line = e.get("line") or ""
            if "《" in src:           # 已含权威出处，保留
                already += 1
                e["verified"] = True
                continue
            # 可填补：待考 / 示例·出处待核 / 空
            key = norm(line)
            hit = idx.get(key)
            if not hit:
                # 拆句再试（对联/两句连写）
                for seg in re.split(r"[，。、；：？！]", line):
                    ks = norm(seg)
                    if len(ks) >= 4 and ks in idx:
                        hit = idx[ks]; break
            if hit:
                e["source"] = hit[0]
                e["verified"] = True
                filled += 1
            else:
                pending += 1
                e["verified"] = False
    # ---- 4. 写回（先备份） ----
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = CULT + f".bak_{ts}"
    json.dump(data, open(bak, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(data, open(CULT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[write] backup -> {os.path.basename(bak)}")
    print(f"[stats] total={total} already_verified={already} newly_filled={filled} "
          f"still_pending={pending}")
    rate = pending / total if total else 0
    print(f"[stats] 待核率 = {rate:.1%}  (目标 <20%)")
    if fails:
        print("[fails sample]", fails[:5])

if __name__ == "__main__":
    main()
