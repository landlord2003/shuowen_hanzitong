// 同步 build_web.py：删除 render() 段的重复行与死代码行，并加"已落后"警示注释
const fs = require('fs');
const F = 'D:/WorkBuddy/projects/说文解字/build_web.py';
let s = fs.readFileSync(F, 'utf8');
const EOL = s.indexOf('\r\n') >= 0 ? '\r\n' : '\n';
console.log('EOL = ' + (EOL === '\r\n' ? 'CRLF' : 'LF'));

let lines = s.split(/\r?\n/);
const before = lines.length;
const removed = [];
lines = lines.filter(l => {
  // 1) 重复的 filterChars 调用（保留 applyFavFilter 那行）
  if (l === "js_parts.append('  var filtered = filterChars();')") { removed.push('重复 filterChars 行'); return false; }
  // 2) 硬编码字卡 return（挡掉 charCardHTML 的死代码）
  if (l.indexOf("js_parts.append('    return \"<div class=") === 0 && l.indexOf('charCardHTML') < 0 && l.indexOf("pinyin") > 0) {
    removed.push('死代码字卡 return 行'); return false;
  }
  return true;
});
console.log('删除 ' + (before - lines.length) + ' 行: ' + removed.join(' / '));

s = lines.join(EOL);

// 3) 顶部加警示注释（幂等）
const WARN = [
  '# -*- coding: utf-8 -*-',
  '#',
  '# ⚠️ 权威源提示（2026-09-15 起）：本脚本已不是 index.html 的权威生成源。',
  '# 线上 index.html 后续通过 apply_*.cjs 增量补丁维护，至少包含：三页 SPA(pages.js)、',
  '# 飞花令(feihualing.json)、拼音搜索归一化(normPinyin)、确定性拼音排序(cmpByPinyin/',
  '# pinyinSortKey/pinyinTone)、字卡 charCardHTML（收藏★/每日一字高亮/注音）、六书第五类',
  '# 「会意兼形声」等。这些改动尚未回迁本脚本——直接重建会让产物回退。',
  '# 若要重建：先逐一 merge 上述补丁，或改由 apply_*.cjs 继续增量维护。',
].join(EOL);

if (s.indexOf('# ⚠️ 权威源提示') < 0) {
  s = s.replace('# -*- coding: utf-8 -*-', WARN);
  console.log('✓ 已插入权威源警示注释');
} else {
  console.log('- 警示注释已存在');
}

fs.writeFileSync(F, s, 'utf8');
console.log('写入 ' + s.length + ' 字节');
