// P1-4 余量扩展抽检 · 研判 v3（降噪版）
// 关键修正：①去掉 "X象形" 捕获（误抓"是/的/字"等虚词）
//          ②偏旁归一（氵→水 扌→手 纟→糸 月→肉 艹→艸 亻→人 讠→言 阝→阜 刂→刀 灬→火 灬 忄→心 …）
//          ③过滤虚词/停用字  ④跳过"旧story误…已更正"的否证语境
const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字';
const cj = JSON.parse(fs.readFileSync(ROOT + '/data/characters.json', 'utf8'));
const cand = JSON.parse(fs.readFileSync(ROOT + '/data/p1_candidates.json', 'utf8'));
const lm = {};
for (const c of cj.characters) lm[c.char] = { liushu: c.liushu, shuowen: c.shuowen || '' };

const NORM = { '氵':'水','氺':'水','扌':'手','纟':'糸','糹':'糸','艹':'艸','月':'肉','阝':'阜','刂':'刀','灬':'火','忄':'心','讠':'言','訁':'言','饣':'食','飠':'食','钅':'金','釒':'金','礻':'示','衤':'衣','辶':'辵','廴':'廴','丬':'爿','牜':'牛','虍':'虎','罒':'网','覀':'西','王':'玉' };
const STOP = new Set('是 的 字 其 自 为 用 代 初 之 以 而 等 可 即 也 所 在 有 和 与 由 此 又 后 前 上 下 内 外 人 中 间 从 于 至 到 来 去 出 入 大 小 多 少 现 古 旧 本 指 表 意 义 称 叫 作 变 化 成 例 如 像 象 形 声 会 转 假 借 通 同 原 初 新 简 繁 体 的 了 着 过 被 把 让 使 得 能 会 要 就 都 还 只 又 再 更 最 很 太 真 正 反 却 但 若 如 果 因 故 所'.split(' '));
const norm = c => NORM[c] || c;

function swParts(sw) {
  if (!sw || !/从|象/.test(sw)) return null;
  const s = new Set();
  for (const m of sw.matchAll(/从(.)/g)) if (/[\u4e00-\u9fff]/.test(m[1])) s.add(norm(m[1]));
  for (const m of sw.matchAll(/象(.)/g)) if (/[\u4e00-\u9fff]/.test(m[1])) s.add(norm(m[1]));
  return s;
}
// 只取"强构形断言"（story 自己明确声明了构件组合）
function storyParts(st) {
  const s = [];
  for (const m of st.matchAll(/从([\u4e00-\u9fff])从([\u4e00-\u9fff])/g)) s.push(m[1], m[2]);
  for (const m of st.matchAll(/由[「'"]?([\u4e00-\u9fff])[」'"]?[和与][「'"]?([\u4e00-\u9fff])[」'"]?(?:组|构|合)/g)) s.push(m[1], m[2]);
  for (const m of st.matchAll(/[「'"]?([\u4e00-\u9fff])[」'"]?(?:和|与)[「'"]?([\u4e00-\u9fff])[」'"]?组成/g)) s.push(m[1], m[2]);
  return s;
}

const A = [];
for (const c of cand) {
  const ch = c.ch, info = lm[ch]; if (!info) continue;
  const st = c.story || '', sw = info.shuowen || '';
  // 否证语境：整段含"已更正/旧story/误作/误为" → 跳过（其中出现的旧构件不算）
  if (/已更正|旧 ?story|误作|误为|旧说|原文误/.test(st)) continue;
  const sp = swParts(sw); if (!sp || !sp.size) continue;
  const parts = storyParts(st).map(norm).filter(p => p !== norm(ch) && !STOP.has(p));
  const bad = [...new Set(parts)].filter(p => !sp.has(p));
  if (bad.length) A.push({ ch, liushu: info.liushu, badParts: bad, swParts: [...sp], story: st, shuowen: sw });
}

A.sort((a, b) => b.badParts.length - a.badParts.length);
fs.writeFileSync(ROOT + '/data/p1_judge_v3.json', JSON.stringify({ highConfErr: A }, null, 0));
fs.writeFileSync(ROOT + '/_p1_judge_v3.txt',
  '=== 高置信·构件与《说文》冲突: ' + A.length + ' ===\n' +
  A.map(r => '【' + r.ch + '】(' + r.liushu + ') story构件[' + r.badParts.join('/') + '] ∉ 说文[' + r.swParts.join('/') + ']\n   STORY: ' + r.story.slice(0, 130) + '\n   SHUOWEN: ' + r.shuowen.slice(0, 70)).join('\n'));
console.log('高置信冲突:', A.length);
console.log(A.slice(0, 60).map(r => r.ch + ' story[' + r.badParts.join('/') + '] vs 说文[' + r.swParts.join('/') + ']').join('\n'));
