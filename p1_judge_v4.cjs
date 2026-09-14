// P1-4 余量扩展抽检 · 研判 v4（高精度）
// 约束：①只比较《说文》构形分≥2 的字（避免"从鳥在木上"式只给义符的误判）
//      ②story 只认强构形断言（从X从Y / 由X与Y组成）
//      ③偏旁异体 + 简繁双重归一
const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字';
const cj = JSON.parse(fs.readFileSync(ROOT + '/data/characters.json', 'utf8'));
const cand = JSON.parse(fs.readFileSync(ROOT + '/data/p1_candidates.json', 'utf8'));
const lm = {};
for (const c of cj.characters) lm[c.char] = { liushu: c.liushu, shuowen: c.shuowen || '' };

const NORM = {
  // 偏旁异体
  '氵':'水','氺':'水','扌':'手','纟':'糸','糹':'糸','艹':'艸','⺾':'艸','月':'肉','⺼':'肉','阝':'阜','刂':'刀','灬':'火','忄':'心','讠':'言','訁':'言','饣':'食','飠':'食','钅':'金','釒':'金','礻':'示','衤':'衣','辶':'辵','丬':'爿','牜':'牛','虍':'虎','罒':'网','覀':'西',
  // 简→繁（构件常见）
  '门':'門','马':'馬','车':'車','贝':'貝','见':'見','鸟':'鳥','鱼':'魚','页':'頁','龙':'龍','齿':'齒','长':'長','风':'風','龟':'龜','韦':'韋','与':'與','万':'萬','云':'雲','气':'氣','凤':'鳳','兰':'蘭','马':'馬','专':'專','为':'爲','头':'頭','只':'只','产':'產','亲':'親','爱':'愛','奋':'奮','卤':'鹵','鸟':'鳥','麦':'麥','黄':'黃','齐':'齊','齿':'齒','东':'東','乐':'樂','车':'車','贝':'貝','页':'頁','风':'風','龙':'龍','马':'馬','鸟':'鳥','鱼':'魚','龟':'龜'
};
const STOP = new Set('是的字其自为用代初之以而等可即也所在有和与由此又后前上下内外人中间从于至到来去出入大小多少现古旧本指表意义称叫作变化成例如像象形声会转假借通同原先新简体了着过被把让使得能会要就都还只再更最很太真正反却但若如果因故所'.split(''));
const norm = c => NORM[c] || c;

function parts(sw, strongOnly) {
  if (!sw || !/从/.test(sw)) return null;
  const s = new Set();
  for (const m of sw.matchAll(/从(.)/g)) if (/[\u4e00-\u9fff]/.test(m[1])) s.add(norm(m[1]));
  for (const m of sw.matchAll(/象(.)/g)) if (/[\u4e00-\u9fff]/.test(m[1])) s.add(norm(m[1]));
  return s;
}
function storyParts(st) {
  const s = [];
  for (const m of st.matchAll(/从([\u4e00-\u9fff])从([\u4e00-\u9fff])/g)) s.push(m[1], m[2]);
  for (const m of st.matchAll(/由[「'"]?([\u4e00-\u9fff])[」'"]?[和与][「'"]?([\u4e00-\u9fff])[」'"]?(?:组|构|合)/g)) s.push(m[1], m[2]);
  for (const m of st.matchAll(/[「'"]?([\u4e00-\u9fff])[」'"]?(?:和|与)[「'"]?([\u4e00-\u9fff])[」'"]?组成/g)) s.push(m[1], m[2]);
  return s;
}

const A = [];   // 高置信：双方都显式给构件，story 有构件 ∉ 说文
const LOOSE = []; // 中置信：说文仅部分构件，story 多出构件（噪声大，单列）
for (const c of cand) {
  const ch = c.ch, info = lm[ch]; if (!info) continue;
  const st = c.story || '', sw = info.shuowen || '';
  if (/已更正|旧 ?story|误作|误为|旧说|原文误/.test(st)) continue;
  const sp = parts(sw); if (!sp || !sp.size) continue;
  const bad = [...new Set(storyParts(st).map(norm).filter(p => p !== norm(ch) && !STOP.has(p)))].filter(p => !sp.has(p));
  if (!bad.length) continue;
  const rec = { ch, liushu: info.liushu, badParts: bad, swParts: [...sp], story: st, shuowen: sw };
  if (sp.size >= 2) A.push(rec); else LOOSE.push(rec);
}
A.sort((a, b) => b.badParts.length - a.badParts.length);
fs.writeFileSync(ROOT + '/data/p1_judge_v4.json', JSON.stringify({ highConf: A, midConf: LOOSE }, null, 0));
fs.writeFileSync(ROOT + '/_p1_judge_v4.txt',
  '=== 高置信·构件冲突(说文构件≥2): ' + A.length + ' ===\n' +
  A.map(r => '【' + r.ch + '】(' + r.liushu + ') story[' + r.badParts.join('/') + '] 不在说文[' + r.swParts.join('/') + ']\n   STORY: ' + r.story.slice(0, 140) + '\n   SHUOWEN: ' + r.shuowen.slice(0, 80)).join('\n') +
  '\n\n=== 中置信(说文仅列义符): ' + LOOSE.length + ' ===' +
  LOOSE.map(r => '\n【' + r.ch + '】story[' + r.badParts.join('/') + '] 说文仅[' + r.swParts.join('/') + ']').join(''));
console.log('高置信:', A.length, ' 中置信:', LOOSE.length);
console.log('--- 高置信全部 ---');
console.log(A.map(r => r.ch + ' story[' + r.badParts.join('/') + '] 说文[' + r.swParts.join('/') + ']').join('\n'));
