// 诊断：《说文》源结构 + trad 归属
const fs = require('fs');
const path = require('path');
const D = 'D:/WorkBuddy/projects/说文解字/.workbuddy/charlist/shuowen/data';

const files = fs.readdirSync(D).filter(f => f.endsWith('.json'));
const entries = [];
for (const f of files) {
  try { entries.push(JSON.parse(fs.readFileSync(path.join(D, f), 'utf8'))); } catch (e) { }
}
console.log('条目数:', entries.length);

const wordheadSet = new Set();
const variantMap = {};   // 重文wordhead -> {parent, expl}
const indexMap = {};     // index -> entry
for (const e of entries) {
  wordheadSet.add(e.wordhead);
  for (const v of (e.variants || [])) {
    if (v.wordhead) variantMap[v.wordhead] = { parent: e.wordhead, expl: v.explanation || '' };
  }
  for (const ix of (e.indexes || [])) {
    if (!indexMap[ix]) indexMap[ix] = e;
  }
}
console.log('wordhead 数:', wordheadSet.size);
console.log('variants(重文) 数:', Object.keys(variantMap).length);
console.log('indexes 键数:', Object.keys(indexMap).length);

// 看 indexes 到底装了什么
const sample = entries.find(e => e.wordhead === '一');
console.log('「一」indexes:', JSON.stringify(sample.indexes));

function diag(ch) {
  const isWH = wordheadSet.has(ch);
  const isVar = !!variantMap[ch];
  const ix = indexMap[ch];
  console.log(`【${ch}】 wordhead=${isWH} 重文=${isVar}${isVar ? '(母字:' + variantMap[ch].parent + ')' : ''} index→${ix ? ix.wordhead : '无'}`);
}
console.log('\n--- 关键样本 ---');
for (const ch of ['匭', '簋', '頏', '亢', '馭', '御', '渺', '眇', '吭', '肮', '卤', '鹵', '栖', '棲', '肤', '膚', '臚', '鹊', '鵲', '舄']) diag(ch);

console.log('\n--- 查 簋 条目的 variants/indexes ---');
const g = entries.find(e => e.wordhead === '簋');
if (g) {
  console.log('wordhead=簋 explanation=', g.explanation);
  console.log('variants=', JSON.stringify((g.variants || []).map(v => v.wordhead + ':' + v.explanation)));
  console.log('indexes=', JSON.stringify(g.indexes));
}
console.log('\n--- 查 亢 条目 ---');
const k = entries.find(e => e.wordhead === '亢');
if (k) { console.log('explanation=', k.explanation); console.log('variants=', JSON.stringify((k.variants || []).map(v => v.wordhead + ':' + v.explanation))); console.log('indexes=', JSON.stringify(k.indexes)); }
