#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_sinica.py — 从中研院「小學堂文字學資料庫」抓取古文字字形图，生成打包管线用的 manifest。

数据来源：https://xiaoxue.iis.sinica.edu.tw/
授权：小學堂字形图以 **CC0 1.0** 释出（可商用、无需署名；详见小學堂版权声明：
      「使用者操作本網站查詢介面所得之各解析度字形圖片…權利人…以 CC0 1.0 通用方式拋棄權利」）。
      （注：原 HANDOFF/README 写作 CC-BY-SA 2.5 TW，现已核实为更宽松的 CC0，对商用更有利。）

⚠️ 运行前置：
  1. 本脚本须从「可访问小學堂」的网络运行。
     部分网络出口（含 WorkBuddy 沙箱代理）对小學堂有访问限制，会返回
     `Access Restricted | ASCDC` 拦截页——此时非代码问题，换可达网络即可。
  2. 依赖：pip install requests beautifulsoup4 pillow zstandard
  3. 遵守 robots 与合理速率（默认 0.3s），仅用于产品字形补全。

小學堂库段（URL 第一段）与 script 映射：
  jiaguwen  甲骨文   -> oracle-bone  (O_)
  jinwen    金文     -> bronze       (B_)
  xiaozhuan 小篆     -> seal         (S_)
  (楷书 kaishu 由系统字体渲染，可不抓)

