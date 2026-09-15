/* 将 index.html 由「单页长滚动」改造为三页 SPA：
 *   ① 认识（知识卡片 / 数据说明 / 统计卡片）
 *   ② 字库（每日一字 + 字查询）
 *   ③ 游戏（飞花令 / 六书闯关 入口卡片）
 * 做法：对 body 骨架（var DATA 之前的 21KB）做精确字符串替换，每步断言命中且仅命中一次。
 *      内联数据段（13MB 单行）完全不碰。
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

/* ---------- 读飞花令 meta（用于统计卡片数字） ---------- */
let FHL = null;
try {
  const j = JSON.parse(fs.readFileSync('data/feihualing.json', 'utf8'));
  FHL = j.meta;
} catch (e) { console.log('!! 飞花令 meta 不可用：' + e.message); }
const fmt = function (n) { return (n || 0).toLocaleString ? (n || 0).toLocaleString('en-US') : String(n || 0); };
const fhlPoems = FHL ? fmt(FHL.poems) : '—';
const fhlSegs = FHL ? fmt(FHL.segments) : '—';
const fhlChars = FHL ? String(FHL.chars) : '—';

/* ================= 1. 三页样式 + 顶部导航 ================= */
const CSS = [
  '<style id="pages-style">',
  '.page{display:none}',
  '.page.active{display:block;animation:pageIn .18s ease}',
  '@keyframes pageIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}',
  '.page-nav{position:sticky;top:0;z-index:60;display:flex;gap:8px;background:rgba(26,26,46,.95);backdrop-filter:blur(8px);border-bottom:1px solid var(--border);padding:10px 16px 12px;margin:-16px -16px 18px}',
  '.page-tab{flex:1 1 0;text-align:center;padding:9px 6px;border-radius:10px;border:1px solid var(--border);background:var(--card);color:var(--text2);font-size:14px;cursor:pointer;font-family:inherit;transition:.15s}',
  '.page-tab:hover{border-color:var(--accent);color:var(--text)}',
  '.page-tab.active{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}',
  '.stat-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(154px,1fr));gap:10px;margin:16px 0 20px}',
  '.stat-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px 16px}',
  '.stat-card b{display:block;font-size:23px;color:var(--text);line-height:1.25;font-weight:700}',
  '.stat-card span{display:block;font-size:12px;color:var(--text3);margin-top:5px;line-height:1.5}',
  '.stat-card.accent{border-color:var(--accent);background:linear-gradient(160deg,rgba(83,74,183,.20),var(--card))}',
  '.stat-card.accent b{color:#c9bfff}',
  '.intro-cta{text-align:center;margin:22px 0 10px}',
  '.intro-cta button{background:var(--accent);border:none;color:#fff;border-radius:10px;padding:12px 30px;font-size:15.5px;font-weight:600;cursor:pointer;font-family:inherit;margin:0 5px}',
  '.intro-cta button:hover{opacity:.9}',
  '.intro-cta button.ghost{background:var(--card);color:var(--text);border:1px solid var(--border)}',
  '.game-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px;margin:16px 0}',
  '.game-card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px 20px;display:flex;flex-direction:column;gap:8px;transition:.15s}',
  '.game-card:hover{transform:translateY(-2px)}',
  '.game-card .ico{font-size:34px;line-height:1}',
  '.game-card h3{margin:0;font-size:17px;color:var(--text)}',
  '.game-card p{margin:0;font-size:13px;color:var(--text2);line-height:1.75;flex:1}',
  '.game-card .go{align-self:flex-start;margin-top:8px;padding:9px 24px;border-radius:9px;border:none;color:#fff;font-size:14.5px;font-weight:600;cursor:pointer;font-family:inherit}',
  '.game-card.fhl{border-color:rgba(138,111,216,.55)}.game-card.fhl .go{background:linear-gradient(135deg,#534ab7,#8a6fd8)}',
  '.game-card.qz{border-color:rgba(63,174,134,.55)}.game-card.qz .go{background:linear-gradient(135deg,#1f7a5c,#3fae86)}',
  '.game-card .meta{font-size:11.5px;color:var(--text3);line-height:1.6}',
  '@media(max-width:640px){.page-nav{position:static;margin:-16px -16px 14px}.stat-cards{grid-template-columns:repeat(auto-fill,minmax(132px,1fr))}}',
  '</style>'
].join('');

const NAV = [
  '<div class="page-nav" id="pageNav">',
  '<button class="page-tab active" data-page="intro">📖 认识</button>',
  '<button class="page-tab" data-page="main">🔍 字库</button>',
  '<button class="page-tab" data-page="game">🎮 游戏</button>',
  '</div>'
].join('');

