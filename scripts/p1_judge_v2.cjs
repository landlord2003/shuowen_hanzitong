// P1-4 余量扩展抽检 · 研判 v2
// 目标：从 p1_candidates.json 里，用《说文》原文作权威基准，
//      精确挑出"story 构件断言与《说文》不符"的高置信错误，剔除此前的自然语言误报。
const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字';
const cj = JSON.parse(fs.readFileSync(ROOT + '/data/characters.json', 'utf8'));
const cand = JSON.parse(fs.readFileSync(ROOT + '/data/p1_candidates.json', 'utf8'));

const lm = {};
for (const c of cj.characters) lm[c.char] = { liushu: c.liushu, shuowen: c.shuowen || '' };

// 从《说文》原文提取构件字（权威）
function swParts(sw) {
  if (!sw) return null;
  const has = /从|象/.test(sw);
  if (!has) return null;
  const parts = new Set();
  for (const m of sw.matchAll(/从(.)/g)) if (/[\u4e00-\u9fff]/.test(m[1])) parts.add(m[1]);
  for (const m of sw.matchAll(/象(.)/g)) if (/[\u4e00-\u9fff]/.test(m[1])) parts.add(m[1]);
  for (const m of sw.matchAll(/从(.)从(.)/g)) { parts.add(m[1]); parts.add(m[2]); }
  return parts;
}

// 从 story 提取"真正的构件断言"（排除自然语言"从X中/里/到…"）
function storyParts(st) {
  const parts = [];
  // (1) 从X从Y / 从X、从Y —— 强构形断言
  for (const m of st.matchAll(/从([\u4e00-\u9fff])(?:从|、|，|和|与)/g)) parts.push(m[1]);
  for (const m of st.matchAll(/从([\u4e00-\u9fff])从([\u4e00-\u9fff])/g)) parts.push(m[1], m[2]);
  // (2) 由X和/与Y组成（构造断言）
  for (const m of st.matchAll(/由[「'"]?([\u4e00-\u9fff])[」'"]?[和与][「'"]?([\u4e00-\u9fff])[」'"]?(?:组|构|合)/g)) parts.push(m[1], m[2]);
  // (3) X表声 / X象形（紧跟"象形/表声"的字符）
  for (const m of st.matchAll(/([\u4e00-\u9fff])象形/g)) parts.push(m[1]);
  // 排除自然语言：出现在"从…中/里/内/外/上/下/到/此/来/而/属"前的从字
  return parts.filter(p => /[\u4e00-\u9fff]/.test(p));
}

const ERR_PART = [];   // 真错误：story 构件字不在《说文》构件集里，且《说文》有构形
const CONFLICT = [];   // 六书自述与字段矛盾（story 自称会意/形声，字段却是象形/指事）
const GARBLED = [];    // 自指 / 乱码 / 自我复制

for (const c of cand) {
  const ch = c.ch, info = lm[ch]; if (!info) continue;
  const st = c.story || '', sw = info.shuowen || '';
  const sp = swParts(sw);

  // 六书自述矛盾
  const stSays = /是会意字|属于会意|会意字/.test(st) ? '会意' : (/是形声字|属于形声|形声字/.test(st) ? '形声' : null);
  if (stSays && ['象形', '指事'].includes(info.liushu))
    CONFLICT.push({ ch, liushu: info.liushu, says: stSays, story: st, shuowen: sw });

  // 自指 / 乱码
  if (new RegExp('由[「\'"]?' + ch + '[」\'"]?[和与]').test(st) || new RegExp(ch + '字由[「\'"]?' + ch).test(st))
    GARBLED.push({ ch, liushu: info.liushu, story: st, shuowen: sw });
  if (/[ザヅァ-ヶ]|丷|丶[^，。]/.test(st))
    GARBLED.push({ ch, liushu: info.liushu, story: st, shuowen: sw });

  // 真构件错误
  if (sp && sp.size) {
    const parts = storyParts(st);
    const bad = [...new Set(parts)].filter(p => p !== ch && !sp.has(p) && !sw.includes('象' + p));
    if (bad.length) ERR_PART.push({ ch, liushu: info.liushu, badParts: bad, swParts: [...sp], story: st, shuowen: sw });
  }
}

// 去重（同一字可能进多桶）
const seen = new Set();
const dedup = arr => arr.filter(r => { if (seen.has(r.ch)) return false; seen.add(r.ch); return true; });
const A = dedup(ERR_PART), B = dedup(CONFLICT), C = dedup(GARBLED);

fs.writeFileSync(ROOT + '/data/p1_judge_v2.json', JSON.stringify({ errPart: A, conflict: B, garbled: C }, null, 0));
const fmt = r => '【' + r.ch + '】(' + r.liushu + ')' +
  (r.badParts ? ' story构件[' + r.badParts.join('/') + '] ∉ 说文构件[' + r.swParts.join('/') + ']' : '') +
  (r.says ? ' story自称' + r.says + '但字段=' + r.liushu : '') +
  '\n   STORY: ' + r.story.slice(0, 110) + '\n   SHUOWEN: ' + r.shuowen.slice(0, 70);
fs.writeFileSync(ROOT + '/_p1_judge_v2.txt',
  '=== A 真构件错误: ' + A.length + ' ===\n' + A.map(fmt).join('\n') +
  '\n\n=== B 六书自述矛盾: ' + B.length + ' ===\n' + B.map(fmt).join('\n') +
  '\n\n=== C 自指/乱码: ' + C.length + ' ===\n' + C.map(fmt).join('\n'));
console.log('A 真构件错误:', A.length, '| B 六书矛盾:', B.length, '| C 自指乱码:', C.length);
console.log('--- A ---');
console.log(A.map(r => r.ch + ': [' + r.badParts.join('/') + '] vs 说文[' + r.swParts.join('/') + ']').join('\n'));
