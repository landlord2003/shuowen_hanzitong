# -*- coding: utf-8 -*-
"""Wikimedia 古文字抓取 · index.php 分类页版（不依赖 api.php）

背景：本机代理出口 IP 对 Wikimedia **api.php** 配额近乎为零（实测持续 429），
但 **index.php（页面渲染）不受此限流**（实测连续请求全 200）。因此改用：

    https://commons.wikimedia.org/w/index.php?title=Category:{汉字}&action=render

取该字分类页 HTML，从中提取两类古文字形文件：
  ① ACC 编号文件：ACC-j#####(甲骨) / ACC-b#####(金文) / ACC-s#####(小篆) / ACC-L#####(大篆)
  ② 汉字命名文件：{字}-oracle/-bronze/-seal/-bigseal/-silk/-slip.svg

再用 thumb.php 栅格化为 160×160 PNG（thumb.php 不限流）。

断点续传：已有 wa_{id}_{script}.png 自动跳过。
"""
import os
import re
import sys
import json
import time
import threading
import urllib.parse
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import make_session, normalize_png, Attribution, LICENSES  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "_glyph_tmp")
CHARS = r"E:\Workbuddy\说文解字\data\characters.json"

CAT = "https://commons.wikimedia.org/w/index.php?title=Category:{c}&action=render"
THUMB = "https://commons.wikimedia.org/w/thumb.php?f={name}&w=512"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

# ACC 编号前缀 -> 脚本
# 实测（2026-09-11，读文件页 action=raw 的 {{ACClicense}} 模板确认）：
#   ACC-j##### = oracle（小写 j）
#   ACC-B##### = bronze（**大写** B；旧代码只注册小写 b，导致整批被丢弃）
#   ACC-s##### = seal（小写 s）
#   ACC-L##### = bigseal|Great seal（**大写** L；旧代码错映射为 seal，把大篆当小篆）
ACC_LETTER = {"j": "oracle-bone", "J": "oracle-bone",
              "b": "bronze", "B": "bronze",
              "s": "seal", "S": "seal",
              "L": "bigseal", "l": "bigseal"}
# 汉字命名后缀 -> 脚本（顺序即优先级）
NAMED = [("-oracle", "oracle-bone"), ("-bronze", "bronze"),
         ("-seal", "seal"), ("-bigseal", "bigseal"),
         ("-silk", "bamboo-silk"), ("-slip", "bamboo-silk")]

# 全局限流协调（软限流：失败即退避）
_LK = threading.Lock()
_COOLDOWN = [0.0]
_FAILS = [0]
MAX_PER_SCRIPT = 1


def _wait():
    while True:
        with _LK:
            remain = _COOLDOWN[0] - time.time()
        if remain <= 0:
            return
        time.sleep(min(remain, 3.0))


def _note_fail():
    with _LK:
        _FAILS[0] += 1
        _COOLDOWN[0] = time.time() + min(5 * _FAILS[0], 60)
    print("  [软限流] 冷却 %.0fs（累计失败 %d）" % (min(5 * _FAILS[0], 60), _FAILS[0]), flush=True)


def _note_ok():
    with _LK:
        _FAILS[0] = max(0, _FAILS[0] - 1)


def _page(session, catname):
    """取分类页 HTML，返回文本或 None。"""
    for _ in range(3):
        _wait()
        try:
            r = session.get(CAT.format(c=urllib.parse.quote(catname)), timeout=30)
            if r.status_code == 200:
                _note_ok()
                return r.text
            if r.status_code in (429, 503):
                _note_fail()
                continue
            return ""
        except Exception:
            _note_fail()
            time.sleep(1)
    return None


