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
 * 来源：character-evolution-dataset-1bit (底层 EVOBC, CC BY-NC-SA 4.0)
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

# 2) 复制 dataset.bin
shutil.copyfile(SRC_BIN, DST_BIN)
print("[2/3] bin     ->", DST_BIN, "(%d bytes)" % os.path.getsize(DST_BIN))

# 3) 复制 fzstd umd
shutil.copyfile(SRC_FZSTD, DST_FZSTD)
print("[3/3] fzstd   ->", DST_FZSTD, "(%d bytes)" % os.path.getsize(DST_FZSTD))

print("DONE")
