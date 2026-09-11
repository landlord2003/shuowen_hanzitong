"""One-shot build: simplest possible, all Chinese pre-escaped, zero template tricks"""
import json

with open('data/characters.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Pure ASCII JSON
json_ascii = json.dumps(data, ensure_ascii=True)

# 隶书逐字来源映射（char -> linhai / qingliu / none），供详情页来源徽章标注
try:
    with open('data/clerical_source.json', 'r', encoding='utf-8') as _csf:
        src_map = json.load(_csf)
except Exception:
    src_map = {}

# 字体 cmap 覆盖集（由 extract_cmap.py 离线提取，落在 data/font_glyphs.json）
# 用途：字体兜底时判定「该字体是否真含此字」。浏览器 document.fonts.check 仅检测字体是否
# 加载，不检测字形覆盖——字体缺字时它会返回 true，导致把缺字渲染成楷体回退字（误导）。
# 故改用此集合做成员判定：字体真不含该字则保持 pending（显示「根据汉典查询，此字目前未发现该阶段字形」）。
try:
    with open('data/font_glyphs.json', 'r', encoding='utf-8') as _fgf:
        _font_glyphs = json.load(_fgf)
except Exception:
    _font_glyphs = {}

# 书法欣赏字体 cmap 覆盖集（由 tools/extract_calli_cmap.py 离线提取，落在 data/calli_glyphs.json）
# 用途同 STAGE_FONT_GLYPHS：门控缺字，避免书法字体缺字时回退成系统宋体（误导）。
try:
    with open('data/calli_glyphs.json', 'r', encoding='utf-8') as _cgf:
        _calli_glyphs = json.load(_cgf)
except Exception:
    _calli_glyphs = {}

# Helper: escape a Chinese string to \uXXXX
def u(s):
    # Return BARE \uXXXX escapes for Chinese (no quote wrapper). Call sites supply
    # their own JS string delimiters (single or double quotes) around u(...).
    # e.g. u("笔顺") -> "\u7b14\u987a"
    r = []
    for ch in s:
        cp = ord(ch)
        if cp > 127:
            r.append('\\u' + format(cp, '04x'))
        else:
            r.append(ch)
    return ''.join(r)

# Build the ENTIRE HTML as one big string with \uXXXX for ALL Chinese in JS
lines = []
lines.append('<!DOCTYPE html>')
lines.append('<html lang="zh-CN">')
lines.append('<head><meta charset="UTF-8"><title>说文解字·汉字通</title>')
lines.append('<style>')
lines.append(':root{--bg:#1a1a2e;--card:#1e2a4a;--text:#e0e0e0;--text2:#999;--text3:#666;--accent:#534ab7;--accent2:rgba(83,74,183,.2);--border:#2a2a4a;--radius:8px}')
lines.append('*{box-sizing:border-box}')
lines.append('body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--text);padding:16px;margin:0;max-width:1200px;margin:0 auto}')
lines.append('h1{font-size:22px;margin:0 0 4px}.sub{font-size:13px;color:var(--text3);margin:0 0 16px}')
lines.append('input{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--text);font-size:15px;margin-bottom:12px;outline:none}')
lines.append('input:focus{border-color:var(--accent)}')
lines.append('.filters{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}')
lines.append('.filter-btn{padding:4px 12px;border:1px solid var(--border);border-radius:4px;background:transparent;color:var(--text2);cursor:pointer;font-size:12px;transition:all .15s}')
lines.append('.filter-btn.active,.filter-btn:hover{background:var(--accent2);border-color:var(--accent);color:#fff}')
lines.append('.stats{color:var(--text3);font-size:13px;margin-bottom:10px}')
lines.append('.char-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(80px,1fr));gap:8px;margin-bottom:20px}')
lines.append('.char-card{background:var(--card);border-radius:var(--radius);padding:12px 8px 6px;text-align:center;cursor:pointer;position:relative;transition:transform .15s;font-size:28px;color:var(--text);overflow:hidden}')
lines.append('.char-card:hover{transform:translateY(-2px)}')
lines.append('.char-card .pinyin{font-size:11px;color:var(--text3);margin-top:2px}')
lines.append('.no-results{text-align:center;padding:40px;color:var(--text3);grid-column:1/-1}')
lines.append('.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:100;overflow-y:auto;padding:20px}')
lines.append('.overlay.show{display:block}')
lines.append('.detail-panel{background:var(--bg);border:1px solid var(--border);border-radius:12px;max-width:1180px;margin:30px auto;padding:26px;position:relative}')
lines.append('.detail-close{position:absolute;top:12px;right:16px;background:none;border:none;color:var(--text2);font-size:24px;cursor:pointer}')
lines.append('.detail-char{font-size:64px;text-align:center;margin:8px 0}')
lines.append('.detail-pinyin{text-align:left;font-size:18px;color:var(--text2);margin-bottom:12px}')
lines.append('.detail-info{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;font-size:13px}')
lines.append('.detail-info div{color:var(--text3);background:var(--card);border:1px solid var(--border);border-radius:8px;padding:9px 11px;display:flex;flex-direction:column;gap:3px;line-height:1.3}.detail-info span{color:var(--text);margin-left:0;font-size:16px;font-weight:600}.detail-info i.src-mini{margin:0;padding:0;border:none;background:transparent;color:var(--text3);font-size:10px}')
lines.append('.detail-section{margin:16px 0}')
lines.append('.detail-section h4{font-size:14px;color:var(--accent);margin:0 0 6px;border-bottom:1px solid var(--border);padding-bottom:4px}')
lines.append('.detail-section p{font-size:14px;line-height:1.7;color:var(--text2);margin:0}')
lines.append('.detail-hero{display:flex;gap:32px;align-items:flex-start;flex-wrap:wrap;justify-content:center;margin:6px 0 4px}')
lines.append('.detail-hero .hero-left{flex:0 0 auto}')
lines.append('.detail-hero .hero-right{flex:1 1 320px;max-width:460px;min-width:280px}')
lines.append('.detail-cols{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start;margin:16px 0}')
lines.append('@media (max-width:640px){.detail-hero{flex-direction:column}.detail-cols{grid-template-columns:1fr}.evo-timeline{flex-wrap:wrap;overflow-x:visible}}')
lines.append('.evo-timeline{display:flex;align-items:flex-start;gap:8px;flex-wrap:nowrap;overflow-x:auto;margin:8px 0;justify-content:center}')
lines.append('.evo-step{text-align:center;flex:1 1 0;min-width:0;padding:8px 4px;border-radius:8px;background:var(--card);border:1px solid var(--border)}')
lines.append('.calli-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:10px;margin:8px 0}')
lines.append('.calli-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 6px;text-align:center}')
lines.append('.calli-char{font-size:48px;line-height:1.1;color:var(--text)}')
lines.append('.calli-name{font-size:12px;color:var(--text3);margin-top:6px}')
lines.append('.evo-step .era-name{font-size:11px;color:var(--text2);margin-bottom:4px}')
lines.append('.evo-step .era-img{width:100%;max-width:72px;height:auto;aspect-ratio:1/1;object-fit:contain;display:block;margin:0 auto;background:#0a0a0a;border:1px solid #555;border-radius:4px}')
lines.append('.evo-step.pending{border-style:dashed;opacity:.92}')
lines.append('.evo-step.pending .era-pending{font-size:11px;color:var(--text3);padding:18px 0;letter-spacing:2px}')
lines.append('.evo-step.no-ancient{border-style:solid;opacity:.55;border-color:var(--border)}')
lines.append('.evo-step .era-no-ancient{font-size:11px;color:var(--text3);padding:16px 0;letter-spacing:1px;line-height:1.3}')
lines.append('.era-desc{font-size:10px;color:var(--text3);line-height:1.45;margin:4px 2px 0;text-align:center;max-width:88px}')
lines.append('.era-desc.pending-desc{opacity:.7}')
lines.append('.cultural-section{background:linear-gradient(180deg,rgba(83,74,183,.10),rgba(83,74,183,.03));border:1px solid var(--accent);border-radius:10px;padding:14px 16px;margin:14px 0}')
lines.append('.cultural-section h4{color:var(--accent)}')
lines.append('.cultural-section .story-box{margin-bottom:10px}')
lines.append('.cultural-section .label{font-size:12px;color:var(--text2);font-weight:600;margin:10px 0 4px}')
lines.append('.cultural-section .story-box p{margin:0;line-height:1.7;font-size:14px;color:var(--text)}')
lines.append('.cultural-section .idiom-list{display:flex;flex-wrap:wrap;gap:6px}')
lines.append('.cultural-section .idiom{display:inline-flex;flex-direction:column;background:var(--card);border:1px solid var(--border);border-radius:6px;padding:4px 9px;font-size:13px;color:var(--text)}')
lines.append('.cultural-section .idiom i{font-style:normal;font-size:11px;color:var(--text3);margin-top:2px}')
lines.append('.cultural-section .poem-list{display:flex;flex-direction:column;gap:6px}')
lines.append('.cultural-section .poem{background:var(--card);border-left:3px solid var(--accent);border-radius:4px;padding:6px 10px}')
lines.append('.cultural-section .poem span{font-size:14px;line-height:1.55;color:var(--text)}')
lines.append('.cultural-section .poem i{font-style:normal;font-size:11px;color:var(--text3);margin-top:3px;display:block}')
lines.append('.evo-arrow{color:var(--accent);font-size:14px;padding-top:24px}')
lines.append('.meaning-compare{display:grid;grid-template-columns:1fr 1fr;gap:12px}')
lines.append('.meaning-box{background:var(--card);border-radius:var(--radius);padding:12px}')
lines.append('.meaning-box .label{font-size:12px;color:var(--accent);margin-bottom:4px}')
lines.append('.meaning-box .content{font-size:14px;color:var(--text);line-height:1.6}')
lines.append('.oracle-note{background:rgba(180,140,90,.1);border-left:3px solid rgba(180,140,90,.5);padding:8px 12px;margin:8px 0;font-size:13px;color:var(--text2);line-height:1.6;border-radius:0 6px 6px 0}')
lines.append('.src-mini{display:inline-block;font-style:normal;font-size:10px;color:var(--text3);border:1px solid var(--border);border-radius:3px;padding:1px 6px;margin:2px 0 2px 6px;vertical-align:middle;white-space:normal;overflow-wrap:anywhere;word-break:break-all;max-width:100%}')
lines.append('.clerical-badge{display:inline-block;font-size:10px;font-weight:500;border-radius:3px;padding:1px 6px;margin:2px 4px 0 0;vertical-align:middle}')
lines.append('.clerical-badge.linhai{color:#1a7f4e;background:rgba(26,127,78,.12);border:1px solid rgba(26,127,78,.4)}')
lines.append('.clerical-badge.qingliu{color:#1a6fd6;background:rgba(26,111,214,.12);border:1px solid rgba(26,111,214,.4)}')
lines.append('.clerical-badge.none{color:var(--text3);background:var(--card);border:1px solid var(--border)}')
lines.append('.src-line{font-size:13px;color:var(--text2);margin:6px 0;line-height:1.7}')
lines.append('.src-line b{color:var(--text)}')
lines.append('.trace-note{background:rgba(255,180,0,.08);border-left:3px solid #ffb400;padding:8px 12px;font-size:13px;color:var(--text2);border-radius:0 6px 6px 0;margin:6px 0;line-height:1.7}')
lines.append('.dispute-badge{font-style:normal;font-size:10px;color:#ffd27f;border:1px solid #6b5a2a;background:rgba(255,180,0,.12);border-radius:3px;padding:1px 6px;margin-left:6px;vertical-align:middle;white-space:nowrap;cursor:help}')
lines.append('.dispute-note{background:rgba(255,180,0,.08);border-left:3px solid #ffb400;padding:6px 12px;font-size:12px;color:var(--text2);border-radius:0 6px 6px 0;margin:6px 0;line-height:1.6}')
lines.append('.evo-step.font-fill{border-color:#3a5a8a}')
lines.append('.era-font{font-size:44px;color:var(--text);line-height:1.5;padding:6px 0;display:block}')
lines.append('.duan-box{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:8px 12px;margin:6px 0}')
lines.append('.duan-box summary{cursor:pointer;font-size:13px;color:var(--accent);user-select:none}')
lines.append('.duan-box p{font-size:13px;color:var(--text2);line-height:1.8;margin:8px 0 0;max-height:240px;overflow-y:auto}')
lines.append('.ext-link{text-align:center;margin:16px 0}.ext-link a{color:var(--accent);text-decoration:none;font-size:13px}')
lines.append('.footer{text-align:center;color:var(--text3);font-size:12px;padding:20px}')
lines.append('.cov-table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px}')
lines.append('.cov-table th,.cov-table td{border:1px solid var(--border);padding:6px 10px;text-align:center}')
lines.append('.cov-table th{background:var(--bg2);color:var(--text)}')
lines.append('.cov-table td:first-child{text-align:left;color:var(--text)}')
lines.append('.cov-note p{font-size:12px;color:var(--text3);line-height:1.7;margin:8px 0 0}')
lines.append('.src-legend{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 18px;margin:18px 0 0;font-size:13px;color:var(--text2)}')
lines.append('.src-legend h3{font-size:14px;color:var(--accent);margin:0 0 10px}')
lines.append('.src-legend ul{margin:0;padding-left:18px}')
lines.append('.src-legend li{margin:5px 0;line-height:1.7}')
lines.append('.src-legend b{color:var(--text)}')
lines.append('.src-legend .warn{color:#ffb400}')
lines.append('.info-panel{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:0 18px;margin:0 0 16px;font-size:13px;color:var(--text2)}')
lines.append('.info-panel summary{cursor:pointer;font-size:14px;font-weight:600;color:var(--accent);padding:14px 0;user-select:none}')
lines.append('.info-panel[open] summary{border-bottom:1px solid var(--border);margin-bottom:14px}')
lines.append('.info-panel .src-legend{border:none;padding:0 0 14px;margin:0;background:transparent}')
lines.append('.stroke-section{margin:6px 0 0}')
lines.append('.stroke-fallback{display:flex;flex-direction:column;align-items:center;gap:8px;padding:6px 0}')
lines.append('.stroke-fallback .fallback-char{font-size:150px;line-height:1.05;color:var(--text);font-family:"KaiTi","STKaiti","SimSun",serif}')
lines.append('.hw-target{display:flex;justify-content:center;align-items:center;min-height:220px;margin:4px 0}')
lines.append('.hw-target svg{display:block}')
lines.append('.stroke-svg{width:210px;height:210px;background:var(--card);border:1px solid var(--border);border-radius:8px;display:block;margin:6px auto}')
lines.append('.stroke-fill{fill:var(--text);stroke:var(--text);stroke-width:2;opacity:0}')
lines.append('@keyframes strokePop{0%{opacity:0;fill:var(--accent)}55%{opacity:1;fill:var(--accent)}100%{opacity:1;fill:var(--text)}}')
lines.append('.stroke-dot{opacity:0}')
lines.append('@keyframes strokeFade{0%{opacity:0}100%{opacity:1}}')
lines.append('.stroke-controls{text-align:center;margin:6px 0 2px}')
lines.append('.stroke-controls .filter-btn{font-size:12px;padding:4px 12px}')
lines.append('.stroke-step-label{font-size:12px;color:var(--text2);margin-left:10px}')
lines.append('</style></head><body>')
lines.append('<style>.daily-banner{display:flex;align-items:center;gap:14px;background:linear-gradient(135deg,var(--card),#1c1c22);border:1px solid var(--border);border-radius:12px;padding:14px 18px;margin-bottom:14px;flex-wrap:wrap}.daily-label{font-size:12px;font-weight:700;color:var(--accent);letter-spacing:2px;white-space:nowrap}.daily-char{font-size:42px;font-weight:700;line-height:1;cursor:pointer;color:var(--text)}.daily-char:hover{color:var(--accent)}.daily-py{font-size:15px;color:var(--text2)}.daily-desc{font-size:14px;color:var(--text2);flex:1;min-width:200px;line-height:1.6}.fav-btn{margin-left:auto;background:var(--card);border:1px solid var(--border);color:var(--text);border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer}.fav-btn:hover{border-color:var(--accent);color:var(--accent)}.char-card{position:relative}.fav-dot{position:absolute;top:4px;right:8px;color:#ffb300;font-size:14px}.daily-card{outline:2px solid var(--accent);outline-offset:-2px}.filter-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}</style>')

lines.append('<style>.welcome-modal{position:fixed;inset:0;background:rgba(0,0,0,.82);display:none;align-items:center;justify-content:center;z-index:80}.welcome-modal.show{display:flex}.welcome-box{background:#16161a;border:1px solid var(--border);border-radius:16px;padding:26px 30px;max-width:560px;width:92vw;box-shadow:0 20px 60px rgba(0,0,0,.5)}.welcome-box h2{margin:0 0 10px;color:var(--accent);font-size:22px}.welcome-box p{line-height:1.75;color:var(--text2);margin:8px 0;font-size:14px}.welcome-box ul{margin:10px 0;padding-left:20px;line-height:2;color:var(--text2);font-size:14px}.welcome-box .welcome-src{font-size:12px;color:var(--text3);border-top:1px solid var(--border);padding-top:12px;margin-top:14px}.welcome-btn{margin-top:14px;background:var(--accent);color:#fff;border:none;border-radius:8px;padding:10px 22px;font-size:15px;cursor:pointer;font-weight:600}.welcome-btn:hover{opacity:.9}.help-btn{margin-left:10px;background:var(--card);border:1px solid var(--border);color:var(--text);border-radius:50%;width:26px;height:26px;cursor:pointer;font-size:14px;vertical-align:middle}.help-btn:hover{border-color:var(--accent);color:var(--accent)}</style>')
lines.append('<div id="welcomeModal" class="welcome-modal"><div class="welcome-box"><h2>说文解字 · 汉字通</h2><p>本 App 收录 8105 个规范汉字，提供字源图、字形演变、六书、本义/今义、《说文》原文与字源故事。</p><ul><li>🔍 顶部搜索框：按拼音 / 部首 / 单字检索</li><li>📜 点任意字卡 → 查看「字形演变」逐阶段标注</li><li>🧱 古字形标注：<b>✓ 有字形</b>（直接显示）｜<b>— 汉典等字书暂未收录其古形</b>（后起字 / 形声 / 简化字等本无该阶段字形，或本库未收，<b>非「待补」</b>）｜<b>隶书</b>以字体替代（未收汉隶真迹）</li><li>📊 底部「古字形阶段覆盖统计」说明各书体收录比例</li></ul><p class="welcome-src">字源图 GlyphWiki（CC BY-SA 2.1 JP）｜篆书 崇羲篆体（CC-BY-ND-3.0-TW）｜甲骨/金文 cluesurf/mark（OFL）｜隶书 临海隶书＋青柳隶书（免费商用）</p><button class="welcome-btn" onclick="closeWelcome()">开始探索 →</button></div></div>')
lines.append('<h1>说文解字·汉字通</h1>')
lines.append('<p class="sub">8105字·字源溯源（100%，GlyphWiki CC BY-SA 2.1 JP）＋字形演变（甲骨758·金文1056·简帛612·大篆1362·小篆2848 字真迹已收；隶书以临海＋青柳隶书字体替代，未收汉隶真迹）｜缺失阶段＝据汉典等字书暂未收录此形（非「待补」）</p>')
lines.append('<input id="searchInput" placeholder="搜索：拼音(如 shuǐ)、部首(如 水)、字(如 海)；笔画筛选见下方按钮" autofocus>')
lines.append('<div id="dailyBanner" class="daily-banner"></div>')
lines.append('<div class="filters" id="liushuFilters">')
for ls in ['全部', '象形', '指事', '会意', '形声']:
    active = ' active' if ls == '全部' else ''
    lines.append('<button class="filter-btn' + active + '" data-ls="' + ls + '">' + ls + '</button>')
lines.append('</div>')
lines.append('<div class="filters" id="categoryFilters">')
for cat in ['全部', '自然', '人体', '动物', '植物', '器物', '社会', '抽象']:
    active = ' active' if cat == '全部' else ''
    lines.append('<button class="filter-btn' + active + '" data-cat="' + cat + '">' + cat + '</button>')
lines.append('</div>')
lines.append('<div class="filters" id="sortControls">')
lines.append('<span style="color:var(--text3);font-size:13px;margin-right:8px">排序</span>')
lines.append('<button class="filter-btn active" data-sort="default">默认</button>')
lines.append('<button class="filter-btn" data-sort="pinyin">拼音</button>')
lines.append('<button class="filter-btn" data-sort="stroke">笔画</button>')
lines.append('<button class="filter-btn" id="favToggle" onclick="toggleFavOnly()">★ 收藏夹</button>')
lines.append('</div>')
lines.append('<div class="filters" id="strokeFilters">')
for sf in ['全部', '1-5', '6-10', '11-15', '16+']:
    active = ' active' if sf == '全部' else ''
    lines.append('<button class="filter-btn' + active + '" data-stroke="' + sf + '">' + sf + '</button>')
lines.append('</div>')
lines.append('<div class="stats" id="stats"></div>')
lines.append('<details class="info-panel" open><summary>&#128218; 数据来源与说明（点击展开/收起）</summary>')
lines.append('<div class="src-legend"><h3>什么是「六书」？</h3><p style="margin:0 0 10px;line-height:1.7">「六书」是古人分析汉字造字与用字方法而归纳出的六种条例，由东汉许慎在《说文解字》中系统阐述。App 中的六书分类用于快速理解一个字的构形逻辑：</p><ul><li><b>象形</b>：描摹物体外形，如「日、月、山、水」</li><li><b>指事</b>：用抽象符号或在象形字上加指示符号表示抽象概念，如「上、下、本、末」</li><li><b>会意</b>：把两个或多个字组合起来表示新意，如「明（日月并照）、休（人倚木而息）」</li><li><b>形声</b>：由表示意义类别的「形旁」和表示读音的「声旁」组成，如「江（水形工声）、湖（水形胡声）」</li><li><b>转注</b>：部首相同、意义相通、可互相解释的字，如「考」与「老」</li><li><b>假借</b>：借用同音字表达新概念，如「令（本义发号，借为县令）、长（本义久远，借为长官）</li></ul><p style="margin:8px 0 0;font-size:12px;color:var(--text3)">注：本 App 将常见字归入象形、指事、会意、形声四类；转注、假借更多是用字法，未作为单字主分类。</p></div>')
lines.append('<div class="src-legend"><h3>数据来源与说明</h3><ul><li><b>说文原文 / 反切 / 段玉裁注 / 异体重文</b>：出自《说文解字》（东汉·许慎），含清代段玉裁注</li><li><b>后起字溯源</b>：出自《玉篇》（543年）、《广韵》（1008年）、《康熙字典》（1716年）。《康熙字典》为集大成字书，整合历代韵书反切与释义；《玉篇》《广韵》年代更早，可定位更早的字义</li><li><b class="warn">⚠️ 音译字提示</b>：部分字古字书释义与今义不同——如「啡」古为「唾声」非「咖啡」、「吨」古为「气相冲」非重量单位、「她」古为「姐」非第三人称。此类已在溯源中单独标注</li><li><b>字源图（单字最古老构形）</b>：取自 GlyphWiki 汉字溯源图层（CC BY-SA 2.1 JP，可商用，须署名 + 衍生同授权），已落地 8105 字，黑底白描拓片风</li><li><b>甲骨→金文→简牍帛书→大篆→小篆→隶书演变图</b>：字形取自 Wikimedia Commons 古文字形 SVG（公版，可自由商用），经本机换源管线栅格化为 160×160 拓片风灰度图；大篆（籀文）为新增独立书体；<b>未收录的字形阶段标注为「根据汉典查询，此字目前未发现该阶段字形」</b>——即该字为后起字 / 形声 / 简化字等，据汉典等字书暂未收录此形，<b>非「数据待补」</b>；隶书未收汉隶真迹，以临海＋青柳隶书字体替代</li><li><b>六书 / 本义 / 今义 / 演变</b>：AI 生成，待核验</li><li><b>五行属性</b>：民俗归类（字源五行法），非文字学客观属性；依「字义＞偏旁」判定并标注出处，约 44% 字（人体、动作、抽象、虚词等）无明确归属</li></ul></div>')
lines.append('<div class="src-legend cov-note"><h3>古字形阶段覆盖统计</h3>')
lines.append('<p style="margin:0 0 10px;line-height:1.7">下表对比「各古文字阶段历史上能写的字数（学界基准）」与「本产品在 8105 个规范汉字中实际收录展示的字数」：</p>')
lines.append('<table class="cov-table">')
lines.append('<tr><th>古文字阶段</th><th>历史可考总字（基准）</th><th>本产品覆盖（8105 内）</th><th>占历史总字</th><th>占常用字</th></tr>')
lines.append('<tr><td>甲骨文</td><td>约 4000+<br>（据《甲骨文编》等）</td><td>758 字<br>（真迹）</td><td>—</td><td>9.4%</td></tr>')
lines.append('<tr><td>金文</td><td>约 3500+<br>（据《金文编》等）</td><td>1056 字<br>（真迹）</td><td>—</td><td>13.0%</td></tr>')
lines.append('<tr><td>篆书</td><td>9353 字头<br>（《说文解字》小篆）</td><td>2903 字<br>（真迹：大篆1362＋小篆2848 去重）</td><td>—</td><td>35.8%</td></tr>')
lines.append('<tr><td>隶书</td><td>约 9353<br>（承篆，《说文》字头）</td><td>0 真迹 / 7351 字<br>（临海＋青柳隶书字体替代）</td><td>—</td><td>90.7%<br>（字体）</td></tr>')
lines.append('<tr><td>简牍帛书</td><td>无统一总表<br>（出土文献散见）</td><td>612 字<br>（真迹）</td><td>—</td><td>7.6%</td></tr>')
lines.append('</table>')
lines.append('<p>口径说明：①「历史可考总字」采用学界对该书体已发现/已释读单字的统计——甲骨文《甲骨文编》约 4000+ 字头、金文《金文编》约 3500+ 字头、篆书《说文解字》9353 字头、隶书承篆以《说文》为基准；②「本产品覆盖（真迹）」为本产品在 8105 常用字中<b>历史上确有该形、且已收录其真迹</b>的字数（甲骨/金文/简帛/大篆/小篆 真迹已基本完备）；③ 其余字<b>据汉典等字书暂未收录该阶段字形</b>（后起字/形声/简化字等后世造字），并非「数据待补」——详情页统一标注「根据汉典查询，此字目前未发现该阶段字形」；④ 隶书阶段<b>未收汉隶真迹</b>（0 真迹），由临海隶书（6722 字，82.9%）＋青柳隶书补缺（629 字）以字体替代呈现，达 7351 字=90.7%，详情页逐字标注字体来源；余约 9% 简体字无隶书字形回退楷体。</p>')
lines.append('</div>')
lines.append('</details>')
lines.append('<div class="char-grid" id="charGrid"></div>')
lines.append('<div class="footer">字源图：GlyphWiki（CC BY-SA 2.1 JP）｜篆书：崇羲篆体（CC-BY-ND-3.0-TW）｜甲骨/金文：cluesurf/mark（OFL）｜隶书：临海隶书＋青柳隶书（免费商用，猫啃网 maoken.com）｜简牍帛书：出土文献真迹612字｜说文解字·汉字通</div>')
lines.append('<div class="overlay" id="overlay"><div class="detail-panel" id="detail" onclick="event.stopPropagation()"></div></div>')

# Now the script tag - ALL Chinese pre-escaped
js_parts = []
js_parts.append('var DATA = ' + json_ascii + ';')
# 嵌入"仅字源、无真迹古文字段"缺字集，供演变行诚实标注（避免空白"待补全"误导）
try:
    with open('data/glyph_missing.json', encoding='utf-8') as _mf:
        _missing_chars = json.load(_mf).get('chars', [])
except Exception:
    _missing_chars = []
js_parts.append('var NO_ANCIENT_GLYPH = new Set(' + json.dumps(_missing_chars, ensure_ascii=True) + ');')
js_parts.append('var CHARS = DATA.characters;')
js_parts.append('var SRC_YP = "' + u('《玉篇》（543年）') + '";')
js_parts.append('var SRC_GY = "' + u('《广韵》（1008年）') + '";')
js_parts.append('var SRC_KX = "' + u('《康熙字典》（1716年）') + '";')
js_parts.append('var WUXING_LABEL = {"' + u('偏旁') + '": "' + u('出：偏旁部首') + '", "' + u('字义') + '": "' + u('出：字义·五行理论') + '"};')
js_parts.append('var CDS_READER = null;')
js_parts.append('(function(){')
js_parts.append('  if (!window.__CDS || !window.fzstd) return;')
js_parts.append('  fetch("data/dataset.bin?v=20260912d").then(function(r){ if(!r.ok) return null; return r.arrayBuffer(); }).then(function(ab){')
js_parts.append('    if(!ab) return;')
js_parts.append('    CDS_READER = new __CDS.DatasetReader(new Uint8Array(ab));')
js_parts.append('    document.body.classList.add("has-local-glyphs");')
js_parts.append('  }).catch(function(){ CDS_READER = null; });')
js_parts.append('})();')
js_parts.append('/* oracle overlay 已真重打包进 dataset.bin，运行时层移除（2026-09-12） */')
js_parts.append('var STROKE_DB = null;')
js_parts.append('(function(){')
js_parts.append('  fetch("data/stroke_data.json?v=20260910h").then(function(r){ return r.ok ? r.json() : null; }).then(function(d){ STROKE_DB = d; }).catch(function(){});')
js_parts.append('})();')
js_parts.append('function glyphToDataURL(raw){')
js_parts.append('  var w = raw.width, h = raw.height;')
js_parts.append('  var src = raw.pixels;')
js_parts.append('  var mask = new Uint8Array(w*h);')
js_parts.append('  for (var i=0;i<w*h;i++){ mask[i] = src[i] > 110 ? 1 : 0; }')
js_parts.append('  var d = new Uint8Array(w*h);')
js_parts.append('  for (var y=0;y<h;y++){ for (var x=0;x<w;x++){ var on=0;')
js_parts.append('    for (var dy=-1;dy<=1 && !on;dy++){ for (var dx=-1;dx<=1;dx++){')
js_parts.append('      var nx=x+dx, ny=y+dy; if (nx<0||ny<0||nx>=w||ny>=h) continue;')
js_parts.append('      if (mask[ny*w+nx]){ on=1; break; } } }')
js_parts.append('    d[y*w+x] = on; } }')
js_parts.append('  var c = document.createElement("canvas");')
js_parts.append('  c.width = w; c.height = h;')
js_parts.append('  var ctx = c.getContext("2d");')
js_parts.append('  var img = ctx.createImageData(w,h);')
js_parts.append('  for (var i=0;i<w*h;i++){')
js_parts.append('    if (d[i]) { img.data[i*4]=240; img.data[i*4+1]=240; img.data[i*4+2]=240; img.data[i*4+3]=255; }')
js_parts.append('    else { img.data[i*4]=25; img.data[i*4+1]=25; img.data[i*4+2]=25; img.data[i*4+3]=255; }')
js_parts.append('  }')
js_parts.append('  ctx.putImageData(img, 0, 0);')
js_parts.append('  return c.toDataURL("image/png");')
js_parts.append('}')
js_parts.append('function buildLocalStages(baseChar, hasTrad, c){')
js_parts.append('  var glyphs = CDS_READER.glyphsForCharacter(baseChar);')
js_parts.append('  if ((!glyphs || !glyphs.length) && hasTrad) glyphs = CDS_READER.glyphsForCharacter(c.char);')
js_parts.append('  if (!glyphs || !glyphs.length) return [];')
js_parts.append('  var order = ["glyphwiki","oracle-bone","bronze","bamboo-silk","bigseal","seal","clerical","regular"];')
js_parts.append('  var stages = [];')
js_parts.append('  var gcode = c.char.codePointAt(0).toString(16).toUpperCase();')
js_parts.append('  for (var i=0;i<order.length;i++){')
js_parts.append('    var script = order[i];')
js_parts.append('    if (script === "regular") continue;')
js_parts.append('    var list = glyphs.filter(function(g){ return g.script === script; });')
js_parts.append('    if (!list.length && script === "bigseal") continue;')  # 大篆覆盖有限，无则不出占位槽
js_parts.append('    if (list.length){')
js_parts.append('      var raw = CDS_READER.getRaw(list[0].key);')
js_parts.append('      var era = __CDS.SCRIPT_METADATA[script].chinese;')
js_parts.append('      stages.push({era: era, img: glyphToDataURL(raw)});')
js_parts.append('    } else if (script === "oracle-bone" && false) {')
js_parts.append('      stages.push({era: __CDS.SCRIPT_METADATA[script].chinese, img: glyphToDataURL(ORACLE_OVERLAY[c.char])});')
js_parts.append('    } else {')
js_parts.append('      stages.push({era: __CDS.SCRIPT_METADATA[script].chinese, pending: true, script: script, code: gcode});')
js_parts.append('    }')
js_parts.append('  }')
js_parts.append('  if (hasTrad) stages.push({era:"' + u('繁体') + '", glyph: c.trad});')
js_parts.append('  stages.push({era:"' + u('简体') + '", glyph: c.char});')
js_parts.append('  return stages;')
js_parts.append('}')
# 空字形时的极简演变：只展示繁简对比（不再 fallback 远程 39017.com，后起字本无古字形）
js_parts.append('function buildFallbackStages(c, hasTrad){')
js_parts.append('  var order = ["glyphwiki","oracle-bone","bronze","bamboo-silk","seal","clerical"];')
js_parts.append('  var stages = [];')
js_parts.append('  var fbcode = c.char.codePointAt(0).toString(16).toUpperCase();')
js_parts.append('  order.forEach(function(script){')
js_parts.append('    if (script === "oracle-bone" && false) {')
js_parts.append('      stages.push({era: __CDS.SCRIPT_METADATA[script].chinese, img: glyphToDataURL(ORACLE_OVERLAY[c.char])});')
js_parts.append('    } else {')
js_parts.append('      stages.push({era: __CDS.SCRIPT_METADATA[script].chinese, pending: true, script: script, code: fbcode});')
js_parts.append('    }')
js_parts.append('  });')
js_parts.append('  if (hasTrad) stages.push({era:"' + u('繁体') + '", glyph: c.trad});')
js_parts.append('  stages.push({era:"' + u('简体') + '", glyph: c.char});')
js_parts.append('  return stages;')
js_parts.append('}')
# 古文字阶段运行时补全：仅依赖已落地的开源古文字字体（FontFace + document.fonts.check 网关）。
# 曾尝试经 GlyphWiki 关联字形后缀（-j/-t/-b/-s）探测甲骨/金文/篆/隶，经核验该命名不成立：
#   GlyphWiki 的 -t/-k/-g/-v 实为「地区变体」（台湾/香港/大陆/异体，见 u8ff0-t 等），并非书体阶段；
#   GlyphWiki 本身是宋体/楷书字形库，无系统化的甲骨/金文/篆/隶书体后缀命名（u4EBA-j/-t/-b/-s 实测全 404）。
#   故关闭 GlyphWiki 后缀探测，改回只走 bundled 字体兜底，避免误把台湾异体当「隶书」显示。
# 甲骨/金文/篆：已由 cluesurf/mark(OFL) + 崇羲篆體(CC-BY-ND-3.0-TW) 离线补全；隶书：临海隶书＋青柳隶书双来源（见 manifest.json）。
js_parts.append('function fillAncientGlyphs(){')
js_parts.append('  var nodes = document.querySelectorAll(".evo-step.pending[data-script]");')
js_parts.append('  nodes.forEach(function(node){')
js_parts.append('    var script = node.getAttribute("data-script");')
js_parts.append('    var code = node.getAttribute("data-code");')
js_parts.append('    if (!script || !code) return;')
js_parts.append('    var era = node.querySelector(".era-name") ? node.querySelector(".era-name").textContent : "";')
js_parts.append('    tryFontStage(script, code, node, era);')
js_parts.append('  });')
js_parts.append('  // post font-fill: chars with only glyph-source (no real ancient stage) stay pending; never render blank placeholder')
js_parts.append('  nodes.forEach(function(node){')
js_parts.append('    if (!node.classList.contains("pending")) return;')
js_parts.append('    var code = node.getAttribute("data-code"); if (!code) return;')
js_parts.append('    var ch = String.fromCodePoint(parseInt(code, 16));')
js_parts.append('    if (typeof NO_ANCIENT_GLYPH !== "undefined" && NO_ANCIENT_GLYPH.has(ch)) { if (script === "clerical") return;')
js_parts.append('      node.classList.remove("pending"); node.classList.add("no-ancient");')
js_parts.append('      var era = node.querySelector(".era-name") ? node.querySelector(".era-name").textContent : "";')
js_parts.append('      node.innerHTML = "<div class=\'era-name\'>" + era + "</div><div class=\'era-no-ancient\'>根据汉典查询，此字目前未发现" + era + "字形</div>";')
js_parts.append('    }')
js_parts.append('  });')
js_parts.append('}')
# 字体降级层：开源古文字字体就位后，离线补满四阶段（清单与授权见 data/fonts/manifest.json）
# 用 FontFace 加载 + document.fonts.check 网关，避免缺字显示豆腐块；字体缺失则静默跳过，退回"待补全"
js_parts.append(r'''var STAGE_FONTS = {
  "oracle-bone": {"file":"data/fonts/oracle-bone.otf","family":"AncientOracle"},
  "bronze": {"file":"data/fonts/bronze-script.otf","family":"AncientBronze"},
  "seal": {"file":"data/fonts/chongxi-seal.otf","family":"ChongXiSeal"},
  "clerical": {"file":"data/fonts/clerical-script.ttf","family":"AncientClerical"}
};''')
js_parts.append(r'''var CLERICAL_QINGLIU = {"file":"data/fonts/clerical-qingliu.ttf","family":"AncientClericalQingliu"};''')
# 字体 cmap 覆盖集：key=书体, value=该字体含的 Unicode 码点（十进制）数组（离线提取）
js_parts.append('var STAGE_FONT_GLYPHS = ' + json.dumps(_font_glyphs, ensure_ascii=True, separators=(",", ":")) + ';')
js_parts.append('for (var _gk in STAGE_FONT_GLYPHS) STAGE_FONT_GLYPHS[_gk] = new Set(STAGE_FONT_GLYPHS[_gk]);')
js_parts.append('var CLERICAL_SOURCE = ' + json.dumps(src_map, ensure_ascii=True, separators=(",",":")) + ';')
js_parts.append(r'''var __fontReady = {};
(function preloadAncientFonts(){
  if (typeof FontFace === "undefined" || !document.fonts) return;
  Object.keys(STAGE_FONTS).forEach(function(s){
    var f = STAGE_FONTS[s];
    try {
      var ff = new FontFace(f.family, "url(" + f.file + ")");
      ff.load().then(function(loaded){ document.fonts.add(loaded); __fontReady[s] = true; if (window.__refillFont) window.__refillFont(); }).catch(function(){ __fontReady[s] = false; });
    } catch(e) { __fontReady[s] = false; }
  });
  // Qingliu lishu as second clerical source (fills Linhai gaps), preloaded separately
  try {
    var qf = new FontFace(CLERICAL_QINGLIU.family, "url(" + CLERICAL_QINGLIU.file + ")");
    qf.load().then(function(loaded){ document.fonts.add(loaded); __fontReady["clerical-qingliu"] = true; if (window.__refillFont) window.__refillFont(); }).catch(function(){ __fontReady["clerical-qingliu"] = false; });
  } catch(e) { __fontReady["clerical-qingliu"] = false; }
})();''')
js_parts.append(r'''function tryFontStage(script, code, node, era){
  var f = STAGE_FONTS[script];
  if (!f) return;
  var ch = String.fromCodePoint(parseInt(code, 16));
  // clerical dual-source: Linhai first, fallback Qingliu; tag font source per char
  if (script === "clerical") {
    var srcKey = (typeof CLERICAL_SOURCE !== "undefined") ? (CLERICAL_SOURCE[ch] || "none") : "none";
    if (srcKey === "none") return;  // neither font has it; keep pending placeholder
    var fam, srcLabel, famKey = (srcKey === "linhai") ? "clerical" : "clerical-qingliu";
    var _cset = STAGE_FONT_GLYPHS[famKey];
    if (!__fontReady[famKey] || !_cset || !_cset.has(parseInt(code, 16))) return;  // font truly lacks this glyph: keep pending, never render kaisho fallback
    fam = (srcKey === "linhai") ? f.family : CLERICAL_QINGLIU.family;
    srcLabel = (srcKey === "linhai") ? "\u4e34\u6d77\u96b6\u4e66" : "\u9752\u67f3\u96b6\u4e66";
    node.classList.remove("pending"); node.classList.remove("no-ancient");
    node.classList.add("font-fill");
    node.setAttribute("data-clerical-src", srcKey);
    node.innerHTML = "<div class='era-name'>" + era + "</div>" + (window.ERA_DESC && ERA_DESC[era] ? "<div class='era-desc'>" + ERA_DESC[era] + "</div>" : "") + "<span class='era-font' style='font-family:" + fam + "'>" + ch + "</span><div class='clerical-badge " + srcKey + "'>" + srcLabel + "</div>";
    return;
  }
  if (!__fontReady[script]) return;
  var _set = STAGE_FONT_GLYPHS[script];
  if (!_set || !_set.has(parseInt(code, 16))) return;  // font truly lacks glyph: keep pending (shows "no such historical form"), never render kaisho fallback
  node.classList.remove("pending");
  node.classList.add("font-fill");
  node.innerHTML = "<div class='era-name'>" + era + "</div>" + (window.ERA_DESC && ERA_DESC[era] ? "<div class='era-desc'>" + ERA_DESC[era] + "</div>" : "") + "<span class='era-font' style='font-family:" + f.family + "'>" + ch + "</span>";
}''')
js_parts.append(r'''window.__refillFont = function(){ try { fillAncientGlyphs(); } catch(e){} };''')
# 书法欣赏：4 个 Google Fonts OFL 可商用书法家字体（楷/行/行草），门控缺字不回退系统字
js_parts.append(r'''var CALLI_FONTS = [
  {"name":"楷书·马善政","family":"MaShanZheng","file":"data/fonts/kai-MaShanZheng.ttf"},
  {"name":"行书·龙藏","family":"LongCang","file":"data/fonts/xing-LongCang.ttf"},
  {"name":"行书·志莽","family":"ZhiMangXing","file":"data/fonts/xing-ZhiMangXing.ttf"},
  {"name":"行草·刘建毛","family":"LiuJianMaoCao","file":"data/fonts/xingcao-LiuJianMaoCao.ttf"}
];''')
js_parts.append('var CALLI_GLYPHS = ' + json.dumps(_calli_glyphs, ensure_ascii=True, separators=(",",":")) + ';')
js_parts.append('for (var _ck in CALLI_GLYPHS) CALLI_GLYPHS[_ck] = new Set(CALLI_GLYPHS[_ck]);')
js_parts.append('var __calliReady = {};')
js_parts.append(r'''(function preloadCalliFonts(){
  if (typeof FontFace === "undefined" || !document.fonts) return;
  CALLI_FONTS.forEach(function(f){
    try {
      var ff = new FontFace(f.family, "url(" + f.file + ")");
      ff.load().then(function(loaded){ document.fonts.add(loaded); __calliReady[f.family] = true;
        if (window.__currentCharId != null) { try { showDetail(window.__currentCharId); } catch(e){} }
      }).catch(function(){ __calliReady[f.family] = false; });
    } catch(e) { __calliReady[f.family] = false; }
  });
})();''')
js_parts.append(r'''function buildCalliHTML(c){
  if (typeof CALLI_FONTS === "undefined" || !CALLI_FONTS.length) return "";
  var ch = c.char; var cp = ch.codePointAt(0);
  var cards = [];
  CALLI_FONTS.forEach(function(f){
    if (!__calliReady[f.family]) return;  // 字体未就绪：等加载完成由 preload 回调重渲染
    var set = (typeof CALLI_GLYPHS !== "undefined" && CALLI_GLYPHS[f.family]) ? CALLI_GLYPHS[f.family] : null;
    if (set && !set.has(cp)) return;  // 该字体不含此字：跳过，不回退为系统字
    cards.push("<div class='calli-card'><div class='calli-char' style='font-family:\"" + f.family + "\"'>" + ch + "</div><div class='calli-name'>" + f.name + "</div></div>");
  });
  if (!cards.length) return "";
  return "<div class='detail-section calli-section'><h4>书法欣赏（名家字体·OFL 可商用）</h4><div class='calli-grid'>" + cards.join("") + "</div><i class='src-mini'>字体：马善政楷书 / 龙藏行书 / 志莽行书 / 刘建毛行草（Google Fonts，SIL Open Font License，可商用）</i></div>";
}''')
js_parts.append('var activeLiuShu = "' + u('全部') + '";')
js_parts.append('var activeCategory = "' + u('全部') + '";')
js_parts.append('var activeSort = "default";')
js_parts.append('var activeStroke = "' + u('全部') + '";')
js_parts.append('function getCategory(c) { return c.category || "' + u('其他') + '"; }')
js_parts.append('function filterChars() {')
js_parts.append('  var q = document.getElementById("searchInput").value.trim().toLowerCase();')
js_parts.append('  return CHARS.filter(function(c) {')
js_parts.append('    if (activeLiuShu !== "' + u('全部') + '") { var _ls = c.liushu || ""; var _ok = (_ls === activeLiuShu) || (activeLiuShu === "' + u('会意') + '" && _ls.indexOf("' + u('会意') + '") >= 0) || (activeLiuShu === "' + u('形声') + '" && _ls.indexOf("' + u('形声') + '") >= 0); if (!_ok) return false; }')
js_parts.append('    if (activeCategory !== "' + u('全部') + '" && getCategory(c) !== activeCategory) return false;')
js_parts.append('    if (activeStroke !== "' + u('全部') + '") {')
js_parts.append('      var sc = c.stroke;')
js_parts.append('      if (activeStroke === "1-5" && !(sc <= 5)) return false;')
js_parts.append('      if (activeStroke === "6-10" && !(sc >= 6 && sc <= 10)) return false;')
js_parts.append('      if (activeStroke === "11-15" && !(sc >= 11 && sc <= 15)) return false;')
js_parts.append('      if (activeStroke === "16+" && !(sc >= 16)) return false;')
js_parts.append('    }')
js_parts.append('    if (!q) return true;')
js_parts.append('    if (q.length === 1 && q >= "a" && q <= "z") {')
js_parts.append('      var tm={"\\u0101":"a","\\u00e1":"a","\\u01ce":"a","\\u00e0":"a","\\u0113":"e","\\u00e9":"e","\\u011b":"e","\\u00e8":"e","\\u012b":"i","\\u00ed":"i","\\u01d0":"i","\\u00ec":"i","\\u014d":"o","\\u00f3":"o","\\u01d2":"o","\\u00f2":"o","\\u016b":"u","\\u00fa":"u","\\u01d4":"u","\\u00f9":"u"};')
js_parts.append('      var f0=c.pinyin[0]; var fb=tm[f0]||f0;')
js_parts.append('      if (fb===q) return true;')
js_parts.append('    }')
js_parts.append('    return c.char===q||c.trad===q||c.pinyin.toLowerCase().indexOf(q)>=0||c.radical===q||c.radical_name.indexOf(q)>=0;')
js_parts.append('  });')
js_parts.append('}')
js_parts.append('function render() {')
js_parts.append('  var filtered = filterChars();')
js_parts.append('  var filtered = applyFavFilter(filterChars());')
js_parts.append('  if (activeSort==="pinyin") filtered.sort(function(a,b){return a.pinyin.localeCompare(b.pinyin,"zh")});')
js_parts.append('  else if (activeSort==="stroke") filtered.sort(function(a,b){return a.stroke-b.stroke||a.pinyin.localeCompare(b.pinyin,"zh")});')
js_parts.append('  document.getElementById("stats").textContent = "' + u('共 ') + '" + filtered.length + " / " + CHARS.length + "' + u(' 字') + '";')
js_parts.append('  var grid = document.getElementById("charGrid");')
js_parts.append('  if (filtered.length === 0) { grid.innerHTML = "<div class=\'no-results\'>' + u('没有匹配的汉字') + '</div>"; return; }')
js_parts.append('  grid.innerHTML = filtered.map(function(c){')
js_parts.append('    return "<div class=\'char-card\' onclick=\'showDetail(" + c.id + ")\'>" + c.char + "<div class=\'pinyin\'>" + c.pinyin + "</div></div>";')
js_parts.append('    return charCardHTML(c);')
js_parts.append('  }).join("");')
js_parts.append('}')
js_parts.append('function showDetail(id) {')
js_parts.append('  window.__currentCharId = id;')
js_parts.append('  var c = CHARS.find(function(x){return x.id===id;});')
js_parts.append('  var c = CHARS.find(function(x){return x.id===id;}); currentId = c.id; currentChar = c.char;')
js_parts.append('  if (!c) return;')
js_parts.append('  var unicode = c.char.codePointAt(0).toString(16).toUpperCase();')
js_parts.append('  var hasTrad = c.trad !== c.char;')
js_parts.append('  var baseChar = hasTrad ? c.trad : c.char;')
js_parts.append('  var stages = [];')
js_parts.append('  if (CDS_READER) {')
js_parts.append('    stages = buildLocalStages(baseChar, hasTrad, c);')
js_parts.append('  }')
js_parts.append('  if (!stages.length) {')
js_parts.append('    // glyph dataset not covered (later-added chars e.g. ma/ye/men); do not force remote image')
js_parts.append('    stages = buildFallbackStages(c, hasTrad);')
js_parts.append('  }')
js_parts.append(r'''  var houqiNote = "";''')
js_parts.append(r'''  var hqCurated = c.shuowen && c.shuowen.replace("\uff08","").indexOf("\u540e\u8d77\u5b57") === 0;''')
js_parts.append(r'''  var A_ORA="\u7532\u9aa8\u6587", A_BRZ="\u91d1\u6587", A_BAM="\u7b80\u724d\u5e1b\u4e66";''')
js_parts.append(r'''  var hasAncient = stages.some(function(s){ return s.era===A_ORA||s.era===A_BRZ||s.era===A_BAM; });''')
js_parts.append(r'''  if (hqCurated || !hasAncient) {''')
js_parts.append(r'''    var tag = hqCurated ? "\u540e\u8d77\u5b57\uff08\u665a\u51fa\u5b57\uff09" : "\u65e0\u65e9\u671f\u53e4\u6587\u5b57\u5f62";''')
js_parts.append(r'''    houqiNote = "<div class='trace-note'><b>\u26a0 " + tag + "</b>\uff1a";''')
js_parts.append(r'''    houqiNote += hqCurated ? "\u300a\u8bf4\u6587\u89e3\u5b57\u300b\u672a\u6536\u5f55\u672c\u5b57\uff08\u6216\u4e3a\u540e\u4e16/\u8fd1\u4ee3\u65b0\u9020\uff09\uff0c" : "\u672c\u5e93\u672a\u6536\u5f55\u672c\u5b57\u7532\u9aa8/\u91d1\u6587\u7b49\u65e9\u671f\u5b57\u5f62\uff0c";''')
js_parts.append(r'''    houqiNote += "\u4e0b\u65b9\u5c55\u793a\u4e3a\u5b57\u6e90\u6784\u5f62\u4e0e\u540e\u4e16\u4e66\u4f53\uff0c\u975e\u8be5\u5b57\u7684\u53e4\u6587\u5b57\u6f14\u53d8\u3002</div>";''')
js_parts.append(r'''  }''')
js_parts.append('  var evoHTML = stages.map(function(s,i){')
js_parts.append('    var arrow = i>0 ? "<div class=\'evo-arrow\'>&rarr;</div>" : "";')
js_parts.append('''    if (s.img) { return arrow + "<div class='evo-step'><div class='era-name'>" + s.era + "</div>" + (ERA_DESC[s.era] ? "<div class='era-desc'>" + ERA_DESC[s.era] + "</div>" : "") + "<img class='era-img' src='" + s.img + "'>" + "</div>"; }''')
js_parts.append(r'''    if (s.pending) { var _script = s.script || ""; var _plabel = (_script === "clerical") ? "\u672a\u6536\u5f55\u6c49\u96b6\u771f\u8ff9\u00b7\u4ee5\u5b57\u4f53\u66ff\u4ee3" : ("\u5386\u53f2\u4e0a\u4e0d\u5b58\u5728\u6b64\u5b57\u7684" + s.era + "\u5b57\u5f62"); return arrow + "<div class='evo-step pending" + (_script === "clerical" ? "" : " no-ancient") + "' data-script='" + _script + "' data-code='" + (s.code||"") + "'><div class='era-name'>" + s.era + "</div>" + (ERA_DESC[s.era] ? "<div class='era-desc pending-desc'>" + ERA_DESC[s.era] + "</div>" : "") + "<div class='era-pending'>" + _plabel + "</div></div>"; }''')
js_parts.append('    return arrow + "<div class=\'evo-step\'><div class=\'era-name\'>\" + s.era + \"</div>\" + (ERA_DESC[s.era] ? \"<div class=\'era-desc\'>\" + ERA_DESC[s.era] + \"</div>\" : \"\") + \"<span style=\'font-size:24px\'>\" + s.glyph + \"</span></div>\";')
js_parts.append('  }).join("");')
js_parts.append('  setTimeout(function(){ try { fillAncientGlyphs(); } catch(e){} }, 0);')
js_parts.append('  var strokeHTML = "";')
js_parts.append('  if (STROKE_DB && STROKE_DB[c.char]) {')
js_parts.append('    strokeHTML = renderStrokeSVG(c.char);')
js_parts.append('  } else {')
js_parts.append('    strokeHTML = "<div class=\'stroke-fallback\'><span class=\'fallback-char\'>" + c.char + "</span><div class=\'src-mini\'>' + u('笔顺动画待数据接入') + '</div></div>";')
js_parts.append('  }')
js_parts.append('  var calliHTML = buildCalliHTML(c);')
js_parts.append('  var noteHTML = c.oracle_note ? "<div class=\'oracle-note\'>' + u('⭐甲骨文说明：') + '" + c.oracle_note + "</div>" : "";')
js_parts.append('    document.getElementById("detail").innerHTML = ')
js_parts.append('    detailHeaderHTML(c) +')
js_parts.append('    "<div class=\'detail-hero\'>" +')
js_parts.append('      "<div class=\'hero-left\'>" + strokeHTML + "</div>" +')
js_parts.append('      "<div class=\'hero-right\'>" +')
js_parts.append('        "<div class=\'detail-pinyin\'>" + (hasTrad ? "<span class=\'trad-mini\'>" + c.trad + "</span> " : "") + (typeof renderPinyinAudio===\'function\' ? renderPinyinAudio(c) : c.pinyin) + "</div>" +')
js_parts.append('        "<div class=\'detail-info\'>" +')
js_parts.append('          "<div>' + u('六书') + ': <span>" + c.liushu + "</span>" + (c.liushu_disputed ? "<span class=\'dispute-badge\' title=\'" + (c.liushu_disputed_note||"") + "\'>学界有争议</span>" : "") + "</div>" +')
js_parts.append('          "<div>' + u('部首') + ': <span>" + c.radical + "(" + c.radical_name + ")</span></div>" +')
js_parts.append('          "<div>' + u('笔画') + ': <span>" + c.stroke + "</span></div>" +')
js_parts.append('          "<div>' + u('五行') + ': <span>" + (c.wuxing||"-") + "</span><i class=\'src-mini\'>" + (WUXING_LABEL[c.wuxing_source] || "' + u('民俗参考·非文字学属性') + '") + "</i></div>" +')
js_parts.append('          "<div>' + u('拼音') + ': <span>" + c.pinyin + "</span></div>" +')
js_parts.append('          (c.fanqie ? "<div>' + u('反切') + ': <span>" + c.fanqie + "</span><i class=\'src-mini\'>' + u('出《说文》') + '</i></div>" : "") +')
js_parts.append('        "</div>" +')
js_parts.append('      "</div>" +')
js_parts.append('    "</div>" +')
js_parts.append('    "<div class=\'detail-section\'><h4>' + u('字形演变') + '</h4><i class=\'src-mini\'>' + u('字源图：GlyphWiki（CC BY-SA 2.1 JP）｜篆书：崇羲篆体（CC-BY-ND-3.0-TW）｜甲骨/金文：cluesurf/mark（OFL）｜隶书：临海隶书＋青柳隶书（免费商用，猫啃网）｜笔顺：Hanzi Writer Data（Make Me a Hanzi · Arphic 公共许可，可商用）') + '</i>" + houqiNote + noteHTML + "<div class=\'evo-timeline\'>" + evoHTML + "</div></div>" +')
js_parts.append('    calliHTML +')
js_parts.append('    "<div class=\'detail-cols\'>" +')
js_parts.append('      "<div class=\'detail-section\'><h4>' + u('演变过程') + '</h4><p>" + (c.evolution||"") + "</p><i class=\'src-mini\'>' + u('AI生成·待核验') + '</i></div>" +')
js_parts.append('      (c.trace_kangxi || c.trace_yupian || c.trace_guangyun || c.trace_note ? "<div class=\'detail-section\'><h4>' + u('后起字溯源') + '</h4>" +')
js_parts.append('        (c.trace_note ? "<p class=\'trace-note\'>" + c.trace_note + "</p>" : "") +')
js_parts.append('        (c.trace_yupian ? "<p class=\'src-line\'><b>" + SRC_YP + ":</b>" + c.trace_yupian + "</p>" : "") +')
js_parts.append('        (c.trace_guangyun ? "<p class=\'src-line\'><b>" + SRC_GY + ":</b>" + c.trace_guangyun + "</p>" : "") +')
js_parts.append('        (c.trace_kangxi ? "<p class=\'src-line\'><b>" + SRC_KX + ":</b>" + c.trace_kangxi + "</p>" : "") +')
js_parts.append('      "</div>" : "") +')
js_parts.append('    "</div>" +')
js_parts.append('    "<div class=\'detail-cols\'>" +')
js_parts.append('      "<div class=\'detail-section\'><h4>' + u('本义 vs 今义') + '</h4>" +')
js_parts.append('        "<div class=\'meaning-compare\'>" +')
js_parts.append('          "<div class=\'meaning-box\'><div class=\'label\'>' + u('本义（原始含义）') + '</div><div class=\'content\'>" + (c.original||"") + "</div></div>" +')
js_parts.append('          "<div class=\'meaning-box\'><div class=\'label\'>' + u('今义（现代用法）') + '</div><div class=\'content\'>" + (c.modern||"") + "</div></div>" +')
js_parts.append('        "</div><i class=\'src-mini\'>' + u('AI生成·待核验') + '</i>" +')
js_parts.append('      "</div>" +')
js_parts.append('      "<div class=\'detail-section\'><h4>' + u('说文解字') + '</h4>" +')
js_parts.append('        "<p>" + (c.shuowen||"") + "</p>" +')
js_parts.append('        (c.duan_note ? "<details class=\'duan-box\'><summary>' + u('段玉裁注') + '</summary><p>" + c.duan_note + "</p></details>" : "") +')
js_parts.append('        (c.variant ? "<p class=\'src-line\'><b>' + u('异体重文') + ':</b>" + c.variant + "</p>" : "") +')
js_parts.append('        "<i class=\'src-mini\'>' + u('出：《说文解字》') + '</i>" +')
js_parts.append('      "</div>" +')
js_parts.append('    "</div>" +')
js_parts.append('    (CULTURAL_DB && CULTURAL_DB[c.char] ? "<div class=\'detail-section cultural-section\'><h4>" + "' + u('字源故事 · 成语 · 诗词') + '" + "</h4>" + culturalHTML(CULTURAL_DB[c.char]) + "<i class=\'src-mini\'>" + "' + u('AI生成·待抽检') + '" + "</i></div>" : "");')
js_parts.append('  document.getElementById("overlay").classList.add("show");')
js_parts.append('  document.body.style.overflow = "hidden";')
js_parts.append('}')
js_parts.append('function closeDetail() {')
js_parts.append('  window.__currentCharId = null;')
js_parts.append('  document.getElementById("overlay").classList.remove("show");')
js_parts.append('  document.body.style.overflow = "";')
js_parts.append('}')
js_parts.append('document.getElementById("searchInput").addEventListener("input", render);')
js_parts.append('document.getElementById("liushuFilters").addEventListener("click", function(e){')
js_parts.append('  if (e.target.classList.contains("filter-btn")) {')
js_parts.append('    document.querySelectorAll("#liushuFilters .filter-btn").forEach(function(b){b.classList.remove("active")});')
js_parts.append('    e.target.classList.add("active"); activeLiuShu = e.target.dataset.ls; render();')
js_parts.append('  }')
js_parts.append('});')
js_parts.append('document.getElementById("categoryFilters").addEventListener("click", function(e){')
js_parts.append('  if (e.target.classList.contains("filter-btn")) {')
js_parts.append('    document.querySelectorAll("#categoryFilters .filter-btn").forEach(function(b){b.classList.remove("active")});')
js_parts.append('    e.target.classList.add("active"); activeCategory = e.target.dataset.cat; render();')
js_parts.append('  }')
js_parts.append('});')
js_parts.append('document.getElementById("strokeFilters").addEventListener("click", function(e){')
js_parts.append('  if (e.target.classList.contains("filter-btn")) {')
js_parts.append('    document.querySelectorAll("#strokeFilters .filter-btn").forEach(function(b){b.classList.remove("active")});')
js_parts.append('    e.target.classList.add("active"); activeStroke = e.target.dataset.stroke; render();')
js_parts.append('  }')
js_parts.append('});')
js_parts.append('document.getElementById("sortControls").addEventListener("click", function(e){')
js_parts.append('  if (e.target.classList.contains("filter-btn")) {')
js_parts.append('    document.querySelectorAll("#sortControls .filter-btn").forEach(function(b){b.classList.remove("active")});')
js_parts.append('    e.target.classList.add("active"); activeSort = e.target.dataset.sort; render();')
js_parts.append('  }')
js_parts.append('});')
js_parts.append('document.addEventListener("keydown", function(e){ if(e.key==="Escape") closeDetail(); });')
js_parts.append('var __welcomeEl = document.getElementById("welcomeModal");')
js_parts.append('function closeWelcome(){ if(__welcomeEl){ __welcomeEl.classList.remove("show"); try{ localStorage.setItem("swjz_welcome_seen","1"); }catch(e){} } }')
js_parts.append('function openWelcome(){ if(__welcomeEl) __welcomeEl.classList.add("show"); }')
js_parts.append('if (__welcomeEl && !localStorage.getItem("swjz_welcome_seen")) { __welcomeEl.classList.add("show"); }')
js_parts.append('render();')
js_parts.append('render(); renderDaily();')

lines.append('<script src="data/fzstd.umd.js"></script>')
lines.append('<script src="data/dataset-reader.js"></script>')
lines.append('<script src="data/cultural-ui.js"></script>')
lines.append('<script src="data/pinyin-utils.js"></script>')
lines.append('<script src="data/hanzi-writer.min.js"></script>')
lines.append('<script src="data/hanzi-writer.min.js"></script>')
lines.append('<script src="data/app-features.js"></script>')
lines.append('<script>' + '\n'.join(js_parts) + '</script>')
lines.append('</body></html>')

result = '\n'.join(lines)

# Write
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(result)

# Verify: check no non-ASCII OUTSIDE JS string literals / comments.
# Chinese inside JS string literals (e.g. template labels) is valid JS and should not fail.
import re
m = re.search(r'<script>(.*?)</script>', result, re.DOTALL)
if m:
    js = m.group(1)
    # Strip block comments /* */ and line comments // first
    stripped = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
    stripped = re.sub(r'//[^\n]*', '', stripped)
    # Strip string literals (single, double, template). Naive but sufficient for hygiene check.
    stripped = re.sub(r'"(\\.|[^"\\])*"', '', stripped)
    stripped = re.sub(r"'(\\.|[^'\\])*'", '', stripped)
    stripped = re.sub(r'`(\\.|[^`\\])*`', '', stripped)
    na_total = sum(1 for c in js if ord(c) > 127)
    na_outside = sum(1 for c in stripped if ord(c) > 127)
    print(f'JS: {len(js)} chars, {na_total} non-ASCII total, {na_outside} non-ASCII OUTSIDE strings/comments  {"OK" if na_outside==0 else "FAIL(bare CJK/comment)"}')

# Also check HTML body non-ASCII count (this is OK)
html_only = result[:result.find('<script>')] + result[result.find('</script>')+9:]
na_html = sum(1 for c in html_only if ord(c) > 127)
print(f'HTML body: {na_html} non-ASCII (expected > 0 for Chinese labels)')

print(f'Total: {len(result)} bytes, {len(data["characters"])} chars')
