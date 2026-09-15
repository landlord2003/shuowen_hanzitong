// 落盘第二轮：① 12 挂起字按《说文》字面 + 段注改判 ② 蟊「两条并收」 ③ UI 显示 liushu_remark
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

// 𧔨（原误挂于「蛑」）的段注，本轮移交给「蟊」
const ZUN_DUAN = '〔蟲食艸𣒨者。〕艸當作苗。小雅。去其螟螣。及其蟊賊。釋蟲。食苗𣒨、蟊。毛傳。食𣒨曰蟊。螟𧎢已見虫部。𧎢是介屬。螟𧎢是𧝹屬。／〔从蟲。弔象形。〕謂上體象此蟲繚繞於苗榦之形。與䖵部蠿蟊字从䖵矛聲不同也。今人則盡叚蟊爲之矣。莫浮切。三部。／〔吏抵冒取民財則生。〕抵當作牴。觸也。冒者、冡而前也。吏不卹其民。彊禦而取民財、則生此。抵冒亦見董仲舒傳。冒古音茂。以㬪韵爲訓。／〔𧔨或从敄。〕敄聲也。此則與虫部螌蝥同字。／〔古文𧔨。从虫。从牟。〕牟聲。竹、邑相張君碑。蛑賊不起。凡漢人言侵牟皆蛑之叚借。';

const FIX = {
  // ——— 12 挂起字：按《说文》字面 + 段注明断 ———
  '寸': { liushu: '会意', liushu_remark: '《说文》「从又从一」，段注明言「故字從又一。會意也」，原标指事改会意' },
  '刃': { liushu: '象形', liushu_remark: '《说文》「象刀有刃之形」，按《说文》字面归象形；经典文字学多归指事，存此以备两说' },
  '血': { liushu: '象形', liushu_remark: '《说文》「从皿，一象血形」，按《说文》字面归象形；经典文字学多归指事，存此以备两说' },
  '亦': { liushu: '象形', liushu_remark: '《说文》「从大，象兩亦之形」，按《说文》字面归象形；经典文字学多归指事，存此以备两说' },
  '局': { liushu_remark: '《说文》「从口在尺下，復局之」为本训；段注谓句末「象形」属「一曰博，所以行棊」别义，故本训仍归会意' },
  '雷': { liushu: '象形', liushu_remark: '《说文》「从雨，畾象回轉形」，按《说文》字面归象形' },
  '夬': { liushu: '象形', liushu_remark: '《说文》「从又，纡象決形」，按《说文》字面归象形' },
  '亘': { liushu_remark: '《说文》「从二从囘」，段注明言「會意」，故仍归会意（复算器因句末「象亘回形」误判象形，已纠正）' },
  '廪': { liushu: '象形', liushu_remark: '《说文》「从入，回象屋形」，按《说文》字面归象形' },
  '簪': { liushu: '象形', liushu_remark: '《说文》「从人，匕象簪形」，段注「此非相與比敘之匕，乃象兂之形」，按字面归象形' },
  '夔': { liushu: '象形', liushu_remark: '《说文》「从夊；象有角、手、人面之形」，按《说文》字面归象形' },
  '毕': { liushu: '会意', liushu_remark: '《说文》「从𠦒，象畢形」，段注「從田𠦒會意」（「或曰甶聲」为别说），原标象形改会意' },
  // ——— 蟊：两条并收 ———
  '蟊': {
    original: '蟲食艸根者',
    shuowen: '蟲食艸根者。从蟲，象其形。吏抵冒取民財則生。',
    evolution: '《说文》蟲部作「𧔨」，訓「蟲食艸根者」；䖵部另有「蟊」訓「蠿蟊也」，段注谓二字絕異。今「蟊」指食苗根的害虫，即𧔨一系之义。',
    duan_note: ZUN_DUAN,
    variant: '《说文》䖵部另有「蟊，蠿蟊也。从䖵矛聲」（莫交切）；段玉裁注：「此字與蟲部食艸根者絕異。莫交切。古音謀在三部。」',
  },
};
const chars = Object.keys(FIX);
console.log('FIX 字数:', chars.length, chars.join(''));

function apply(list) {
  let n = 0; const missed = [], detail = [];
  for (const ch of chars) {
    const rec = list.find(c => c.char === ch);
    if (!rec) { missed.push(ch); continue; }
    const f = FIX[ch];
    for (const k in f) if (rec[k] !== f[k]) { detail.push(ch + '.' + k); rec[k] = f[k]; n++; }
  }
  return { n, missed, detail };
}

