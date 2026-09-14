// 说文解字 App · Sprint 2 文化与美学增强（外部 UI 模块）
// 本文件为全局脚本，由 build_web.py 在 dataset-reader.js 之后、内联脚本之前加载。

// 文化内容数据库（字源故事 / 成语 / 诗词），由 tools/gen_cultural.py 经本地 Ollama 生成。
var CULTURAL_DB = null;
(function () {
  fetch("data/cultural.json?v=20260911i")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      CULTURAL_DB = d;
      if (typeof renderDaily === 'function') renderDaily();
      // 若用户已在详情页（cultural.json 异步加载慢于首次点击），加载完成后重渲染当前字，避免文化区块空窗
      if (window.__currentCharId != null && typeof showDetail === 'function') {
        try { showDetail(window.__currentCharId); } catch (e) {}
      }
    })
    .catch(function () {});
})();

// 演变阶段解说文字（事实性公版知识，非 AI 生成）。
var ERA_DESC = {
  "字源": "取自 GlyphWiki 汉字溯源图层，黑底白描拓片风，呈现该字最古老的构形依据。",
  "甲骨文": "商代契刻于龟甲兽骨的占卜文字，笔画瘦硬方折、象形性最强。",
  "金文": "商周铸刻于青铜器钟鼎的铭文，线条圆润肥厚、渐趋规整。",
  "简牍帛书": "战国至汉晋书写于竹简木牍与丝帛的手写体，处隶变之中，率意自然。",
  "篆文": "秦代小篆，线条匀圆等长、结构对称，为第一次文字统一的标准体。",
  "隶书": "秦汉隶变之体，化圆为方、波磔分明，奠定方块汉字骨架。",
  "楷书": "汉末成熟的现行正体，横平竖直、端正方整，沿用至今。"
};

var LBL_STORY = "字源小故事";
var LBL_IDIOM = "相关成语";
var LBL_POEM = "诗词引用";

// 渲染单字文化内容区块（story / idioms / poems）。
function culturalHTML(d) {
  var h = "";
  if (d && d.story) {
    h += "<div class='story-box'><div class='label'>" + LBL_STORY + "</div><p>" + d.story + "</p></div>";
  }
  if (d && d.idioms && d.idioms.length) {
    h += "<div class='label'>" + LBL_IDIOM + "</div><div class='idiom-list'>";
    h += d.idioms.map(function (it) {
      return "<span class='idiom'>" + it.w + "<i>" + (it.meaning || "") + "</i></span>";
    }).join("");
    h += "</div>";
  }
  if (d && d.poems && d.poems.length) {
    h += "<div class='label'>" + LBL_POEM + "</div><div class='poem-list'>";
    h += d.poems.map(function (p) {
      var verified = p.source && p.source.indexOf('待考') < 0 && p.source.indexOf('示例') < 0 && p.source.indexOf('未知') < 0;
      var tag = verified ? "✓ " + p.source : (p.source && p.source.indexOf('待考') >= 0 ? "示例·出处待核" : (p.source || "示例·出处待核"));
      return "<div class='poem'><span>" + p.line + "</span><i>" + tag + "</i></div>";
    }).join("");
    h += "</div>";
  }
  return h;
}
