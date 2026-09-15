// 对 trad!=char 的 2928 字按《说文》源分桶分析
const fs = require('fs'), path = require('path');
const D = 'D:/WorkBuddy/projects/说文解字/.workbuddy/charlist/shuowen/data';
const wordheadSet = new Set(), variantMap = {}, variantOwn = {}, indexMap = {}, entryByWH = {};
for (const f of fs.readdirSync(D).filter(f => f.endsWith('.json'))) {
  let e; try { e = JSON.parse(fs.readFileSync(path.join(D, f), 'utf8')); } catch (x) { continue; }
  wordheadSet.add(e.wordhead); entryByWH[e.wordhead] = e;
  for (const v of (e.variants || [])) if (v.wordhead) { variantMap[v.wordhead] = e.wordhead; variantOwn[v.wordhead] = { parent: e.wordhead, expl: v.explanation || '' }; }
  for (const ix of (e.indexes || [])) if (!indexMap[ix]) indexMap[ix] = e;
}
const cj = JSON.parse(fs.readFileSync('D:/WorkBuddy/projects/说文解字/data/characters.json', 'utf8'));
const buckets = { A_松散索引: [], B_重文错配: [], C_char是字头: [], D_index指向非字头: [], E_其他: [] };
for (const c of cj.characters) {
  const cur = c.trad || ''; if (!cur || cur === c.char) continue;
  const cIsWH = wordheadSet.has(c.char);
  const isVarOfCur = variantMap[c.char] === cur;
  const curIsWH = wordheadSet.has(cur);
  const ix = indexMap[c.char];
  const ixWH = ix ? ix.wordhead : null;
  if (cIsWH) buckets.C_char是字头.push([c.char, cur, 'ix→' + ixWH]);
  else if (isVarOfCur) buckets.B_重文错配.push([c.char, cur, variantOwn[c.char].expl.slice(0, 30)]);
  else if (curIsWH && ixWH === cur) buckets.A_松散索引.push([c.char, cur]);
  else if (ixWH && !wordheadSet.has(ixWH)) buckets.D_index指向非字头.push([c.char, cur, ixWH]);
  else buckets.E_其他.push([c.char, cur, 'ix→' + ixWH, 'curIsWH=' + curIsWH]);
}
for (const k in buckets) console.log(k + ': ' + buckets[k].length);
const out = [];
for (const k in buckets) { out.push('===== ' + k + ' (' + buckets[k].length + ') ====='); buckets[k].forEach(r => out.push(r.join('  '))); }
fs.writeFileSync('D:/WorkBuddy/projects/说文解字/_trad_buckets.txt', out.join('\n'), 'utf8');
// 西 条目
const x = entryByWH['西'];
console.log('\n西.wordhead=' + x.wordhead + ' expl=' + x.explanation);
console.log('西.variants=' + JSON.stringify((x.variants || []).map(v => v.wordhead)));
console.log('西.indexes=' + JSON.stringify(x.indexes));
