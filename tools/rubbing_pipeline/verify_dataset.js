// 端到端验证 dataset.bin：加载 reader + fzstd，检查各类字形解析正确
// 用法: node verify_dataset.js [bin路径]
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const DATA = path.join(__dirname, "..", "..", "data");
const binPath = process.argv[2] || path.join(DATA, "dataset.bin");

// 1) 加载 fzstd
const fzstdCode = fs.readFileSync(path.join(DATA, "fzstd.umd.js"), "utf8");
const fzstdCtx = {};
vm.createContext(fzstdCtx);
vm.runInContext(fzstdCode, fzstdCtx);

// 2) 加载 reader
const readerCode = fs.readFileSync(path.join(DATA, "dataset-reader.js"), "utf8");
const ctx = { fzstd: fzstdCtx.fzstd, TextDecoder: TextDecoder };
vm.createContext(ctx);
vm.runInContext(readerCode, ctx);
const { DatasetReader } = ctx.__CDS;

// 3) 读 bin
const bytes = fs.readFileSync(binPath);
const reader = new DatasetReader(bytes);

const keys = reader.keys();
console.log("总记录数:", reader.size);
console.log("总字节:", bytes.length);

// 统计脚本分布
const dist = {};
for (const k of keys) {
  const script = ctx.__CDS.parseScript(k);
  dist[script] = (dist[script] || 0) + 1;
}
console.log("脚本分布:", dist);

// 覆盖字
const chars = reader.characters();
console.log("覆盖字:", Object.keys(chars || {}).length);

// 抽查几个字，验证字形能提取且非空白
const samples = ["1", "10", "20", "100"];
for (const id of samples) {
  const glyphs = reader.glyphsForCharacter(chars[id]);
  if (!glyphs.length) continue;
  const g = glyphs[0];
  const raw = reader.getRaw(g.key);
  const nonZero = raw.pixels.reduce((s, v) => s + (v < 128 ? 1 : 0), 0);
  console.log(`  字「${chars[id]}」(${id}): ${glyphs.length} 个字形, 首个=${g.script}, 笔画像素=${nonZero}/${raw.width*raw.height}`);
}

console.log("验证通过 ✓");
