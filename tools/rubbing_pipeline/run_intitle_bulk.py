# -*- coding: utf-8 -*-
"""Wikimedia 古文字形 · 批量枚举适配器（不依赖 api.php，也不逐字查询）

原理：Commons 的 Special:Search 支持**短语式文件名搜索**
      intitle:"-bronze.svg"
    纯度 ~99%，且能用 offset 分页。因此可用几十次请求枚举**全站**字形文件，
    而不是对 8105 个字各查一次分类页（旧 run_indexphp.py 的做法，需 88 分钟）。

额外收益：
  ① 找到**未被归入「Category:汉字」**的文件（分类反查的漏网之鱼）
  ② 新增书体维度：大篆(bigseal)、汗簡(hanjian)

用法：
    python run_intitle_bulk.py --dry           # 只枚举与统计，不下载
    python run_intitle_bulk.py                 # 全量枚举 + 下载
    python run_intitle_bulk.py --fix-bigseal   # 修正被误标为「篆文」的大篆
"""
import os, re, sys, json, time, argparse, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session, normalize_png, Attribution, LICENSES

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
SEARCH = ("https://commons.wikimedia.org/w/index.php?title=Special:Search"
          "&ns6=1&fulltext=1&limit=500&offset={off}&search={q}")
THUMB = "https://commons.wikimedia.org/w/thumb.php?f={name}&w=512"

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "_glyph_tmp")
CHARS = r"E:\Workbuddy\说文解字\data\characters.json"

# 后缀 -> 书体名（书体名需与 pack_dataset.SCRIPT_PREFIX 对齐）
SUFFIX_SCRIPT = [
    ("bigseal", "bigseal"),      # 大篆 / 籀文（新增书体，前缀 D_）
    ("oracle", "oracle-bone"),
    ("bronze", "bronze"),
    ("seal", "seal"),
    ("silk", "bamboo-silk"),
    ("slip", "bamboo-silk"),
]
ALL_SUFFIXES = [s for s, _ in SUFFIX_SCRIPT] + ["clerical", "ancient", "zhou", "shang", "warring", "spring"]

_CJK = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U0003FFFF]")


def fetch(url, retries=4):
    for i in range(retries):
        try:
            r = SESS.get(url, timeout=45)
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 503):
                time.sleep(4 * (i + 1)); continue
            return ""
        except Exception:
            time.sleep(1.5)
    return None


def enumerate_suffix(suf, max_pages=12):
    """枚举 intitle:"-<suf>.svg"，返回文件名集合（已 unquote）。"""
    q = urllib.parse.quote('intitle:"-%s.svg"' % suf)
    found, off, page = set(), 0, 0
    while page < max_pages:
        html = fetch(SEARCH.format(off=off, q=q))
        if not html:
            break
        names = {urllib.parse.unquote(x).replace("_", " ")
                 for x in re.findall(r'File:([^"#/?]+?\.svg)', html, re.I)}
        # 只保留确实以 -<suf>.svg 结尾的（排除搜索噪声）
        names = {n for n in names if re.search(r"[-_ ]%s(?:[-_ ]\d+)?\.svg$" % re.escape(suf), n, re.I)}
        new = names - found
        found |= names
        off += 500
        page += 1
        print("    [%s] 第%d页 +%d（累计 %d）" % (suf, page, len(new), len(found)), flush=True)
        if len(new) == 0:
            break
        time.sleep(1.5)
    return found


