// 解码 data/dataset.bin 的 CEDS header，统计 8105 字各古文字段覆盖率
// 仅解压 header（一个 zstd 帧）即可拿到 keys + characters 映射，无需解 body 区块
globalThis.self = globalThis;
const fs = require('fs');
const zlib = require('zlib');

const code = fs.readFileSync('data/dataset-reader.js', 'utf8');
const fn = new Function('self', 'require', 'module', 'exports', code);
const mod = { exports: {} };
fn(globalThis, require, mod, mod.exports);
const { DatasetReader } = globalThis.__CDS;

const bytes = new Uint8Array(fs.readFileSync('data/dataset.bin'));
const decompress = (buf) => {
  const b = Buffer.isBuffer(buf) ? buf : Buffer.from(buf);
  return zlib.zstdDecompressSync(b);
};
const reader = new DatasetReader(bytes, decompress);

// 基础信息
const header = reader; // 私有字段不可直接读；用公开方法
const ANCIENT = new Set(['glyphwiki', 'oracle-bone', 'bronze', 'bamboo-silk', 'seal', 'clerical']);
const stageCount = { 'glyphwiki': 0, 'oracle-bone': 0, 'bronze': 0, 'bamboo-silk': 0, 'seal': 0, 'clerical': 0 };
const charStageMap = {}; // char -> Set(scripts)

const data = JSON.parse(fs.readFileSync('data/characters.json', 'utf8'));
const chars = data.characters;

let noAncient = [];
let hasSourceOnly = []; // 仅有字源(glyphwiki) 无其他古文字形
let totalWithAnyAncient = 0;

for (const c of chars) {
  const setS = new Set();
  for (const ch of [c.char, c.trad]) {
    if (!ch) continue;
    const gs = reader.glyphsForCharacter(ch);
    for (const g of gs) if (ANCIENT.has(g.script)) setS.add(g.script);
  }
  charStageMap[c.char] = setS;
  const ancientList = [...setS];
  for (const s of ancientList) stageCount[s]++;
  if (setS.size === 0) {
    noAncient.push(c.char);
  } else {
    totalWithAnyAncient++;
    if (setS.size === 1 && setS.has('glyphwiki')) hasSourceOnly.push(c.char);
  }
}

const report = {
  total: chars.length,
  stageCount,
  stagePercent: Object.fromEntries(Object.entries(stageCount).map(([k, v]) => [k, +(v / chars.length * 100).toFixed(1)])),
  noAncientCount: noAncient.length,
  noAncientPercent: +(noAncient.length / chars.length * 100).toFixed(1),
  hasSourceOnlyCount: hasSourceOnly.length,
  totalWithAnyAncient,
  noAncientSample: noAncient.slice(0, 300)
};

// 缺失字按六书分布（洞察）
const liushuDist = {};
for (const c of chars) {
  if (charStageMap[c.char].size === 0) {
    liushuDist[c.liushu] = (liushuDist[c.liushu] || 0) + 1;
  }
}
report.noAncientByLiushu = liushuDist;

console.log(JSON.stringify(report, null, 2));

// 写出逐字阶段映射（供 Python 合并字体 cmap 计算有效覆盖率）
const perChar = {};
for (const c of chars) {
  perChar[c.char] = [...charStageMap[c.char]];
}
fs.writeFileSync('data/_dataset_stages.json', JSON.stringify(perChar));

// 写出缺字清单（仅字源、无真迹古文字段）供产品嵌入
fs.writeFileSync('data/glyph_missing.json', JSON.stringify({ count: hasSourceOnly.length, chars: hasSourceOnly }, null, 0));
console.log('\n[wrote] data/_dataset_stages.json (per-char stages)');
console.log('[wrote] data/glyph_missing.json  only-source chars=', hasSourceOnly.length);
