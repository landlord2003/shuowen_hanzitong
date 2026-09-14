/* 六书闯关 · 学习计划 —— 说文解字·汉字通 增值模块
 * 数据：复用页面已有 CHARS（8105 字），零新增数据资产
 * 三关：六书辨识 / 部首辨识 / 笔画数；进度与打卡存 localStorage
 */
(function () {
  'use strict';
  var LS_KEY = 'swjz_quiz_v1';
  var PER_LEVEL = 6;
  var PASS = 5;                 // 每关 ≥5/6 解锁下一关
  var DAILY_GOAL = 10;

  var LEVELS = [
    { id: 1, name: '六书辨识', tip: '这个字属于「六书」中的哪一类？' },
    { id: 2, name: '部首辨识', tip: '这个字属于哪个部首？' },
    { id: 3, name: '笔画数', tip: '这个字总共有几画？' }
  ];
  var LS_MAIN = ['象形', '指事', '会意', '形声'];

  var CSS = [
    '.qz-entry{background:linear-gradient(135deg,#1f7a5c,#3fae86);border:none;color:#fff;font-weight:600;padding:8px 16px}',
    '.qz-mask{position:fixed;inset:0;background:rgba(0,0,0,.86);display:none;align-items:center;justify-content:center;z-index:91;padding:16px}',
    '.qz-mask.show{display:flex}',
    '.qz-box{background:var(--card,#1e2a4a);border:1px solid var(--border,#2a2a4a);border-radius:16px;width:100%;max-width:660px;max-height:92vh;overflow:auto;padding:20px 22px;box-shadow:0 24px 70px rgba(0,0,0,.6)}',
    '.qz-box h2{margin:0 0 6px;font-size:20px;color:#9fe6c8}',
    '.qz-box .qz-sub{font-size:12.5px;color:var(--text3,#666);line-height:1.7;margin:0 0 14px}',
    '.qz-close{position:sticky;top:0;float:right;background:none;border:none;color:var(--text3,#666);font-size:22px;cursor:pointer;line-height:1}',
    '.qz-levels{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 16px}',
    '.qz-lv{flex:1 1 150px;border:1px solid var(--border,#2a2a4a);border-radius:12px;padding:12px 14px;background:rgba(255,255,255,.03)}',
    '.qz-lv.locked{opacity:.5}',
    '.qz-lv.done{border-color:#2e9e63}',
    '.qz-lv b{display:block;font-size:15px;margin-bottom:4px}',
    '.qz-lv span{font-size:12px;color:var(--text3,#666)}',
    '.qz-lv button{margin-top:10px}',
    '.qz-word{text-align:center;margin:4px 0 16px}',
    '.qz-word .ch{display:inline-block;font-size:60px;line-height:1.1;padding:6px 24px;border-radius:14px;background:rgba(31,122,92,.2);border:1px solid rgba(63,174,134,.5);color:#dff7ec}',
    '.qz-word .hint{display:block;font-size:12px;color:var(--text3,#666);margin-top:8px}',
    '.qz-opt{display:block;width:100%;text-align:left;padding:12px 14px;margin-bottom:9px;border-radius:10px;border:1px solid var(--border,#2a2a4a);background:rgba(255,255,255,.03);color:var(--text,#e0e0e0);font-size:15.5px;cursor:pointer;transition:.15s;font-family:inherit}',
    '.qz-opt:hover:not(:disabled){border-color:#3fae86;background:rgba(63,174,134,.14)}',
    '.qz-opt.right{border-color:#2e9e63;background:rgba(46,158,99,.18)}',
    '.qz-opt.wrong{border-color:#c1473f;background:rgba(193,71,63,.16)}',
    '.qz-opt:disabled{cursor:default;opacity:.92}',
    '.qz-bar{display:flex;gap:14px;align-items:center;font-size:13px;color:var(--text2,#999);margin-bottom:12px;flex-wrap:wrap}',
    '.qz-bar b{color:#9fe6c8}',
    '.qz-btn{padding:9px 20px;border-radius:9px;border:1px solid #1f7a5c;background:#1f7a5c;color:#fff;font-size:14.5px;cursor:pointer;font-family:inherit}',
    '.qz-btn.ghost{background:transparent;color:var(--text2,#999);border-color:var(--border,#2a2a4a)}',
    '.qz-btn[disabled]{opacity:.45;cursor:not-allowed}',
    '.qz-foot{margin-top:14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}',
    '.qz-plan{display:flex;gap:18px;flex-wrap:wrap;margin:8px 0 4px}',
    '.qz-plan div{font-size:13px;color:var(--text2,#999)}',
    '.qz-plan b{color:#9fe6c8;font-size:17px}',
    '.qz-prog{height:8px;border-radius:6px;background:rgba(255,255,255,.09);overflow:hidden;margin:8px 0 14px}',
    '.qz-prog i{display:block;height:100%;background:linear-gradient(90deg,#1f7a5c,#3fae86)}',
    '.qz-wrongs{margin:8px 0 0;padding:0;list-style:none;font-size:13.5px;line-height:1.8;max-height:170px;overflow:auto}',
    '.qz-wrongs li{padding:5px 0;border-bottom:1px dashed var(--border,#2a2a4a)}',
    '.qz-wrongs .w{color:#e8c86a;font-weight:700}',
    '.qz-wrongs .s{color:var(--text3,#666);font-size:12px}'
  ].join('');

  var st = null, el = {}, store = null;

  /* ---------------- 存档 ---------------- */
  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function load() {
    var def = { unlocked: 1, done: {}, wrong: {}, today: '', todayCount: 0, streak: 0, lastDay: '' };
    try {
      var s = JSON.parse(localStorage.getItem(LS_KEY) || 'null');
      if (s && typeof s === 'object') { for (var k in def) if (!(k in s)) s[k] = def[k]; }
      else s = def;
      return s;
    } catch (e) { return def; }
  }
  function save() { try { localStorage.setItem(LS_KEY, JSON.stringify(store)); } catch (e) { } }
  function rollDay() {
    var t = today();
    if (store.today === t) return;
    // 打卡：昨天打过 → 连续+1；否则重置为 1
    var y = new Date(); y.setDate(y.getDate() - 1);
    var ys = y.getFullYear() + '-' + String(y.getMonth() + 1).padStart(2, '0') + '-' + String(y.getDate()).padStart(2, '0');
    store.streak = (store.lastDay === ys) ? (store.streak || 0) + 1 : 1;
    store.lastDay = t;
    store.today = t;
    store.todayCount = 0;
    save();
  }

  /* ---------------- 工具 ---------------- */
  function rnd(n) { return Math.floor(Math.random() * n); }
  function pick(a) { return a[rnd(a.length)]; }
  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) { var j = rnd(i + 1), t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function injectCSS() {
    if (document.getElementById('qz-style')) return;
    var s = document.createElement('style'); s.id = 'qz-style'; s.textContent = CSS; document.head.appendChild(s);
  }

  /* ---------------- 出题 ---------------- */
  function buildLevel(lv) {
    var C = (window.CHARS || []).filter(function (c) { return c && c.char && c.liushu; });
    var qs = [], used = {}, guard = 0;
    while (qs.length < PER_LEVEL && guard++ < 4000) {
      var c = pick(C);
      if (used[c.char]) continue;
      var q = null;
      if (lv === 1) {
        if (c.liushu === '会意兼形声') continue;            // 边界类不入题，避免歧义
        if (LS_MAIN.indexOf(c.liushu) < 0) continue;
        q = { c: c, right: c.liushu, opts: shuffle(LS_MAIN.slice()), hint: '哪一类？' };
      } else if (lv === 2) {
        if (!c.radical_name) continue;
        var others = [], g2 = 0;
        while (others.length < 3 && g2++ < 300) {
          var r = pick(C).radical_name;
          if (r && r !== c.radical_name && others.indexOf(r) < 0) others.push(r);
        }
        if (others.length < 3) continue;
        q = { c: c, right: c.radical_name, opts: shuffle([c.radical_name].concat(others)), hint: '哪个部首？' };
      } else {
        if (typeof c.stroke !== 'number' || !c.stroke) continue;
        var s = {}, cand = [];
        var deltas = shuffle([-3, -2, -1, 1, 2, 3]);
        for (var i = 0; i < deltas.length && cand.length < 3; i++) {
          var v = c.stroke + deltas[i];
          if (v >= 1 && v !== c.stroke && !s[v]) { s[v] = 1; cand.push(v); }
        }
        if (cand.length < 3) continue;
        q = { c: c, right: c.stroke, opts: shuffle([c.stroke].concat(cand)).map(String), hint: '共几画？' };
      }
      used[c.char] = 1;
      qs.push(q);
    }
    return qs;
  }

  /* ---------------- 渲染 ---------------- */
  function shell() {
    var box = document.createElement('div');
    box.className = 'qz-box';
    box.addEventListener('click', function (e) { e.stopPropagation(); });
    el.mask.innerHTML = '';
    el.mask.appendChild(box);
    el.box = box;
    return box;
  }
  function close() { el.mask.classList.remove('show'); }

  function renderHome() {
    rollDay();
    var box = shell();
    var pct = Math.min(100, Math.round(store.todayCount / DAILY_GOAL * 100));
    var h = '<button class="qz-close" title="关闭">×</button>';
    h += '<h2>🏯 六书闯关 · 学习计划</h2>';
    h += '<p class="qz-sub">三关递进：<b>六书辨识 → 部首辨识 → 笔画数</b>，每关 ' + PER_LEVEL + ' 题，答对 ' + PASS + ' 题及以上解锁下一关。' +
      '全部字题取自本 App 的 8105 字真实字段，无 AI 生成内容。</p>';
    h += '<div class="qz-plan"><div>今日已答 <b>' + store.todayCount + '</b> / ' + DAILY_GOAL + ' 题</div>' +
      '<div>连续打卡 <b>' + (store.streak || 0) + '</b> 天</div>' +
      '<div>错题本 <b>' + Object.keys(store.wrong || {}).length + '</b> 字</div></div>';
    h += '<div class="qz-prog"><i style="width:' + pct + '%"></i></div>';
    h += '<div class="qz-levels">';
    LEVELS.forEach(function (lv) {
      var locked = (lv.id > store.unlocked);
      var done = !!store.done[lv.id];
      h += '<div class="qz-lv' + (locked ? ' locked' : '') + (done ? ' done' : '') + '">' +
        '<b>第 ' + lv.id + ' 关 · ' + lv.name + '</b>' +
        '<span>' + (locked ? '需先通关第 ' + (lv.id - 1) + ' 关' : (done ? '已通关 ' + store.done[lv.id] + '/' + PER_LEVEL : lv.tip)) + '</span>' +
        '<button class="qz-btn' + (locked ? '" disabled' : '') + '" data-lv="' + lv.id + '">' +
        (locked ? '未解锁' : (done ? '再练一次' : '开始闯关')) + '</button></div>';
    });
    h += '</div>';
    var wn = Object.keys(store.wrong || {}).length;
    if (wn) {
      h += '<p class="qz-sub" style="margin-top:6px">错题本（点字可查看详情）：</p><ul class="qz-wrongs">';
      Object.keys(store.wrong).slice(0, 40).forEach(function (ch) {
        var w = store.wrong[ch];
        h += '<li><span class="w">' + ch + '</span>　<span class="s">' +
          (w.miss || '') + '</span></li>';
      });
      h += '</ul><div class="qz-foot"><button class="qz-btn ghost" id="qz-clear">清空错题本</button></div>';
    }
    h += '<div class="qz-foot"><button class="qz-btn ghost" id="qz-close2">关闭</button></div>';
    box.innerHTML = h;
    box.querySelector('.qz-close').onclick = close;
    box.querySelector('#qz-close2').onclick = close;
    var cl = box.querySelector('#qz-clear');
    if (cl) cl.onclick = function () { store.wrong = {}; save(); renderHome(); };
    Array.prototype.forEach.call(box.querySelectorAll('.qz-lv button'), function (b) {
      if (b.disabled) return;
      b.onclick = function () { startLevel(parseInt(b.dataset.lv, 10)); };
    });
  }

  function startLevel(lv) {
    st = { lv: lv, qs: buildLevel(lv), i: 0, ok: 0, logged: [] };
    if (!st.qs.length) { alert('题库取题失败，请刷新重试'); return; }
    renderQ();
  }

  function renderQ() {
    var q = st.qs[st.i], box = shell();
    var h = '<button class="qz-close" title="关闭">×</button>';
    h += '<div class="qz-bar"><span>第 ' + st.lv + ' 关 · ' + LEVELS[st.lv - 1].name + '</span>' +
      '<span>第 <b>' + (st.i + 1) + '</b>/' + st.qs.length + ' 题</span><span>答对 <b>' + st.ok + '</b></span></div>';
    h += '<div class="qz-word"><span class="ch">' + q.c.char + '</span>' +
      '<span class="hint">' + q.hint + '</span></div>';
    for (var i = 0; i < q.opts.length; i++) {
      h += '<button class="qz-opt" data-i="' + i + '">' + q.opts[i] + '</button>';
    }
    h += '<div class="qz-foot"><span id="qz-fb" style="font-size:13.5px;color:var(--text2)"></span></div>';
    box.innerHTML = h;
    box.querySelector('.qz-close').onclick = close;
    Array.prototype.forEach.call(box.querySelectorAll('.qz-opt'), function (b) {
      b.onclick = function () { answer(b, q); };
    });
  }

  function answer(btn, q) {
    var rightStr = String(q.right);
    var picked = btn.textContent;
    var ok = (picked === rightStr);
    Array.prototype.forEach.call(el.box.querySelectorAll('.qz-opt'), function (b) {
      b.disabled = true;
      if (b.textContent === rightStr) b.classList.add('right');
      else if (b === btn) b.classList.add('wrong');
    });
    if (ok) { st.ok++; el.box.querySelector('#qz-fb').innerHTML = '✅ 正确'; }
    else {
      el.box.querySelector('#qz-fb').innerHTML = '❌ 正确答案：' + rightStr;
      store.wrong[q.c.char] = { miss: '应为「' + rightStr + '」，你选了「' + picked + '」（第' + st.lv + '关 ' + LEVELS[st.lv - 1].name + '）' };
    }
    st.logged.push(q.c.char);
    store.todayCount = (store.todayCount || 0) + 1;
    save();
    var foot = el.box.querySelector('.qz-foot');
    var nx = document.createElement('button');
    nx.className = 'qz-btn'; nx.style.marginLeft = 'auto';
    nx.textContent = (st.i + 1 < st.qs.length) ? '下一题 →' : '看结果 →';
    nx.onclick = function () { st.i++; if (st.i < st.qs.length) renderQ(); else renderEnd(); };
    foot.appendChild(nx);
    nx.focus();
  }

  function renderEnd() {
    var pass = st.ok >= PASS;
    var box = shell();
    var h = '<button class="qz-close" title="关闭">×</button>';
    h += '<h2>第 ' + st.lv + ' 关 · ' + (pass ? '通关 ✅' : '未通关') + '</h2>';
    h += '<div class="qz-bar"><span>答对 <b>' + st.ok + '</b>/' + st.qs.length +
      '</span><span>通关线 ' + PASS + '</span><span>今日累计 <b>' + store.todayCount + '</b>/' + DAILY_GOAL + '</span></div>';
    if (pass) {
      if (!store.done[st.lv] || store.done[st.lv] < st.ok) store.done[st.lv] = st.ok;
      if (st.lv + 1 <= LEVELS.length && store.unlocked < st.lv + 1) store.unlocked = st.lv + 1;
      save();
      h += '<p class="qz-sub">' + (st.lv < LEVELS.length ? '已解锁第 ' + (st.lv + 1) + ' 关「' + LEVELS[st.lv].name + '」。' : '三关全部通关，闯关模式完成 🎉') + '</p>';
    } else {
      h += '<p class="qz-sub">再练一次就能过关（答对 ' + PASS + ' 题即可）。错题已收进错题本。</p>';
    }
    h += '<div class="qz-foot"><button class="qz-btn" id="qz-again">再练一次</button>' +
      '<button class="qz-btn ghost" id="qz-home">返回关卡</button></div>';
    box.innerHTML = h;
    box.querySelector('.qz-close').onclick = close;
    box.querySelector('#qz-again').onclick = function () { startLevel(st.lv); };
    box.querySelector('#qz-home').onclick = function () { renderHome(); };
  }

  function open() { el.mask.classList.add('show'); renderHome(); }

  function mount() {
    injectCSS();
    store = load();
    var mask = document.createElement('div');
    mask.className = 'qz-mask';
    mask.addEventListener('click', function (e) { if (e.target === mask) close(); });
    document.body.appendChild(mask);
    el.mask = mask;

    var btn = document.createElement('button');
    btn.className = 'filter-btn qz-entry';
    btn.textContent = '🏯 六书闯关';
    btn.title = '六书辨识 / 部首辨识 / 笔画数 三关 + 每日学习计划、错题本';
    btn.onclick = open;

    var shared = document.getElementById('fhl-game-row');
    if (shared) { shared.appendChild(btn); return; }
    var row = document.createElement('div');
    row.className = 'filters';
    row.appendChild(btn);
    var sf = document.getElementById('strokeFilters');
    if (sf && sf.parentNode) sf.parentNode.insertBefore(row, sf.nextSibling);
    else document.body.appendChild(row);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();

  if (typeof window !== 'undefined' && window.__QZ_TEST__) {
    window.__QZ__ = { buildLevel: buildLevel, LEVELS: LEVELS, setStore: function (s) { store = s; } };
  }
})();
