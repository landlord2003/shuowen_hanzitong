const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字';
const cj = JSON.parse(fs.readFileSync(ROOT + '/data/characters.json', 'utf8'));
const cult = JSON.parse(fs.readFileSync(ROOT + '/data/cultural.json', 'utf8'));

// 已修字（B2 20 + B3 17 + fix_cultural_quality 10）
const FIXED = new Set([
  '个','丸','广','比','巨','乡','仆','币','仅','计','书','幻','术','扔','千','厅','专','允','仑','凶', // B2
  '匕','刁','乞','么','亡','丐','扎','匹','介','乏','斗','订','冗','队','刊','巧','可',             // B3
  '大','插','坂','苷','唏','耜','彀','彳','桊','蛑'                                           // fix_quality
]);

// 风险六书：会意/象形/指事最易被 Ollama 杜撰构件
const RISK = new Set(['会意', '象形', '指事', '会意兼形声']);

// 强信号（具体构件拆分断言——最易被 Ollama 杜撰；排除"《说文》/许慎/段玉裁/小篆"等弱引用）
const SIG = /从.{0,3}从|由.{0,4}和.{0,4}组成|字由|部件|构成|象.{0,6}形|分化|省声|亦声|甲骨?文作|金文作|小篆作|籀文作|本作/;

const out = [];
for (const c of cj.characters) {
  const ch = c.char;
  if (FIXED.has(ch)) continue;
  if (!RISK.has(c.liushu)) continue;
  const e = cult[ch];
  if (!e || !e.story) continue;
  const st = e.story;
  if (SIG.test(st)) out.push({ ch, liushu: c.liushu, story: st });
}
// 按 story 长度降序（越长越可能含杜撰细节）
out.sort((a, b) => b.story.length - a.story.length);
fs.writeFileSync(ROOT + '/data/p1_candidates.json', JSON.stringify(out));
fs.writeFileSync(ROOT + '/_p1_prefilter.txt', '候选(风险六书+构件信号,排除已修' + FIXED.size + '字): ' + out.length + '\n' + out.slice(0, 80).map(x => x.ch + '(' + x.liushu + ')').join(' '));
console.log('P1候选数:', out.length, ' (总数风险六书字:', cj.characters.filter(c => RISK.has(c.liushu)).length, ')');
console.log('前40:', out.slice(0, 40).map(x => x.ch).join(''));
