// 修正注音型 original（含 夯），写回 characters.json + index.html 内联 DATA
const fs = require('fs');
const B = 'D:/WorkBuddy/projects/说文解字/';

function escStr(s, ascii) {
  let o = '"';
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    if (c === 0x22) o += '\\"'; else if (c === 0x5C) o += '\\\\';
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

const SKIP = new Set(['七', '切', '乐']);          // 原值本就是义训，非注音
const MANUAL = {
  '勾': '勾本作句，同「句」（曲）', '吓': '怒聲恐人，亦作赫', '努': '勉也、用力也',
  '帮': '幫衣，治履邊也', '拯': '救也，助也', '架': '杙也，所以舉物',
  '绑': '今俗作綁笞之字', '套': '凡物重沓者爲套', '烹': '本作亯，俗「亨」字',
  '答': '當也，報也，合也', '踩': '跳也', '赣': '賜也', '拥': '抱也', '揪': '手揪也',
};
const FIX = {};
for (const x of JSON.parse(fs.readFileSync(B + '_orig_fix_cand.json', 'utf8'))) {
  if (SKIP.has(x.char)) continue;
  const g = MANUAL[x.char] || x.new;
  if (!g) { console.log('⚠️ 无义可用，跳过:', x.char); continue; }
  FIX[x.char] = g + '（出《康熙字典》）';
}
// 夯：与提取器同源，但需要保留原有源标注一致性
FIX['夯'] = '人用力以堅舉物（出《康熙字典》）';
const chars = Object.keys(FIX);
console.log('待改 original 字数:', chars.length);

function apply(list) {
  let n = 0; const missed = [];
  for (const ch of chars) {
    const rec = list.find(c => c.char === ch);
    if (!rec) { missed.push(ch); continue; }
    if (rec.original !== FIX[ch]) { rec.original = FIX[ch]; n++; }
  }
  return { n, missed };
}

// characters.json
const CP = B + 'data/characters.json';
const cRaw = fs.readFileSync(CP, 'utf8');
let modeC = null;
for (const a of [false, true]) for (const sp of [false, true]) if (ser(JSON.parse(cRaw), a, sp) === cRaw) { modeC = { a, sp }; break; }
if (!modeC) { console.log('⚠️ characters.json 往返不一致，中止'); process.exit(1); }
const cData = JSON.parse(cRaw);
const r1 = apply(cData.characters);
console.log('characters.json 改:', r1.n, '未匹配:', r1.missed.join(',') || '无');
fs.writeFileSync(CP, ser(cData, modeC.a, modeC.sp), 'utf8');

// index.html
const HP = B + 'index.html';
let H = fs.readFileSync(HP, 'utf8');
const MK = 'var DATA = ', i0 = H.indexOf(MK), iChars = H.indexOf('var CHARS', i0);
const seg = H.slice(i0 + MK.length, iChars);
const jsonText = seg.slice(0, seg.lastIndexOf('}') + 1), tail = seg.slice(seg.lastIndexOf('}') + 1);
const DATA = JSON.parse(jsonText);
if (ser(DATA, true, true) !== jsonText) { console.log('⚠️ index.html DATA 往返不一致，中止'); process.exit(1); }
const r2 = apply(DATA.characters);
console.log('index.html 改:', r2.n, '未匹配:', r2.missed.join(',') || '无');
H = H.slice(0, i0 + MK.length) + ser(DATA, true, true) + tail + H.slice(iChars);
fs.writeFileSync(HP, H, 'utf8');
console.log('DONE');
