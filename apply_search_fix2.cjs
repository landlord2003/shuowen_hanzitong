// apply_search_fix2.cjs — ①单字母搜索改为「音节首字母」匹配（不再「包含即命中」）
//                       ②排序改为按「命中的音节」排（多音字次音命中不再顶到最前）
//                       ③字卡高亮命中的音节；④知识卡片新增「反切」一节
const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字/';
const F = ROOT + 'index.html';
const AF = ROOT + 'data/app-features.js';
let H = fs.readFileSync(F, 'utf8');
const EOL = H.indexOf('\r\n') >= 0 ? '\r\n' : '\n';
const L = a => a.split('\n').join(EOL);
const log = [];
function rep(name, oldS, newS) {
  if (H.indexOf(oldS) < 0) { console.error('X 未找到锚点: ' + name); process.exit(1); }
  if (H.split(oldS).length > 2) { console.error('X 锚点不唯一: ' + name); process.exit(1); }
  H = H.replace(oldS, newS); log.push('v ' + name);
}

if (H.indexOf('function pinyinSylls(') >= 0) { console.log('已打过补丁，退出'); process.exit(0); }

// ===== 1) filterChars：单字母只匹配「音节以该字母开头」 =====
const OLD_FILTER = L([
  '    if (!q) return true;',
  '    var _py = normPinyin(c.pinyin).toLowerCase();',
  '    if (q.length === 1 && q >= "a" && q <= "z") {',
  '      if (_py.charAt(0) === q) return true;',
  '    }',
  '    return c.char===q||c.trad===q||_py.indexOf(q)>=0||c.pinyin.toLowerCase().indexOf(q)>=0||c.radical===q||(c.radical_name||"").indexOf(q)>=0;'
].join('\n'));
const NEW_FILTER = L([
  '    if (!q) return true;',
  '    var _py = normPinyin(c.pinyin).toLowerCase();',
  '    if (q.length === 1 && q >= "a" && q <= "z") {',
  '      // 单字母 = 检索「以该字母开头的音节」（多音字任一读法命中即可）',
  '      // 注意：不能再落到下面的「包含」分支，否则 h 会命中 zh/ch/sh、a 会命中 tian 之类',
  '      var _sy = _py.split("/");',
  '      for (var _si = 0; _si < _sy.length; _si++) { if (_sy[_si].charAt(0) === q) return true; }',
  '      return false;',
  '    }',
  '    return c.char===q||c.trad===q||_py.indexOf(q)>=0||c.pinyin.toLowerCase().indexOf(q)>=0||c.radical===q||(c.radical_name||"").indexOf(q)>=0;'
].join('\n'));
rep('1) filterChars 单字母改按音节首字母', OLD_FILTER, NEW_FILTER);

// ===== 2) 排序键/声调改用「命中的音节」 =====
const OLD_SORT = L([
  'function pinyinSortKey(c){var s=normPinyin(c.pinyin).toLowerCase();var i=s.indexOf("/");if(i>=0)s=s.slice(0,i);return s;}',
  'function cmpByPinyin(a,b){',
  '  var x=pinyinSortKey(a),y=pinyinSortKey(b);',
  '  if(x!==y)return x<y?-1:1;',
  '  var ta=pinyinTone(a.pinyin),tb=pinyinTone(b.pinyin);',
  '  if(ta!==tb)return ta-tb;'
].join('\n'));
const NEW_SORT = L([
  '// q = 当前搜索词（归一化小写）；单字母时排序键取「以该字母开头的那个音节」',
  '// 例：搜 t 时「弹 dàn/tán」按 tán 排到 tan 区，而非按 dàn 挤到最前',
  'function pinyinSylls(c){return {raw:(c.pinyin||"").split("/"),nrm:normPinyin(c.pinyin).toLowerCase().split("/")};}',
  'function matchedSyllIdx(c,q){',
  '  var s=pinyinSylls(c);',
  '  if(q&&q.length===1){for(var i=0;i<s.nrm.length;i++){if(s.nrm[i].charAt(0)===q)return i;}}',
  '  return 0;',
  '}',
  'function pinyinSortKey(c,q){var s=pinyinSylls(c);return s.nrm[matchedSyllIdx(c,q)]||"";}',
  'function cmpByPinyin(a,b,q){',
  '  var x=pinyinSortKey(a,q),y=pinyinSortKey(b,q);',
  '  if(x!==y)return x<y?-1:1;',
  '  var sa=pinyinSylls(a),sb=pinyinSylls(b);',
  '  var ta=pinyinTone(sa.raw[matchedSyllIdx(a,q)]||""),tb=pinyinTone(sb.raw[matchedSyllIdx(b,q)]||"");',
  '  if(ta!==tb)return ta-tb;'
].join('\n'));
rep('2) 排序按命中音节（pinyinSylls/matchedSyllIdx）', OLD_SORT, NEW_SORT);

