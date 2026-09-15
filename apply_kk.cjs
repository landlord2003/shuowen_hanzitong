/* 把 index.html 的「知识卡片」区块交给 data/knowledge.js 渲染
 * 1) 原 block（六书 / 古文字起源 / 反切 三大段）整体替换为容器 #kkBlock
 * 2) 在 pages.js 之后挂载 knowledge.js
 */
const fs = require('fs');
const R = 'D:/WorkBuddy/projects/说文解字/';
const F = R + 'index.html';
let H = fs.readFileSync(F, 'utf8');

const EOL = H.indexOf('\r\n') >= 0 ? '\r\n' : '\n';
console.log('EOL = ' + JSON.stringify(EOL));

// ---- 1) 替换知识卡片 block ----
const START_TAG = '<div class="intro-block"><h2>📚 知识卡片';
const NEXT_TAG = '<div class="intro-block"><h2>📊 数据说明';
const s = H.indexOf(START_TAG);
const e = H.indexOf(NEXT_TAG);
if (s < 0) { console.log('✗ 未找到知识卡片区块起点'); process.exit(1); }
if (e < 0 || e <= s) { console.log('✗ 未找到下一个区块（数据说明）作为终点'); process.exit(1); }
console.log('旧区块长度 = ' + (e - s) + ' 字符');

const NEW_BLOCK =
  '<div class="intro-block" id="kkBlock">' +
  '<h2>📚 知识卡片 · 每日一课</h2>' +
  '<p class="sub" style="margin:0 0 14px">正在加载知识卡片…</p>' +
  '</div>' + EOL;

H = H.slice(0, s) + NEW_BLOCK + H.slice(e);
console.log('✓ 知识卡片区块已替换为容器 #kkBlock');

// ---- 2) 挂载 knowledge.js ----
const ANCHOR = '<script src="data/pages.js"></script>';
if (H.indexOf('data/knowledge.js') < 0) {
  if (H.indexOf(ANCHOR) < 0) { console.log('✗ 未找到 pages.js script 锚点'); process.exit(1); }
  H = H.replace(ANCHOR, ANCHOR + EOL + '<script src="data/knowledge.js"></script>');
  console.log('✓ 已挂载 data/knowledge.js');
} else {
  console.log('- knowledge.js 已挂载，跳过');
}

fs.writeFileSync(F, H, 'utf8');

// ---- 自检 ----
const chk = fs.readFileSync(F, 'utf8');
console.log('--- 自检 ---');
console.log('  kkBlock 容器 = ' + chk.includes('id="kkBlock"'));
console.log('  knowledge.js 标签 = ' + chk.includes('<script src="data/knowledge.js"></script>'));
console.log('  残留「什么是「反切」？」= ' + chk.includes('什么是「反切」？'));
console.log('  残留「各古文字字形的起源」= ' + chk.includes('各古文字字形的起源'));
console.log('  数据说明区块仍在 = ' + chk.includes('📊 数据说明'));
console.log('  intro-block 总数 = ' + (chk.match(/class="intro-block"/g) || []).length);
console.log('  script 标签总数 = ' + (chk.match(/<script/g) || []).length);
