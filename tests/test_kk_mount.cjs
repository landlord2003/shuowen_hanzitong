/* 知识卡片挂载验证 —— 关键：DOM 桩必须**预置 index.html 里那个静态占位 #kkBlock**，
 * 否则复现不了线上「正在加载…永不消失」的故障。
 *
 * 用法：node _kkfix_test.cjs <knowledge.js 路径> <标签>
 * 对旧版（git HEAD）应判定 FAIL，对修复版应判定 PASS —— 用来证明本测试有效。
 */
const fs = require('fs');
const path = require('path');
const ROOT = 'D:/WorkBuddy/projects/说文解字/';

const SRC_FILE = process.argv[2];
const LABEL = process.argv[3] || '?';
const out = [];
const log = function (s) { out.push(s); };

/* ---------------- 极简 DOM 桩 ---------------- */
const htmlWrites = [];   /* 记录每一次 innerHTML 写入，用于断言"内容真的渲染了" */

function KE(html, tag) {
  this._html = html || '';
  this.tagName = (tag || 'div').toUpperCase();
  this.className = '';
  this.id = '';
  this.style = {};
  this.textContent = '';
  this._ev = {};
  this.parentNode = null;
}
Object.defineProperty(KE.prototype, 'innerHTML', {
  get: function () { return this._html; },
  set: function (v) { this._html = String(v); htmlWrites.push(this._html); }
});
KE.prototype._inner = function (sel) {
  if (sel.charAt(0) === '#') {
    const id = sel.slice(1);
    const m = this._html.match(new RegExp('<([a-zA-Z0-9]+)[^>]*\\sid="' + id + '"[^>]*>([\\s\\S]*?)<\\/\\1>'));
    return m ? new KE(m[2], m[1]) : null;
  }
  if (sel.charAt(0) === '.') {
    const cls = sel.slice(1);
    const re = new RegExp('<([a-zA-Z0-9]+)[^>]*\\sclass="[^"]*\\b' + cls + '\\b[^"]*"[^>]*>([\\s\\S]*?)<\\/\\1>');
    const m = this._html.match(re);
    return m ? new KE(m[2], m[1]) : null;
  }
  const re = new RegExp('<' + sel + '[^>]*>([\\s\\S]*?)<\\/' + sel + '>');
  const m = this._html.match(re);
  if (!m) return null;
  const e = new KE(m[1], sel);
  e.textContent = m[1].replace(/<[^>]*>/g, '');
  return e;
};
KE.prototype.querySelector = function (sel) { return this._inner(sel); };
KE.prototype.querySelectorAll = function (sel) {
  if (sel.charAt(0) === '.') {
    const cls = sel.slice(1);
    const n = (this._html.match(new RegExp('<[a-zA-Z0-9]+[^>]*\\sclass="[^"]*\\b' + cls + '\\b[^"]*"', 'g')) || []).length;
    const arr = [];
    for (let i = 0; i < n; i++) arr.push(new KE(this._html, 'div'));
    return arr;
  }
  return [];
};
KE.prototype.addEventListener = function (ev, fn) { (this._ev[ev] = this._ev[ev] || []).push(fn); };
KE.prototype.classList = { add() { }, remove() { }, contains() { return false; } };
KE.prototype.appendChild = function (c) { return c; };
KE.prototype.getAttribute = function () { return null; };

const headKids = [];
const dclListeners = [];

/* ★ 模拟 index.html 的真实结构：静态占位容器（自带 id="kkBlock"，内含"正在加载…"） */
const kkBlock = new KE('<h2>📚 知识卡片 · 每日一课</h2><p class="sub" style="margin:0 0 14px">正在加载知识卡片…</p>');
kkBlock.id = 'kkBlock';
kkBlock.className = 'intro-block';

const pageIntro = new KE('', 'section');
pageIntro.id = 'page-intro';
pageIntro.getElementById = null;

const documentStub = {
  /* 最坏情况：DCL 尚未触发（后面 14MB 内联脚本还在编译） */
  readyState: 'loading',
  head: { appendChild: function (n) { headKids.push(n); } },
  getElementById: function (id) {
    if (id === 'page-intro') return pageIntro;
    if (id === 'kkBlock') return kkBlock;
    if (id === 'kk-style') return headKids.filter(function (c) { return c.id === 'kk-style'; })[0] || null;
    return null;
  },
  createElement: function (t) { return new KE('', t); },
  addEventListener: function (ev, fn) { dclListeners.push(fn); },
  querySelectorAll: function () { return []; },
  body: new KE('', 'body')
};
pageIntro.querySelectorAll = function (sel) {
  if (sel === '.intro-block') return [kkBlock];
  return [];
};
pageIntro.querySelector = function (sel) { return kkBlock._inner(sel); };

const localStorageStub = {
  _d: {},
  getItem: function (k) { return Object.prototype.hasOwnProperty.call(this._d, k) ? this._d[k] : null; },
  setItem: function (k, v) { this._d[k] = String(v); },
  removeItem: function (k) { delete this._d[k]; }
};
const windowStub = {};

