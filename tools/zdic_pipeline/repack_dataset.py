# -*- coding: utf-8 -*-
"""Plan2 修复版重打包（不重新抓取，只重打包）。

背景：上一版 repack() 把已经二值化的 _plan2_cache/*.png 又喂给
_img_proc.load_image_as_gray()，Otsu 在两灰度级直方图上退化到阈值 0，
导致所有金文记录被写成全 0 空图（verify 显示 nonzero=0）。

本脚本：
- 从 Plan1 基线 data/dataset.bin.bak6 读入；
- 缓存 PNG 本身已是干净的 0/255 掩码，直接用 PIL 读取（不再过 _img_proc）；
- 只替换金文记录，其余记录字节级不变；
- 校验 diffs=0、无坏尺寸、替换记录非空，通过才落盘。
"""
import os, sys, json, struct, shutil, traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import zstandard as zstd
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
BIN = os.path.join(ROOT, "data", "dataset.bin")
SRC = os.environ.get("SWJ_BASE_BIN") or BIN   # 基线 bin（默认用当前 dataset.bin）
CACHE = os.path.join(ROOT, "_plan2_cache")
# 允许命令行覆盖：python _repack_plan2b.py [cache_dir] [baseline_bin]
if len(sys.argv) > 1:
    CACHE = sys.argv[1]
if len(sys.argv) > 2:
    SRC = sys.argv[2]
OUT = os.path.join(ROOT, "_diag_out")
LOG = os.path.join(OUT, os.path.basename(CACHE) + "_repack.log")
MAGIC = b"CEDS0002"
MIN_NZ_RATIO = 0.0002
MAX_NZ_RATIO = 0.90

def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(m) + "\n")