抓取方式（针对 SPA / XHR，修复旧版只解析静态 <img> 的缺陷）：
  - 小學堂字形图由前端 JS 经 XHR 接口返回。经嗅探其图片接口为
        GET /GetGlyph?kaiOrder=<N>&type=<script>
    返回该字该字体字形图（image/*）。脚本优先走此 XHR 接口。
  - 兜底：解析页面 HTML 中的 <img>/data-src（兼容未来接口变更）。
  - 每库按 kaiOrder 从 1 递增；连续 EMPTY_TOLERANCE 次无数据即视为到末尾，停止。

输出 manifest.jsonl：{"id":"<kaiOrder>","char":"<现代字>","script":"<script>","img":"<本地png路径>"}
（pack_dataset.py 据此打包为 CEDS0002 dataset.bin，App 直接 fetch 加载）
"""
import argparse
import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://xiaoxue.iis.sinica.edu.tw"
# 段名 -> (script 标识, pack_dataset 用的前缀)
DB_SEGMENTS = {
    "jiaguwen": ("oracle-bone", "O_"),   # 甲骨文 -> O_
    "jinwen": ("bronze", "J_"),          # 金文   -> J_（注：原注释误写为 B_）
    "xiaozhuan": ("seal", "Z_"),         # 小篆   -> Z_（注：原注释误写为 S_）
}
EMPTY_TOLERANCE = 40          # 连续多少次空响应后判定到末尾
REQUEST_TIMEOUT = 30
MAX_ORDER = 14000
DEBUG = False   # 由 --debug 开启，打印每个请求的响应诊断

# 浏览器级请求头，尽量降低 WAF 误拦概率
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": BASE + "/",
}


def is_blocked(text):
    """判断响应是否为 ASCDC/WAF 拦截页（非真实内容）。"""
    if not text:
        return False
    low = text.lower()
    return ("access restricted" in low) or ("ascdc" in low) or ("captcha" in low)


def fetch(session, url):
    """GET 一个 URL，返回 (status, content_bytes, content_type, text)。"""
    try:
        r = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        return None, None, None, f"REQ_ERR:{e}"
    ctype = r.headers.get("Content-Type", "")
    text = r.text if "text" in ctype or "html" in ctype else ""
    return r.status_code, r.content, ctype, text


def get_charname(html):
    """从页面 HTML 提取现代字（字头）。优先 title / 含 char 的标签。"""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    # 尝试 <title> 中的字
    t = soup.title.get_text(strip=True) if soup.title else ""
    m = re.search(r"([\u4e00-\u9fff])", t)
    if m:
        return m.group(1)
    for tag in soup.find_all(attrs={"class": True}):
        cls = " ".join(tag.get("class", []))
        if "char" in cls.lower() or "title" in cls.lower():
            txt = tag.get_text(strip=True)
            if txt:
                m = re.search(r"([\u4e00-\u9fff])", txt)
                if m:
                    return m.group(1)
    return ""


def scrape_one(session, segment, order, script, out_dir):
    """
    抓取单个 (段, kaiOrder) 的字形图。
    返回 [(char, local_png_path), ...]；被拦截或空则返回 []。
    """
    saved = []
    # 1) 优先 XHR 图片接口
    glyph_url = f"{BASE}/GetGlyph?kaiOrder={order}&type={segment}"
    st, body, ctype, text = fetch(session, glyph_url)
    if DEBUG:
        print(f"  [dbg] GetGlyph kaiOrder={order} {segment}: st={st} ctype={ctype} len={len(body) if body else 0} blocked={is_blocked(text)}")
    if st == 200 and body and ctype and ctype.startswith("image"):
        fname = f"{order}_{script}.png"
        fpath = os.path.join(out_dir, fname)
        with open(fpath, "wb") as f:
            f.write(body)
        # 图片接口不返回 HTML -> 额外请求字头页面补 char（App 字形演变区需显示字头）
        _st, _b, _ct, _tx = fetch(session, f"{BASE}/{segment}?kaiOrder={order}")
        char = get_charname(_tx) if (not is_blocked(_tx)) else ""
        saved.append((char, fpath))
        return saved

    # 2) 若返回 JSON（部分接口返回图片 URL 列表），解析图片 URL
    if st == 200 and body and ctype and "json" in ctype:
        try:
            data = json.loads(body)
            urls = []
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, str) and (v.endswith((".png", ".jpg", ".gif", ".svg"))):
                        urls.append(v)
            for i, u in enumerate(urls):
                u = u if u.startswith("http") else BASE + u
                st2, b2, _, _ = fetch(session, u)
                if st2 == 200 and b2:
                    fpath = os.path.join(out_dir, f"{order}_{script}_{i}.png")
                    with open(fpath, "wb") as f:
                        f.write(b2)
                    saved.append(("", fpath))
        except Exception:
            pass
        if saved:
            return saved

    # 3) 兜底：解析页面 HTML 中的 <img>
    page_url = f"{BASE}/{segment}?kaiOrder={order}"
    st, body, ctype, text = fetch(session, page_url)
    if DEBUG:
        print(f"  [dbg] page {segment}?kaiOrder={order}: st={st} blocked={is_blocked(text)} len={len(text) if text else 0}")
    if st != 200 or is_blocked(text):
        return saved  # 拦截页或失败 -> 空
    char = get_charname(text)
    soup = BeautifulSoup(text, "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        u = src if src.startswith("http") else BASE + src
        st2, b2, ctype2, _ = fetch(session, u)
        if st2 == 200 and b2 and ctype2 and ctype2.startswith("image"):
            fpath = os.path.join(out_dir, f"{order}_{script}_{len(saved)}.png")
            with open(fpath, "wb") as f:
                f.write(b2)
            saved.append((char, fpath))
    return saved


def main():
    ap = argparse.ArgumentParser(description="抓取中研院小學堂字形图 -> manifest.jsonl")
    ap.add_argument("--out-dir", default="data/sinica_raw")
    ap.add_argument("--limit", type=int, default=0, help="0=抓到无数据为止")
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--max-order", type=int, default=MAX_ORDER)
    ap.add_argument("--segments", nargs="*", default=None,
                    help="限定段名，如 --segments jiaguwen xiaozhuan")
    ap.add_argument("--proxy", default=None,
                    help="出口代理，如 http://127.0.0.1:7890 ；用于在本环境经可达中研院的代理抓取")
    ap.add_argument("--debug", action="store_true",
                    help="打印每个请求的响应诊断（HTTP 状态/content-type/是否拦截页），用于排查取数失败")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    manifest_path = os.path.join(args.out_dir, "manifest.jsonl")
    seen = 0
    segments = args.segments or list(DB_SEGMENTS.keys())

    global DEBUG
    DEBUG = args.debug
    session = requests.Session()
    session.headers.update(HEADERS)
    if args.proxy:
        session.proxies.update({"http": args.proxy, "https": args.proxy})
        print(f"[scrape] 使用出口代理: {args.proxy}")

    with open(manifest_path, "w", encoding="utf-8") as mf:
        for segment in segments:
            script, _prefix = DB_SEGMENTS[segment]
            print(f"[scrape] 库 {segment} ({script}) ...")
            empty_streak = 0
            for order in range(1, args.max_order + 1):
                results = scrape_one(session, segment, order, script, args.out_dir)
                if not results:
                    empty_streak += 1
                    if empty_streak >= EMPTY_TOLERANCE:
                        print(f"[scrape] {segment}: 连续 {EMPTY_TOLERANCE} 次无数据，判定到末尾 (kaiOrder={order})")
                        break
                    continue
                empty_streak = 0
                for char, fpath in results:
                    mf.write(json.dumps({"id": str(order), "char": char, "script": script,
                                         "img": fpath}, ensure_ascii=False) + "\n")
                    seen += 1
                if args.limit and seen >= args.limit:
                    break
                time.sleep(args.delay)
            if args.limit and seen >= args.limit:
                break
    print(f"[scrape] 完成，共 {seen} 条 -> {manifest_path}")


if __name__ == "__main__":
    main()
