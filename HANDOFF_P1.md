# 说文解字 App — P1 夜班交接文档（2026-09-10）

> 给「另一台机器 / 夜班同事」做 **P1 阶段** 用。P0（六书人工终审回写 + 文档订正）已 commit 入库。
> 配套总交接见 `HANDOFF.md`（字形数据落地、授权、部署）。**本文件只讲 P1 怎么干、红线在哪、做完怎么验收。**

---

## 0. 一句话目标

在已可商用的「图文版」基础上，把**古文字字形覆盖**和**字源文化内容**做厚：补隶书、扩甲骨/金文量、做书法字体矩阵、抽检字源故事准确性。所有改动**必须 `python build_web.py` 重建 `index.html` 后在浏览器实测**，且**严格守住授权红线**。

---

## 1. 仓库与拉取

```bash
git clone https://gitee.com/landlord2003/shuo-wen_-jie-zi.git
# 已 clone 则： git pull origin main
```

- 主分支 `main`。拉到最新即可（已含 P0 提交 `8c242c5`）。
- 字形数据 `data/dataset.bin`(9.67MB CEDS) 与 `data/fonts/*.otf` 已入库，**pull 后无需补数据**。

---

## 2. 环境与依赖

- Python 3.13（构建已验证可跑）。
- 依赖（仅重建/补数据时需要）：`pip install requests beautifulsoup4 pillow zstandard`（见 `requirements.txt`）。
- 预览必须走 HTTP，不能 `file://` 双击：
  ```bash
  python -m http.server 8765 --bind 127.0.0.1
  # 开 http://127.0.0.1:8765/index.html
  ```

---

## 3. 三个数据文件 —— 格式与改动纪律（关键，别踩坑）

| 文件 | 结构 | 改动纪律 |
|---|---|---|
| `data/characters.json` | **单行紧凑 JSON**（`ensure_ascii=False, separators=(',',':')`）。顶层 `{"meta":{...},"characters":[{char, trad, modern, liushu, liushu_remark, shuowen, duan_note, ...}]}` | ① 回写/修订**必须按 `char` 字段严格匹配**，勿用 `trad` 回退（8105 字里部分字以繁体/异体为 `char`，如 馼→𫘜、晛→𬀪、飨→饗、眇→渺，用 trad 回退会改错对象）。② 改完保持紧凑格式，不要格式化展开。 |
| `data/cultural.json` | **平铺字典**：`{"一":{story,idioms,poems}, "二":{...}, ...}`，**每个汉字是顶层 key**，不是 `{"characters":[...]}` 列表。共 8105 条 | ① 按字符 key 读写。② 字段：`story`(串)、`idioms`(成语数组 `[{w,meaning}]`)、`poems`(诗句数组 `[{line,source}]`)。③ 勿整体重排导致 diff 爆炸。 |
| `data/dataset.bin` | CEDS/zstd 字源位图库（GlyphWiki 体系），9.67MB | 一般**只读**；扩甲骨/金文覆盖走 `tools/rubbing_pipeline/` 重新打包，勿手改。 |

- 六书权威口径：**以 `characters.json` 的 `liushu` + `liushu_remark`（人工终审 P0）为准**。文化故事 `story` 若与 `liushu` 冲突，以 data 为准（见 §6 审计已知问题）。

---

## 4. 构建（每次改数据后必做）

```bash
python build_web.py     # 用 characters.json + cultural.json 重建 index.html
```

- `build_web.py` 把数据内联进 `index.html`（单文件 App，~13.7MB）。
- 重建后必须起 `http.server` 实测：抽查目标字、六书筛选、各古文字阶段是否渲染。

---

## 5. P1 四项任务（验收标准 + 红线）

### P1-1 隶书补源（覆盖 0% → 有值）
- **做法**：在可达环境取一版**干净可商用**隶书字体，丢 `data/fonts/clerical-script.ttf`（或 `.otf`），App 字体降级层自动生效，隶书阶段从「待补全」变可用。
- **操作指南**：`tools/rubbing_pipeline/HANDOFF_隶书字体.md`。
- **验收**：浏览器开任意字，隶书阶段出图（非占位）。
- 🔴 **红线**：隶书字体**必须非 NC**。首选中研院/崇羲隶书（CC BY-SA 2.5 TW），或逐项核验确为非 NC 的字体。**禁止塞入 CC BY-NC / 商用需授权字体**。

### P1-2 甲骨 / 金文扩量（现 甲骨824 / 金1399）
- **做法**：覆盖数字来自 `data/dataset.bin`（GlyphWiki 字源体系）里各字可用的古文字阶段。扩量 = 用更宽的 GlyphWiki 阶段探测重新打包：
  - 探测/抓取：`tools/rubbing_pipeline/adapters/glyphwiki.py`（字源体系）、`wikimedia_ancient.py`（甲骨金文书影，公版）。
  - 重新打包：`tools/rubbing_pipeline/pack_existing.py` / `merge_bins.py`。
  - 覆盖率测量方法见 `tools/glyph_coverage_report.md`。
