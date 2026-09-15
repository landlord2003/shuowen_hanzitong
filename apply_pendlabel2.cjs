// 升级缺失阶段归因规则 v1 -> v4：引入逐字「古已有之」判据（反切/实质说文释义）
const fs = require('fs');
const B = 'D:/WorkBuddy/projects/说文解字/';
const HP = B + 'index.html';
let H = fs.readFileSync(HP, 'utf8');

// --- 1) 替换 pendLabel 助手整块 ---
const S0 = H.indexOf('// 缺失阶段归因：');
const S1 = H.indexOf('function showDetail(id) {');
if (S0 < 0 || S1 < 0 || S1 < S0) { console.log('⚠️ 未定位 pendLabel 块'); process.exit(1); }
const HELPER = [
  '// 缺失阶段归因（v4）：',
  '//  · 甲骨/金文——本库已近收全（955/1120、2049/2072），缺者多为权威源亦无 → 未发现',
  '//  · 更早书体已见——较晚书体（简帛/小篆/隶书本库覆盖不足）多有著录 → 有此字形，待补',
  '//  · 本库无任何真迹，但该字古已有之（有反切或实质《说文》释义）→ 有此字形，待补',
  '//  · 后起字（无著录/标「后起字·俗字·新造」）→ 据权威源未发现',
  'var ERA_RANK = { "甲骨文": 1, "金文": 2, "大篆": 3, "简牍帛书": 4, "小篆": 5, "隶书": 6 };',
  'var ERA_ANCIENT = { "甲骨文": 1, "金文": 1, "大篆": 1, "简牍帛书": 1, "小篆": 1, "隶书": 1 };',
  'var SW_LATE = /后起|说文》无|說文》無|说文无|俗字|新造|本作|无此字|未见/;',
  'function isAncientChar(c) {',
  '  if (!c) return false;',
  '  if (c.fanqie && String(c.fanqie).trim()) return true;',
  '  var sw = c.shuowen ? String(c.shuowen).trim() : "";',
  '  return !!(sw && !SW_LATE.test(sw));',
  '}',
  'function pendLabel(era, presentEras, c) {',
  '  var NONE = { cls: "pend-none", text: "根据权威数据源，未发现有此字形" };',
  '  var TODO = { cls: "pend-todo", text: "有此字形，待补" };',
  '  if (era === "甲骨文" || era === "金文") return NONE;',
  '  var any = false, r = ERA_RANK[era] || 99, e;',
  '  for (e in presentEras) { any = true; if ((ERA_RANK[e] || 99) < r) return TODO; }',
  '  if (any) return NONE;',
  '  return isAncientChar(c) ? TODO : NONE;',
  '}',
  ''
].join('\r\n') + 'function showDetail(id) {';
H = H.slice(0, S0) + HELPER + H.slice(S1 + 'function showDetail(id) {'.length);

// --- 2) presentEras 只统计真迹书体（排除 字源/繁体/简体）---
const OLD_PE = '  stages.forEach(function(s){ if (s.img || s.glyph) presentEras[s.era] = 1; });';
if (!H.includes(OLD_PE)) { console.log('⚠️ 未找到 presentEras 锚点'); process.exit(1); }
H = H.replace(OLD_PE, '  stages.forEach(function(s){ if ((s.img || s.glyph) && ERA_ANCIENT[s.era]) presentEras[s.era] = 1; });');

// --- 3) pending 分支：隶书也用同一规则 ---
const OLD_P = 'var _p = (_script === "clerical") ? { cls: "", text: "未收录汉隶真迹·以字体替代" } : pendLabel(s.era, presentEras, c.char);';
if (!H.includes(OLD_P)) { console.log('⚠️ 未找到 pending 分支锚点'); process.exit(1); }
H = H.replace(OLD_P, 'var _p = pendLabel(s.era, presentEras, c);');

fs.writeFileSync(HP, H, 'utf8');
console.log('升级完成；含 ERA_ANCIENT =', (H.match(/ERA_ANCIENT/g) || []).length,
            '; isAncientChar =', (H.match(/isAncientChar/g) || []).length,
            '; pendLabel 调用 =', (H.match(/pendLabel\(s\.era, presentEras, c\)/g) || []).length);
console.log('DONE');