// ===== 3) 声明 searchQueryNorm（供字卡高亮） =====
const ANCHOR_NP = 'function normPinyin(s){var o="";s=s||"";for(var i=0;i<s.length;i++){var ch=s.charAt(i);o+=(PINYIN_TONE[ch]||ch);}return o;}';
rep('3) 声明 searchQueryNorm',
  ANCHOR_NP,
  ANCHOR_NP + EOL + 'var searchQueryNorm = "";  // 当前搜索词（归一化小写），供字卡高亮命中音节');

// ===== 4) render：记录查询词 + 把 q 传给比较器 =====
const OLD_RENDER = L([
  'function render() {',
  '  var filtered = applyFavFilter(filterChars());',
  '  if (activeSort==="pinyin") filtered.sort(cmpByPinyin);',
  '  else if (activeSort==="stroke") filtered.sort(function(a,b){return a.stroke-b.stroke||cmpByPinyin(a,b)});'
].join('\n'));
const NEW_RENDER = L([
  'function render() {',
  '  searchQueryNorm = (document.getElementById("searchInput").value||"").trim().toLowerCase();',
  '  var filtered = applyFavFilter(filterChars());',
  '  if (activeSort==="pinyin") filtered.sort(function(a,b){return cmpByPinyin(a,b,searchQueryNorm)});',
  '  else if (activeSort==="stroke") filtered.sort(function(a,b){return a.stroke-b.stroke||cmpByPinyin(a,b,searchQueryNorm)});'
].join('\n'));
rep('4) render 传 q', OLD_RENDER, NEW_RENDER);

// ===== 5) CSS：命中音节高亮 =====
const OLD_CSS = '.filter-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}</style>';
rep('5) CSS .py-hit',
  OLD_CSS,
  '.filter-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}.py-hit{color:var(--accent);font-weight:700}</style>');

// ===== 6) 知识卡片：标题 + 反切一节 =====
rep('6a) 知识卡片标题加「反切」',
  '<h2>📚 知识卡片 · 六书与古文字起源</h2>',
  '<h2>📚 知识卡片 · 六书、古文字起源与反切</h2>');

const OLD_END = L([
  '<li><b>楷书（汉末成熟，魏晋定型）</b>：由隶书进一步笔画化、结构方正规范而来，沿用至今的标准字体（本产品以系统字体呈现，非古文字真迹）。</li>',
  '</ul>',
  '</div>',
  '</div>'
].join('\n'));
const FANQIE_HTML = [
  '<li><b>楷书（汉末成熟，魏晋定型）</b>：由隶书进一步笔画化、结构方正规范而来，沿用至今的标准字体（本产品以系统字体呈现，非古文字真迹）。</li>',
  '</ul>',
  '<h3 style="margin:18px 0 8px">什么是「反切」？</h3>',
  '<p style="margin:0 0 10px;line-height:1.7">「反切」是汉魏以来传统的注音方法：<b>用两个汉字拼注第三个字的读音</b>——<b>上字取声母，下字取韵母与声调</b>。本 App 详情页的「反切」一栏展示该字在《说文》等字书中的音切，「说文音」即据此音切折合出的古读。</p>',
  '<ul style="margin:0 0 10px;padding-left:20px;line-height:1.8">',
  '<li><b>怎么拼</b>：如「<b>一</b>」《说文》作「<b>於悉切</b>」——上字「於」取声母 <b>y</b>，下字「悉」取韵母 <b>i</b>，拼得 <b>yī</b>，与今读相同。</li>',
  '<li><b>为什么不直接等于今读</b>：反切记录的是<b>唐宋以前的语音系统</b>，须经语音演变折合才是今音。如「<b>江</b>」《说文》作「<b>古雙切</b>」——上取声母 g、下取韵母 uang，直拼为 *guāng（* 表示按音切拼出、实际不存在的音节），而今读 <b>jiāng</b>：中古「见母」逢细音后颚化为 j，即「见母颚化」。</li>',
  '<li><b>古读与今读可以不同</b>：如「<b>缇</b>」《说文》作「<b>他禮切</b>」，折合为 <b>tǐ</b>（古读）；《广韵》作「杜奚切」，折合为 <b>tí</b>，与今读一致。这正是本 App 把读音分作两栏的原因——<b>拼音</b>＝现代规范音，<b>说文音</b>＝据《说文》音切折合的古读（两读相同者标注「与今读同」）。</li>',
  '</ul>',
  '<p style="margin:0;font-size:12px;color:var(--text3)">说明：「说文音」为按音切规则折合的结果，供溯源参考，不作为现代读音规范；8105 字中有反切者 5378 字，其余多为后起字（字书未收，故无反切）。</p>',
  '</div>',
  '</div>'
].join('\n');
rep('6b) 知识卡片加「反切」一节', OLD_END, FANQIE_HTML);

