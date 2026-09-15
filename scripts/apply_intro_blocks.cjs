/* 认识页收尾：
 *   ① 把原 <details class="info-panel"> 拆成两块独立卡片：📚 知识卡片 / 📊 数据说明
 *   ② 补 .intro-block 样式
 *   ③ 更新使用说明弹窗（搜索框位置 + 新增游戏页条目）
 */
const fs = require('fs');
const P = 'index.html';
let H = fs.readFileSync(P, 'utf8');
const CRLF = '\r\n';

function once(name, from, to, expect) {
  expect = expect === undefined ? 1 : expect;
  const n = H.split(from).length - 1;
  if (n !== expect) throw new Error('[' + name + '] 命中 ' + n + ' 次，期望 ' + expect + ' 次');
  H = H.replace(from, to);
  console.log('✓ ' + name);
}

fs.copyFileSync(P, 'index.html.bak_pre_introblocks');

/* ① 拆块 */
const a = H.indexOf('<details class="info-panel" open>');
if (a < 0) throw new Error('未找到 info-panel');
const sumEnd = H.indexOf('</summary>', a) + '</summary>'.length;
const l1 = H.indexOf('<div class="src-legend">', sumEnd);
const l2 = H.indexOf('<div class="src-legend">', l1 + 1);
const det = H.indexOf('</details>', a);
if (l1 < 0 || l2 < 0 || det < 0) throw new Error('块定位失败');
console.log('✓ 定位：details@' + a + ' 末@' + sumEnd + ' 块2@' + l2 + ' /details@' + det);

H = H.slice(0, a)
  + '<div class="intro-block"><h2>📚 知识卡片 · 六书与古文字起源</h2>'
  + H.slice(sumEnd, l2)
  + '</div>' + CRLF
  + '<div class="intro-block"><h2>📊 数据说明 · 来源与覆盖统计</h2>'
  + H.slice(l2, det)
  + '</div>'
  + H.slice(det + '</details>'.length);
console.log('✓ 拆成 知识卡片 / 数据说明 两块');

/* ② 样式 */
once('intro-block 样式',
  '<style id="pages-style">',
  '<style id="pages-style">' + CRLF +
  '.intro-block{margin:18px 0}' + CRLF +
  '.intro-block>h2{font-size:17px;margin:0 0 10px;color:var(--text);padding-bottom:6px;border-bottom:1px solid var(--border)}' + CRLF +
  '.page #page-game-title{}');

/* ③ 使用说明弹窗 */
once('弹窗：搜索框改到字库页',
  '<li>🔍 顶部搜索框：按拼音 / 部首 / 单字检索</li>',
  '<li>🔍 「字库」页：顶部搜索框（拼音 / 部首 / 单字）＋ 六书 / 分类 / 笔画 / 排序筛选</li>');

once('弹窗：补游戏页条目',
  '<li>📊 「认识」页有知识卡片、数据说明与古字形覆盖统计</li>',
  '<li>📊 「认识」页有统计卡片、知识卡片与数据说明</li>' + CRLF +
  '<li>🎮 「游戏」页：飞花令（全宋诗＋宋词元曲语料）与六书闯关 · 学习计划</li>');

fs.writeFileSync(P, H, 'utf8');
console.log('\n写入完成 ' + (H.length / 1048576).toFixed(2) + ' MB');
console.log('intro-block：' + (H.match(/class="intro-block"/g) || []).length +
  '　info-panel 残留：' + (H.match(/class="info-panel"/g) || []).length +
  '　details 残留：' + (H.match(/<details/g) || []).length);
const s = H.slice(0, H.indexOf('var DATA = '));
console.log('全宋诗 ' + (s.match(/全宋诗/g) || []).length + ' 处　全唐诗 ' + (s.match(/全唐诗/g) || []).length + ' 处');
