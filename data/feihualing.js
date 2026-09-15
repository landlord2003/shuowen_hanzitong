/* 飞花令 —— 说文解字·汉字通 增值模块
 * 自包含：自注入入口按钮 / 样式 / 弹层；数据来自 data/feihualing.json（运行时 fetch）
 * 语料：宋词·元曲·诗经·楚辞·曹操·纳兰性德（简体原文，排除繁体源避免转换误字）
 */
(function () {
  'use strict';
  var URL_DATA = 'data/feihualing.json';
  var PER_ROUND = 8;
  var data = null, pending = false, waiters = [];

  var CSS = [
    '.fhl-entry{background:linear-gradient(135deg,#534ab7,#8a6fd8);border:none;color:#fff;font-weight:600;padding:8px 16px}',
    '.fhl-mask{position:fixed;inset:0;background:rgba(0,0,0,.86);display:none;align-items:center;justify-content:center;z-index:90;padding:16px}',
    '.fhl-mask.show{display:flex}',
    '.fhl-box{background:var(--card,#1e2a4a);border:1px solid var(--border,#2a2a4a);border-radius:16px;width:100%;max-width:660px;max-height:92vh;overflow:auto;padding:20px 22px;box-shadow:0 24px 70px rgba(0,0,0,.6)}',
    '.fhl-box h2{margin:0 0 6px;font-size:20px;color:#c9bfff}',
    '.fhl-box .fhl-sub{font-size:12.5px;color:var(--text3,#666);line-height:1.7;margin:0 0 14px}',
    '.fhl-word{text-align:center;margin:6px 0 14px}',
    '.fhl-word .ch{display:inline-block;font-size:64px;line-height:1.1;padding:8px 26px;border-radius:14px;background:rgba(83,74,183,.22);border:1px solid rgba(83,74,183,.5);color:#e6e0ff}',
    '.fhl-word .tip{display:block;font-size:12px;color:var(--text3,#666);margin-top:8px}',
    '.fhl-opt{display:block;width:100%;text-align:left;padding:12px 14px;margin-bottom:9px;border-radius:10px;border:1px solid var(--border,#2a2a4a);background:rgba(255,255,255,.03);color:var(--text,#e0e0e0);font-size:15.5px;cursor:pointer;transition:.15s;font-family:inherit}',
    '.fhl-opt:hover:not(:disabled){border-color:var(--accent,#534ab7);background:rgba(83,74,183,.14)}',
    '.fhl-opt .src{display:block;font-size:11.5px;color:var(--text3,#666);margin-top:5px}',
    '.fhl-opt.right{border-color:#2e9e63;background:rgba(46,158,99,.18)}',
    '.fhl-opt.wrong{border-color:#c1473f;background:rgba(193,71,63,.16)}',
    '.fhl-opt:disabled{cursor:default;opacity:.92}',
    '.fhl-bar{display:flex;gap:14px;align-items:center;font-size:13px;color:var(--text2,#999);margin-bottom:12px;flex-wrap:wrap}',
    '.fhl-bar b{color:#c9bfff}',
    '.fhl-btn{padding:9px 20px;border-radius:9px;border:1px solid var(--accent,#534ab7);background:var(--accent,#534ab7);color:#fff;font-size:14.5px;cursor:pointer;font-family:inherit}',
    '.fhl-btn.ghost{background:transparent;color:var(--text2,#999);border-color:var(--border,#2a2a4a)}',
    '.fhl-foot{margin-top:14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}',
    '.fhl-grade{font-size:30px;color:#e8c86a;margin:2px 0 10px;text-align:center}',
    '.fhl-review{margin:12px 0 0;padding:0;list-style:none;font-size:13.5px;line-height:1.9}',
    '.fhl-review li{padding:6px 0;border-bottom:1px dashed var(--border,#2a2a4a)}',
    '.fhl-review .w{color:#e8c86a;font-weight:700}',
    '.fhl-review .s{color:var(--text3,#666);font-size:12px}',
    '.fhl-close{position:sticky;top:0;float:right;background:none;border:none;color:var(--text3,#666);font-size:22px;cursor:pointer;line-height:1}'
  ].join('');

  function injectCSS() {
    if (document.getElementById('fhl-style')) return;
    var s = document.createElement('style');
    s.id = 'fhl-style';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function ensure(cb) {
    if (data) return cb();
    waiters.push(cb);
    if (pending) return;
    pending = true;
    fetch(URL_DATA).then(function (r) { return r.json(); }).then(function (j) {
      data = j; pending = false;
      waiters.splice(0).forEach(function (f) { try { f(); } catch (e) { } });
    }).catch(function (e) {
      pending = false;
      var ws = waiters.splice(0);
      ws.forEach(function (f) { try { f(e); } catch (x) { } });
    });
  }

  function rnd(n) { return Math.floor(Math.random() * n); }
  function pick(a) { return a[rnd(a.length)]; }
  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) { var j = rnd(i + 1); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }

  var st = null, el = {};

  function buildQuestions() {
    var keys = Object.keys(data.chars);
    var used = shuffle(keys.slice()).slice(0, PER_ROUND);
    var qs = [];
    for (var i = 0; i < used.length; i++) {
      var ch = used[i];
      var right = pick(data.chars[ch]);
      var opts = [right], guard = 0;
      while (opts.length < 4 && guard++ < 200) {
        var d = pick(data.pool);
        if (d[0].indexOf(ch) >= 0) continue;
        var dup = false;
        for (var k = 0; k < opts.length; k++) if (opts[k][0] === d[0]) dup = true;
        if (!dup) opts.push(d);
      }
      qs.push({ ch: ch, right: right, opts: shuffle(opts), answered: false, ok: false });
    }
    return qs;
  }

  function renderShell() {
    var box = document.createElement('div');
    box.className = 'fhl-box';
    box.addEventListener('click', function (e) { e.stopPropagation(); });
    el.mask.innerHTML = '';
    el.mask.appendChild(box);
    el.box = box;
    return box;
  }

  function close() { el.mask.classList.remove('show'); }

  /* ---------- 起始页 ---------- */
  function renderStart() {
    var box = renderShell();
    var m = data.meta;
    box.innerHTML =
      '<button class="fhl-close" title="关闭">×</button>' +
      '<h2>🎋 飞花令</h2>' +
      '<p class="fhl-sub">规则：系统给出一个<b>令字</b>，从四句中选出<b>真正含该字</b>的那一句。' +
      '共 ' + PER_ROUND + ' 题，答对 10 分，连对额外加分。<br>' +
      '语料：' + m.corpus.join('·') + '，共 ' + m.poems.toLocaleString() + ' 首、' +
      m.segments.toLocaleString() + ' 句（均为简体原文，未做简繁转换）；令字 ' + m.chars + ' 个。</p>' +
      '<div class="fhl-foot"><button class="fhl-btn" id="fhl-go">开始飞花令</button>' +
      '<button class="fhl-btn ghost" id="fhl-cancel">关闭</button>' +
      '<span style="font-size:12px;color:var(--text3)">数据构建于 ' + m.built + '</span></div>';
    box.querySelector('.fhl-close').onclick = close;
    box.querySelector('#fhl-cancel').onclick = close;
    box.querySelector('#fhl-go').onclick = start;
  }

  /* ---------- 对局 ---------- */
  function start() {
    st = { qs: buildQuestions(), i: 0, ok: 0, streak: 0, best: 0, log: [], t0: Date.now() };
    renderQuestion();
  }

  function renderQuestion() {
    var q = st.qs[st.i], box = renderShell();
    var h = '<button class="fhl-close" title="关闭">×</button>';
    h += '<div class="fhl-bar"><span>第 <b>' + (st.i + 1) + '</b> / ' + st.qs.length + ' 题</span>' +
      '<span>得分 <b>' + score() + '</b></span>' +
      '<span>连对 <b>' + st.streak + '</b></span></div>';
    h += '<div class="fhl-word"><span class="ch">' + q.ch + '</span>' +
      '<span class="tip">哪一句含有「' + q.ch + '」？</span></div>';
    for (var i = 0; i < q.opts.length; i++) {
      h += '<button class="fhl-opt" data-i="' + i + '">' + q.opts[i][0] +
        '<span class="src">——' + q.opts[i][1] + '</span></button>';
    }
    h += '<div class="fhl-foot"><span id="fhl-fb" style="font-size:13.5px;color:var(--text2)"></span></div>';
    box.innerHTML = h;
    box.querySelector('.fhl-close').onclick = close;
    Array.prototype.forEach.call(box.querySelectorAll('.fhl-opt'), function (b) {
      b.onclick = function () { answer(parseInt(b.dataset.i, 10)); };
    });
    el.box = box;
  }

  function score() { return st.ok * 10 + st.best * 5; }

  function answer(idx) {
    var q = st.qs[st.i];
    if (q.answered) return;
    q.answered = true;
    var correctIdx = q.opts.indexOf(q.right);
    q.ok = (idx === correctIdx);
    var btns = el.box.querySelectorAll('.fhl-opt');
    Array.prototype.forEach.call(btns, function (b, i) {
      b.disabled = true;
      if (i === correctIdx) b.classList.add('right');
      else if (i === idx) b.classList.add('wrong');
    });
    if (q.ok) {
      st.ok++; st.streak++; if (st.streak > st.best) st.best = st.streak;
      el.box.querySelector('#fhl-fb').innerHTML = '✅ 答对了　——' + q.right[1];
    } else {
      st.streak = 0;
      el.box.querySelector('#fhl-fb').innerHTML = '❌ 应选「' + q.right[0] + '」　——' + q.right[1];
    }
    st.log.push({ ch: q.ch, line: q.right[0], src: q.right[1], ok: q.ok });
    var foot = el.box.querySelector('.fhl-foot');
    var next = document.createElement('button');
    next.className = 'fhl-btn';
    next.style.marginLeft = 'auto';
    next.textContent = (st.i + 1 < st.qs.length) ? '下一题 →' : '看结果 →';
    next.onclick = function () {
      st.i++;
      if (st.i < st.qs.length) renderQuestion(); else renderEnd();
    };
    foot.appendChild(next);
    next.focus();
  }

  function renderEnd() {
    var secs = Math.round((Date.now() - st.t0) / 1000);
    var ratio = st.ok / st.qs.length;
    var grade = ratio === 1 ? '🌸 花神' : ratio >= 0.875 ? '🍶 诗仙' : ratio >= 0.625 ? '📜 骚客' : ratio >= 0.375 ? '🖌 学童' : '🌱 开蒙';
    var box = renderShell();
    var h = '<button class="fhl-close" title="关闭">×</button>';
    h += '<h2>本局结果</h2>';
    h += '<div class="fhl-grade">' + grade + '</div>';
    h += '<div class="fhl-bar" style="justify-content:center"><span>得分 <b>' + score() + '</b></span>' +
      '<span>答对 <b>' + st.ok + '</b>/' + st.qs.length + '</span>' +
      '<span>最长连对 <b>' + st.best + '</b></span><span>用时 <b>' + secs + '</b> 秒</span></div>';
    h += '<p class="fhl-sub" style="margin-top:14px">本局出现的含令字诗句（可背下来，下局更稳）：</p>';
    h += '<ul class="fhl-review">';
    st.log.forEach(function (x) {
      h += '<li><span class="w">' + x.ch + '</span>　' + x.line +
        '　<span class="s">——' + x.src + (x.ok ? '' : '（漏选）') + '</span></li>';
    });
    h += '</ul>';
    h += '<div class="fhl-foot"><button class="fhl-btn" id="fhl-again">再来一局</button>' +
      '<button class="fhl-btn ghost" id="fhl-quit">关闭</button></div>';
    box.innerHTML = h;
    box.querySelector('.fhl-close').onclick = close;
    box.querySelector('#fhl-again').onclick = start;
    box.querySelector('#fhl-quit').onclick = close;
  }

  /* ---------- 入口 ---------- */
  function open() {
    ensure(function (err) {
      if (err || !data) {
        el.mask.classList.add('show');
        var b = renderShell();
        b.innerHTML = '<h2>飞花令</h2><p class="fhl-sub">数据加载失败：' +
          '请确认 <code>data/feihualing.json</code> 存在，且通过 http 服务打开本页' +
          '（不能以 file:// 直接双击打开）。</p>' +
          '<div class="fhl-foot"><button class="fhl-btn ghost" id="fhl-x">关闭</button></div>';
        b.querySelector('#fhl-x').onclick = close;
        return;
      }
      el.mask.classList.add('show');
      refreshMeta();
      renderStart();
    });
  }

  /* ---------- 游戏页入口卡片 ---------- */
  var metaEl = null;

  function refreshMeta() {
    if (!metaEl || !data || !data.meta) return;
    var m = data.meta;
    var wan = function (n) { return (n / 10000).toFixed(2) + ' 万'; };
    metaEl.textContent = '语料 ' + wan(m.poems) + ' 首 / ' + wan(m.segments) + ' 句 · ' + m.chars + ' 个令字';
  }

  function makeCard() {
    var d = document.createElement('div');
    d.className = 'game-card fhl';
    d.innerHTML =
      '<div class="ico">🎋</div>' +
      '<h3>飞花令</h3>' +
      '<p>系统给出一个「令字」，从四句诗中选出真正含该字的那一句。共 ' + PER_ROUND +
      ' 题，答对 10 分、连对额外加分；结束时有本局诗句回顾，可背下来。</p>' +
      '<div class="meta">语料：全宋诗 · 宋词 · 元曲 · 诗经 · 楚辞 · 曹操 · 纳兰性德</div>' +
      '<button class="go">开始飞花令 →</button>';
    d.querySelector('.go').onclick = open;
    metaEl = d.querySelector('.meta');
    return d;
  }

  function mount() {
    injectCSS();
    var mask = document.createElement('div');
    mask.className = 'fhl-mask';
    mask.addEventListener('click', function (e) { if (e.target === mask) close(); });
    document.body.appendChild(mask);
    el.mask = mask;

    var host = document.getElementById('gameCards');
    if (host) { host.appendChild(makeCard()); return; }

    // 兜底：无游戏页时仍以按钮形式挂在筛选栏后
    var row = document.createElement('div');
    row.className = 'filters';
    row.id = 'fhl-game-row';
    var btn = document.createElement('button');
    btn.className = 'filter-btn fhl-entry';
    btn.textContent = '🎋 飞花令';
    btn.title = '以「令字」找诗句的小游戏';
    btn.onclick = open;
    row.appendChild(btn);
    var sf = document.getElementById('strokeFilters');
    if (sf && sf.parentNode) sf.parentNode.insertBefore(row, sf.nextSibling);
    else document.body.appendChild(row);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();

  // 测试钩子（仅在页面显式设置 window.__FHL_TEST__ 时暴露核心逻辑，正常使用不受影响）
  if (typeof window !== 'undefined' && window.__FHL_TEST__) {
    window.__FHL__ = { ensure: ensure, buildQuestions: buildQuestions, setData: function (d) { data = d; } };
  }
})();