fs.writeFileSync(F, H, 'utf8');

// ===== 7) app-features.js：字卡高亮命中音节 =====
let A = fs.readFileSync(AF, 'utf8');
const AEOL = A.indexOf('\r\n') >= 0 ? '\r\n' : '\n';
const AL = a => a.split('\n').join(AEOL);
if (A.indexOf('function hiPinyin(') >= 0) { console.log('app-features 已打过补丁'); }
else {
  const OLD_CC = AL([
    '// 字符卡片（含收藏星标 + 每日一字高亮）',
    'function charCardHTML(c) {',
    '  var fav = favSet.has(c.char) ? "<span class=\'fav-dot\'>★</span>" : "";',
    '  var daily = (c.char === dailyChar) ? " daily-card" : "";',
    '  return "<div class=\'char-card" + daily + "\' onclick=\'showDetail(" + c.id + ")\'>" + fav + c.char +',
    '         "<div class=\'pinyin\'>" + c.pinyin + " <span class=\'bopo\'>" + (typeof pinyinToBopomofo===\'function\'?pinyinToBopomofo(c.pinyin):\'\') + "</span></div></div>";',
    '}'
  ].join('\n'));
  const NEW_CC = AL([
    '// 高亮当前搜索命中的音节：单字母＝整个音节，多字母＝音节内的匹配片段',
    'function hiPinyin(raw) {',
    '  raw = raw || "";',
    '  var q = (typeof searchQueryNorm === "string") ? searchQueryNorm : "";',
    '  if (!q || typeof normPinyin !== "function") return raw;',
    '  var parts = raw.split("/"), nrm = normPinyin(raw).toLowerCase().split("/");',
    '  if (parts.length !== nrm.length) return raw;',
    '  for (var i = 0; i < nrm.length; i++) {',
    '    var j = (q.length === 1) ? (nrm[i].charAt(0) === q ? 0 : -1) : nrm[i].indexOf(q);',
    '    if (j < 0) continue;',
    '    var len = (q.length === 1) ? parts[i].length : q.length;',
    '    var hit = parts[i].slice(j, j + len);',
    '    if (!hit) continue;',
    '    parts[i] = parts[i].slice(0, j) + "<b class=\'py-hit\'>" + hit + "</b>" + parts[i].slice(j + len);',
    '    break;',
    '  }',
    '  return parts.join("/");',
    '}',
    '// 字符卡片（含收藏星标 + 每日一字高亮 + 搜索命中高亮）',
    'function charCardHTML(c) {',
    '  var fav = favSet.has(c.char) ? "<span class=\'fav-dot\'>★</span>" : "";',
    '  var daily = (c.char === dailyChar) ? " daily-card" : "";',
    '  return "<div class=\'char-card" + daily + "\' onclick=\'showDetail(" + c.id + ")\'>" + fav + c.char +',
    '         "<div class=\'pinyin\'>" + hiPinyin(c.pinyin) + " <span class=\'bopo\'>" + (typeof pinyinToBopomofo===\'function\'?pinyinToBopomofo(c.pinyin):\'\') + "</span></div></div>";',
    '}'
  ].join('\n'));
  if (A.indexOf(OLD_CC) < 0) { console.error('X 未找到 charCardHTML 锚点'); process.exit(1); }
  A = A.replace(OLD_CC, NEW_CC);
  fs.writeFileSync(AF, A, 'utf8');
  log.push('v 7) charCardHTML 高亮命中音节 (app-features.js)');
}

console.log(log.join('\n'));
console.log('EOL idx.html = ' + JSON.stringify(EOL) + ' ; app-features = ' + JSON.stringify(AEOL));
fs.writeFileSync(ROOT + '_apply2_log.txt', log.join('\n') + '\nEOL idx.html = ' + JSON.stringify(EOL) + ' ; app-features = ' + JSON.stringify(AEOL) + '\n', 'utf8');