// ===== 1) characters.json =====
const CP = B + 'data/characters.json';
const cRaw = fs.readFileSync(CP, 'utf8');
let modeC = null;
for (const a of [false, true]) for (const sp of [false, true]) if (ser(JSON.parse(cRaw), a, sp) === cRaw) { modeC = { a, sp }; break; }
if (!modeC) { console.log('⚠️ characters.json 往返不一致，中止'); process.exit(1); }
console.log('characters.json 模式:', JSON.stringify(modeC));
const cData = JSON.parse(cRaw);
const r1 = apply(cData.characters);
console.log('characters.json 改字段:', r1.n, '未匹配:', r1.missed.join(',') || '无');
console.log('  明细:', r1.detail.join(' '));
fs.writeFileSync(CP, ser(cData, modeC.a, modeC.sp), 'utf8');

// ===== 2) index.html：DATA + UI =====
const HP = B + 'index.html';
let H = fs.readFileSync(HP, 'utf8');
const MK = 'var DATA = ';
const i0 = H.indexOf(MK), iChars = H.indexOf('var CHARS', i0);
const seg = H.slice(i0 + MK.length, iChars);
const jsonText = seg.slice(0, seg.lastIndexOf('}') + 1), tail = seg.slice(seg.lastIndexOf('}') + 1);
const DATA = JSON.parse(jsonText);
if (ser(DATA, true, true) !== jsonText) { console.log('⚠️ index.html DATA 往返不一致，中止'); process.exit(1); }
const r2 = apply(DATA.characters);
console.log('index.html DATA 改字段:', r2.n, '未匹配:', r2.missed.join(',') || '无');
H = H.slice(0, i0 + MK.length) + ser(DATA, true, true) + tail + H.slice(iChars);

// --- 2a) 六书行加「审校按」徽章（含转义） ---
const ESC = `(function(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/'/g,'&#39;')})`;
const OLD_A = `(c.liushu_disputed ? "<span class='dispute-badge' title='" + (c.liushu_disputed_note||"") + "'>学界有争议</span>" : "")`;
const NEW_A = `(c.liushu_disputed ? "<span class='dispute-badge' title='" + ${ESC}(c.liushu_disputed_note) + "'>学界有争议</span>" : "") + (c.liushu_remark ? "<span class='remark-badge' title='" + ${ESC}(c.liushu_remark) + "'>审校按</span>" : "")`;
if (!H.includes(OLD_A)) { console.log('⚠️ 未找到六书行锚点，中止'); process.exit(1); }
H = H.replace(OLD_A, NEW_A);

// --- 2b) 详情面板加全文可见注记（detail-info 之后） ---
const NL = '\r\n';
const SEC = '    "<div class=\'detail-section\'><h4>\\u5b57\\u5f62\\u6f14\\u53d8</h4>';
const ANCHOR_B = '        "</div>" +' + NL + '      "</div>" +' + NL + '    "</div>" +' + NL + SEC;
const NEW_B = '        "</div>" +' + NL +
  '        (c.liushu_remark ? "<div class=\'liushu-remark\'>审校按：" + ' + ESC + '(c.liushu_remark) + "</div>" : "") +' + NL +
  '      "</div>" +' + NL + '    "</div>" +' + NL + SEC;
if (!H.includes(ANCHOR_B)) { console.log('⚠️ 未找到 detail-info 收尾锚点，中止'); process.exit(1); }
H = H.replace(ANCHOR_B, NEW_B);

// --- 2c) 追加徽章 / 注记样式 ---
const OLD_CSS = `.dispute-badge{font-style:normal;font-size:10px;color:#ffd27f;border:1px solid #6b5a2a;background:rgba(255,180,0,.12);border-radius:3px;padding:1px 6px;margin-left:6px;vertical-align:middle;white-space:nowrap;cursor:help}`;
const NEW_CSS = OLD_CSS +
  `.remark-badge{font-style:normal;font-size:10px;color:#9fc7ff;border:1px solid #35507a;background:rgba(80,150,255,.12);border-radius:3px;padding:1px 6px;margin-left:6px;vertical-align:middle;white-space:nowrap;cursor:help}` +
  `.liushu-remark{font-size:11px;color:var(--text3);line-height:1.6;margin:-8px 0 14px;padding:6px 10px;background:rgba(80,150,255,.06);border-left:3px solid rgba(80,150,255,.4);border-radius:0 6px 6px 0}`;
if (!H.includes(OLD_CSS)) { console.log('⚠️ 未找到 dispute-badge 样式，中止'); process.exit(1); }
H = H.replace(OLD_CSS, NEW_CSS);

fs.writeFileSync(HP, H, 'utf8');
console.log('index.html 已写回 (MB):', (H.length / 1048576).toFixed(2));
console.log('含 remark-badge:', (H.match(/remark-badge/g) || []).length, ' 含 liushu-remark:', (H.match(/liushu-remark/g) || []).length);
console.log('DONE');
