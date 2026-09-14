// 从本地《说文》源仓库检索目标字的权威条目
const fs = require('fs'), path = require('path');
const DIR = 'D:/WorkBuddy/projects/说文解字/.workbuddy/charlist/shuowen/data';
const files = fs.readdirSync(DIR).filter(f => /^\d+\.json$/.test(f));
const idx = {};
for (const f of files) {
  let j; try { j = JSON.parse(fs.readFileSync(path.join(DIR, f), 'utf8')); } catch (e) { continue; }
  const keys = new Set([j.wordhead, ...(j.indexes || [])]);
  for (const k of keys) {
    if (!k) continue;
    (idx[k] = idx[k] || []).push({
      file: f, wordhead: j.wordhead, radical: j.radical,
      explanation: j.explanation, components: j.components,
      variants: (j.variants || []).map(v => v.wordhead),
      pinyin: j.pinyin_full
    });
  }
}
const TARGETS = ['匭', '頏', '馭', '臺', '渺', '眇', '簋', '亢', '御',
  '尤', '尢', '卤', '鹵', '栖', '棲', '仝', '全', '叨', '饕', '抄', '鈔', '店', '坫', '仗', '杖', '托', '侂',
  '坰', '夯', '皋', '麦', '麥', '亟', '尿', '先', '寇', '亘'];
const out = [];
for (const t of TARGETS) {
  const hits = idx[t];
  if (!hits) { out.push('【' + t + '】 未在《说文》源中找到（可能为后起字/异体未收）'); continue; }
  for (const h of hits) {
    out.push('【' + t + '】 file=' + h.file + ' 字头=' + h.wordhead + ' 部首=' + h.radical + ' 拼音=' + (h.pinyin || ''));
    out.push('   训释: ' + (h.explanation || '').slice(0, 200));
    out.push('   构件: ' + JSON.stringify(h.components || []) + '  异体: ' + JSON.stringify(h.variants || []));
  }
}
fs.writeFileSync('D:/WorkBuddy/projects/说文解字/_zw/_LOOKUP.txt', out.join('\n'), 'utf8');
console.log('entries indexed:', Object.keys(idx).length, ' targets:', TARGETS.length);
