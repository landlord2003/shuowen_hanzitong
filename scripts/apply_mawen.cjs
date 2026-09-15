// 落盘：士/六/冬 补 liushu_remark（保持象形）、履 改会意、蛑 重写为「蝤蛑」
// 同步 data/characters.json + index.html 内联 DATA
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

const FIX = {
  // —— 士/六/冬：保持象形，仅补审计注记 ——
  '士': {
    liushu_remark: '《说文》「从一从十」为会意，甲骨文象斧钺之形（王/士同形）为象形，本项目依现代文字学（有甲骨文铁证）归象形',
  },
  '六': {
    liushu_remark: '《说文》「从入从八」为会意，甲骨文象房屋（廬）之形为象形，本项目依现代文字学（有甲骨文铁证）归象形',
  },
  '冬': {
    liushu_remark: '《说文》「从仌从夂」（夂为古文终字）为会意，甲骨文象丝绳末端打结之形（「终」本字）为象形，本项目依现代文字学（有甲骨文铁证）归象形',
  },
  // —— 履：象形 → 会意（《说文》「从尸从彳从夊」） ——
  '履': {
    liushu: '会意',
    liushu_remark: '《说文》「从尸从彳从夊」为会意，原标象形误',
  },
  // —— 蛑：整条重写为「蝤蛑」（梭子蟹），剥离误挂的「蟊/𧔨」训释 ——
  '蛑': {
    pinyin: 'móu',
    fanqie: '莫浮切',
    liushu: '形声',
    original: '蝤蛑，似蟹而大（出《康熙字典》）',
    modern: '蝤蛑（梭子蟹）',
    shuowen: '（《说文》「蛑」为「蟊」之古文，从虫从牟；非今义，今指「蝤蛑」，即梭子蟹。）',
    evolution: '《说文》「蛑」为「蟊（𧔨）」之古文（从虫从牟）；后世专以称「蝤蛑」，一种大型海蟹。',
    duan_note: '',
    variant: '',
  },
};
const chars = Object.keys(FIX);
console.log('FIX 字数:', chars.length, chars.join(''));

function apply(list) {
  let n = 0; const missed = [];
  const detail = [];
  for (const ch of chars) {
    const rec = list.find(c => c.char === ch);
    if (!rec) { missed.push(ch); continue; }
    const f = FIX[ch];
    for (const k in f) {
      if (rec[k] !== f[k]) { detail.push(ch + '.' + k); rec[k] = f[k]; n++; }
    }
  }
  return { n, missed, detail };
}

// 1) characters.json（紧凑、非 ascii）
const CP = B + 'data/characters.json';
const cRaw = fs.readFileSync(CP, 'utf8');
let modeC = null;
for (const a of [false, true]) for (const sp of [false, true]) if (ser(JSON.parse(cRaw), a, sp) === cRaw) { modeC = { a, sp }; break; }
console.log('characters.json 模式:', JSON.stringify(modeC));
if (!modeC) { console.log('⚠️ characters.json 往返不一致，中止'); process.exit(1); }
const cData = JSON.parse(cRaw);
const r1 = apply(cData.characters);
console.log('characters.json 改字段:', r1.n, '未匹配:', r1.missed.join(',') || '无');
console.log('  明细:', r1.detail.join(' '));
fs.writeFileSync(CP, ser(cData, modeC.a, modeC.sp), 'utf8');

// 2) index.html 内联 DATA（spaced + ascii）
const HP = B + 'index.html';
let H = fs.readFileSync(HP, 'utf8');
const MK = 'var DATA = ';
const i0 = H.indexOf(MK), iChars = H.indexOf('var CHARS', i0);
const seg = H.slice(i0 + MK.length, iChars);
const jsonText = seg.slice(0, seg.lastIndexOf('}') + 1), tail = seg.slice(seg.lastIndexOf('}') + 1);
const DATA = JSON.parse(jsonText);
if (ser(DATA, true, true) !== jsonText) { console.log('⚠️ index.html DATA 往返不一致，中止'); process.exit(1); }
const r2 = apply(DATA.characters);
console.log('index.html 改字段:', r2.n, '未匹配:', r2.missed.join(',') || '无');
H = H.slice(0, i0 + MK.length) + ser(DATA, true, true) + tail + H.slice(iChars);
fs.writeFileSync(HP, H, 'utf8');
console.log('index.html 已写回 (MB):', (H.length / 1048576).toFixed(2));
console.log('DONE');
