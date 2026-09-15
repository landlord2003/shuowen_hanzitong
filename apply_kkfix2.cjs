/* 修复知识卡片「正在加载…」永不消失 + 挂载时机过晚
 *
 * 病根 1（P0·功能完全失效）：mount() 首行 `document.getElementById('kkBlock')`
 *   命中的是 index.html 里的**静态占位容器**（它自带 id="kkBlock"），于是走进
 *   「已挂载、只重渲染」分支；而该容器里没有 #kkToday / #kkAllBody，
 *   renderToday()/renderAll() 双双 `if (!host) return;` 静默返回 →
 *   占位文案永远留在页面上。旧测试的 DOM 桩是"从零搭 page-intro"，
 *   没有这个预置容器，所以桩测通过、真机失效。
 *
 * 病根 2（慢）：挂载被推迟到 DOMContentLoaded，而紧随本脚本之后的
 *   14MB 内联 DATA 脚本（结尾还调 render(); renderDaily();）必须先编译执行完，
 *   DCL 才触发 → 知识卡片要等好几秒。
 *   本脚本位于 #kkBlock 之后，容器解析完即可挂载，无需等 DCL。
 */
const fs = require('fs');
const F = 'D:/WorkBuddy/projects/说文解字/data/knowledge.js';
let h = fs.readFileSync(F, 'utf8');
const EOL = h.indexOf('\r\n') >= 0 ? '\r\n' : '\n';
const L = function () { return Array.prototype.join.call(arguments, EOL); };

/* ---- 1) 重写 mount() ---- */
const OLD_MOUNT = L(
  '  function mount() {',
  '    /* 已挂载则只重渲染，避免重复替换容器（脚本被加载两次 / 手工再调用时） */',
  '    var done = document.getElementById(\'kkBlock\');',
  '    if (done) {',
  '      elBox = done;',
  '      base = defaultIndex();',
  '      off = readOff();',
  '      renderToday();',
  '      renderAll();',
  '      return;',
  '    }',
  '    var sec = document.getElementById(\'page-intro\');',
  '    if (!sec) return;',
  '    var blocks = sec.querySelectorAll(\'.intro-block\'), target = null;',
  '    for (var i = 0; i < blocks.length; i++) {',
  '      var h = blocks[i].querySelector(\'h2\');',
  '      if (h && h.textContent.indexOf(\'知识卡片\') >= 0) { target = blocks[i]; break; }',
  '    }',
  '    if (!target) return;',
  '',
  '    if (!document.getElementById(\'kk-style\')) {',
  '      var s = document.createElement(\'style\');',
  '      s.id = \'kk-style\'; s.textContent = CSS;',
  '      document.head.appendChild(s);',
  '    }',
  '',
  '    var box = document.createElement(\'div\');',
  '    box.className = \'intro-block\';',
  '    box.id = \'kkBlock\';',
  '    box.innerHTML = buildShell();',
  '    target.parentNode.replaceChild(box, target);',
  '',
  '    elBox = box;',
  '    base = defaultIndex();',
  '    off = readOff();',
  '    renderToday();',
  '    renderAll();',
  '  }'
);

const NEW_MOUNT = L(
  '  /* 是否「已由本模块挂载过」：只认带 #kkToday 的容器，',
  '     静态占位容器（index.html 里那个带「正在加载知识卡片…」的 #kkBlock）不算，',
  '     否则会把它当成品，导致 renderToday/renderAll 找不到宿主而静默空转。 */',
  '  function isMounted(el) { return !!(el && el.querySelector && el.querySelector(\'#kkToday\')); }',
  '',
  '  function mount() {',
  '    var box = document.getElementById(\'kkBlock\');',
  '',
  '    /* 已挂载 → 只重渲染，避免重复替换容器（脚本被加载两次 / 手工再调用时） */',
  '    if (isMounted(box)) {',
  '      elBox = box;',
  '      base = defaultIndex();',
  '      off = readOff();',
  '      renderToday();',
  '      renderAll();',
  '      return;',
  '    }',
  '',
  '    var sec = document.getElementById(\'page-intro\');',
  '    if (!sec) return;',
  '',
  '    if (!box) {',
  '      /* 兜底：占位容器不存在时，按小标题找到旧的知识卡片区块并原地替换 */',
  '      var blocks = sec.querySelectorAll(\'.intro-block\'), target = null;',
  '      for (var i = 0; i < blocks.length; i++) {',
  '        var h2 = blocks[i].querySelector(\'h2\');',
  '        if (h2 && h2.textContent.indexOf(\'知识卡片\') >= 0) { target = blocks[i]; break; }',
  '      }',
  '      if (!target) return;',
  '      box = document.createElement(\'div\');',
  '      box.className = \'intro-block\';',
  '      box.id = \'kkBlock\';',
  '      target.parentNode.replaceChild(box, target);',
  '    }',
  '',
  '    if (!document.getElementById(\'kk-style\')) {',
  '      var s = document.createElement(\'style\');',
  '      s.id = \'kk-style\'; s.textContent = CSS;',
  '      document.head.appendChild(s);',
  '    }',
  '',
  '    /* 静态占位容器直接复用（就地填入外壳），无占位容器时才走上面的新建分支 */',
  '    box.className = \'intro-block\';',
  '    box.id = \'kkBlock\';',
  '    box.innerHTML = buildShell();',
  '',
  '    elBox = box;',
  '    base = defaultIndex();',
  '    off = readOff();',
  '    renderToday();',
  '    renderAll();',
  '  }'
);

if (h.indexOf(OLD_MOUNT) < 0) { console.log('X 未找到 mount() 原文，中止（先回读文件确认）'); process.exit(1); }
h = h.replace(OLD_MOUNT, NEW_MOUNT);
console.log('OK mount() 已重写（区分静态占位容器 / 已挂载容器）');

/* ---- 2) 提前挂载时机 ---- */
const OLD_GATE = L(
  '  if (document.readyState === \'loading\') document.addEventListener(\'DOMContentLoaded\', mount);',
  '  else mount();'
);
const NEW_GATE = L(
  '  /* 本脚本位于 #kkBlock 之后，容器已解析完即可挂载——不必等 DOMContentLoaded：',
  '     紧随其后的 14MB 内联 DATA 脚本会把 DCL 拖后数秒，期间只能看到「正在加载…」。',
  '     容器若不在（脚本被挪到 <head> 等），才退回 DOMContentLoaded。 */',
  '  if (document.getElementById(\'page-intro\') || document.readyState !== \'loading\') mount();',
  '  else document.addEventListener(\'DOMContentLoaded\', mount);'
);
if (h.indexOf(OLD_GATE) < 0) { console.log('X 未找到挂载时机原文，中止'); process.exit(1); }
h = h.replace(OLD_GATE, NEW_GATE);
console.log('OK 挂载时机已提前（容器在即挂载，不再等 DCL）');

fs.writeFileSync(F, h, 'utf8');
console.log('已写入 ' + F + ' (' + Buffer.byteLength(h, 'utf8') + ' bytes)');
