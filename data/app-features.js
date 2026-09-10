// 说文解字 App · Sprint 4 P2 留存/传播增强（外部模块）
// 由 build_web.py 在 cultural-ui.js 之后、内联脚本之前加载。
// 依赖内联脚本全局：CHARS / showDetail / render / closeDetail / glyphToDataURL / CDS_READER / __CDS
// 依赖 cultural-ui.js 全局：CULTURAL_DB

// ---- 注入分享卡 / 测验 样式 ----
(function () {
  var css = "" +
    ".bopo{font-size:12px;color:var(--text3);margin-left:3px;letter-spacing:1px}" +
    ".share-modal{position:fixed;inset:0;background:rgba(0,0,0,.72);display:none;align-items:center;justify-content:center;z-index:60}" +
    ".share-modal.show{display:flex}.share-box{background:#16161a;border:1px solid var(--border);border-radius:14px;padding:16px}" +
    ".share-canvas{display:block;border-radius:8px;max-width:88vw;height:auto;background:#0f0f12}" +
    ".share-actions{display:flex;gap:10px;justify-content:center;margin-top:12px}" +
    ".share-actions button{background:var(--card);border:1px solid var(--border);color:var(--text);border-radius:8px;padding:8px 16px;cursor:pointer}" +
    ".share-actions button:hover{border-color:var(--accent);color:var(--accent)}" +
    ".share-btn{margin-left:8px}" +
    ".quiz-modal{position:fixed;inset:0;background:rgba(0,0,0,.72);display:none;align-items:center;justify-content:center;z-index:60}" +
    ".quiz-modal.show{display:flex}.quiz-box{background:#16161a;border:1px solid var(--border);border-radius:14px;padding:20px;width:420px;max-width:92vw}" +
    ".quiz-q{font-size:18px;margin-bottom:4px;color:var(--text)}" +
    ".quiz-char{font-size:64px;text-align:center;margin:10px 0;color:var(--text);cursor:pointer}" +
    ".quiz-opt{display:block;width:100%;text-align:left;background:var(--card);border:1px solid var(--border);color:var(--text);border-radius:8px;padding:10px 14px;margin:8px 0;cursor:pointer;font-size:15px}" +
    ".quiz-opt:hover{border-color:var(--accent)}" +
    ".quiz-opt.correct{background:#1f3d2b;border-color:#3fbf6f;color:#bff5d0}" +
    ".quiz-opt.wrong{background:#3d1f1f;border-color:#bf3f3f;color:#f5bfbf}" +
    ".quiz-meta{color:var(--text3);font-size:13px;margin-top:10px;text-align:center}";
  var st = document.createElement('style');
  st.textContent = css;
  document.head.appendChild(st);
})();

var favSet = loadFav();
var showFavOnly = false;
var currentId = null;
var currentChar = null;
var dailyChar = null;

function loadFav() {
  try { return new Set(JSON.parse(localStorage.getItem('swjz_fav') || '[]')); }
  catch (e) { return new Set(); }
}
function saveFav() {
  try { localStorage.setItem('swjz_fav', JSON.stringify([...favSet])); } catch (e) {}
}
function toggleFav(ch) {
  if (favSet.has(ch)) favSet.delete(ch); else favSet.add(ch);
  saveFav();
}
// 收藏夹筛选：包裹内联 filterChars 的结果
function applyFavFilter(list) {
  if (!showFavOnly) return list;
  return list.filter(function (c) { return favSet.has(c.char); });
}
// 字符卡片（含收藏星标 + 每日一字高亮）
function charCardHTML(c) {
  var fav = favSet.has(c.char) ? "<span class='fav-dot'>★</span>" : "";
  var daily = (c.char === dailyChar) ? " daily-card" : "";
  return "<div class='char-card" + daily + "' onclick='showDetail(" + c.id + ")'>" + fav + c.char +
         "<div class='pinyin'>" + c.pinyin + " <span class='bopo'>" + (typeof pinyinToBopomofo==='function'?pinyinToBopomofo(c.pinyin):'') + "</span></div></div>";
}
// 详情头部（关闭按钮 + 收藏按钮 + 分享卡按钮）
function detailHeaderHTML(c) {
  var label = favSet.has(c.char) ? "★ 已收藏" : "☆ 收藏";
  return "<button class='detail-close' onclick='closeDetail()'>&times;</button>" +
         "<button class='fav-btn' onclick='toggleFavBtn()'>" + label + "</button>" +
         "<button class='fav-btn share-btn' onclick='openShareCard()'>分享卡</button>";
}
function toggleFavBtn() {
  if (!currentChar) return;
  toggleFav(currentChar);
  render();
  if (currentId !== null) showDetail(currentId);
}
function toggleFavOnly() {
  showFavOnly = !showFavOnly;
  var b = document.getElementById('favToggle');
  if (b) b.classList.toggle('active', showFavOnly);
  render();
}
// 每日一字：按年内第几天确定性选取，文化内容加载后自动刷新文案
function renderDaily() {
  var now = new Date();
  var start = new Date(now.getFullYear(), 0, 0);
  var day = Math.floor((now - start) / 86400000);
  var c = CHARS[day % CHARS.length];
  if (!c) return;
  dailyChar = c.char;
  var one = (CULTURAL_DB && CULTURAL_DB[c.char] && CULTURAL_DB[c.char].story)
            ? CULTURAL_DB[c.char].story
            : (c.original || '');
  var banner = document.getElementById('dailyBanner');
  if (!banner) return;
  banner.innerHTML =
    "<span class='daily-label'>每日一字</span>" +
    "<span class='daily-char' onclick='showDetail(" + c.id + ")'>" + c.char + "</span>" +
    "<span class='daily-py'>" + c.pinyin + " <span class='bopo'>" + (typeof pinyinToBopomofo==='function'?pinyinToBopomofo(c.pinyin):'') + "</span></span>" +
    "<span class='daily-desc'>" + (one || '') + "</span>";
  render();
}

