# -*- coding: utf-8 -*-
"""一次性构建 A1 方案的静态资源：
1) 把 DatasetReader (ES module) 转成 IIFE 版 (普通 <script> 可加载，file:// 双击可用)
2) 复制 dataset.bin 到项目 data/
3) 复制 fzstd UMD 到项目 data/
"""
import shutil
import os

BASE = r"D:\WorkBuddy\projects\说文解字"
PKG = os.path.join(BASE, ".workbuddy", "dataset-1bit", "node_modules", "character-evolution-dataset-1bit")
DATA = os.path.join(BASE, "data")

SRC_MJS = os.path.join(PKG, "dist", "dataset-B3c26RiO.mjs")
SRC_BIN = os.path.join(PKG, "dataset.bin")
SRC_FZSTD = os.path.join(BASE, ".workbuddy", "dataset-1bit", "node_modules", "fzstd", "umd", "index.js")

DST_READER = os.path.join(DATA, "dataset-reader.js")
DST_BIN = os.path.join(DATA, "dataset.bin")
DST_FZSTD = os.path.join(DATA, "fzstd.umd.js")

# 1) 转 IIFE
with open(SRC_MJS, "r", encoding="utf-8") as f:
    code = f.read()

lines = code.split("\n")
body_lines = [l for l in lines if not l.strip().startswith("import ")]
body_lines = [l for l in body_lines if not l.strip().startswith("export ")]
body = "\n".join(body_lines).strip()

header = """/* 精简浏览器端 dataset reader（IIFE，普通 <script> 可加载，file:// 双击可用）
 * 依赖：全局 fzstd（先加载 fzstd.umd.js）
 * 代码库：character-evolution-dataset-1bit（MIT，作者 Leon Si）——仅读取/解码逻辑
 * 数据来源：已切换为「中央研究院漢字構形資料庫 / 小學堂」（CC BY-SA 2.5 TW，可商用，须署名 + 衍生同授权）
 *   旧版非商业授权字形图已下架，禁止再拷入 dataset.bin
 */
(function (global) {
"use strict";
var decompress = (global.fzstd && global.fzstd.decompress) ? global.fzstd.decompress : null;
"""

footer = """
var SCRIPT_METADATA = {
  "oracle-bone": { chinese: "甲骨文" },
  "bronze": { chinese: "金文" },
  "bamboo-silk": { chinese: "简牍帛书" },
  "seal": { chinese: "篆文" },
  "clerical": { chinese: "隶书" },
  "regular": { chinese: "楷书" },
  "other": { chinese: "其他" }
};
global.__CDS = {
  DatasetReader: DatasetReader,
  MAGIC: MAGIC,
  parseScript: parseScript,
  SCRIPT_METADATA: SCRIPT_METADATA
};
})(typeof self !== "undefined" ? self : this);
"""

out = header + body + "\n" + footer
with open(DST_READER, "w", encoding="utf-8") as f:
    f.write(out)
print("[1/3] reader  ->", DST_READER, "(%d chars)" % len(out))

# 2) dataset.bin —— 已由 sinica_pipeline 管线管理，禁止拷入 EVOBC(NC) 原包
#    SRC_BIN 指向 npm 包里的 EVOBC 数据（CC BY-NC-SA 4.0），商用侵权，故此处不再覆盖。
#    合规空 bin（154B，MAGIC=CEDS0002，0 记录）现已就位，App 自动降级为纯文字字形演变。
#    待从可联网环境跑通 sinica_pipeline 后，再用合规字形覆盖本文件。
if os.path.exists(DST_BIN):
    print("[2/3] bin     -> 保留现有合规 dataset.bin (%d bytes)，跳过 EVOBC 拷贝" % os.path.getsize(DST_BIN))
else:
    print("[2/3] bin     -> 警告：缺失 dataset.bin，请运行 sinica_pipeline/gen_empty_bin.py 生成合规空包")

# 3) 复制 fzstd umd
shutil.copyfile(SRC_FZSTD, DST_FZSTD)
print("[3/3] fzstd   ->", DST_FZSTD, "(%d bytes)" % os.path.getsize(DST_FZSTD))

print("DONE")
