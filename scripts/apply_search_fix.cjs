// 三项修正：① 拼音搜索归一化（去声调）② 六书筛选补「会意兼形声」③ 「认识」→「介绍」
const fs = require('fs');
const P = 'index.html';
let H = fs.readFileSync(P, 'utf8');
const before = H;
const log = [];

function rep(name, from, to, expect) {
  const n = from instanceof RegExp ? (H.match(from) || []).length : H.split(from).length - 1;
  if (n !== (expect === undefined ? 1 : expect)) {
    console.log('✗ ' + name + '：命中 ' + n + ' 次，期望 ' + (expect === undefined ? 1 : expect) + ' —— 中止');
    process.exit(1);
  }
  H = H.replace(from, to);
  log.push('✓ ' + name);
}

// ---------- ① 拼音归一化 ----------
// 1a. 注入 helpers（锚在 function getCategory 之前，单行锚点）
const ANCHOR = 'function getCategory(c) {';
const HELPERS =
  'var PINYIN_TONE={"\\u0101":"a","\\u00e1":"a","\\u01ce":"a","\\u00e0":"a",' +
  '"\\u0113":"e","\\u00e9":"e","\\u011b":"e","\\u00e8":"e",' +
  '"\\u012b":"i","\\u00ed":"i","\\u01d0":"i","\\u00ec":"i",' +
  '"\\u014d":"o","\\u00f3":"o","\\u01d2":"o","\\u00f2":"o",' +
  '"\\u016b":"u","\\u00fa":"u","\\u01d4":"u","\\u00f9":"u",' +
  '"\\u00fc":"v","\\u01d6":"v","\\u01d8":"v","\\u01da":"v","\\u01dc":"v"};\r\n' +
  'function normPinyin(s){var o="";s=s||"";for(var i=0;i<s.length;i++){var ch=s.charAt(i);o+=(PINYIN_TONE[ch]||ch);}return o;}\r\n';
rep('①a 注入 normPinyin', ANCHOR, HELPERS + ANCHOR);

// 1b. 重写匹配分支：单字母查首字母，多字母查去调拼音
const OLD_TAIL =
  '    if (q.length === 1 && q >= "a" && q <= "z") {\r\n' +
  '      var tm={"\\u0101":"a","\\u00e1":"a","\\u01ce":"a","\\u00e0":"a","\\u0113":"e","\\u00e9":"e","\\u011b":"e","\\u00e8":"e","\\u012b":"i","\\u00ed":"i","\\u01d0":"i","\\u00ec":"i","\\u014d":"o","\\u00f3":"o","\\u01d2":"o","\\u00f2":"o","\\u016b":"u","\\u00fa":"u","\\u01d4":"u","\\u00f9":"u"};\r\n' +
  '      var f0=c.pinyin[0]; var fb=tm[f0]||f0;\r\n' +
  '      if (fb===q) return true;\r\n' +
  '    }\r\n' +
  '    return c.char===q||c.trad===q||c.pinyin.toLowerCase().indexOf(q)>=0||c.radical===q||c.radical_name.indexOf(q)>=0;';
const NEW_TAIL =
  '    var _py = normPinyin(c.pinyin).toLowerCase();\r\n' +
  '    if (q.length === 1 && q >= "a" && q <= "z") {\r\n' +
  '      if (_py.charAt(0) === q) return true;\r\n' +
  '    }\r\n' +
  '    return c.char===q||c.trad===q||_py.indexOf(q)>=0||c.pinyin.toLowerCase().indexOf(q)>=0||c.radical===q||(c.radical_name||"").indexOf(q)>=0;';
rep('①b 重写匹配分支', OLD_TAIL, NEW_TAIL);

// 1c. 六书筛选逻辑改为精确匹配（配合新增第 5 个 chip，避免重复计数）
const OLD_LS =
  'var _ok = (_ls === activeLiuShu) || (activeLiuShu === "\\u4f1a\\u610f" && _ls.indexOf("\\u4f1a\\u610f") >= 0) || (activeLiuShu === "\\u5f62\\u58f0" && _ls.indexOf("\\u5f62\\u58f0") >= 0);';
const NEW_LS = 'var _ok = (_ls === activeLiuShu);';
rep('①c 六书筛选改精确匹配', OLD_LS, NEW_LS);

// ---------- ② 六书筛选补第 5 个 chip ----------
const OLD_CHIP = '<button class="filter-btn" data-ls="形声">形声</button>\r\n</div>';
const NEW_CHIP = '<button class="filter-btn" data-ls="形声">形声</button>\r\n<button class="filter-btn" data-ls="会意兼形声">会意兼形声</button>\r\n</div>';
rep('② 新增「会意兼形声」chip', OLD_CHIP, NEW_CHIP);

// 2b. 知识卡片补「会意兼形声」条目
rep(
  '②b 知识卡片补条目',
  '湖（水形胡声）」</li>',
  '湖（水形胡声）」</li>' +
  '<li><b>会意兼形声</b>：会意的两部件中其一声旁兼表读音（《说文》称「某亦聲」），如「眇（从目从少，少亦聲）、字（从宀从子，子亦聲）」</li>'
);
// 2c. 列表里「假借」条目漏了收尾引号
rep('②c 补假借条目漏引号', '借为长官）</li>', '借为长官）」</li>');
// 2d. 说明文案：改为「会意兼形声」自成一类
rep(
  '②d 说明文案同步',
  '注：本 App 将常见字归入象形、指事、会意、形声四类；转注、假借更多是用字法，未作为单字主分类。「会意兼形声」为《说文》「从X从Y，Y亦聲」一类兼有声符的会意字，单独标注、并同时计入「会意」「形声」筛选。',
  '注：本 App 将常见字归入象形、指事、会意、形声四类，另设「会意兼形声」一类（《说文》「从X从Y，Y亦聲」兼有声符的会意字，共 130 字，自成一类、单独筛选）；转注、假借属用字法，未作为单字主分类。'
);
// 2e. 搜索框提示：拼音可省声调
rep(
  '②e 搜索框提示',
  'placeholder="搜索：拼音(如 shuǐ)、部首(如 水)、字(如 海)；笔画筛选见下方按钮"',
  'placeholder="搜索：拼音，可省声调（如 shui / shuǐ）、部首（如水）、字（如海）"'
);

// ---------- ③ 认识 → 介绍 ----------
rep('③a 导航 tab 文案', '<button class="page-tab active" data-page="intro">📖 认识</button>', '<button class="page-tab active" data-page="intro">📖 介绍</button>');
rep('③b 使用说明文案', '📊 「认识」页有统计卡片、知识卡片与数据说明', '📊 「介绍」页有统计卡片、知识卡片与数据说明');

fs.writeFileSync(P, H, 'utf8');
console.log(log.join('\n'));
console.log('\n文件大小 ' + (before.length / 1048576).toFixed(2) + 'MB → ' + (H.length / 1048576).toFixed(2) + 'MB，净增 ' + (H.length - before.length) + ' 字节');