// ---- 单字分享卡（canvas 渲染 + 下载 PNG） ----
function getGlyphURL(c) {
  if (!CDS_READER || !CDS_READER.glyphsForCharacter) return null;
  var base = (c.trad && c.trad !== c.char) ? c.trad : c.char;
  var glyphs = CDS_READER.glyphsForCharacter(base);
  if ((!glyphs || !glyphs.length) && c.char) glyphs = CDS_READER.glyphsForCharacter(c.char);
  if (!glyphs || !glyphs.length) return null;
  var list = glyphs.filter(function (g) { return g.script === 'glyphwiki'; });
  if (!list.length) return null;
  var raw = CDS_READER.getRaw(list[0].key);
  if (!raw) return null;
  return (typeof glyphToDataURL === 'function') ? glyphToDataURL(raw) : null;
}
function wrapText(ctx, text, x, y, maxW, lh) {
  if (!text) return;
  var line = ''; var yy = y;
  for (var i = 0; i < text.length; i++) {
    var test = line + text[i];
    if (ctx.measureText(test).width > maxW && line) { ctx.fillText(line, x, yy); line = text[i]; yy += lh; }
    else line = test;
  }
  if (line) ctx.fillText(line, x, yy);
}
function drawShareCard(c, story) {
  var canvas = document.getElementById('shareCanvas');
  var W = 600, H = 760;
  canvas.width = W; canvas.height = H;
  var ctx = canvas.getContext('2d');
  ctx.fillStyle = '#0f0f12'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#1c1c22'; ctx.fillRect(24, 24, W - 48, H - 48);
  ctx.fillStyle = '#e8c87a'; ctx.font = 'bold 26px serif'; ctx.textAlign = 'center';
  ctx.fillText('说 文 解 字', W / 2, 72);
  var drawRest = function () {
    ctx.fillStyle = '#f0f0f0'; ctx.font = 'bold 150px "KaiTi","STKaiti",serif';
    ctx.fillText(c.char, W / 2, 320);
    ctx.fillStyle = '#c8c8c8'; ctx.font = '22px serif';
    ctx.fillText(c.pinyin + '  ·  ' + c.liushu, W / 2, 368);
    ctx.fillStyle = '#d8d8d8'; ctx.font = '18px serif'; ctx.textAlign = 'left';
    wrapText(ctx, story || '', 60, 430, W - 120, 30);
    ctx.fillStyle = '#888'; ctx.font = '15px serif'; ctx.textAlign = 'center';
    ctx.fillText('字源：GlyphWiki CC BY-SA 2.1 JP ｜ 说文解字 App', W / 2, H - 50);
  };
  var url = getGlyphURL(c);
  if (url) {
    var img = new Image();
    img.onload = function () {
      var size = 200;
      ctx.drawImage(img, W / 2 - size / 2, 110, size, size);
      drawRest();
    };
    img.onerror = drawRest;
    img.src = url;
  } else { drawRest(); }
}
function openShareCard() {
  if (currentId === null) return;
  var c = CHARS.find(function (x) { return x.id === currentId; });
  if (!c) return;
  var story = (CULTURAL_DB && CULTURAL_DB[c.char] && CULTURAL_DB[c.char].story)
              ? CULTURAL_DB[c.char].story : (c.original || '');
  var modal = document.getElementById('shareModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'shareModal';
    modal.className = 'share-modal';
    modal.innerHTML = "<div class='share-box'><canvas id='shareCanvas' class='share-canvas'></canvas>" +
                      "<div class='share-actions'><button onclick='downloadShareCard()'>下载图片</button>" +
                      "<button onclick='closeShareCard()'>关闭</button></div></div>";
    document.body.appendChild(modal);
    modal.addEventListener('click', function (e) { if (e.target === modal) closeShareCard(); });
  }
  modal.classList.add('show');
  drawShareCard(c, story);
}
function downloadShareCard() {
  var canvas = document.getElementById('shareCanvas');
  if (!canvas) return;
  var a = document.createElement('a');
  a.download = '说文字_' + (currentChar || '字') + '.png';
  a.href = canvas.toDataURL('image/png');
  a.click();
}
function closeShareCard() {
  var m = document.getElementById('shareModal');
  if (m) m.classList.remove('show');
}

