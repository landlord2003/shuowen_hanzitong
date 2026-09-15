/* 三页导航 —— 说文解字·汉字通
 * 把原本的长滚动单页拆成：① 认识（intro）② 字库（main）③ 游戏（game）
 * 纯前端 tab 切换：只切 .page 的显示，DOM 全部保留（字库渲染逻辑不受影响）
 */
(function () {
  'use strict';
  var PAGES = ['intro', 'main', 'game'];
  var cur = 'intro';

  function switchPage(id, silent) {
    if (PAGES.indexOf(id) < 0) return;
    var sec = document.getElementById('page-' + id);
    if (!sec) return;
    cur = id;
    Array.prototype.forEach.call(document.querySelectorAll('.page'), function (s) {
      s.classList.remove('active');
    });
    sec.classList.add('active');
    Array.prototype.forEach.call(document.querySelectorAll('.page-tab'), function (b) {
      var on = b.getAttribute('data-page') === id;
      if (on) b.classList.add('active'); else b.classList.remove('active');
    });
    try { window.scrollTo(0, 0); } catch (e) { }
    if (!silent) { try { history.replaceState(null, '', '#' + id); } catch (e) { } }
    // 字库页首次进入时重绘一次，确保隐藏期间的尺寸计算正确（网格为纯 CSS，仅作兜底）
    if (id === 'main' && typeof window.render === 'function') {
      try { window.render(); } catch (e) { }
    }
  }

  function mount() {
    var nav = document.getElementById('pageNav');
    if (nav) {
      nav.addEventListener('click', function (e) {
        var t = e.target;
        while (t && t !== nav && !t.classList.contains('page-tab')) t = t.parentNode;
        if (t && t !== nav) switchPage(t.getAttribute('data-page'));
      });
    }
    var h = (location.hash || '').replace(/^#/, '');
    if (PAGES.indexOf(h) >= 0) switchPage(h, true);
  }

  window.switchPage = switchPage;

  /* 导航骨架（#pageNav / .page）在静态 HTML 里已就绪，且位于本脚本之前，
     因此无需等 DOMContentLoaded——紧随其后的 14MB 内联 DATA 脚本会把 DCL 拖后数秒，
     那段时间标签点不动、#main 深链也不切页。
     骨架若不在（脚本被挪到 <head> 等），才退回 DOMContentLoaded。 */
  if (document.getElementById('pageNav') || document.readyState !== 'loading') mount();
  else document.addEventListener('DOMContentLoaded', mount);
})();