- **验收**：重建后 `tools/glyph_coverage_report.md` 的 甲骨/金文 覆盖率数字 ↑；App 内对应阶段出图字增多。
- 🔴 **红线**：只用 **GlyphWiki(CC BY-SA 2.1 JP) / Wikimedia 公版 / OFL** 源。**中研院在线接口受地理封锁不可达，勿重试 sinica_pipeline**。

### P1-3 书法字体矩阵（各阶段多字重/多风格）
- **做法**：在 `data/fonts/` 增补同阶段不同风格/字重的开源字体（如多款甲骨、多款篆体），并在字体降级层 `manifest.json` 登记，UI 提供切换。
- **验收**：UI 可切换同阶段不同书法字体，渲染正常。
- 🔴 **红线**：每款字体须可商用（OFL / CC BY-SA / CC-BY-ND 须署名且不改）。**崇羲篆体是 CC-BY-ND-3.0-TW，禁止修改其字形文件**。新增字体在 `manifest.json` 写清授权与署名。

### P1-4 字源故事抽检（cultural.json 准确性）
- **背景**：`cultural.json` 已 8105/8105 全覆盖、0 空值、0 错误标记（结构完整）。但 AI 生成内容**存在准确性隐患**，已审计发现：
  - **六书不一致 10 字**：`story` 明示某「X字」但 `characters.json` 的 `liushu` 不同 —— 大(指事/象形)、插/坂/苷/唏/耜/彀/桊/蛑(会意/形声)、彳(会意/象形)。应以人工终审 data 为准，修正 story 或加「待考」标注。
  - **成语/诗句编造风险**：抽样见疑似非标准成语（如「分班教学」「托故毁约」「托人之危」）与疑似编造诗句出处（如 李贺《感讽五首》"班荆不语对山河…"）。需用权威成语词典/诗句库核验，或明确标注「示例/待考」避免误人子弟。
  - 成语复用 125 个（各出现 2 次）——轻微，可接受。
- **做法**：用 `tools/check_cultural.py` 复跑一致性检查；对 `idioms`/`poems` 抽样比对权威语料；修正以 data 六书为准、清理编造项。
- **验收**：六书不一致归零或已标注；编造成语/诗句清零或标注「待考」；重建后 App 文化卡片无误人子弟内容。
- 🔴 **红线**：文化内容面向教学，**宁可标「待考」也不得保留编造的成语/诗句出处**。

---

## 6. 授权红线总表（抄 `HANDOFF.md`，P1 改动必看）

| 来源 | 许可证 | 约束 |
|---|---|---|
| GlyphWiki 字源（dataset.bin） | CC BY-SA 2.1 JP | 可商用，须署名 + 衍生同授权 |
| cluesurf/mark 甲骨金文字体 | OFL | 可商用，须保留版权声明 |
| 崇羲篆体 | CC-BY-ND-3.0-TW | 可商用，须署名，**禁止修改字形** |
| 隶书（待补） | 须非 NC | 首选 CC BY-SA 2.5 TW / 核验非 NC |
| 旧 EVOBC | CC BY-NC-SA 4.0 | **已下架换源，本仓无残留，勿 reintroduce** |

- App 已内置各来源署名，**勿删**。
- 任何新增字形/字体，入库前必须确认许可证可商用且记录署名。

---

## 7. 完成自检清单（交付前必过）

- [ ] `python build_web.py` 重建成功，`index.html` 体积合理。
- [ ] `python -m http.server` 起服务，浏览器实测：目标字渲染、六书筛选（含「会意兼形声」两按钮都显）、各阶段出图。
- [ ] 覆盖率数字（`tools/glyph_coverage_report.md`）较 P0 有提升（对应任务）。
- [ ] 六书不一致归零/已标注（P1-4）。
- [ ] 无 NC / 未署名字形入库；新增字体授权写进 `manifest.json`。
- [ ] `git status` 干净（仅预期改动），`git diff --stat` 复核无意外文件。
- [ ] 提交信息写明 P1-x 任务与覆盖率变化；push 到 `origin main`。

---

## 8. 别碰的坑（继承 P0 教训）

1. **勿跑 `tools/sinica_pipeline/scrape_sinica.py`** —— 中研院小學堂对本机与海外均 "Access Restricted"，必失败。
2. **改 `characters.json` 严格按 `char` 匹配**，勿用 `trad` 回退（异体字抢匹配 bug 已踩过）。
3. **`cultural.json` 是平铺字典不是列表**，按 key 读写，别当 `d['characters']` 列表处理。
4. **保持紧凑 JSON 格式**，别格式化展开导致 diff 爆炸、合并冲突。
5. **重建后再测**，直接改 `index.html` 内联数据会被下次 `build_web.py` 覆盖。

---

## 9. 上下文 / 关联文档

- 总交接：`HANDOFF.md`
- 路线图与下阶段：`产品化路线图_对标与下阶段.md`
- 六书终审依据：`六书终审_P0人工清单再审.md` / `六书终审_声素复核_核对结论.md`
- 字形覆盖率：`tools/glyph_coverage_report.md`
- 隶书补源：`tools/rubbing_pipeline/HANDOFF_隶书字体.md`
- 文化生成/检查：`tools/gen_cultural.py` / `tools/check_cultural.py`
- 项目归属：老吴（吴自强）「虚拟经营」A 线 · 说文解字 App
