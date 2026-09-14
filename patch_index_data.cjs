// 把 4 字勘误定向写入 index.html 内联 DATA（Python json.dumps ensure_ascii 格式）
const fs = require('fs');
const B = 'D:/WorkBuddy/projects/说文解字/';
const HP = B + 'index.html';
let H = fs.readFileSync(HP, 'utf8');

// ---- Python json.dumps(ensure_ascii=True) 兼容序列化器 ----
function escStr(s) {
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
    else if (c < 0x20 || c > 0x7F) o += '\\u' + c.toString(16).padStart(4, '0').toLowerCase();
    else o += s[i];
  }
  return o + '"';
}
function ser(v) {
  if (v === null) return 'null';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : String(v);
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  if (typeof v === 'string') return escStr(v);
  if (Array.isArray(v)) return '[' + v.map(ser).join(', ') + ']';
  return '{' + Object.keys(v).map(k => escStr(k) + ': ' + ser(v[k])).join(', ') + '}';
}

// ---- 定位并抽取 DATA JSON ----
const MK = 'var DATA = ';
const i0 = H.indexOf(MK);
if (i0 < 0) { console.log('未找到 var DATA'); process.exit(1); }
const iChars = H.indexOf('var CHARS', i0);
const seg = H.slice(i0 + MK.length, iChars);
const lastBrace = seg.lastIndexOf('}');
const jsonText = seg.slice(0, lastBrace + 1);
const tail = seg.slice(lastBrace + 1);
let DATA;
try { DATA = JSON.parse(jsonText); } catch (e) { console.log('DATA 解析失败', e.message); process.exit(1); }
console.log('DATA 解析成功: characters=' + DATA.characters.length);

const rt = ser(DATA) === jsonText;
console.log('往返字节一致:', rt);
if (!rt) { console.log('⚠️ 往返不一致——中止以免破坏 index.html。'); process.exit(1); }

// ---- 应用 4 处勘误 ----
const FIX = {
  '匦': { trad: '匭', radical: '匚', radical_name: '匚部', shuowen: '古文簋。从匚軌。', original: '匣也' },
  '颃': { trad: '頏', radical: '頁', radical_name: '頁部', shuowen: '亢或从頁。从頁亢聲。', original: '人頸也' },
  '渺': { trad: '渺', radical: '水', radical_name: '水部', shuowen: '（后起字，从水眇声，《说文》未收。）', original: '水面辽阔' },
  '驭': { trad: '馭', radical: '馬', radical_name: '馬部', shuowen: '（《说文》御之或体，从馬从又。）', original: '使馬也' },
};
let n = 0;
for (const c of DATA.characters) {
  const f = FIX[c.char];
  if (!f) continue;
  for (const k in f) { c[k] = f[k]; n++; }
}
console.log('应用字段数:', n);

const newJson = ser(DATA);
H = H.slice(0, i0 + MK.length) + newJson + tail + H.slice(iChars);

// 顺带 bump cultural.json 缓存戳
const CUIP = B + 'data/cultural-ui.js';
let cui = fs.readFileSync(CUIP, 'utf8');
const before = cui;
cui = cui.replace(/data\/cultural\.json\?v=[0-9a-z]+/, 'data/cultural.json?v=20260914b');
fs.writeFileSync(CUIP, cui, 'utf8');
console.log('cultural-ui.js 缓存戳 bump:', before !== cui);

fs.writeFileSync(HP, H, 'utf8');
console.log('index.html 已写回，新大小(MB):', (H.length / 1048576).toFixed(2));
