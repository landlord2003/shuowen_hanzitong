#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成合规「空但有效」的 dataset.bin（0 记录），替换 EVOBC 的 NC 侵权文件。
App 检测到 0 字形记录会自动降级为「楷/繁文字 + AI 演变说明」的文字版，零侵权风险。
待在可达网络跑通 scrape+pack 管线后，用真实中研院字形图覆盖即可。"""
import json
import struct
import sys
import zstandard

MAGIC = b"CEDS0002"

def build_empty():
    header = {
        "keys": "",
        "widths": [], "heights": [], "channels": [],
        "blockSize": 1024, "blocks": [], "windowLog": 0,
        "characters": {}, "quantizeLevels": None, "maxSide": None, "blackWhite": True,
    }
    hb = json.dumps(header, ensure_ascii=False).encode("utf-8")
    ch = zstandard.ZstdCompressor().compress(hb)
    out = bytearray()
    out += MAGIC
    out += struct.pack("<I", len(ch))
    out += ch
    return bytes(out)

if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "data/dataset.bin"
    data = build_empty()
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"[gen] 合规空 dataset.bin 已写出: {out_path} ({len(data)} bytes)")
