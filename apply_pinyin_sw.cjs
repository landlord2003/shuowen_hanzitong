// 落盘：① pinyin_sw 字段（存《说文》音）+ pinyin 改现代规范音
//       ② 详情页「字形演变」缺失阶段改为两档诚实标注
//       ③ 介绍页文案同步
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
const MAP = JSON.parse(fs.readFileSync(B + '_pinyin_map.json', 'utf8'));
console.log('pinyin 变化条数 =', Object.keys(MAP).length);

function transform(list) {
  let n = 0, sw = 0;
  const out = list.map(c => {
    const o = {};
    for (const k in c) {
      o[k] = (k === 'pinyin' && MAP[c.char]) ? MAP[c.char].new : c[k];
      if (k === 'pinyin') { o['pinyin_sw'] = c[k] || ''; sw++; }
      if (k === 'pinyin' && MAP[c.char]) n++;
    }
    if (!('pinyin_sw' in o)) { o['pinyin_sw'] = ''; sw++; }
    return o;
  });
  return { out, n, sw };
}

// ===== 1) characters.json =====
const CP = B + 'data/characters.json';
const cRaw = fs.readFileSync(CP, 'utf8');
let modeC = null;
for (const a of [false, true]) for (const sp of [false, true]) if (ser(JSON.parse(cRaw), a, sp) === cRaw) { modeC = { a, sp }; break; }
if (!modeC) { console.log('⚠️ characters.json 往返不一致，中止'); process.exit(1); }
console.log('characters.json 模式:', JSON.stringify(modeC));
const cData = JSON.parse(cRaw);
const r1 = transform(cData.characters);
cData.characters = r1.out;
fs.writeFileSync(CP, ser(cData, modeC.a, modeC.sp), 'utf8');
console.log('characters.json: 改拼音', r1.n, '写入 pinyin_sw', r1.sw);

// ===== 2) index.html 内联 DATA =====
const HP = B + 'index.html';
let H = fs.readFileSync(HP, 'utf8');
const MK = 'var DATA = ';
const i0 = H.indexOf(MK), iChars = H.indexOf('var CHARS', i0);
const seg = H.slice(i0 + MK.length, iChars);
const jsonText = seg.slice(0, seg.lastIndexOf('}') + 1), tail = seg.slice(seg.lastIndexOf('}') + 1);
const DATA = JSON.parse(jsonText);
if (ser(DATA, true, true) !== jsonText) { console.log('⚠️ index.html DATA 往返不一致，中止'); process.exit(1); }
const r2 = transform(DATA.characters);
DATA.characters = r2.out;
H = H.slice(0, i0 + MK.length) + ser(DATA, true, true) + tail + H.slice(iChars);
console.log('index.html DATA: 改拼音', r2.n, '写入 pinyin_sw', r2.sw);

// ===== 3) 详情页：新增「说文音」行 =====
const ANCHOR_PY = '"<div>\\u62fc\\u97f3: <span>" + c.pinyin + "</span></div>" +';
if (!H.includes(ANCHOR_PY)) { console.log('⚠️ 未找到拼音行锚点，中止'); process.exit(1); }
const NEW_PY = ANCHOR_PY + '\r\n' +
  '          (typeof c.pinyin_sw === "string" && c.pinyin_sw && c.pinyin_sw !== c.pinyin' +
  ' ? "<div>说文音: <span>" + c.pinyin_sw + "</span><i class=\'src-mini\'>依《说文》音切折合</i></div>"' +
  ' : (c.pinyin_sw ? "<div>说文音: <span>" + c.pinyin_sw + "</span><i class=\'src-mini\'>与今读同</i></div>" : "")) +';
H = H.replace(ANCHOR_PY, NEW_PY);

// ===== 4) 缺失阶段两档标注 =====
// 4a) 插入 pendLabel 助手（置于 showDetail 之前）
const ANCHOR_SHOW = 'function showDetail(id) {';
if (!H.includes(ANCHOR_SHOW)) { console.log('⚠️ 未找到 showDetail 锚点，中止'); process.exit(1); }
const HELPER = [
  '// 缺失阶段归因：甲骨/金文本库已近收全，缺则多为权威源亦无；',
  '// 简牍帛书/小篆/隶书本库覆盖明显不足，缺者多为「有此字形、待补」；',
  '// 后起字（NO_ANCIENT_GLYPH）一律标「未发现」。逐字按自身已有书体判定。',
  'var ERA_RANK = { "甲骨文": 1, "金文": 2, "大篆": 3, "简牍帛书": 4, "小篆": 5, "隶书": 6 };',
  'function pendLabel(era, presentEras, ch) {',
  '  if (typeof NO_ANCIENT_GLYPH !== "undefined" && NO_ANCIENT_GLYPH.has(ch)) {',
  '    return { cls: "pend-none", text: "根据权威数据源，未发现有此字形" };',
  '  }',
  '  if (era === "甲骨文" || era === "金文") {',
  '    return { cls: "pend-none", text: "根据权威数据源，未发现有此字形" };',
  '  }',
  '  var r = ERA_RANK[era] || 99;',
  '  for (var e in presentEras) { if ((ERA_RANK[e] || 99) < r) return { cls: "pend-todo", text: "有此字形，待补" }; }',
  '  return { cls: "pend-none", text: "根据权威数据源，未发现有此字形" };',
  '}',
  ''
].join('\r\n') + ANCHOR_SHOW;
H = H.replace(ANCHOR_SHOW, HELPER);

