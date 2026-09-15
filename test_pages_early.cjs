/* 三页导航「立即挂载」验证 —— 断言脚本执行完即可切换页面，不必等 DOMContentLoaded
 * 用法：node _pages_early_test.cjs <pages.js 路径> <标签>
 */
const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字/';
const SRC_FILE = process.argv[2];
const LABEL = process.argv[3] || '?';
const out = [];
const log = s => out.push(s);

function makeEl(id) {
  const el = { id: id, _cls: new Set(), _ev: {} };
  el.classList = {
    add: c => el._cls.add(c),
    remove: c => el._cls.delete(c),
    contains: c => el._cls.has(c)
  };
  el.addEventListener = (ev, fn) => { (el._ev[ev] = el._ev[ev] || []).push(fn); };
  el.getAttribute = () => null;
  el.parentNode = null;
  return el;
}

const nav = makeEl('pageNav');
const pages = { intro: makeEl('page-intro'), main: makeEl('page-main'), game: makeEl('page-game') };
pages.intro._cls.add('active');   /* 静态 HTML：<section class="page active" id="page-intro"> */

const dcl = [];
const documentStub = {
  readyState: 'loading',          /* DCL 尚未触发（被 14MB 内联 DATA 脚本挡着） */
  getElementById: function (id) {
    if (id === 'pageNav') return nav;
    const k = id.replace(/^page-/, '');
    return pages[k] || null;
  },
  querySelectorAll: function (sel) { return sel === '.page' ? [pages.intro, pages.main, pages.game] : []; },
  addEventListener: function (ev, fn) { dcl.push(fn); },
  createElement: function () { return makeEl('x'); },
  body: makeEl('body')
};
const windowStub = { scrollTo: function () { } };
const locationStub = { hash: '#main' };   /* 模拟带锚点刷新 */
const historyStub = { replaceState: function () { } };

const src = fs.readFileSync(SRC_FILE, 'utf8');
log('======== 验证对象：' + LABEL + ' ========');
try {
  new Function('window', 'document', 'location', 'history', 'console', src)(
    windowStub, documentStub, locationStub, historyStub, console);
} catch (e) { log('!! 抛异常：' + e.message); }

const earlyOk = dcl.length === 0;
const switched = pages.main._cls.has('active') && !pages.intro._cls.has('active');

log('  立即挂载（无 DCL 监听）  = ' + (earlyOk ? 'PASS' : 'FAIL（挂了 ' + dcl.length + ' 个监听，要等内联脚本编译完）'));
log('  #main 深链即时切页       = ' + (switched ? 'PASS' : 'FAIL（仍停在首页 intro）'));
log('  window.switchPage 已导出 = ' + (typeof windowStub.switchPage === 'function' ? 'PASS' : 'FAIL'));

/* 阶段二：DCL 触发后（旧版只在这里才动） */
if (dcl.length) {
  log('  --- 模拟 DCL 触发 ---');
  dcl.forEach(f => { try { f(); } catch (e) { log('  监听抛错：' + e.message); } });
  log('  DCL 后切页 = ' + (pages.main._cls.has('active') ? 'PASS' : 'FAIL'));
}

const pass = earlyOk && switched;
log('==== 总结论：' + LABEL + ' → ' + (pass ? 'PASS ✔' : 'FAIL ✘') + ' ====');
fs.writeFileSync(ROOT + '_pages_' + LABEL + '.txt', out.join('\n'), 'utf8');
console.log(out.join('\n'));
