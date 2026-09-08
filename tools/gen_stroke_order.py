#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 data/strokes.min.json —— 8105 字的笔顺 SVG 路径数据。

数据来源：Hanzi Writer Data（https://github.com/chanind/hanzi-writer-data，
MIT 许可，公有领域字形分解，可商用；仅取 strokes 字段的 SVG path，不含第三方字体）。

输出格式（极简，前端直接消费）：
    { "<汉字>": ["M...Z", "M...Z", ...], ... }   # 每个字 = 按书写顺序的笔画 path 数组

使用（需联网）：
    python tools/gen_stroke_order.py                 # 默认抓取全部 8105 字
    python tools/gen_stroke_order.py --limit 50     # 先小批量试跑
    python tools/gen_stroke_order.py --workers 8    # 调并发

说明：
- 字源 App 的「笔顺」区块会自动 fetch data/strokes.min.json；
  该文件不存在时，详情页显示「待补全」提示，不影响其他功能。
- 部分罕见字 Hanzi Writer Data 可能缺数据，脚本会跳过并在结尾报告缺失数。
- 运行需要网络（国内可换 CDN，见 BASE_URL）。
"""
import argparse
import json
import os
import sys
import urllib.request
from urllib.parse import quote
import concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS_JSON = os.path.join(ROOT, "data", "characters.json")
OUT_JSON = os.path.join(ROOT, "data", "strokes.min.json")
# Hanzi Writer Data 在 jsDelivr 上的原始数据（每字一个 JSON，含 strokes/medians）
BASE_URL = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0/{c}.json"
UA = {"User-Agent": "Mozilla/5.0 (shuowen-app stroke fetcher)"}


def fetch_one(ch):
    url = BASE_URL.format(c=quote(ch, safe=""))
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        strokes = data.get("strokes")
        if not strokes:
            return ch, None
        return ch, strokes
    except Exception:
        return ch, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 个字（试跑用）")
    ap.add_argument("--workers", type=int, default=8, help="并发数")
    ap.add_argument("--resume", action="store_true", help="若已存在输出则在其基础上补全缺失字")
    args = ap.parse_args()

    with open(CHARS_JSON, encoding="utf-8") as f:
        chars = json.load(f)["characters"]
    targets = [c["char"] for c in chars]
    if args.limit:
        targets = targets[: args.limit]

    result = {}
    if args.resume and os.path.exists(OUT_JSON):
        with open(OUT_JSON, encoding="utf-8") as f:
            result = json.load(f)
        targets = [t for t in targets if t not in result]
        print(f"[resume] 已有 {len(result)} 字，待补 {len(targets)} 字")

    missing = 0
    done = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for ch, strokes in ex.map(fetch_one, targets):
            if strokes:
                result[ch] = strokes
                done += 1
            else:
                missing += 1
            if (done + missing) % 500 == 0:
                print(f"  进度 {done+missing}/{len(targets)}  成功 {done} 缺失 {missing}")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

    print(f"完成：成功 {done} 字，缺失 {missing} 字")
    print(f"输出：{OUT_JSON}  ({os.path.getsize(OUT_JSON)//1024} KB)")
    if missing:
        print("提示：缺失字多为极罕见字，Hanzi Writer Data 未收录；可忽略或后续换源补充。")


if __name__ == "__main__":
    main()
