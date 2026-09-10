# 交接：说文解字 App 「隶书」阶段字体取字

> 用途：本机（沙箱）三源全封，无法自行取字。本文档交**海外伙伴**或**用户浏览器**执行取字，落入 `data/fonts/clerical-script.ttf` 即自动生效。

## 1. 背景与现状（2026-09-10 核实）

App 字形演变六阶段：甲骨 → 金文 → 简牍帛书 → 篆 → 隶 → 楷。
当前落地情况（靠 bundled 字体离线渲染，运行时 `FontFace`+`document.fonts.check` 网关）：

| 阶段 | 状态 | 字体 |
|---|---|---|
| 甲骨 | ✅ | `data/fonts/oracle-bone.otf`（cluesurf/mark, OFL） |
| 金文 | ✅ | `data/fonts/bronze-script.otf`（cluesurf/mark, OFL） |
| 篆 | ✅ | `data/fonts/chongxi-seal.otf`（崇羲篆體, CC-BY-ND-3.0-TW） |
| **隶书** | ❌ 待补全 | `data/fonts/clerical-script.ttf` 缺失 → 显示「待补全」 |

**为什么本机取不到（已实测）：**
- 中研院漢字構形資料庫 / 小學堂 `xiaoxue.iis.sinica.edu.tw` → 返回「Access Restricted」地理封锁页（HTTP 200 实为封锁页）。大陆与海外均不可达。
- 猫啃网 `maoken.com` → 沙箱被 Cloudflare **403**（机器人拦截）；**用户浏览器/海外住宅 IP 可正常访问**（崇羲篆體即经此取得）。
- GlyphWiki `glyphwiki.org` → 沙箱被 Cloudflare 拦（`u4EBA.png` 也 404）；其 `-t/-k/-g/-v` 是**地区变体**（台湾/香港/大陆/异体），**不是书体阶段**，原 App 探测命名已确认为错、已关闭。
- GitHub raw/API 沙箱可达，但**全站无干净 OFL 隶书字体**（cluesurf/mark 无 clerical 目录；Google Fonts/LXGW/Source Han 均非隶书）。

## 2. 接线已就位，只需丢字体文件

`build_web.py` 中 `STAGE_FONTS` 已指向：
```
"clerical": {"file":"data/fonts/clerical-script.ttf","family":"AncientClerical"}
```
把取到的字体重命名为 `clerical-script.ttf` 放入 `D:\WorkBuddy\projects\说文解字\data\fonts\` 即可，无需改代码。
（注：`.ttf` 或 `.otf` 均可，但 `STAGE_FONTS` 写的是 `.ttf`，若用 `.otf` 需同步改 build_web.py 第 263 行。）

## 3. 取字源（按优先级）

### 首选：中研院 / 崇羲 隶书（CC BY-SA 2.5 TW，干净可商用，须署名）
- 崇羲篆體同家族很可能有隶书字重。在猫啃网搜「隶书」「崇羲」「小學堂」「中研院」：
  - https://www.maoken.com/freefonts/ （搜索框搜 隶书）
  - 或镜像站（小學堂镜像 / GitHub 上搜 `chongxi` `lishu` `clerical`）
- 授权核对：须为 **CC BY-SA 2.5 TW / CC BY / OFL** 之一（可商用，条件=署名+衍生同授权）。**严禁 NC / Non-Commercial**。

### 备选：青柳隶书（Qingliu Lishu）
- 猫啃网 `maoken.com/freefonts/2508.html`，页面标「允许任何个人和企业免费商用」。
- ⚠️ 须逐项核验：① 是否真·可商用（无 NC 字样）；② 有无隐藏限制（如「禁止embedding」「禁止改字」「商用需授权」）；③ 是否含完整 8105 字覆盖（常见免费隶书仅 3000~6000 字，缺字会回退楷体，可接受但需知情）。

### 明确排除（不要取）
- 方正隶书（FZLiShu）/ 华文隶书 / 文鼎隶书：商业字体，NC，**侵权风险**。
- AaFangfanglishu：明确 Non-Commercial。
- onlinewebfonts 上的 trial / RichWin 共享版：不可商用。
- ZhengmingLishu（正文隶书）：授权矛盾 + 仅 1183/8105 字，已 REJECT。

## 4. 取字后核验（在取字机器上跑）

```bash
pip install fonttools
python - <<'PY'
from fontTools.ttLib import TTFont
f = TTFont("clerical-script.ttf")
# 1) 字体格式
print("sfntVersion:", f.sfntVersion)   # 'OTTO'=CFF/OpenType, '\x00\x01\x00\x00'=TrueType
# 2) 内嵌授权串（搜 OFL / CC / Non-Commercial / NC）
import re
name = f["name"]
blob = " ".join(n.toUnicode() for n in name.names if n.toUnicode())
for kw in ["OFL","SIL Open Font","CC BY","CC-BY","Non-Commercial","Non-commercial","NC","商业","商用","禁止"]:
    if kw in blob: print("LICENSE HIT:", kw)
# 3) Unicode 覆盖（对比 8105 字）
cmap = f.getBestCmap()
target = [c for c in range(0x4E00,0x9FFF+1)]  # 基本汉字区粗估
hit = sum(1 for c in target if c in cmap)
print(f"CJK 基本区覆盖: {hit}/约{(0x9FFF-0x4E00+1)}")
PY
```
- 要求：授权串**不能出现** `Non-Commercial / NC / 禁止商用 / 仅供个人`；最好出现 `OFL` 或 `CC BY`。
- 覆盖：尽量 > 6000 字；< 3000 字请标注「部分覆盖，缺字回退楷体」。

## 5. 在 App 中验证
1. 把字体放入 `data/fonts/clerical-script.ttf`。
2. 本地起预览（见项目 README / `build_web.py` 说明），浏览器打开任一千字详情 → 字形演变 → 隶书 阶段应显示隶书字形而非「待补全」。
3. 抽查：人/水/日/木/火/土/月/山/川 等常见字均应显示。

## 6. 授权署名（上线前必做）
若用中研院/崇羲/CC 字体，App 页脚「数据来源」须加：**「隶书：<字体名>（<许可证>，来源 <出处>）」**。
当前页脚已预留该位置（build_web.py 第 143 / 377 行）。
