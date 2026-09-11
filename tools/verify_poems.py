#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对 cultural.json 中 source=='待考' 的诗句做正向核验：
用 chinese-poetry 离线数据集（MIT）逐句检索，命中则恢复真实 author+title，
不命中则保留 '待考'。

数据集位置：.cache/poetry_src/ （sparse-clone 的 json/唐诗宋诗 + ci/宋词 + other/诗经）
不进 git 仓；仅把核验出的真出处写回 cultural.json 并提交。
"""
import opencc, json, sqlite3, re, os, glob, sys

ROOT = os.path.join(os.path.dirname(__file__), "..", ".cache", "poetry_src")
CULT = os.path.join(os.path.dirname(__file__), "..", "data", "cultural.json")

t2s = opencc.OpenCC("t2s")

def norm(s):
    """繁->简，仅保留汉字，去标点/空白。"""
    s = t2s.convert(s or "")
    return re.sub(r"[^\u4e00-\u9fff]", "", s)

def build_index():
    idx = {}  # norm_sentence -> (author, title)
    def add(author, title, paras):
        if not paras:
            return
        for para in paras:
            if not para:
                continue
            k = norm(para)
            if k and k not in idx:
                idx[k] = (author or "佚名", title or "")
    # 唐诗 / 宋诗 json
    n_json = 0
    for f in glob.glob(os.path.join(ROOT, "json", "*.json")):
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print("  [warn] skip json", f, e, file=sys.stderr)
            continue
        if isinstance(data, list):
            for e in data:
                if isinstance(e, dict):
                    add(e.get("author"), e.get("title"), e.get("paragraphs"))
            n_json += 1
    print("唐诗/宋诗 json 文件:", n_json, "| 当前索引句数:", len(idx))
    # 宋词 sqlite
    db = os.path.join(ROOT, "ci", "ci.sqlite")
    if os.path.exists(db):
        con = sqlite3.connect(db)
        cur = con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tbls = [r[0] for r in cur.fetchall()]
        print("ci 表:", tbls)
        for t in tbls:
            try:
                cur = con.execute(f"SELECT * FROM {t} LIMIT 1")
                cols = [d[0].lower() for d in cur.description]
                author_c = next((c for c in cols if "author" in c or "作者" in c), None)
                title_c = next((c for c in cols if c in ("title",) or "title" in c or "词牌" in c or "name" in c), None)
                content_c = next((c for c in cols if "content" in c or "paragraph" in c or "text" in c or "rhythmic" in c), None)
                if not content_c:
                    content_c = cols[-1]
                print(f"  {t}: author={author_c} title={title_c} content={content_c}")
                for row in con.execute(f"SELECT * FROM {t}"):
                    d = dict(zip([c[0] for c in cur.description], row))
                    author = d.get(author_c) if author_c else None
                    title = d.get(title_c) if title_c else None
                    content = d.get(content_c) if content_c else None
                    if content:
                        paras = re.split(r"[\n。.；;，,]", str(content))
                        add(author, title, paras)
            except Exception as e:
                print("  [warn] ci table", t, e, file=sys.stderr)
        print("加宋词后索引句数:", len(idx))
    else:
        print("  [warn] ci.sqlite 不存在")
    # 诗经等 other
    for f in glob.glob(os.path.join(ROOT, "other", "*.json")):
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, list):
            for e in data:
                if isinstance(e, dict):
                    add(e.get("author"), e.get("title"), e.get("paragraphs"))
    print("总索引句数:", len(idx))
    return idx

def verify(idx, dry_run=True):
    d = json.load(open(CULT, encoding="utf-8"))
    hit = 0
    miss = 0
    changed = []
    for ch, v in d.items():
        if not isinstance(v, dict):
            continue
        for p in (v.get("poems") or []):
            if isinstance(p, dict) and p.get("source") == "待考":
                kk = norm(p.get("line", ""))
                if kk in idx:
                    author, title = idx[kk]
                    new_src = f"{author}《{title}》"
                    if not dry_run:
                        p["source"] = new_src
                    hit += 1
                    changed.append((ch, p.get("line", ""), new_src))
                else:
                    miss += 1
    print(f"待考核验: 命中={hit} 未命中(保留待考)={miss}")
    return d, hit, miss, changed

if __name__ == "__main__":
    dry = "--write" not in sys.argv
    print("=== 构建古诗索引 ===")
    idx = build_index()
    print("=== 核验待考诗句 (dry_run=%s) ===" % dry)
    d, hit, miss, changed = verify(idx, dry_run=not dry)
    if not dry:
        json.dump(d, open(CULT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print("已写回 cultural.json")
    # 抽样展示命中
    print("=== 命中样例(前15) ===")
    for c in changed[:15]:
        print("  ", c[0], "|", c[1], "->", c[2])