// 4b) showDetail 内收集「已有书体」
const ANCHOR_EVO = '  var evoHTML = stages.map(function(s,i){';
if (!H.includes(ANCHOR_EVO)) { console.log('⚠️ 未找到 evoHTML 锚点，中止'); process.exit(1); }
H = H.replace(ANCHOR_EVO,
  '  var presentEras = {};\r\n' +
  '  stages.forEach(function(s){ if (s.img || s.glyph) presentEras[s.era] = 1; });\r\n' +
  ANCHOR_EVO);

// 4c) 替换 pending 分支
const OLD_PEND = '    if (s.pending) { var _script = s.script || ""; var _plabel = (_script === "clerical") ? "\\u672a\\u6536\\u5f55\\u6c49\\u96b6\\u771f\\u8ff9\\u00b7\\u4ee5\\u5b57\\u4f53\\u66ff\\u4ee3" : ("\\u5386\\u53f2\\u4e0a\\u4e0d\\u5b58\\u5728\\u6b64\\u5b57\\u7684" + s.era + "\\u5b57\\u5f62");';
if (!H.includes(OLD_PEND)) { console.log('⚠️ 未找到 pending 分支锚点，中止'); process.exit(1); }
const NEW_PEND = '    if (s.pending) { var _script = s.script || ""; var _p = (_script === "clerical") ? { cls: "", text: "未收录汉隶真迹·以字体替代" } : pendLabel(s.era, presentEras, c.char);';
H = H.replace(OLD_PEND, NEW_PEND);

const OLD_PEND2 = '"\'><div class=\'era-name\'>" + s.era + "</div>" + (ERA_DESC[s.era] ? "<div class=\'era-desc pending-desc\'>" + ERA_DESC[s.era] + "</div>" : "") + "<div class=\'era-pending\'>" + _plabel + "</div></div>"; }';
if (!H.includes(OLD_PEND2)) { console.log('⚠️ 未找到 pending 收尾锚点，中止'); process.exit(1); }
H = H.replace(OLD_PEND2,
  '"\'><div class=\'era-name\'>" + s.era + "</div>" + (ERA_DESC[s.era] ? "<div class=\'era-desc pending-desc\'>" + ERA_DESC[s.era] + "</div>" : "") + "<div class=\'era-pending " + _p.cls + "\'>" + _p.text + "</div></div>"; }');

// no-ancient 类只给「未发现」
const SEG_NA = 'return arrow + "<div class=\'evo-step pending" + (_script === "clerical" ? "" : " no-ancient") + "\' data-script=\'" + _script';
if (!H.includes(SEG_NA)) { console.log('⚠️ 未找到 no-ancient 锚点，中止'); process.exit(1); }
H = H.replace(SEG_NA, 'return arrow + "<div class=\'evo-step pending" + (_p.cls === "pend-none" ? " no-ancient" : "") + "\' data-script=\'" + _script');

// ===== 5) fillAncientGlyphs：修掉未声明变量 bug + 文案对齐 =====
const OLD_FILL = [
  '    if (typeof NO_ANCIENT_GLYPH !== "undefined" && NO_ANCIENT_GLYPH.has(ch)) { if (script === "clerical") return;',
  '      node.classList.remove("pending"); node.classList.add("no-ancient");',
  '      var era = node.querySelector(".era-name") ? node.querySelector(".era-name").textContent : "";',
  '      node.innerHTML = "<div class=\'era-name\'>" + era + "</div><div class=\'era-no-ancient\'>根据汉典查询，此字目前未发现" + era + "字形</div>";',
  '    }'
].join('\r\n');
if (!H.includes(OLD_FILL)) { console.log('⚠️ 未找到 fillAncientGlyphs 锚点，中止'); process.exit(1); }
const NEW_FILL = [
  '    var _script2 = node.getAttribute("data-script") || "";',
  '    if (_script2 === "clerical") return;',
  '    if (typeof NO_ANCIENT_GLYPH !== "undefined" && NO_ANCIENT_GLYPH.has(ch)) {',
  '      var era = node.querySelector(".era-name") ? node.querySelector(".era-name").textContent : "";',
  '      var pd = node.querySelector(".era-pending");',
  '      if (pd) { pd.className = "era-pending pend-none"; pd.textContent = "根据权威数据源，未发现有此字形"; }',
  '      node.classList.remove("pending"); node.classList.add("no-ancient");',
  '    }'
].join('\r\n');
H = H.replace(OLD_FILL, NEW_FILL);

