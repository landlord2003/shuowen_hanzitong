# -*- coding: utf-8 -*-
"""Wikimedia Commons「Ancient Chinese characters (ACC)」分类反查适配器。

与旧 wikimedia_seal.py（盲猜 {char}-seal.svg）不同，本适配器对每个字查
`Category:{汉字}` 分类，聚合该字在 ACC 项目下的**全部**字形文件，再按文件名
后缀映射到脚本类型：

    后缀                脚本(script)        说明
    -oracle*            oracle-bone       甲骨文（含 -oracle-western/-oracle-zhouyuan 变体）
    -bronze*            bronze            金文（含 -bronze-shang/spring/warring 变体）
    -seal / -bigseal    seal              小篆 / 大篆
    -silk / -slip       bamboo-silk       简牍 / 帛书
    -ancient / -zhou / -odd    other      其它古形（暂归 other，不渲染）

授权：ACC 项目全部 Public Domain / CC0，可自由商用（署名 appreciated 非强制）。

网络：走本机梯子（sources.make_session），Wikimedia 对 thumb.php 直链限流宽松，
但分类查询走 api.php，需控制并发与延迟。

断点续传：已存在的 png 直接复用（按 md5 文件名落盘），重复运行只补漏。
"""
import os
import json
import time
import hashlib

from sources import download_file, normalize_png, LICENSES, make_session

API = "https://commons.wikimedia.org/w/api.php"
THUMB = "https://commons.wikimedia.org/w/thumb.php?f={name}&w=512"

USER_AGENT = "rubbing-pipeline/1.0 (local research; contact: none)"
REQUEST_DELAY = 0.8  # 每字之间的延迟（秒），降低 api.php 限流概率

# 全局限流协调（线程共享）：一旦收到 429，所有线程冷却到 deadline 后再继续
import threading
_RATE = threading.Lock()
_COOLDOWN_UNTIL = 0.0  # 冷却截止时间戳（epoch 秒）


def _rate_wait():
    """若处于 429 冷却期，则阻塞等待。返回当前是否需等待。"""
    global _COOLDOWN_UNTIL
    while True:
        with _RATE:
            remain = _COOLDOWN_UNTIL - time.time()
        if remain <= 0:
            return
        time.sleep(min(remain, 5.0))


def _rate_backoff(retry_after=None):
    """收到 429 时全局退避。retry_after 为 Retry-After 秒数，默认 30s 起步。"""
    global _COOLDOWN_UNTIL
    wait = max(30.0, float(retry_after or 0))
    with _RATE:
        _COOLDOWN_UNTIL = time.time() + wait
    print(f"  [wikimedia_ancient] 收到 429，全局冷却 {wait:.0f}s ...", flush=True)

# 文件名后缀 -> 脚本类型（顺序即优先级，先匹配先得）
SUFFIX_MAP = [
    ("-oracle", "oracle-bone"),
    ("-bronze", "bronze"),
    ("-seal", "seal"),
    ("-bigseal", "seal"),
    ("-silk", "bamboo-silk"),
    ("-slip", "bamboo-silk"),
]

# 每种脚本每个字最多保留几张（oracle 常有 -oracle / -oracle-zhouyuan 多个变体）
MAX_PER_SCRIPT = 1


def _strip(v):
    if v is None:
        return ""
    return str(v).strip().strip("'\"")


def _md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _classify(filename):
    """根据文件名（去掉 File: 前缀）判断脚本类型；None 表示不相关。"""
    low = filename.lower()
    for suf, script in SUFFIX_MAP:
        if suf in low:
            return script
    return None


