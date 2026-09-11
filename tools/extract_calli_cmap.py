"""提取 4 个书法家字体(楷/行/行草)的 cmap 覆盖集，门控书法欣赏区块的缺字回退。
输出 data/calli_glyphs.json：{family: [十进制码点...]}。
字体：data/fonts/{kai-MaShanZheng,xing-LongCang,xing-ZhiMangXing,xingcao-LiuJianMaoCao}.ttf
"""
import json, os
from fontTools.ttLib import TTFont

FONTS = {
    "MaShanZheng": "data/fonts/kai-MaShanZheng.ttf",
    "LongCang":    "data/fonts/xing-LongCang.ttf",
    "ZhiMangXing": "data/fonts/xing-ZhiMangXing.ttf",
    "LiuJianMaoCao": "data/fonts/xingcao-LiuJianMaoCao.ttf",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {}
for family, rel in FONTS.items():
    fp = os.path.join(ROOT, rel)
    if not os.path.exists(fp):
        print("MISSING", fp); continue
    f = TTFont(fp)
    cmap = f.getBestCmap()  # {codepoint(int): glyphName}
    out[family] = sorted(cmap.keys())
    print(f"OK {family}: {len(out[family])} codepoints")
    f.close()

dst = os.path.join(ROOT, "data", "calli_glyphs.json")
with open(dst, "w", encoding="utf-8") as fo:
    json.dump(out, fo, ensure_ascii=False, separators=(",", ":"))
print("wrote", dst)
