const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字';
const cj = JSON.parse(fs.readFileSync(ROOT + '/data/characters.json', 'utf8'));
const cand = JSON.parse(fs.readFileSync(ROOT + '/data/p1_candidates.json', 'utf8'));
const lm = {};
for (const c of cj.characters) lm[c.char] = { liushu: c.liushu, shuowen: c.shuowen || '', original: c.original || '' };

const HARD = [];   // 六书类型与构件描述明显冲突（确定性高）
const SOFT = [];   // 构件字《说文》未提及（待人工研判）
for (const c of cand) {
  const ch = c.ch; const info = lm[ch]; if (!info) continue;
  const st = c.story; const sw = info.shuowen || '';
  const reasons = [];
  // 硬冲突：象形/指事被拆为构件组合；会意却用象形描述
  if ((info.liushu === '象形' || info.liushu === '指事') && /从.{0,3}从|由.{0,4}和.{0,4}组成|字由|部件|构成/.test(st))
    reasons.push('六书=' + info.liushu + '但story拆构件');
  if (info.liushu === '会意' && /象.{0,6}形/.test(st)) reasons.push('会意却称象X形');
  if (info.liushu === '会意兼形声' && /象.{0,6}形/.test(st)) reasons.push('兼形声却称象X形');
  // 软冲突：story 部件字《说文》完全未提及（且说文有构形结构）
  const parts = [...st.matchAll(/从(.)/g)].map(m => m[1]);
  if (sw && (sw.includes('从') || sw.includes('象'))) {
    for (const p of parts) if (p && !sw.includes(p)) reasons.push('部件[' + p + ']未见于说文');
  }
  if (!reasons.length) continue;
  const rec = { ch, liushu: info.liushu, reasons: reasons.join('; '), story: st, shuowen: sw };
  if (/六书=|却称象X形/.test(reasons.join(''))) HARD.push(rec); else SOFT.push(rec);
}
HARD.sort((a, b) => b.story.length - a.story.length);
SOFT.sort((a, b) => b.story.length - a.story.length);
const out = { hard: HARD, soft: SOFT };
fs.writeFileSync(ROOT + '/data/p1_judge.json', JSON.stringify(out));
function fmt(r) { return '【' + r.ch + '】(' + r.liushu + ') ' + r.reasons + '\n   STORY: ' + r.story.slice(0, 120) + '\n   SHUOWEN: ' + r.shuowen.slice(0, 80); }
fs.writeFileSync(ROOT + '/_p1_judge.txt',
  '=== 硬冲突(确定性高): ' + HARD.length + ' ===\n' + HARD.map(fmt).join('\n') +
  '\n\n=== 软冲突(待研判): ' + SOFT.length + ' ===\n' + SOFT.slice(0, 50).map(fmt).join('\n'));
console.log('硬冲突:', HARD.length, ' 软冲突:', SOFT.length);
console.log(HARD.slice(0, 25).map(r => r.ch + ' ' + r.reasons).join('\n'));