def scan_char(session, ch, trad):
    """返回 {script: [filename,...]}"""
    found = {}
    names = []
    for n in (ch, trad):
        if n and n not in names:
            names.append(n)
    for name in names:
        html = _page(session, name)
        if not html:
            continue
        for letter, num in re.findall(r"ACC-([a-zA-Z])(\d{3,6})\.svg", html):
            sc = ACC_LETTER.get(letter)
            if sc:
                found.setdefault(sc, []).append("ACC-%s%s.svg" % (letter, num))
        for base in re.findall(r"File:([^\"#/]*?(?:-oracle|-bronze|-seal|-bigseal|-silk|-slip)[^\"#/]*)\.svg", html):
            base = urllib.parse.unquote(base)  # 分类页里是 URL 编码名，须先解码，否则二次编码 404
            low = base.lower()
            for suf, sc in NAMED:
                if suf in low:
                    found.setdefault(sc, []).append(base + ".svg")
                    break
        if found:
            break
    # 去重；优先取名字最短的基础变体（如 厂-oracle.svg 优先于 厂-oracle-2.svg）
    return {k: sorted(set(v), key=lambda s: (len(s), s)) for k, v in found.items()}


def download_glyph(session, name, png_path):
    if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
        return True
    for _ in range(2):
        try:
            r = session.get(THUMB.format(name=urllib.parse.quote(name)), timeout=60,
                            allow_redirects=True)
            if r.status_code == 200 and r.content:
                with open(png_path, "wb") as f:
                    f.write(r.content)
                return normalize_png(png_path, size=160, keep_alpha=True)
            if r.status_code == 404:
                return False
        except Exception:
            time.sleep(1)
    return False


def main(limit=None, workers=4, only_missing=True):
    chars = json.load(open(CHARS, encoding="utf-8"))["characters"]
    os.makedirs(OUT_DIR, exist_ok=True)

    # 断点：已有 wa_ 文件的 id -> 脚本集合
    have = {}
    for fn in os.listdir(OUT_DIR):
        m = re.match(r"wa_(\d+)_(\S+)\.png$", fn)
        if m:
            have.setdefault(m.group(1), set()).add(m.group(2))

    if only_missing:
        # 优先跑"一个字形都没有"的字
        todo = [c for c in chars if not have.get(str(c["id"]))]
    else:
        todo = list(chars)
    todo.sort(key=lambda c: (len(have.get(str(c["id"]), ())), c["id"]))
    if limit:
        todo = todo[:limit]

    print("[indexphp] 待处理 %d 字（已有数据 %d 字），workers=%d" % (len(todo), len(have), workers), flush=True)
    session = make_session()
    session.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    attr = Attribution()
    t0 = time.time()
    stat = {"scanned": 0, "hit": 0, "down": 0}
    lk = threading.Lock()

    def one(c):
        s = make_session()
        s.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        _wait()
        fmap = scan_char(s, c["char"], c.get("trad"))
        got = 0
        for sc, files in fmap.items():
            png = os.path.join(OUT_DIR, "wa_%s_%s.png" % (c["id"], sc))
            if os.path.exists(png) and os.path.getsize(png) > 0:
                continue
            for name in files[:MAX_PER_SCRIPT]:
                if download_glyph(s, name, png):
                    got += 1
                    attr.add(sc, "Wikimedia Commons (ACC ancient script SVG)", LICENSES["pd"])
                    break
        with lk:
            stat["scanned"] += 1
            if fmap:
                stat["hit"] += 1
            stat["down"] += got
            n = stat["scanned"]
            if n % 50 == 0:
                el = time.time() - t0
                spd = n / el if el else 0
                eta = (len(todo) - n) / spd / 60 if spd else 0
                print("  进度 %d/%d | 命中字 %d | 新增字形 %d | %.2f 字/秒 | 预计还需 %.0f 分钟"
                      % (n, len(todo), stat["hit"], stat["down"], spd, eta), flush=True)

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, todo))

    dt = time.time() - t0
    print("\n[indexphp] 完成：扫描 %d 字，命中 %d 字，新增字形 %d 张，耗时 %.1f 分钟"
          % (stat["scanned"], stat["hit"], stat["down"], dt / 60), flush=True)
    attr.save(os.path.join(OUT_DIR, "wa_attribution_indexphp.json"))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--all", action="store_true", help="含已有数据的字也重扫")
    a = ap.parse_args()
    main(limit=a.limit, workers=a.workers, only_missing=not a.all)
