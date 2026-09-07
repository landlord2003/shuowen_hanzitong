#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_sinica.py — 从中研院「小學堂文字學資料庫」抓取古文字字形图，生成打包管线用的 manifest。

数据来源：https://xiaoxue.iis.sinica.edu.tw/  (中央研究院 漢字構形資料庫 / 小學堂)
授权：CC-BY-SA 2.5 TW（可商用，须署名 + 衍生同授权）

⚠️ 运行前置：
  1. 本脚本须从「可访问小學堂」的网络运行（部分区域对小學堂有地理访问限制）。
  2. 安装依赖：pip install requests beautifulsoup4 pillow
  3. 爬取请遵守 robots 与合理速率（默认 0.3s 间隔），仅用于个人/产品字形补全。

小學堂库（URL 第一段）与 script 映射：
  jiaguwen  甲骨文   -> oracle-bone  (O_)
  jinwen    金文     -> bronze       (J_)
  jiandu    简牍帛书 -> bamboo-silk  (W_)   (页面段可能为 jiandu / chujian 等，见下)
  xiaozhuan 小篆     -> seal         (Z_)
  (kaishu 楷书 -> regular K_，本 App 楷书用系统字体渲染，可不抓)

每个库按 kaiOrder 从 1 递增抓取；页面中用 charname 关联现代字。
输出 manifest.jsonl：{"id":"<kaiOrder>","char":"<现代字>","script":"<script>","img":"<本地png路径>"}
"""

import argparse
import json
import os
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://xiaoxue.iis.sinica.edu.tw"
DB_SEGMENTS = {
    "jiaguwen": "oracle-bone",
    "jinwen": "bronze",
    "xiaozhuan": "seal",
    # 简牍帛书段名需实测；常见为 jiandu / chujian，脚本会尝试多个
}
BAMBOO_CANDIDATES = ["jiandu", "chujian", "jiandushu", "boshu"]

UA = "Mozilla/5.0 (compatible; ShuowenApp/1.0; +https://example.com)"


def fetch_page(segment, kai_order, timeout=30):
    url = f"{BASE}/{segment}?kaiOrder={kai_order}"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
    if r.status_code != 200:
        return None
    return r.text


def extract_images_and_char(html):
    """返回 (charname, [img_urls]) —— 小學堂页面为 SPA，图由 JS 加载；
    若初始 HTML 无图，则需改用其 XHR 接口（见 README 的『接口嗅探』章节）。"""
    soup = BeautifulSoup(html, "html.parser")
    char = None
    imgs = []
    # charname 通常在某 data 属性或标题区
    for tag in soup.find_all(attrs={"class": True}):
        cls = " ".join(tag.get("class", []))
        if "char" in cls.lower() or "title" in cls.lower():
            txt = tag.get_text(strip=True)
            if txt:
                char = txt
                break
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            imgs.append(src if src.startswith("http") else BASE + src)
    return char, imgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="data/sinica_raw")
    ap.add_argument("--limit", type=int, default=0, help="0=抓到无数据为止")
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--max-order", type=int, default=14000)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    manifest_path = os.path.join(args.out_dir, "manifest.jsonl")
    seen = 0

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    with open(manifest_path, "w", encoding="utf-8") as mf:
        for segment, script in DB_SEGMENTS.items():
            print(f"[scrape] 库 {segment} ({script}) ...")
            for order in range(1, args.max_order + 1):
                html = fetch_page(segment, order)
                if not html:
                    break
                char, imgs = extract_images_and_char(html)
                if not char and not imgs:
                    # 到达末尾或无数据
                    if order > 50:
                        break
                    continue
                saved = []
                for idx, url in enumerate(imgs):
                    ext = "png"
                    fname = f"{order}_{idx}.{ext}"
                    fpath = os.path.join(args.out_dir, fname)
                    try:
                        ir = session.get(url, timeout=30)
                        if ir.status_code == 200 and ir.content:
                            with open(fpath, "wb") as ff:
                                ff.write(ir.content)
                            saved.append(fpath)
                    except Exception:
                        pass
                    time.sleep(args.delay)
                if saved:
                    for sp in saved:
                        mf.write(json.dumps({"id": str(order), "char": char or "",
                                              "script": script, "img": sp},
                                             ensure_ascii=False) + "\n")
                    seen += len(saved)
                if args.limit and seen >= args.limit:
                    break
            if args.limit and seen >= args.limit:
                break
    print(f"[scrape] 完成，共 {seen} 条 -> {manifest_path}")


if __name__ == "__main__":
    main()
