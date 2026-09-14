// 严格校验：把 132 条新 story 的「」去掉后，重新抽取强构形断言，与《说文》比对，报告残留冲突。
const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字';
const cj = JSON.parse(fs.readFileSync(ROOT + '/data/characters.json', 'utf8'));
const cult = JSON.parse(fs.readFileSync(ROOT + '/data/cultural.json', 'utf8'));
const lm = {};
for (const c of cj.characters) lm[c.char] = { liushu: c.liushu, shuowen: c.shuowen || '' };

const NORM = { '氵':'水','扌':'手','纟':'糸','艹':'艸','月':'肉','刂':'刀','礻':'示','讠':'言','钅':'金','辶':'辵','阝':'阜','饣':'食','页':'頁','马':'馬','鸟':'鳥','车':'車','贝':'貝','见':'見','与':'與','云':'雲','万':'萬','齐':'齊','乐':'樂','门':'門','风':'風','龟':'龜','韦':'韋','长':'長','齿':'齒','东':'東','麦':'麥','黄':'黃','产':'產','亲':'親','爱':'愛' };
const norm = c => NORM[c] || c;

const real = JSON.parse(fs.readFileSync(ROOT + '/data/p1_audit_findings.json', 'utf8')).highConf.filter(x => x.verdict === 'REAL').map(x => x.ch);

function swParts(sw) {
  const s = new Set();
  if (!sw || !/从/.test(sw)) return s;
  for (const m of sw.matchAll(/从(.)/g)) if (/[\u4e00-\u9fff]/.test(m[1])) s.add(norm(m[1]));
  return s;
}
function stParts(st) {
  const clean = st.replace(/[「」『』“”"']/g, '').replace(/（[^）]*）/g, '');   // 去引号 + 去夹注，让 从X从Y 直接相邻
  const s = [];
  for (const m of clean.matchAll(/从([\u4e00-\u9fff])从([\u4e00-\u9fff])/g)) s.push(m[1], m[2]);
  for (const m of clean.matchAll(/由([\u4e00-\u9fff])[和与]([\u4e00-\u9fff])(?:组|构|合)/g)) s.push(m[1], m[2]);
  return s;
}

let residual = [], clean = 0, noAssert = [];
for (const ch of real) {
  const e = cult[ch]; const sw = lm[ch] ? lm[ch].shuowen : '';
  const sp = stParts(e.story || '');
  if (sp.length === 0) { noAssert.push(ch); continue; }
  const sset = swParts(sw);
  const bad = sp.filter(p => !sset.has(norm(p)));
  if (bad.length) residual.push(ch + '  新story构件[' + sp.join('/') + ']  说文[' + [...sset].join('/') + ']  多出=' + [...new Set(bad)].join('/'));
  else clean++;
}
const out = [];
out.push('严格校验（去引号）132 字新 story：');
out.push('  无强构形断言(不强校验) = ' + noAssert.length + ' : ' + noAssert.join(' '));
out.push('  断言与《说文》一致 = ' + clean);
out.push('  残留差异 = ' + residual.length);
out.push('--- 残留清单 ---');
out.push(residual.join('\n'));
fs.writeFileSync(ROOT + '/_p1_verify132.txt', out.join('\n'), 'utf8');
console.log(out.slice(0, 3).join('\n'));
console.log('残留:', residual.length);
console.log(residual.join('\n'));
