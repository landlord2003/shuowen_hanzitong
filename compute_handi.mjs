import fs from 'node:fs';
const ROOT = 'D:/WorkBuddy/projects/说文解字';

const cj = JSON.parse(fs.readFileSync(`${ROOT}/data/characters.json`, 'utf8'));
const appSet = new Set(cj.characters.map(c => c.char));

const files = {
  '甲骨文':   `${ROOT}/docs/汉典重建/取图清单_452字_汉典甲骨文.json`,
  '简牍帛书': `${ROOT}/docs/汉典重建/取图清单_1832字_汉典简牍帛书.json`,
  '小篆':     `${ROOT}/docs/汉典重建/取图清单_2821字_汉典小篆.json`,
};

const perScriptIn8105 = {};
const union = new Set();
for (const [name, f] of Object.entries(files)) {
  const arr = JSON.parse(fs.readFileSync(f, 'utf8'));
  let in8105 = 0;
  const chars = new Set();
  for (const r of arr) {
    const ch = r['汉字'];
    if (!ch) continue;
    chars.add(ch);
    if (appSet.has(ch)) { in8105++; union.add(ch); }
  }
  perScriptIn8105[name] = { ledger_chars: chars.size, within_8105: in8105 };
}
console.log(JSON.stringify({ app_total: appSet.size, perScriptIn8105, union_within_8105: union.size }, null, 2));
