// 收尾：① 拼音核查 A 类 35 串档字给出「源字串档·待复核」标注
//       ② 介绍页文案补上逐字判据
const fs = require('fs');
const B = 'D:/WorkBuddy/projects/说文解字/';
const HP = B + 'index.html';
let H = fs.readFileSync(HP, 'utf8');

// ---- 1) 嵌入串档字集合 ----
const SUSPECT = '阵吭住肤朋茶栏鸦眠蚣蛇徘添喧慷影鲫憔瞪螺杻茯娈隼颃涟辍嗟掣赓蝈簪鸺髢彟';
const ANCHOR = '\r\nvar CHARS = DATA.characters;';
if (!H.includes(ANCHOR)) { console.log('⚠️ 未找到 CHARS 锚点'); process.exit(1); }
if (H.includes('var PY_SW_SUSPECT')) { console.log('⚠️ PY_SW_SUSPECT 已存在，跳过'); }
else {
  H = H.replace(ANCHOR, '\r\n// 拼音核查 A 类：源《说文》条目取到的是关联异体/通假字，其音非本字之音，故标注待复核\r\n' +
    'var PY_SW_SUSPECT = new Set(' + JSON.stringify(SUSPECT.split('')) + ');\r\n' + 'var CHARS = DATA.characters;');
  console.log('已嵌入 PY_SW_SUSPECT:', SUSPECT.length, '字');
}

// ---- 2) 详情页「说文音」行区分串档 ----
if (!H.includes('依《说文》音切折合')) { console.log('⚠️ 未找到说文音行'); process.exit(1); }
const OLD_ROW2 = ' ? "<div>说文音: <span>" + c.pinyin_sw + "</span><i class=\'src-mini\'>依《说文》音切折合</i></div>"';
const NEW_ROW2 = ' ? "<div>说文音: <span>" + c.pinyin_sw + "</span>" + (typeof PY_SW_SUSPECT !== "undefined" && PY_SW_SUSPECT.has(c.char) ? "<i class=\'src-mini warn\'>源字串档·待复核</i>" : "<i class=\'src-mini\'>依《说文》音切折合</i>") + "</div>"';
if (!H.includes(OLD_ROW2)) { console.log('⚠️ 未找到说文音行锚点'); process.exit(1); }
H = H.replace(OLD_ROW2, NEW_ROW2);

// ---- 3) 介绍页文案补逐字判据 ----
const T149_OLD = '已著录、本库尚未收录（简牍帛书、小篆、隶书本库覆盖明显不足，多数缺失属此类）';
const T149_NEW = '已著录、本库尚未收录（简牍帛书 612/2420、小篆 2848/5564、隶书 0 真迹，覆盖明显不足，多数缺失属此类）——逐字判据：该字在更早书体已见，或为《说文》著录之古字（有反切或实质《说文》释义）';
if (!H.includes(T149_OLD)) { console.log('⚠️ 未找到 149 判据锚点'); process.exit(1); }
H = H.replace(T149_OLD, T149_NEW);

const T162_OLD = '隶书 0 真迹，覆盖明显不足，缺失多属此类）与';
const T162_NEW = '隶书 0 真迹，覆盖明显不足，缺失多属此类；逐字判据：该字在更早书体已见，或为《说文》著录之古字）与';
if (!H.includes(T162_OLD)) { console.log('⚠️ 未找到 162 判据锚点'); process.exit(1); }
H = H.replace(T162_OLD, T162_NEW);

// ---- 4) src-mini.warn 样式 ----
const CSS_OLD = `.evo-step .era-pending.pend-todo{color:#ffd27f}`;
if (!H.includes(CSS_OLD)) { console.log('⚠️ 未找到 pend-todo 样式'); process.exit(1); }
H = H.replace(CSS_OLD, CSS_OLD + `.src-mini.warn{color:#ffd27f;border-color:#6b5a2a;background:rgba(255,180,0,.10);border-radius:3px;padding:0 4px;font-style:normal}`);

fs.writeFileSync(HP, H, 'utf8');
console.log('PY_SW_SUSPECT 出现次数 =', (H.match(/PY_SW_SUSPECT/g) || []).length,
            '; 源字串档 出现 =', (H.match(/源字串档/g) || []).length,
            '; src-mini.warn =', (H.match(/src-mini\.warn/g) || []).length);
console.log('DONE');