def read_bin(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == MAGIC, "bad magic: %r" % data[:8]
    header_len = struct.unpack("<I", data[8:12])[0]
    body_offset = 12 + header_len
    header = json.loads(zstd.decompress(data[12:12 + header_len]))
    return data, header, body_offset

def load_cache_png(path):
    """缓存 PNG 已是 0/255 掩码，直接读，不走 Otsu。返回 (w,h,px) 或 None。"""
    im = Image.open(path)
    im = im.convert("L")
    w, h = im.size
    if w < 4 or h < 4 or w > 512 or h > 512:
        return None
    px = im.tobytes()
    nz = sum(1 for v in px if v > 0)
    r = nz / float(w * h)
    if not (MIN_NZ_RATIO < r < MAX_NZ_RATIO):
        return None
    # 归一化到 0/255
    return w, h, bytes(255 if v > 127 else 0 for v in px)

def main():
    os.makedirs(OUT, exist_ok=True)
    open(LOG, "w", encoding="utf-8").write("START\n")
    if not os.path.exists(SRC):
        log("FATAL: baseline missing " + SRC); return
    log("baseline: %s (%d bytes)" % (SRC, os.path.getsize(SRC)))

    data, header, body_offset = read_bin(SRC)
    keys = header["keys"].split("\n")
    n = len(keys)
    W, H, CH = header["widths"], header["heights"], header["channels"]
    block_size = header["blockSize"]
    blocks = header["blocks"]
    characters = header.get("characters", {})
    CH = list(CH)
    # 置换前的原始尺寸快照（W/H 与 header 里是同一列表对象，会被就地改写）
    W_orig = list(W)
    H_orig = list(H)

    bronze_keys = [k for k in keys if k.endswith("/J_bronze")]
    log("bronze keys: %d" % len(bronze_keys))

    # 解所有块
    decomp = []
    for bi, b in enumerate(blocks):
        raw_size = sum(W[i] * H[i] * CH[i] for i in range(bi * block_size, min((bi + 1) * block_size, n)))
        comp = data[body_offset + b["fileOffset"]: body_offset + b["fileOffset"] + b["compressedLength"]]
        decomp.append(zstd.decompress(comp, max_output_size=raw_size))

    # 收集缓存
    cache_files = [f for f in os.listdir(CACHE) if f.endswith(".png") and not f.startswith("_tmp_")]
    log("cache png files: %d" % len(cache_files))
    cache_char = set(f[:-4] for f in cache_files)

    replacements = {}
    stats = Counter()
    for key in bronze_keys:
        cid = key.rsplit("/", 1)[0]
        ch = characters.get(cid)
        if not ch:
            stats["no_char"] += 1; continue
        if ch not in cache_char:
            stats["no_cache"] += 1; continue
        r = load_cache_png(os.path.join(CACHE, ch + ".png"))
        if r is None:
            stats["bad_cache"] += 1; continue
        replacements[key] = r
        stats["ok"] += 1
    log("replacement stats: " + repr(dict(stats)))
    log("replacements ready: %d" % len(replacements))

    # 逐块替换
    changed, skipped_empty = [], 0
    for bi in range(len(blocks)):
        start = bi * block_size
        end = min(start + block_size, n)
        recs, pos = [], 0
        for i in range(start, end):
            stride = W[i] * H[i] * CH[i]
            recs.append(list(decomp[bi][pos:pos + stride]))
            pos += stride
        for i in range(start, end):
            key = keys[i]
            if key not in replacements:
                continue
            nw, nh, npx = replacements[key]
            if CH[i] != 1:
                skipped_empty += 1; continue
            if sum(1 for v in npx if v > 0) == 0:
                skipped_empty += 1; continue
            recs[i - start] = list(npx)
            W[i], H[i] = nw, nh
            changed.append(key)
        decomp[bi] = b"".join(bytes(r) for r in recs)

    log("bronze replaced: %d (skipped %d)" % (len(changed), skipped_empty))

    # 重压
    body = bytearray()
    new_blocks = []
    for raw_concat in decomp:
        comp = zstd.ZstdCompressor().compress(raw_concat)
        new_blocks.append({"fileOffset": len(body), "compressedLength": len(comp)})
        body += comp
    header["widths"], header["heights"], header["channels"] = W, H, CH
    header["blocks"] = new_blocks
    comp_header = zstd.ZstdCompressor().compress(json.dumps(header, ensure_ascii=False).encode("utf-8"))
    out = bytearray()
    out += MAGIC
    out += struct.pack("<I", len(comp_header))
    out += comp_header
    out += body

    tmp = BIN + ".plan2b"
    with open(tmp, "wb") as f:
        f.write(out)
    log("new bin size: %d (baseline %d)" % (len(out), len(data)))

    # ---- 校验（按块流式解压一次，避免逐 key 重复解压）----
    def stream(path):
        ds, hd, bo = read_bin(path)
        ks = hd["keys"].split("\n")
        ww, hh, cc = hd["widths"], hd["heights"], hd["channels"]
        bs, blks = hd["blockSize"], hd["blocks"]
        nn = len(ks)
        for bi, blk in enumerate(blks):
            raw_size = sum(ww[i] * hh[i] * cc[i] for i in range(bi * bs, min((bi + 1) * bs, nn)))
            comp = ds[bo + blk["fileOffset"]: bo + blk["fileOffset"] + blk["compressedLength"]]
            raw = zstd.decompress(comp, max_output_size=raw_size)
            pos = 0
            for i in range(bi * bs, min((bi + 1) * bs, nn)):
                stride = ww[i] * hh[i] * cc[i]
                yield ks[i], ww[i], hh[i], cc[i], raw[pos:pos + stride]
                pos += stride

    diffs, checked = 0, 0
    empty, baddim, matched = 0, 0, 0
    dimc = Counter()
    for (k1, w1, h1, c1, p1), (k2, w2, h2, c2, p2) in zip(stream(SRC), stream(tmp)):
        if k1 != k2:
            log("  KEY MISMATCH: %s vs %s" % (k1, k2)); diffs += 1; continue
        if k1 in replacements:
            rw, rh, rpx = replacements[k1]
            if (w2, h2, p2) != (rw, rh, rpx):
                log("  REPLACED RECORD MISMATCH: " + k1); diffs += 1
            else:
                matched += 1
            if sum(1 for v in p2 if v > 0) == 0:
                empty += 1
            if w2 <= 0 or h2 <= 0 or w2 > 512 or h2 > 512:
                baddim += 1
            dimc[(w2, h2)] += 1
            continue
        checked += 1
        if (w1, h1, p1) != (w2, h2, p2):
            diffs += 1
            if diffs <= 10:
                log("  DIFF (unexpected): " + k1)
    log("non-replaced checked: %d, diffs: %d" % (checked, diffs))
    log("replaced verified==cache: %d / %d" % (matched, len(replacements)))
    log("replaced empty glyphs (must be 0): %d" % empty)
    log("replaced bad dims (must be 0): %d" % baddim)
    log("replaced dim distribution (top 6): " + repr(dimc.most_common(6)))

    ok = (diffs == 0 and empty == 0 and baddim == 0
          and matched == len(replacements) and len(changed) > 0)
    if ok:
        os.replace(tmp, BIN)
        log("OK: wrote " + BIN)
    else:
        log("ABORT: temp kept at " + tmp)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("FATAL:\n" + traceback.format_exc())
        raise
