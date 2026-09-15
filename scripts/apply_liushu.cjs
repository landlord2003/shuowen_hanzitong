// 应用六书复核：data/characters.json + index.html 内联 DATA + 统计表
const fs = require('fs');
const B = 'D:/WorkBuddy/projects/说文解字/';

function escStr(s, ascii) {
  let o = '"';
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    if (c === 0x22) o += '\\"';
    else if (c === 0x5C) o += '\\\\';
    else if (c === 0x08) o += '\\b'; else if (c === 0x09) o += '\\t';
    else if (c === 0x0A) o += '\\n'; else if (c === 0x0C) o += '\\f';
    else if (c === 0x0D) o += '\\r';
    else if (c < 0x20 || (ascii && c > 0x7F)) o += '\\u' + c.toString(16).padStart(4, '0').toLowerCase();
    else o += s[i];
  }
  return o + '"';
}
function ser(v, ascii, spaced) {
  const S = spaced ? ', ' : ',', K = spaced ? ': ' : ':';
  if (v === null) return 'null';
  if (typeof v === 'number' || typeof v === 'boolean') return String(v);
  if (typeof v === 'string') return escStr(v, ascii);
  if (Array.isArray(v)) return '[' + v.map(x => ser(x, ascii, spaced)).join(S) + ']';
  return '{' + Object.keys(v).map(k => escStr(k, ascii) + K + ser(v[k], ascii, spaced)).join(S) + '}';
}

const FIX = {};
for (const x of JSON.parse(fs.readFileSync(B + '_liushu_apply.json', 'utf8'))) FIX[x.char] = x.neu;
const chars = Object.keys(FIX);
console.log('FIX 字数:', chars.length);

function apply(list) {
  let n = 0; const missed = [];
  for (const ch of chars) {
    const rec = list.find(c => c.char === ch);
    if (!rec) { missed.push(ch); continue; }
    if (rec.liushu !== FIX[ch]) { rec.liushu = FIX[ch]; n++; }
  }
  return { n, missed };
}
function dist(list) {
  const d = {};
  for (const c of list) d[c.liushu] = (d[c.liushu] || 0) + 1;
  return d;
}

// 1) characters.json
const CP = B + 'data/characters.json';
const cRaw = fs.readFileSync(CP, 'utf8');
let modeC = null;
for (const a of [false, true]) for (const sp of [false, true]) if (ser(JSON.parse(cRaw), a, sp) === cRaw) { modeC = { a, sp }; break; }
console.log('characters.json 模式:', JSON.stringify(modeC));
if (!modeC) { console.log('⚠️ characters.json 往返不一致，中止'); process.exit(1); }
const cData = JSON.parse(cRaw);
const r1 = apply(cData.characters);
console.log('characters.json 改:', r1.n, '未匹配:', r1.missed.join(',') || '无');
fs.writeFileSync(CP, ser(cData, modeC.a, modeC.sp), 'utf8');

// 2) index.html
const HP = B + 'index.html';
let H = fs.readFileSync(HP, 'utf8');
const MK = 'var DATA = ';
const i0 = H.indexOf(MK), iChars = H.indexOf('var CHARS', i0);
const seg = H.slice(i0 + MK.length, iChars);
const jsonText = seg.slice(0, seg.lastIndexOf('}') + 1), tail = seg.slice(seg.lastIndexOf('}') + 1);
const DATA = JSON.parse(jsonText);
if (ser(DATA, true, true) !== jsonText) { console.log('⚠️ index.html DATA 往返不一致，中止'); process.exit(1); }
const r2 = apply(DATA.characters);
console.log('index.html 改:', r2.n, '未匹配:', r2.missed.join(',') || '无');
H = H.slice(0, i0 + MK.length) + ser(DATA, true, true) + tail + H.slice(iChars);

// 3) 统计表
const d = dist(DATA.characters);
const total = DATA.characters.length;
const order = ['形声', '会意', '象形', '指事', '会意兼形声'];
const pct = n => (n / total * 100).toFixed(1) + '%';
let rows = '';
for (const k of order) rows += '<tr><td>' + k + '</td><td>' + d[k] + '</td><td>' + pct(d[k]) + '</td></tr>\r\n';
const re = /<tr><td>形声<\/td>[\s\S]*?(?=<tr><td><b>合计<\/b>)/;
if (!re.test(H)) { console.log('⚠️ 未找到统计表，中止'); process.exit(1); }
H = H.replace(re, rows);
// 注释更新
H = H.replace(/「会意兼形声」为少量边界字单独标注。/, '「会意兼形声」为《说文》「从X从Y，Y亦聲」一类兼有声符的会意字，单独标注、并同时计入「会意」「形声」筛选。');
fs.writeFileSync(HP, H, 'utf8');
console.log('新分布:', JSON.stringify(d));
console.log('index.html 已写回 (MB):', (H.length / 1048576).toFixed(2));
console.log('DONE');