def base_of(name):
    """从 '馬-bronze-2.svg' 取汉字前缀 '馬'；取不到返回 None。"""
    stem = re.sub(r"\.svg$", "", name, flags=re.I)
    m = _CJK.search(stem)
    if not m:
        return None
    # 只接受「单个汉字 + 后缀」形态
    if m.start() != 0:
        return None
    ch = m.group(0)
    rest = stem[m.end():]
    if rest and not re.match(r"^[-_ ]", rest):
        return None
    return ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="只枚举统计，不下载")
    ap.add_argument("--suffixes", default="", help="只跑指定后缀（逗号分隔）")
    a = ap.parse_args()

    chars = json.load(open(CHARS, encoding="utf-8"))["characters"]
    id2char = {str(c["id"]): c.get("char", "") for c in chars}
    c2id = {}
    for c in chars:
        for k in (c.get("char"), c.get("trad")):
            if k and k.strip():
                c2id.setdefault(k.strip(), str(c["id"]))

    want = [(s, sc) for s, sc in SUFFIX_SCRIPT
            if (not a.suffixes) or (s in a.suffixes.split(","))]

    print("[bulk] 开始枚举（Special:Search 短语式，纯度约 99%）")
    per_suffix = {}
    for suf, sc in want:
        names = enumerate_suffix(suf)
        per_suffix[suf] = names
        print("  -%s.svg: 全站 %d 个文件" % (suf, len(names)), flush=True)

    # 归属统计
    print("\n[bulk] 归属统计")
    plan = {}          # (id, script) -> filename
    unmapped = {}
    for suf, sc in want:
        hit = 0
        for n in per_suffix.get(suf, ()):
            ch = base_of(n)
            cid = c2id.get(ch) if ch else None
            if cid:
                hit += 1
                key = (cid, sc)
                # 同一 (id, script) 取文件名最短者（基础形优先）
                if key not in plan or len(n) < len(plan[key]):
                    plan[key] = n
            else:
                unmapped[suf] = unmapped.get(suf, 0) + 1
        print("  -%s.svg -> %s：可映射 %d 字｜无法映射 %d" % (suf, sc, hit, unmapped.get(suf, 0)))

    # 已有产物
    have = set()
    for fn in os.listdir(OUT_DIR):
        m = re.match(r"(?:wa|wb|wm)_(\d+)_(\S+)\.png$", fn)
        if m:
            have.add((m.group(1), m.group(2)))

    todo = [(k, v) for k, v in plan.items() if k not in have]
    print("\n[bulk] 计划新增 (id,script) 组合 %d 个，其中已有 %d，需下载 %d"
          % (len(plan), len(plan) - len(todo), len(todo)))
    from collections import Counter
    print("[bulk] 需下载按书体:", dict(Counter(k[1] for k, _ in todo)))

    if a.dry:
        print("\n[bulk] --dry 结束")
        return

    # 下载（thumb.php 不限流）
    attr_path = os.path.join(OUT_DIR, "wa_attribution_bulk.json")
    try:
        attr = Attribution()
        attr.entries = json.load(open(attr_path, encoding="utf-8"))
    except Exception:
        attr = Attribution()

    ok = fail = 0
    t0 = time.time()
    for i, ((cid, sc), name) in enumerate(todo, 1):
        png = os.path.join(OUT_DIR, "wa_%s_%s.png" % (cid, sc))
        done = False
        for _ in range(2):
            try:
                r = SESS.get(THUMB.format(name=urllib.parse.quote(name)), timeout=60, allow_redirects=True)
                if r.status_code == 200 and r.content:
                    with open(png, "wb") as f:
                        f.write(r.content)
                    if normalize_png(png, size=160, keep_alpha=True):
                        done = True
                    break
                if r.status_code == 404:
                    break
            except Exception:
                time.sleep(1)
        if done:
            ok += 1
            attr.add(sc, "Wikimedia Commons (ACC / ancient script SVG)", LICENSES["pd"])
        else:
            fail += 1
        if i % 100 == 0:
            print("    下载 %d/%d 成功%d 失败%d %.1f分钟"
                  % (i, len(todo), ok, fail, (time.time() - t0) / 60), flush=True)
    attr.save(attr_path)
    print("\n[bulk] 下载完成：成功 %d，失败 %d，耗时 %.1f 分钟" % (ok, fail, (time.time() - t0) / 60))


SESS = None
if __name__ == "__main__":
    SESS = make_session()
    SESS.headers.update({"User-Agent": UA})
    main()
