// 应用全量简繁映射修复：data/characters.json + index.html 内联 DATA
const fs = require('fs');
const B = 'D:/WorkBuddy/projects/说文解字/';

// ---- Python json.dumps 兼容序列化器（两种模式） ----
function escStr(s, ascii) {
  let o = '"';
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    if (c === 0x22) o += '\\"';
    else if (c === 0x5C) o += '\\\\';
    else if (c === 0x08) o += '\\b';
    else if (c === 0x09) o += '\\t';
    else if (c === 0x0A) o += '\\n';
    else if (c === 0x0C) o += '\\f';
    else if (c === 0x0D) o += '\\r';
    else if (c < 0x20 || (ascii && c > 0x7F)) o += '\\u' + c.toString(16).padStart(4, '0').toLowerCase();
    else o += s[i];
  }
  return o + '"';
}
function ser(v, ascii, spaced) {
  const S = spaced ? ', ' : ',';
  const K = spaced ? ': ' : ':';
  if (v === null) return 'null';
  if (typeof v === 'number' || typeof v === 'boolean') return String(v);
  if (typeof v === 'string') return escStr(v, ascii);
  if (Array.isArray(v)) return '[' + v.map(x => ser(x, ascii, spaced)).join(S) + ']';
  return '{' + Object.keys(v).map(k => escStr(k, ascii) + K + ser(v[k], ascii, spaced)).join(S) + '}';
}

// ---- 组装 FIX ----
const fixes = JSON.parse(fs.readFileSync(B + '_s2t_fix.json', 'utf8'));
const FIX = {};
for (const f of fixes) {
  FIX[f.char] = { trad: f.new };
  if (f.mode === 'full') {
    FIX[f.char].shuowen = f.shuowen;
    FIX[f.char].original = f.original;
    FIX[f.char].liushu = f.liushu;
  }
}
// 7 个无《说文》条目字：3 个仅改 trad（㱿/𤟌 即 殼/獎 本字，苧 本就是后起字），4 个清空
Object.assign(FIX, {
  '壳': { trad: '殼' },
  '奖': { trad: '獎' },
  '苎': { trad: '薴' },
  '肮': { trad: '骯', shuowen: '（后起字，《说文》未收）', original: '肮脏（后起字，无古本义）', liushu: '形声' },
  '柠': { trad: '檸', shuowen: '（后起字，《说文》未收）', original: '柠檬（后起字，无古本义）', liushu: '形声' },
  '箓': { trad: '籙', shuowen: '（后起字，《说文》未收）', original: '符箓（后起字，无古本义）', liushu: '形声' },
  '镅': { trad: '鎇', shuowen: '（后起字，《说文》未收）', original: '镅（化学元素，后起字，无古本义）', liushu: '形声' },
});
const chars = Object.keys(FIX);
console.log('FIX 字数:', chars.length);

function apply(list) {
  let n = 0, missed = [];
  for (const ch of chars) {
    const rec = list.find(c => c.char === ch);
    if (!rec) { missed.push(ch); continue; }
    const f = FIX[ch];
    for (const k in f) { rec[k] = f[k]; n++; }
  }
  return { n, missed };
}

// ---- 1) data/characters.json ----
const CP = B + 'data/characters.json';
const cRaw = fs.readFileSync(CP, 'utf8');
let modeC = null;
for (const a of [false, true]) for (const sp of [false, true]) { if (ser(JSON.parse(cRaw), a, sp) === cRaw) { modeC = { a, sp }; break; } }
console.log('characters.json 模式:', JSON.stringify(modeC));
if (!modeC) { console.log('⚠️ characters.json 往返不一致，中止'); process.exit(1); }
const cData = JSON.parse(cRaw);
const r1 = apply(cData.characters);
console.log('characters.json 应用字段:', r1.n, ' 未匹配:', r1.missed.join(',') || '无');
fs.writeFileSync(CP, ser(cData, modeC.a, modeC.sp), 'utf8');

// ---- 2) index.html 内联 DATA ----
const HP = B + 'index.html';
let H = fs.readFileSync(HP, 'utf8');
const MK = 'var DATA = ';
const i0 = H.indexOf(MK);
const iChars = H.indexOf('var CHARS', i0);
const seg = H.slice(i0 + MK.length, iChars);
const lastBrace = seg.lastIndexOf('}');
const jsonText = seg.slice(0, lastBrace + 1);
const tail = seg.slice(lastBrace + 1);
const DATA = JSON.parse(jsonText);
const rt = ser(DATA, true, true) === jsonText;
console.log('index.html DATA 往返一致(ascii=true,spaced):', rt);
if (!rt) { console.log('⚠️ 中止'); process.exit(1); }
const r2 = apply(DATA.characters);
console.log('index.html 应用字段:', r2.n, ' 未匹配:', r2.missed.join(',') || '无');
H = H.slice(0, i0 + MK.length) + ser(DATA, true, true) + tail + H.slice(iChars);
fs.writeFileSync(HP, H, 'utf8');
console.log('index.html 已写回，大小(MB):', (H.length / 1048576).toFixed(2));
console.log('DONE');
