#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""格式自检：合成灰度像素 -> 打包 CEDS0002 -> 用 npm DatasetReader 还原验证。

不依赖 Pillow：直接构造 8x8 灰度像素。验证目标：
  1) 打包出的 bin 能被 character-evolution-dataset-1bit 的 DatasetReader 解析；
  2) glyphsForCharacter("一") 能返回甲骨文(O_)/篆文(Z_) 两个 key；
  3) getRaw 取回像素与写入一致。
同时验证「空数据集」(0 记录) 也能被安全解析。
"""
import json
import os
import struct
import sys
import zstandard

MAGIC = b"CEDS0002"

def make_record(key, char, w=8, h=8, pattern="diag"):
    px = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if pattern == "diag":
                v = 0 if x == y else 255
            elif pattern == "box":
                v = 0 if (x in (0, w-1) or y in (0, h-1)) else 255
            else:
                v = 0 if (x + y) % 2 == 0 else 255
            px[y * w + x] = v
    return {"key": key, "width": w, "height": h, "channels": 1, "pixels": bytes(px), "char": char}

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
        chunk = raws[i:i + block_size]
        raw_concat = b"".join(chunk)
        comp = zstandard.ZstdCompressor().compress(raw_concat)
        blocks.append({"fileOffset": len(body), "compressedLength": len(comp)})
        body += comp
    header = {
        "keys": "\n".join(keys),
        "widths": widths, "heights": heights, "channels": channels,
        "blockSize": block_size, "blocks": blocks, "windowLog": 0,
        "characters": characters, "quantizeLevels": None, "maxSide": None, "blackWhite": True,
    }
    hb = json.dumps(header, ensure_ascii=False).encode("utf-8")
    ch = zstandard.ZstdCompressor().compress(hb)
    out = bytearray()
    out += MAGIC
    out += struct.pack("<I", len(ch))
    out += ch
    out += body
    return bytes(out)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    # 真实测试集：一字多形
    recs = [
        make_record("1/O_oracle-bone", "一", pattern="diag"),
        make_record("1/Z_seal", "一", pattern="box"),
        make_record("2/O_oracle-bone", "二", pattern="check"),
    ]
    chars = {"1": "一", "2": "二"}
    data = pack(recs, chars)
    real_path = os.path.join(here, "test_dataset.bin")
    with open(real_path, "wb") as f:
        f.write(data)
    print(f"[test] 真实数据集: {len(data)} bytes, {len(recs)} 记录")

    # 空数据集测试
    empty = pack([], {})
    empty_path = os.path.join(here, "test_empty.bin")
    with open(empty_path, "wb") as f:
        f.write(empty)
    print(f"[test] 空数据集: {len(empty)} bytes, 0 记录")

    # 调用 Node 用 npm Reader 还原校验
    pkg = "D:/WorkBuddy/projects/说文解字/.workbuddy/dataset-1bit/node_modules/character-evolution-dataset-1bit"
    node = "C:/Users/吴自强/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"
    check_js = os.path.join(pkg, "_verify.cjs")
    with open(check_js, "w", encoding="utf-8") as f:
        f.write(r'''
const { DatasetReader } = require("character-evolution-dataset-1bit");
const { nodeDecompress } = require("character-evolution-dataset-1bit/node");
const fs = require("fs");
const path = process.argv[2];
const buf = fs.readFileSync(path);
const reader = new DatasetReader(new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength), nodeDecompress);
console.log("  size=", reader.size, "characters=", Object.keys(reader.characters()).length);
const g = reader.glyphsForCharacter("一");
console.log("  一字 字形 keys:", g.map(x => x.key + "(" + x.script + ")").join(", "));
if (g.length) {
  const raw = reader.getRaw(g[0].key);
  console.log("  getRaw", g[0].key, ":", raw.width + "x" + raw.height, "ch=" + raw.channels, "首像素=" + raw.pixels[0]);
}
''')
    print("[test] 校验真实数据集:")
    os.system(f'cd "{pkg}" && "{node}" "{check_js}" "{real_path}"')
    print("[test] 校验空数据集:")
    os.system(f'cd "{pkg}" && "{node}" "{check_js}" "{empty_path}"')
    print("[test] OK")
