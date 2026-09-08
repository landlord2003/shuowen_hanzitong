# -*- coding: utf-8 -*-
"""从已抓取好的 PNG（_glyph_tmp/gw_{id}.png）直接打包 dataset.bin，避免重复联网。

适用：glyphwiki 适配器已把 8105 张 SVG 栅格化为 PNG，但因沙箱 bulk-delete 保护导致
打包步骤崩溃；本脚本跳过联网，直接用磁盘上已有的 PNG 补完打包。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinica_pipeline"))
from pack_dataset import build_records, pack  # noqa: E402
from sources import Attribution, LICENSES  # noqa: E402

CHARS = json.load(open(os.path.join(HERE, "..", "..", "data", "characters.json"), encoding="utf-8"))["characters"]
TMP = os.path.join(HERE, "_glyph_tmp")
OUT = os.path.join(HERE, "..", "..", "data", "dataset.bin")
ATTR_OUT = os.path.join(HERE, "..", "..", "data", "dataset.attribution.json")

manifest = []
attr = Attribution()
for c in CHARS:
    cid = str(c.get("id"))
    ch = (c.get("char") or "").strip()
    p = os.path.join(TMP, "gw_%s.png" % cid)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        manifest.append({"id": cid, "char": ch, "script": "glyphwiki", "img": p})
        attr.add("glyphwiki", "GlyphWiki", LICENSES["cc_by_sa_2_1_jp"])

print("[pack] 命中 PNG: %d / %d" % (len(manifest), len(CHARS)))
records, characters = build_records(manifest)
data = pack(records, characters)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "wb").write(data)
attr.save(ATTR_OUT)
print("[pack] 写出 %s (%d bytes)，字 %d，records %d" % (OUT, len(data), len(characters), len(records)))
