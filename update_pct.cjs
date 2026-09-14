const fs = require('fs');
const F = 'D:/WorkBuddy/projects/说文解字/index.html';
let s = fs.readFileSync(F, 'utf8');

// 1) 四列表内：去掉百分比，保留「X 字」与必要的非比例说明
const reps = [
  ['955 字（11.8%）', '955 字'],
  ['1120 字（13.8%）', '1120 字'],
  ['2049 字（25.3%）', '2049 字'],
  ['2072 字（25.6%）', '2072 字'],
  ['1362 字（16.8%）', '1362 字'],
  ['5055 字（62.4%，汉典·传抄古文字口径）', '5055 字（汉典·传抄古文字口径）'],
  ['2848 字（35.1%）', '2848 字'],
  ['5564 字（68.7%）', '5564 字'],
  ['0 真迹 / 7351 字（90.7%，字体）', '0 真迹 / 7351 字（字体）'],
  ['612 字（7.6%）', '612 字'],
  ['2420 字（29.9%，楚系∪秦系）', '2420 字（楚系∪秦系）'],
];
let miss = [];
for (const [a, b] of reps) {
  if (!s.includes(a)) { miss.push(a); continue; }
  s = s.split(a).join(b);
}

// 2) 口径说明清理（原提到百分比的措辞已失真）
const rep2 = [
  ['的字数（解码 dataset.bin 实算，括号内为占 8105 比例）；隶书未收汉隶真迹，由临海＋青柳隶书字体替代呈现 7351 字=90.7%。',
   '的字数（解码 dataset.bin 实算）；隶书未收汉隶真迹，由临海＋青柳隶书字体替代呈现 7351 字。'],
  ['的字数（括号内占 8105 比例）；其中大篆采用汉典',
   '的字数；其中大篆采用汉典'],
];
for (const [a, b] of rep2) {
  if (!s.includes(a)) { miss.push(a); continue; }
  s = s.split(a).join(b);
}

fs.writeFileSync(F, s, 'utf8');
console.log('DONE  miss=', JSON.stringify(miss));
console.log('剩余百分比样例检查:',
  s.includes('11.8%') || s.includes('25.3%') || s.includes('90.7%') || s.includes('占 8105 比例')
    ? '仍有残留!' : '已全部清除');
