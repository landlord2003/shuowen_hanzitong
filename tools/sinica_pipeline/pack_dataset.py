#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pack_dataset.py — 将字形图打包为 CEDS0002 二进制容器（与 character-evolution-dataset-1bit 完全兼容）

本脚本是「说文解字」App 字形图「换源落地」管线的打包环节。
数据来源：台湾中央研究院 漢字構形資料庫 / 小學堂文字學資料庫
授权：CC-BY-SA 2.5 TW（创用CC 姓名标示-相同方式分享 台湾 2.5），可商用，须署名 + 衍生同授权。

CEDS0002 文件格式（逆向自 dataset-reader.js）：
  [ MAGIC "CEDS0002" 8B ][ headerLen u32 LE ][ header zstd ][ block0 zstd ][ block1 zstd ] ...
  header(JSON, 列式):
    keys:        "id/PREFIX_name\nid/PREFIX_name\n..."  (换行分隔)
    widths:     [w0, w1, ...]
    heights:    [h0, h1, ...]
    channels:   [c0, c1, ...]   (1=灰度, 3=RGB)
    blockSize:  每块记录数
    blocks:     [{fileOffset, compressedLength}, ...]   (fileOffset 相对 body 起点)
    windowLog:  0
    characters: {"id": "字", ...}   (id -> 现代字，App 据此反查字形)
    quantizeLevels / maxSide / blackWhite: 可空/False

key 命名约定（dataset-reader.js parseScript）：
    O_ = 甲骨文(oracle-bone)
    J_ = 金文(bronze)
    W_ = 简牍帛书(bamboo-silk)
    Z_ = 篆文(seal)
    L_ = 隶书(clerical)
    K_ / X_ = 楷书(regular)
App 渲染顺序: 甲骨 -> 金文 -> 简帛 -> 篆 -> 隶 -> 楷

用法：
    python pack_dataset.py --manifest manifest.jsonl --out data/dataset.bin
manifest 每行: {"id":"1","char":"一","script":"oracle-bone","img":"path.png"}
   或传目录（脚本会按文件名推断）。
"""

import argparse
import json
import os
import struct
import sys

import zstandard
from PIL import Image

MAGIC = b"CEDS0002"
SCRIPT_PREFIX = {
    "oracle-bone": "O_",
    "bronze": "J_",
    "bamboo-silk": "W_",
    "seal": "Z_",
    "clerical": "L_",
    "regular": "K_",
}


def load_image_as_gray(path, max_side=160, threshold=128):
    """加载图片 -> 1 通道 8bit 灰度像素(0/255)，黑底白字或白底黑字统一成黑字白底(便于 App 黑底显示反向)。"""
    im = Image.open(path).convert("L")  # 灰度
    # 等比缩放到 max_side 以内
    w, h = im.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    px = im.load()
    w, h = im.size
    out = bytearray(w * h)
    # 判断背景：取四角均值，亮=白底 -> 需要反相使字为黑(0)
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    bg_bright = sum(corners) / len(corners) > 127
    for y in range(h):
        for x in range(w):
            v = px[x, y]
            if bg_bright:
                v = 255 - v  # 反相：字变黑
            out[y * w + x] = 0 if v < threshold else 255
    return w, h, bytes(out)


def build_records(manifest):
    """manifest: list of dict(id, char, script, img) -> (records, characters)"""
    records = []
    characters = {}
    for m in manifest:
        sid = m["id"]
        char = m["char"]
        script = m["script"]
        prefix = SCRIPT_PREFIX.get(script, "K_")
        w, h, px = load_image_as_gray(m["img"])
        key = f"{sid}/{prefix}{script}"
        records.append({"key": key, "width": w, "height": h, "channels": 1, "pixels": px})
        characters[sid] = char
    return records, characters


def pack(records, characters, block_size=1024):
    keys = [r["key"] for r in records]
    widths = [r["width"] for r in records]
    heights = [r["height"] for r in records]
    channels = [r["channels"] for r in records]
    raws = [r["pixels"] for r in records]

    blocks = []
    body = bytearray()
    n = len(records)
    for i in range(0, n, block_size):
        chunk = raws[i : i + block_size]
        raw_concat = b"".join(chunk)
        comp = zstandard.ZstdCompressor().compress(raw_concat)
        blocks.append({"fileOffset": len(body), "compressedLength": len(comp)})
        body += comp

    header = {
        "keys": "\n".join(keys),
        "widths": widths,
        "heights": heights,
        "channels": channels,
        "blockSize": block_size,
        "blocks": blocks,
        "windowLog": 0,
        "characters": characters,
        "quantizeLevels": None,
        "maxSide": None,
        "blackWhite": True,
    }
    header_bytes = json.dumps(header, ensure_ascii=False).encode("utf-8")
    comp_header = zstandard.ZstdCompressor().compress(header_bytes)

    out = bytearray()
    out += MAGIC
    out += struct.pack("<I", len(comp_header))
    out += comp_header
    out += body
    return bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="JSONL: {id,char,script,img}")
    ap.add_argument("--out", required=True, help="输出 dataset.bin 路径")
    ap.add_argument("--block-size", type=int, default=1024)
    args = ap.parse_args()

    manifest = []
    with open(args.manifest, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                manifest.append(json.loads(line))
    print(f"[pack] 读取 manifest: {len(manifest)} 条")

    records, characters = build_records(manifest)
    print(f"[pack] 构建记录: {len(records)} 张图, {len(characters)} 个字")
    data = pack(records, characters, args.block_size)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(data)
    print(f"[pack] 写出 {args.out} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
