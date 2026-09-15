// 探 dataset.bin 的键位口径：glyphsForCharacter 用「字」还是「繁体」
const fs = require('fs');
const B = 'D:/WorkBuddy/projects/说文解字/';
global.self = global;
(0, eval)(fs.readFileSync(B + 'data/fzstd.umd.js', 'utf8'));
(0, eval)(fs.readFileSync(B + 'data/dataset-reader.js', 'utf8'));
const { DatasetReader } = global.__CDS;
const bytes = new Uint8Array(fs.readFileSync(B + 'data/dataset.bin'));
const r = new DatasetReader(bytes);
for (const ch of ['扰', '擾', '匦', '匭', '吭', '亢', '肤', '膚', '万', '萬', '着', '著', '卤', '鹵']) {
  const ks = r.keysForCharacter(ch) || [];
  console.log(ch, '键数=' + ks.length, JSON.stringify(ks.slice(0, 5)));
}
