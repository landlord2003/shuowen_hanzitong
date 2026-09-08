# -*- coding: utf-8 -*-
"""
B 路线编排器：把多个公版/CC 数据源的字形图，打包为 App 可用的 data/dataset.bin。

调用方式见 README_B.md。本文件同时提供 --self-test 离线自测（合成数据验证打包链路，不依赖网络）。
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinica_pipeline"))
from pack_dataset import build_records, pack  # noqa: E402
from sources import Attribution  # noqa: E402
from adapters.wikimedia_seal import fetch as wm_fetch  # noqa: E402
from adapters.wikimedia_ancient import fetch as wa_fetch  # noqa: E402
from adapters.glyphwiki import fetch as gw_fetch  # noqa: E402
from adapters import scan_trace  # noqa: E402

SOURCE_FUNCS = {
    "wikimedia_seal": wm_fetch,
    "wikimedia_ancient": wa_fetch,
    "glyphwiki": gw_fetch,
    "scan_trace": scan_trace.fetch,
}


def _strip(v):
    if v is None:
        return ""
    return str(v).strip().strip("'\"")


def load_chars(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    chars = d["characters"] if isinstance(d, dict) and "characters" in d else d
    # 规整字段
    out = []
    for c in chars:
        out.append({
            "id": str(c.get("id")),
            "char": _strip(c.get("char")),
            "trad": _strip(c.get("trad")),
        })
    return out


def self_test():
    """合成 3 个字 + 3 张灰度 PNG，跑通 打包 -> 校验 全链路（不联网）。"""
    from PIL import Image
    import zstandard
    out_dir = os.path.join(HERE, "_selftest_tmp")
    os.makedirs(out_dir, exist_ok=True)
    fake_chars = [
        {"id": "1", "char": "一", "trad": "一"},
        {"id": "2", "char": "水", "trad": "水"},
        {"id": "3", "char": "火", "trad": "火"},
    ]
    manifest = []
    for c in fake_chars:
        png = os.path.join(out_dir, f"t_{c['id']}.png")
        Image.new("L", (160, 160), 255).save(png)
        manifest.append({"id": c["id"], "char": c["char"], "script": "seal", "img": png})
    records, characters = build_records(manifest)
    data = pack(records, characters)
    # 校验 CEDS0002
    assert data[:8] == b"CEDS0002", "MAGIC 校验失败"
    import struct
    hlen = struct.unpack("<I", data[8:12])[0]
    header = json.loads(zstandard.ZstdDecompressor().decompress(data[12:12 + hlen]))
    assert header["keys"].count("\n") + 1 == len(records), "keys 数不匹配"
    assert len(header["characters"]) == 3, "characters 数不匹配"
    print(f"[self-test] OK: bin={len(data)}B, records={len(records)}, chars={len(characters)}")
    # 写出到临时便于人工查看
    bin_path = os.path.join(HERE, "_selftest_dataset.bin")
    with open(bin_path, "wb") as f:
        f.write(data)
    print(f"[self-test] 样例 bin 已写: {bin_path}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", required=False, help="App 的 data/characters.json")
    ap.add_argument("--sources", required=False, help="逗号分隔: wikimedia_seal,glyphwiki,scan_trace")
    ap.add_argument("--out", required=False, help="输出 data/dataset.bin")
    ap.add_argument("--scan-root", default=None)
    ap.add_argument("--bbox-map", default=None)
    ap.add_argument("--limit", type=int, default=None, help="调试：只处理前 N 字")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    missing = [n for n, v in (("--chars", args.chars), ("--sources", args.sources), ("--out", args.out)) if not v]
    if missing:
        ap.error("以下参数必需: " + ", ".join(missing))
    chars = load_chars(args.chars)
    if args.limit:
        chars = chars[:args.limit]
    attr = Attribution()
    manifest = []
    out_dir = os.path.join(HERE, "_glyph_tmp")
    os.makedirs(out_dir, exist_ok=True)

    for name in [s.strip() for s in args.sources.split(",") if s.strip()]:
        fn = SOURCE_FUNCS.get(name)
        if not fn:
            print("忽略未知源:", name)
            continue
        kw = {}
        if name == "scan_trace":
            if not (args.scan_root and args.bbox_map):
                print("scan_trace 需要 --scan-root 与 --bbox-map，跳过")
                continue
            kw = {"scan_root": args.scan_root, "bbox_map": args.bbox_map}
        print(f"[fetch] {name} ...")
        recs = fn(chars, out_dir, attribution=attr, limit=args.limit, **kw)
        print(f"  -> {len(recs)} 条")
        manifest.extend(recs)

    # 去重：同一 (id, script) 保留先到的
    seen, ded = set(), []
    for m in manifest:
        k = (m["id"], m["script"])
        if k in seen:
            continue
        seen.add(k)
        ded.append(m)
    print(f"[manifest] 去重后 {len(ded)} 条")

    records, characters = build_records(ded)
    data = pack(records, characters)
    out_dir2 = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir2, exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(data)
    attr.save(os.path.join(out_dir2, "dataset.attribution.json"))
    print(f"[pack] 写出 {args.out} ({len(data)} bytes), 字 {len(characters)}")
    print(f"[pack] 署名文件 dataset.attribution.json 已生成")


if __name__ == "__main__":
    main()
