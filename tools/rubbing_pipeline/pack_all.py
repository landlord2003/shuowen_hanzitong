# -*- coding: utf-8 -*-
"""从 _glyph_tmp/ 的所有 PNG 直接重新打包 dataset.bin。

扫描三类文件：
    gw_{id}.png   -> GlyphWiki「字源」(glyphwiki)      —— 8105 字，CC BY-SA 2.1 JP
    wm_{id}.png   -> Wikimedia 小篆 (seal)             —— 旧 seal 适配器，公版
    wa_{id}_{script}.png -> Wikimedia 古文字形          —— 新 ancient 适配器，公版
        script ∈ {oracle-bone, bronze, seal, bamboo-silk}

按 (id, script) 去重（优先 gw 字源 > wm 小篆 > wa 古形，同一 script 保留先到），
打包为 CEDS0002，并生成 attribution.json。
"""
import os, sys, json, glob, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sinica_pipeline"))
from pack_dataset import pack, build_records
from sources import LICENSES

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_glyph_tmp")
DATA = r"E:\Workbuddy\说文解字\data"

def main():
    manifest = []
    # 1) glyphwiki（字源）
    for png in sorted(glob.glob(os.path.join(TMP, "gw_*.png"))):
        m = re.match(r"gw_(\d+)\.png$", os.path.basename(png))
        if m:
            manifest.append({"id": m.group(1), "char": None, "script": "glyphwiki", "img": png})
    # 2) wm seal（旧小篆）
    for png in sorted(glob.glob(os.path.join(TMP, "wm_*.png"))):
        m = re.match(r"wm_(\d+)\.png$", os.path.basename(png))
        if m:
            manifest.append({"id": m.group(1), "char": None, "script": "seal", "img": png})
    # 3) wa ancient（新古文字形，分类反查）
    for png in sorted(glob.glob(os.path.join(TMP, "wa_*.png"))):
        m = re.match(r"wa_(\d+)_(.+)\.png$", os.path.basename(png))
        if m:
            manifest.append({"id": m.group(1), "char": None, "script": m.group(2), "img": png})
    # 4) wb ancient（thumb.php 盲猜）
    for png in sorted(glob.glob(os.path.join(TMP, "wb_*.png"))):
        m = re.match(r"wb_(\d+)_(.+)\.png$", os.path.basename(png))
        if m:
            manifest.append({"id": m.group(1), "char": None, "script": m.group(2), "img": png})

    # 用 characters.json 反查每个 id 的现代字
    chars_json = json.load(open(os.path.join(DATA, "characters.json"), encoding="utf-8"))
    chars = chars_json["characters"] if isinstance(chars_json, dict) else chars_json
    id2char = {str(c["id"]): (c.get("char") or "").strip() for c in chars}
    for m in manifest:
        m["char"] = id2char.get(m["id"], "")

    # 去重：同一 (id, script) 保留先到的（gw > wm > wa 顺序已定）
    seen = set()
    ded = []
    for m in manifest:
        k = (m["id"], m["script"])
        if k in seen:
            continue
        seen.add(k)
        ded.append(m)

    print(f"[pack_all] manifest 总数 {len(manifest)}，去重后 {len(ded)}")
    from collections import Counter
    dist = Counter(m["script"] for m in ded)
    print(f"[pack_all] 脚本分布: {dict(dist)}")

    records, characters = build_records(ded)
    data = pack(records, characters)
    out = os.path.join(DATA, "dataset.bin")
    with open(out, "wb") as f:
        f.write(data)
    print(f"[pack_all] 写出 {out} ({len(data)} bytes), 覆盖字 {len(characters)}")

    # attribution
    from sources import Attribution
    attr = Attribution()
    for m in ded:
        s = m["script"]
        if s == "glyphwiki":
            attr.add(s, "GlyphWiki", LICENSES["cc_by_sa_2_1_jp"])
        else:
            attr.add(s, "Wikimedia Commons (Ancient Chinese characters)", LICENSES["pd"])
    attr.save(os.path.join(DATA, "dataset.attribution.json"))
    print(f"[pack_all] attribution 已生成")

if __name__ == "__main__":
    main()