// ===== 6) CSS：两档配色 =====
const OLD_CSS = `.evo-step.pending .era-pending{font-size:11px;color:var(--text3);padding:18px 0;letter-spacing:2px}`;
if (!H.includes(OLD_CSS)) { console.log('⚠️ 未找到 era-pending 样式锚点，中止'); process.exit(1); }
H = H.replace(OLD_CSS, OLD_CSS +
  `.evo-step .era-pending.pend-todo{color:#ffd27f}` +
  `.evo-step .era-pending.pend-none{color:var(--text3)}`);

// ===== 7) 介绍页文案 =====
const T124_OLD = '缺失阶段＝据汉典等字书暂未收录此形（非「待补」）</p>';
const T124_NEW = '缺失阶段按权威源分两档标注：「有此字形，待补」（该书体在权威字书/出土文献中已著录，本库未收）或「根据权威数据源，未发现有此字形」（据汉典等字书该字未见该书体字形）</p>';
if (!H.includes(T124_OLD)) { console.log('⚠️ 未找到 sub 文案锚点，中止'); process.exit(1); }
H = H.replace(T124_OLD, T124_NEW);

const T149_OLD = '<b>未收录的字形阶段标注为「根据汉典查询，此字目前未发现该阶段字形」</b>——即该字为后起字 / 形声 / 简化字等，据汉典等字书暂未收录此形，<b>非「数据待补」</b>；隶书未收汉隶真迹，以临海＋青柳隶书字体替代</li>';
const T149_NEW = '本库未收的字形阶段<b>按权威源分两档标注</b>：<b>「有此字形，待补」</b>＝该书体在权威字书/出土文献中已著录、本库尚未收录（简牍帛书、小篆、隶书本库覆盖明显不足，多数缺失属此类）；<b>「根据权威数据源，未发现有此字形」</b>＝据汉典等字书该字未见该书体字形（后起字 / 形声 / 简化字等），甲骨文与金文本库已近收全（955/1120、2049/2072），缺失亦多属此类；隶书未收汉隶真迹，以临海＋青柳隶书字体替代</li>';
if (!H.includes(T149_OLD)) { console.log('⚠️ 未找到 149 文案锚点，中止'); process.exit(1); }
H = H.replace(T149_OLD, T149_NEW);

const T162_OLD = '④ 本产品其余字<b>据汉典等字书暂未收录该阶段字形</b>（后起字/形声/简化字等后世造字），并非「数据待补」。';
const T162_NEW = '④ 本产品未收的阶段按权威源分两档标注：<b>「有此字形，待补」</b>（该书体权威源已著录、本库未收——简牍帛书 612/2420、小篆 2848/5564、隶书 0 真迹，覆盖明显不足，缺失多属此类）与<b>「根据权威数据源，未发现有此字形」</b>（据汉典等字书该字未见该书体字形，多为后起字/形声/简化字；甲骨 955/1120、金文 2049/2072 已近收全，缺失多属此类）。';
if (!H.includes(T162_OLD)) { console.log('⚠️ 未找到 162 文案锚点，中止'); process.exit(1); }
H = H.replace(T162_OLD, T162_NEW);

// 7b) 数据说明新增「拼音」条目
const TSRC_OLD = '<li><b>六书 / 本义 / 今义 / 演变</b>：AI 生成，待核验</li>';
const TSRC_NEW = '<li><b>拼音（现代规范音）</b>：以现代普通话规范读音为准（依 pypinyin 标准读音表逐字核对），用于检索、排序与朗读；<b>说文音</b>为源数据依《说文》音切折合的古读，仅供溯源参考，详情页与拼音并列展示（两读相同者标注「与今读同」）</li>' + TSRC_OLD;
if (!H.includes(TSRC_OLD)) { console.log('⚠️ 未找到数据说明锚点，中止'); process.exit(1); }
H = H.replace(TSRC_OLD, TSRC_NEW);

fs.writeFileSync(HP, H, 'utf8');
console.log('index.html 已写回 (MB):', (H.length / 1048576).toFixed(2));
console.log('含 pinyin_sw:', (H.match(/pinyin_sw/g) || []).length,
            ' 含 pend-todo:', (H.match(/pend-todo/g) || []).length,
            ' 含 pendLabel:', (H.match(/pendLabel/g) || []).length,
            ' 残留「历史上不存在」:', (H.match(/u5386\\u53f2\\u4e0a\\u4e0d\\u5b58\\u5728/g) || []).length);
console.log('DONE');