/* ---------------- 加载模块 ---------------- */
const src = fs.readFileSync(SRC_FILE, 'utf8');
log('======== 验证对象：' + LABEL + ' ========');
log('文件 = ' + path.basename(SRC_FILE) + ' (' + Buffer.byteLength(src, 'utf8') + ' bytes)');

const placeholderBefore = kkBlock._html.indexOf('正在加载知识卡片') >= 0;
log('加载前 #kkBlock 是静态占位容器 = ' + (placeholderBefore ? '是（与 index.html 一致）' : '否 ← 桩没还原线上结构！'));

try {
  const fn = new Function('window', 'document', 'localStorage', 'console', src);
  fn(windowStub, documentStub, localStorageStub, console);
} catch (e) {
  log('!! 模块执行抛异常：' + e.message);
}

const KK = windowStub.__kk;
log('window.__kk 已导出 = ' + (!!KK));

/* ---------------- 阶段一：脚本刚执行完（浏览器还没到 DCL） ---------------- */
const probe = function () {
  return {
    gone: kkBlock._html.indexOf('正在加载知识卡片') < 0,
    shell: kkBlock._html.indexOf('id="kkToday"') >= 0 && kkBlock._html.indexOf('id="kkAllBody"') >= 0,
    today: htmlWrites.some(function (s) { return s.indexOf('kk-head') >= 0 && s.indexOf('kk-ttl') >= 0; }),
    all: htmlWrites.some(function (s) { return s.indexOf('kk-group') >= 0 && s.indexOf('kk-item') >= 0; }),
    style: headKids.filter(function (c) { return c.id === 'kk-style'; }).length > 0
  };
};
let p = probe();
const earlyOk = p.gone && p.shell && p.today && p.all;

log('');
log('----- 阶段一：脚本执行完（DCL 尚未触发，正是用户打开页面的瞬间）-----');
log('  占位文案已消失            = ' + (p.gone ? 'PASS' : 'FAIL ← 还停在「正在加载知识卡片…」'));
log('  外壳已注入(#kkToday/#kkAllBody) = ' + (p.shell ? 'PASS' : 'FAIL'));
log('  今日一课已渲染(kk-head)   = ' + (p.today ? 'PASS' : 'FAIL'));
log('  全部知识点已渲染(kk-group)= ' + (p.all ? 'PASS' : 'FAIL'));
log('  样式已注入(#kk-style)      = ' + (p.style ? 'PASS' : 'FAIL'));
log('  无需等待 DOMContentLoaded  = ' + (dclListeners.length === 0 ? 'PASS（已立即挂载）' : 'FAIL（挂了 ' + dclListeners.length + ' 个 DCL 监听，要等 14MB 内联脚本编译完）'));
log('  innerHTML 写入次数         = ' + htmlWrites.length);
if (KK) {
  log('  state() = ' + JSON.stringify(KK.state()));
  log('  知识点条数 = ' + KK.items.length + ' ; 分类数 = ' + KK.cats.length);
}

/* ---------------- 阶段二：模拟浏览器最终触发 DCL（旧版只在这里才挂载） ---------------- */
let lateOk = earlyOk;
if (dclListeners.length) {
  log('');
  log('----- 阶段二：DCL 最终触发（等 14MB 内联脚本编译完之后的时点）-----');
  dclListeners.forEach(function (f) { try { f(); } catch (e) { log('  监听抛错：' + e.message); } });
  p = probe();
  lateOk = p.gone && p.shell && p.today && p.all;
  log('  占位文案已消失            = ' + (p.gone ? 'PASS' : 'FAIL ← 即使 DCL 触发，仍停在「正在加载知识卡片…」'));
  log('  外壳已注入                = ' + (p.shell ? 'PASS' : 'FAIL'));
  log('  今日一课已渲染            = ' + (p.today ? 'PASS' : 'FAIL'));
  log('  全部知识点已渲染          = ' + (p.all ? 'PASS' : 'FAIL'));
  if (KK) log('  state() = ' + JSON.stringify(KK.state()));
}

/* 幂等性：再 mount 两次，不应产生新容器 / 不应重注入样式 */
if (KK) {
  const writesA = htmlWrites.length, styleA = headKids.length;
  KK.mount(); KK.mount();
  log('');
  log('----- 幂等性（连续再挂载 ×2）-----');
  log('  样式表数量仍为 1           = ' + (headKids.length === styleA ? 'PASS' : 'FAIL（' + headKids.length + '）'));
  log('  仍能重渲染（写入增加）     = ' + (htmlWrites.length > writesA ? 'PASS' : 'FAIL'));
  log('  #kkBlock 外壳未被破坏      = ' + (kkBlock._html.indexOf('id="kkToday"') >= 0 ? 'PASS' : 'FAIL'));
}

const allPass = earlyOk && lateOk;
log('');
log('  判据 = 「用户打开页面即见今日一课」(阶段一) 且 「DCL 后必然可用」(阶段二)');
log('==== 总结论：' + LABEL + ' → ' + (allPass ? 'PASS ✔' : 'FAIL ✘') + ' ====');

fs.writeFileSync(ROOT + '_kkfix_' + LABEL + '.txt', out.join('\n'), 'utf8');
console.log(out.join('\n'));