// ---- 每日测验（随机 5 题，拼音/六书/部首） ----
function randInt(n) { return Math.floor(Math.random() * n); }
function shuffle(a) { for (var i = a.length - 1; i > 0; i--) { var j = randInt(i + 1); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
function sample(arr, k) { var c = arr.slice(), r = []; while (r.length < k && c.length) r.push(c.splice(randInt(c.length), 1)[0]); return r; }
var quizState = null;
function buildQuestion(c) {
  var type = randInt(3);
  if (type === 0) {
    var opts = sample(CHARS.filter(function (x) { return x.pinyin && x.pinyin !== c.pinyin; }), 3).map(function (x) { return x.pinyin; });
    opts.push(c.pinyin); shuffle(opts);
    return { char: c.char, id: c.id, q: '「' + c.char + '」的拼音是？', opts: opts, ans: c.pinyin };
  } else if (type === 1) {
    var ls = ['象形', '指事', '会意', '形声']; var lo = ls.slice(); shuffle(lo);
    return { char: c.char, id: c.id, q: '「' + c.char + '」属于哪种六书？', opts: lo, ans: c.liushu };
  }
  var ro = sample(CHARS.filter(function (x) { return x.radical && x.radical !== c.radical; }), 3).map(function (x) { return x.radical; });
  ro.push(c.radical); shuffle(ro);
  return { char: c.char, id: c.id, q: '「' + c.char + '」的部首是？', opts: ro, ans: c.radical };
}
function getQuizModal() {
  var m = document.getElementById('quizModal');
  if (!m) {
    m = document.createElement('div');
    m.id = 'quizModal';
    m.className = 'quiz-modal';
    m.innerHTML = "<div class='quiz-box'><div id='quizBody'></div><div class='quiz-meta'><button class='quiz-opt' style='width:auto;display:inline-block' onclick='closeQuiz()'>关闭</button></div></div>";
    document.body.appendChild(m);
    m.addEventListener('click', function (e) { if (e.target === m) closeQuiz(); });
  }
  return m;
}
function openQuiz() {
  var pool = CHARS.filter(function (c) { return c.pinyin && c.liushu && c.radical; });
  if (pool.length < 5) return;
  var qs = sample(pool, 5).map(buildQuestion);
  quizState = { qs: qs, idx: 0, score: 0, answered: false };
  getQuizModal().classList.add('show');
  renderQuiz();
}
function renderQuiz() {
  if (!quizState) return;
  var body = document.getElementById('quizBody');
  if (quizState.idx >= quizState.qs.length) {
    var rate = Math.round(quizState.score / quizState.qs.length * 100);
    body.innerHTML = "<div class='quiz-q' style='text-align:center'>测验完成！</div>" +
      "<div class='quiz-char'>" + quizState.score + " / " + quizState.qs.length + "</div>" +
      "<div class='quiz-meta'>正确率 " + rate + "% ｜ <button class='quiz-opt' style='width:auto;display:inline-block' onclick='openQuiz()'>再来一次</button></div>";
    return;
  }
  var q = quizState.qs[quizState.idx];
  var html = "<div class='quiz-meta'>第 " + (quizState.idx + 1) + " / " + quizState.qs.length + " 题</div>" +
    "<div class='quiz-q'>" + q.q + "</div><div class='quiz-char' onclick='showDetail(" + q.id + ")'>" + q.char + "</div>";
  html += q.opts.map(function (o) {
    return "<button class='quiz-opt' onclick='answerQuiz(\"" + o.replace(/"/g, '') + "\")'>" + o + "</button>";
  }).join("");
  body.innerHTML = html;
}
function answerQuiz(choice) {
  if (!quizState || quizState.answered) return;
  var q = quizState.qs[quizState.idx];
  quizState.answered = true;
  if (choice === q.ans) quizState.score++;
  var opts = document.querySelectorAll('#quizBody .quiz-opt');
  // 标记正确/错误（按文本匹配）
  for (var i = 0; i < opts.length; i++) {
    var t = opts[i].textContent;
    if (t === q.ans) opts[i].classList.add('correct');
    else if (t === choice) opts[i].classList.add('wrong');
    opts[i].setAttribute('disabled', 'disabled');
  }
  setTimeout(function () { quizState.idx++; quizState.answered = false; renderQuiz(); }, 900);
}
function closeQuiz() {
  var m = document.getElementById('quizModal');
  if (m) m.classList.remove('show');
}

// ---- 顶部注入「测验」按钮 ----
(function () {
  function inject() {
    var sc = document.getElementById('sortControls');
    if (sc && !document.getElementById('quizBtn')) {
      var b = document.createElement('button');
      b.id = 'quizBtn'; b.className = 'filter-btn'; b.textContent = '测验';
      b.onclick = openQuiz;
      sc.appendChild(b);
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', inject);
  else inject();
})();

// ---- 笔顺 SVG 渲染（strokes.min.json 为 Hanzi Writer 闭合轮廓路径，y 轴向上需翻转）----
function renderStrokeSVG(char) {
  var data = (typeof STROKE_DB !== 'undefined' && STROKE_DB) ? STROKE_DB[char] : null;
  if (!data || !data.length) return '';
  var uid = 'st' + Math.random().toString(36).slice(2, 9);
  var inner = data.map(function (p, i) {
    var m = p.match(/M\s*([\d.]+)[\s,]+([\d.]+)/);
    var sx = m ? parseFloat(m[1]) : 512;
    var sy = m ? parseFloat(m[2]) : 512;
    var fy = 1024 - sy;
    var delay = ((i + 1) * 0.45).toFixed(2);
    // 翻转组放路径(属性transform)，动画只动 opacity/fill 不影响翻转
    return "<g class='stroke-step'>" +
             "<g transform='translate(0,1024) scale(1,-1)'>" +
               "<path class='stroke-fill' d='" + p + "' style='animation:strokePop .42s ease forwards " + delay + "s'/>" +
             "</g>" +
             "<g class='stroke-dot' style='animation:strokeFade .25s ease forwards " + delay + "s'>" +
               "<circle cx='" + sx + "' cy='" + fy + "' r='26' fill='#7c6ff0' stroke='#fff' stroke-width='3'/>" +
               "<text x='" + sx + "' y='" + (fy + 12) + "' font-size='34' fill='#fff' text-anchor='middle' dominant-baseline='middle' font-weight='bold'>" + (i + 1) + "</text>" +
             "</g>" +
           "</g>";
  }).join('');
  return "<div class='stroke-section' id='" + uid + "'><h4>笔顺</h4>" +
         "<svg class='stroke-svg' id='svg-" + uid + "' viewBox='0 0 1024 1024'>" + inner + "</svg>" +
         "<div class='stroke-controls'><button class='filter-btn' onclick='replayStroke(\"" + uid + "\")'>▶ 重播笔顺</button><span class='stroke-step-label' id='lab-" + uid + "'></span></div>" +
         "<i class='src-mini'>笔顺数据源：Hanzi Writer Data（MIT，公开笔顺轮廓）</i></div>";
}
function replayStroke(uid) {
  var svg = document.getElementById('svg-' + uid);
  var lab = document.getElementById('lab-' + uid);
  if (!svg) return;
  var clone = svg.cloneNode(true);
  clone.id = 'svg-' + uid;
  svg.parentNode.replaceChild(clone, svg);
  if (lab) lab.textContent = '';
  var paths = clone.querySelectorAll('.stroke-fill');
  var total = paths.length;
  if (!total) return;
  var start = null;
  function frame(t) {
    if (start === null) start = t;
    var el = (t - start) / 1000;
    var shown = 0;
    for (var i = 0; i < total; i++) {
      var d = parseFloat(paths[i].style.animationDelay || '0');
      if (el >= d) shown = i + 1;
    }
    if (lab) lab.textContent = (shown ? '第 ' + shown + ' / ' + total : '准备…') + ' 笔';
    if (shown < total) requestAnimationFrame(frame);
    else if (lab) lab.textContent = '共 ' + total + ' 笔';
  }
  requestAnimationFrame(frame);
}
