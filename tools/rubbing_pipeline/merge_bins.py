# -*- coding: utf-8 -*-
"""合并多个 CEDS0002 dataset.bin（按 key 去重，保留先到的）。

用途：A 路线先交付「字源」bin，B 路线后续补全甲骨/金文/篆真迹 bin，
      用本脚本把多份 bin 合并为 App 最终使用的单一 data/dataset.bin。

用法：
    python merge_bins.py --bins data/dataset_glyphwiki.bin,data/dataset_b_route.bin \
        --out data/dataset.bin

注意：合并后 characters 映射取并集；同一 (id,script) 的 key 只保留先出现的。
"""
import argparse
import json
import os
import struct
import sys
import zstandard

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinica_pipeline"))
from pack_dataset import pack  # noqa: E402


def decode_bin(path):
    data = open(path, "rb").read()
    if data[:8] != b"CEDS0002":
        raise SystemExit("不是 CEDS0002 文件: %s" % path)
    hlen = struct.unpack("<I", data[8:12])[0]
    header = json.loads(zstandard.ZstdDecompressor().decompress(data[12:12 + hlen]))
    body = data[12 + hlen:]
    keys = header["keys"].split("\n") if header.get("keys") else []
    W, H, ch = header["widths"], header["heights"], header["channels"]
    bs = header["blockSize"]
    blocks = header["blocks"]

    def block_bytes(bi):
        ref = blocks[bi]
        start = body[ref["fileOffset"]:ref["fileOffset"] + ref["compressedLength"]]
        return zstandard.ZstdDecompressor().decompress(start)

    records = []
    off = 0
    for i in range(len(keys)):
        blk = i // bs
        if i % bs == 0:
            off = 0
        w, h0, c = W[i], H[i], ch[i]
        length = w * h0 * c
        raw = block_bytes(blk)[off:off + length]
        records.append({"key": keys[i], "width": w, "height": h0, "channels": c, "pixels": bytes(raw)})
        off += length
    chars = dict(header.get("characters") or {})
    return records, chars


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bins", required=True, help="逗号分隔的 bin 路径，按出现顺序合并（先到优先）")
    ap.add_argument("--out", required=True, help="输出合并后的 dataset.bin")
    args = ap.parse_args()

    all_recs = []
    chars = {}
    seen = set()
    for p in [x.strip() for x in args.bins.split(",") if x.strip()]:
        recs, c = decode_bin(p)
        for r in recs:
            if r["key"] in seen:
                continue
            seen.add(r["key"])
            all_recs.append(r)
        chars.update(c)
        print("  读入 %s : %d 条" % (p, len(recs)))

    data = pack(all_recs, chars)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    open(args.out, "wb").write(data)
    print("合并完成: %d 条记录 -> %s (%d bytes)" % (len(all_recs), args.out, len(data)))


if __name__ == "__main__":
    main()