/* ================= 2. 页面①：统计卡片 + 底部 CTA ================= */
const STATCARDS = [
  '<div class="stat-cards">',
  '<div class="stat-card accent"><b>8105</b><span>规范汉字全收录（通用规范汉字表）</span></div>',
  '<div class="stat-card accent"><b>100%</b><span>字源图覆盖　GlyphWiki 溯源图层</span></div>',
  '<div class="stat-card"><b>15,931</b><span>古文字形图（真迹 7,826 ＋ 字源 8,105）</span></div>',
  '<div class="stat-card"><b>7</b><span>字形演变阶段（甲骨·金文·简帛·大篆·小篆·隶·楷）</span></div>',
  '<div class="stat-card"><b>8105</b><span>字源故事 / 成语 / 诗句（AI 生成·待抽检）</span></div>',
  '<div class="stat-card"><b>' + fhlPoems + '</b><span>飞花令语料诗篇（全宋诗＋宋词元曲诗经楚辞等）</span></div>',
  '<div class="stat-card"><b>' + fhlSegs + '</b><span>可用诗句（简体，零简繁误字）</span></div>',
  '<div class="stat-card"><b>' + fhlChars + '</b><span>飞花令令字</span></div>',
  '</div>'
].join('');

const INTRO_CTA = [
  '<div class="intro-cta">',
  '<button onclick="switchPage(\'main\')">🔍 进入字库</button>',
  '<button class="ghost" onclick="openWelcome()">❓ 使用说明</button>',
  '</div>'
].join('');

/* ================= 3. 页面③：游戏 ================= */
const GAMEPAGE = [
  '<section class="page" id="page-game">',
  '<h1>🎮 游戏乐园</h1>',
  '<p class="sub">把 8105 个字与全宋诗、宋词元曲变成可玩的内容——边玩边记，比死背字表牢得多。</p>',
  '<div class="game-cards" id="gameCards"></div>',
  '</section>'
].join('');

/* ================= 执行替换 ================= */
fs.copyFileSync(P, 'index.html.bak_pre_pages');
console.log('备份 index.html.bak_pre_pages\r\n');

// R1 <h1> 前：CSS + 导航 + 开「认识」页
once('R1 顶部导航 + 开认识页',
  '<h1>说文解字·汉字通</h1>',
  CSS + NAV + CRLF + '<section class="page active" id="page-intro">' + CRLF + '<h1>说文解字·汉字通</h1>');

// R2 摘出 info-panel（知识卡片 / 数据说明），稍后移到认识页
const dA = H.indexOf('<details class="info-panel" open>');
if (dA < 0) throw new Error('未找到 info-panel');
const dB = H.indexOf('</details>', dA) + '</details>'.length;
const INFO = H.slice(dA, dB);
console.log('✓ 摘出 info-panel ' + INFO.length + ' 字符');
H = H.slice(0, dA) + H.slice(dB);

// R3 p.sub 之后：统计卡片 + info-panel + 底部 CTA
once('R3 认识页正文（统计卡 + 知识/数据说明 + CTA）',
  '缺失阶段＝据汉典等字书暂未收录此形（非「待补」）</p>',
  '缺失阶段＝据汉典等字书暂未收录此形（非「待补」）</p>' + CRLF + STATCARDS + CRLF + INFO + CRLF + INTRO_CTA);

// R4 删掉原位置的 dailyBanner（稍后在字库页顶部重建）
once('R4 移除原每日一字', '<div id="dailyBanner" class="daily-banner"></div>' + CRLF, '');

// R5 searchInput 前：收认识页、开字库页（含重建的每日一字）
once('R5 开字库页 + 每日一字置顶',
  '<input id="searchInput"',
  '</section>' + CRLF + '<section class="page" id="page-main">' + CRLF +
  '<div id="dailyBanner" class="daily-banner"></div>' + CRLF + '<input id="searchInput"');

// R6 charGrid 后：收字库页、开游戏页
once('R6 收字库页 + 开游戏页',
  '<div class="char-grid" id="charGrid"></div>' + CRLF,
  '<div class="char-grid" id="charGrid"></div>' + CRLF + '</section>' + CRLF + GAMEPAGE + CRLF);

// R7 欢迎弹窗不再首屏自动弹出（改由「使用说明」按钮触发）
once('R7 关闭首屏自动弹窗',
  'if (__welcomeEl && !localStorage.getItem("swjz_welcome_seen")) { __welcomeEl.classList.add("show"); }',
  '/* 欢迎弹窗改由「使用说明」按钮触发，不再首屏自动弹出 */');

// R8 欢迎弹窗文案：底部改为认识页
once('R8 弹窗文案',
  '<li>📊 底部「古字形阶段覆盖统计」说明各书体收录比例</li>',
  '<li>📊 「认识」页有知识卡片、数据说明与古字形覆盖统计</li>');

// R9 挂载 pages.js
once('R9 挂载 pages.js',
  '<script src="data/quiz.js"></script>',
  '<script src="data/quiz.js"></script>' + CRLF + '<script src="data/pages.js"></script>');

fs.writeFileSync(P, H, 'utf8');
console.log('\n写入完成：' + (H.length / 1048576).toFixed(2) + ' MB');
console.log('section 数：' + (H.match(/<section class="page/g) || []).length +
  '　page-nav：' + (H.match(/id="pageNav"/g) || []).length +
  '　gameCards：' + (H.match(/id="gameCards"/g) || []).length +
  '　dailyBanner：' + (H.match(/id="dailyBanner"/g) || []).length +
  '　info-panel：' + (H.match(/class="info-panel"/g) || []).length);
