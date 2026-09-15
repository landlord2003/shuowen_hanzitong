// apply_sort_fix.cjs —— 拼音/笔画排序改为确定性比较器
// 背景：原实现依赖 String.localeCompare(py,"zh")，其行为取决于运行环境的 ICU 数据：
//   Node 22 (full-icu) 下正常；但部分 WebView / 精简 ICU 环境下 localeCompare 会退化
//   （忽略 locale 甚至返回 0），sort 变 no-op → 列表保持数据原始序，用户即看到"没排序"。
// 改为「去调拼音字典序 → 声调 1-4-轻声 → 码位」三段键，任何 JS 引擎结果完全一致。
const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字/';
const F = ROOT + 'index.html';

let h = fs.readFileSync(F, 'utf8');
const CRLF = h.indexOf('\r\n') >= 0;
const NL = CRLF ? '\r\n' : '\n';
console.log('换行: ' + (CRLF ? 'CRLF' : 'LF'));

// 幂等
if (h.indexOf('function cmpByPinyin(') >= 0) {
  console.log('已打过补丁，退出');
  process.exit(0);
}

// ---------- 1) 插入确定性比较器（紧跟 normPinyin 之后） ----------
const ANCHOR = 'function normPinyin(s){var o="";s=s||"";for(var i=0;i<s.length;i++){var ch=s.charAt(i);o+=(PINYIN_TONE[ch]||ch);}return o;}';
if (h.indexOf(ANCHOR) < 0) { console.error('✗ 未找到 normPinyin 锚点'); process.exit(1); }

// 声调表（仅取每个音节的第一个带调字符；ü 系/无调归 5 轻声）
const HELPERS = [
  'var PINYIN_TONE_NUM={"\\u0101":1,"\\u00e1":2,"\\u01ce":3,"\\u00e0":4,"\\u0113":1,"\\u00e9":2,"\\u011b":3,"\\u00e8":4,"\\u012b":1,"\\u00ed":2,"\\u01d0":3,"\\u00ec":4,"\\u014d":1,"\\u00f3":2,"\\u01d2":3,"\\u00f2":4,"\\u016b":1,"\\u00fa":2,"\\u01d4":3,"\\u00f9":4,"\\u01d6":1,"\\u01d8":2,"\\u01da":3,"\\u01dc":4};',
  'function pinyinTone(s){s=s||"";for(var i=0;i<s.length;i++){var t=PINYIN_TONE_NUM[s.charAt(i)];if(t)return t;}return 5;}',
  'function pinyinSortKey(c){var s=normPinyin(c.pinyin).toLowerCase();var i=s.indexOf("/");if(i>=0)s=s.slice(0,i);return s;}',
  'function cmpByPinyin(a,b){',
  '  var x=pinyinSortKey(a),y=pinyinSortKey(b);',
  '  if(x!==y)return x<y?-1:1;',
  '  var ta=pinyinTone(a.pinyin),tb=pinyinTone(b.pinyin);',
  '  if(ta!==tb)return ta-tb;',
  '  var pa=a.pinyin||"",pb=b.pinyin||"";',
  '  if(pa!==pb)return pa<pb?-1:1;',
  '  return (a.char||"").codePointAt(0)-(b.char||"").codePointAt(0);',
  '}',
].join(NL);

h = h.replace(ANCHOR, ANCHOR + NL + HELPERS);
console.log('✓ 插入比较器 pinyinTone / pinyinSortKey / cmpByPinyin');

// ---------- 2) 替换排序调用 ----------
const OLD_SORT =
  '  if (activeSort==="pinyin") filtered.sort(function(a,b){return a.pinyin.localeCompare(b.pinyin,"zh")});' + NL +
  '  else if (activeSort==="stroke") filtered.sort(function(a,b){return a.stroke-b.stroke||a.pinyin.localeCompare(b.pinyin,"zh")});';
const NEW_SORT =
  '  if (activeSort==="pinyin") filtered.sort(cmpByPinyin);' + NL +
  '  else if (activeSort==="stroke") filtered.sort(function(a,b){return a.stroke-b.stroke||cmpByPinyin(a,b)});';
if (h.indexOf(OLD_SORT) < 0) { console.error('✗ 未找到排序调用锚点'); process.exit(1); }
h = h.replace(OLD_SORT, NEW_SORT);
console.log('✓ 排序调用改为 cmpByPinyin（不再依赖 localeCompare/ICU）');

// ---------- 3) 清理补丁残留：重复 var ----------
const OLD_HEAD = 'function render() {' + NL + '  var filtered = filterChars();' + NL + '  var filtered = applyFavFilter(filterChars());';
const NEW_HEAD = 'function render() {' + NL + '  var filtered = applyFavFilter(filterChars());';
if (h.indexOf(OLD_HEAD) >= 0) { h = h.replace(OLD_HEAD, NEW_HEAD); console.log('✓ 移除重复的 filterChars() 调用（8105 字过滤由两遍降为一遍）'); }

// 注意：字卡渲染路径（charCardHTML 是否启用）本次不动，保持既有视觉。见汇报说明。

fs.writeFileSync(F, h, 'utf8');
console.log('✓ index.html 已写入 ' + h.length + ' 字节');