def _category_members(session, catname):
    """返回 Category:{catname} 下所有文件名（去掉 File: 前缀）。失败返回 []。
    处理 429 限流：读取 Retry-After 头做全局退避。"""
    files = []
    cont = {}
    attempts = 0
    while attempts < 3:
        _rate_wait()
        attempts += 1
        try:
            params = {
                "action": "query", "format": "json",
                "list": "categorymembers",
                "cmtitle": f"Category:{catname}",
                "cmtype": "file", "cmlimit": "500",
            }
            params.update(cont)
            r = session.get(API, params=params, timeout=30)
            if r.status_code == 429:
                ra = r.headers.get("Retry-After") or r.headers.get("retry-after")
                _rate_backoff(ra)
                attempts = 0  # 冷却后重试，不计入失败次数
                continue
            if "json" not in r.headers.get("content-type", ""):
                time.sleep(2)
                continue
            d = r.json()
            for m in d.get("query", {}).get("categorymembers", []):
                files.append(m["title"].replace("File:", ""))
            if "continue" in d:
                cont = d["continue"]
                time.sleep(0.3)
                continue
            return files
        except Exception:
            time.sleep(2)
    return files


def _resolve_char_names(char, trad_conv):
    """返回候选分类名列表：简体优先，繁体兜底（ACC 分类名通常为简体）。"""
    names = []
    if char:
        names.append(char)
    if trad_conv:
        try:
            t = trad_conv.convert(char)
            if t and t != char:
                names.append(t)
        except Exception:
            pass
    return names


def _opencc():
    try:
        import opencc
        return opencc.OpenCC("s2t")
    except Exception:
        return None


def fetch(chars, out_dir, attribution=None, limit=None, workers=3, **kw):
    """chars: list of dict(id,char,trad)。返回 manifest 列表（含多脚本，每字可多条）。"""
    os.makedirs(out_dir, exist_ok=True)
    results = []
    items = chars if limit is None else chars[:limit]
    session = make_session()
    session.headers.update({"User-Agent": USER_AGENT})
    delay = float(kw.get("delay", REQUEST_DELAY))
    trad_conv = _opencc()

    from concurrent.futures import ThreadPoolExecutor, as_completed

    # 复用 session 做并发，但 api.php 限流（429），worker 数低 + 全局限流退避
    def _process_one(c):
        ch = _strip(c.get("trad")) or _strip(c.get("char"))
        if not ch or len(ch) != 1:
            return []
        _rate_wait()  # 若处于冷却期，先等
        out = []
        seen_script = set()
        for catname in _resolve_char_names(ch, trad_conv):
            files = _category_members(session, catname)
            if not files:
                continue
            for f in files:
                script = _classify(f)
                if not script or script in seen_script:
                    continue
                # 下载 thumb.php PNG
                png_path = os.path.join(out_dir, f"wa_{c['id']}_{script}.png")
                if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
                    out.append({"id": str(c["id"]), "char": ch, "script": script, "img": png_path})
                    seen_script.add(script)
                    continue
                url = THUMB.format(name=f)
                if download_file(url, png_path, session=session, retries=2) and \
                        normalize_png(png_path, size=160, keep_alpha=True):
                    out.append({"id": str(c["id"]), "char": ch, "script": script, "img": png_path})
                    seen_script.add(script)
                    if attribution:
                        attribution.add(script, "Wikimedia Commons (ACC ancient script SVG)", LICENSES["pd"])
                if len(seen_script) >= MAX_PER_SCRIPT * 4:  # 安全上限
                    break
            if out:  # 任一分类名命中即停止（简/繁只需一个）
                break
        return out

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_process_one, c) for c in items]
        for f in as_completed(futs):
            recs = f.result()
            results.extend(recs)
            done += 1
            if done % 100 == 0:
                print(f"  [wikimedia_ancient] 已处理 {done}/{len(items)}，累计字形 {len(results)}")
            time.sleep(0.05)

    print(f"[wikimedia_ancient] 完成：处理 {len(items)} 字，累计字形 {len(results)} 条")
    return results


if __name__ == "__main__":
    # 独立自测：跑 30 字看命中
    import json as _json
    d = _json.load(open(r"E:\Workbuddy\说文解字\data\characters.json", encoding="utf-8"))
    chars = d["characters"] if isinstance(d, dict) else d
    recs = fetch(chars[:30], os.path.join(os.path.dirname(__file__), "..", "_glyph_tmp"), limit=30)
    from collections import Counter
    print("脚本分布:", Counter(r["script"] for r in recs))
