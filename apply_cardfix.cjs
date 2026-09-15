// 修复 render() 里的死代码：硬编码 return 挡掉了 charCardHTML(c)
// 使收藏 ★ / 每日一字高亮 / 注音符号恢复显示；并补上 .bopo 从属样式
const fs = require('fs');
const F = 'D:/WorkBuddy/projects/说文解字/index.html';
let h = fs.readFileSync(F, 'utf8');
const NL = h.indexOf('\r\n') >= 0 ? '\r\n' : '\n';
console.log('换行 = ' + (NL === '\r\n' ? 'CRLF' : 'LF') + ' , 文件 ' + h.length + ' 字节');

// ---- 1) 删除死代码行 ----
const DEAD = "    return \"<div class='char-card' onclick='showDetail(\" + c.id + \")\\'>\" + c.char + \"<div class='pinyin'>\" + c.pinyin + \"</div></div>\";" + NL;
const DEAD_ALT = "    return \"<div class='char-card' onclick='showDetail(\" + c.id + \")\\'>\" + c.char + \"<div class='pinyin'>\" + c.pinyin + \"</div></div>\";";
let hit = false;
if (h.indexOf(DEAD) >= 0) { h = h.replace(DEAD, ''); hit = true; }
else if (h.indexOf(DEAD_ALT) >= 0) { h = h.replace(DEAD_ALT + NL, ''); hit = true; }
console.log(hit ? '✓ 已删除死代码 return（硬编码字卡）' : '✗ 未找到死代码行（可能已修）');

// 清理重复声明的残留（若同段出现两行 var filtered）
const DUP = '  var filtered = filterChars();' + NL + '  var filtered = applyFavFilter(filterChars());';
if (h.indexOf(DUP) >= 0) { h = h.replace(DUP, '  var filtered = applyFavFilter(filterChars());'); console.log('✓ 清理重复 filterChars 调用'); }

// ---- 2) 补 .bopo 样式（当前无定义，注音会与拼音同大小）----
if (h.indexOf('.bopo{') < 0) {
  const anchor = '.fav-dot{position:absolute;top:4px;right:8px;color:#ffb300;font-size:14px}';
  const add = anchor + NL + '.bopo{font-size:9px;color:var(--text3);opacity:.75;margin-left:2px;letter-spacing:.5px}';
  if (h.indexOf(anchor) >= 0) { h = h.replace(anchor, add); console.log('✓ 已补 .bopo 样式（注音更小更淡）'); }
  else { console.log('! 未找到 .fav-dot 锚点，跳过 .bopo 样式'); }
} else { console.log('- .bopo 样式已存在'); }

fs.writeFileSync(F, h, 'utf8');
console.log('✓ 已写入 ' + h.length + ' 字节');

// ---- 3) 校验 ----
const ok = h.indexOf('return charCardHTML(c);') >= 0;
const gone = h.indexOf("onclick='showDetail(\" + c.id + \")\\'>\" + c.char") < 0;
console.log('charCardHTML 生效路径 = ' + ok + ' ; 硬编码字卡已清除 = ' + gone);
