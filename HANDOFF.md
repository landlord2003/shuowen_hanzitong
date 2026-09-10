# 说文解字 App — 交接文档（字形数据已落地 · 2026-09-10 版）

> 写给接手的机器 / 同事。**当前仓库已可合规商用（图文版）**，字形数据已通过多源落地，无需再跑旧的中研院抓取管线。
> 本文件纠正了早期版本"dataset.bin=154B 空包、须跑 sinica_pipeline 抓中研院"的错误表述——那条路径已失效。

---

## 0. TL;DR（一句话）

字形数据**已落地**：`data/dataset.bin`（9.67MB，CEDS/zstd 字源位图库）覆盖字源图 100%，叠加三款开源古文字字体（甲骨/金文 OFL + 崇羲篆体 CC-BY-ND-3.0-TW），App 已是「图文版」。

**⚠️ 旧管线 `tools/sinica_pipeline/` 已废弃**：它依赖台湾中研院 小學堂（`xiaoxue.iis.sinica.edu.tw`），该站**对本机与海外均返回 "Access Restricted" 地理封锁**，抓图步骤必失败。**不要再跑 `scrape_sinica.py`**。

**你只需做一件事（如需补隶书）**：在**可达环境**取一版干净可商用隶书字体，丢进 `data/fonts/clerical-script.ttf`（或 `.otf`）即自动生效，详见 `tools/rubbing_pipeline/HANDOFF_隶书字体.md`。

---

## 1. 当前仓库状态（2026-09-10）

- 主分支：`main`，已连 Gitee：`https://gitee.com/landlord2003/shuo-wen_-jie-zi.git`
- 字形数据：**已落地**
  - `data/dataset.bin` = 9.67MB CEDS 库，**字源图（GlyphWiki 体系）覆盖 8105/8105 = 100%**
  - 三款 bundled 古文字字体（`data/fonts/`）：`oracle-bone.otf`/`bronze-script.otf`（cluesurf/mark，OFL）、`chongxi-seal.otf`（崇羲篆体，CC-BY-ND-3.0-TW）
- 六书：已通过人工终审回写（`六书终审_P0人工清单再审.md` + `六书终审_声素复核_核对结论.md`），`characters.json` 含 `liushu_remark` 留痕。
- 授权署名：App（副标题 / 数据来源卡片 / 页脚 / 详情）已内置各来源署名，**勿删**。
- 全仓无 EVOBC（CC BY-NC-SA 4.0）残留——旧 NC 字形源已下架换源，商业化阻塞已解除。

---

## 1.1 两个数据文件 —— 别混为一谈（关键）

| 文件 | 性质 | 来源 | 本仓库状态 |
|---|---|---|---|
| `data/characters.json` | **文字内容库**（8105 字，含 modern / liushu / shuowen / duan_note 等释义文本） | 通用规范汉字表 + 说文整理 + AI 生成 | 已落地，含六书终审回写 |
| `data/dataset.bin` | **字形图库**（字源位图，9.67MB CEDS） | GlyphWiki 字源体系 | ✅ 已落地（字源 100%） |
| `data/fonts/*.otf` | **古文字字体兜底**（甲骨/金文/篆） | cluesurf/mark(OFL) / 崇羲(CC-BY-ND-3.0-TW) | ✅ 已入库（.gitignore 已放行） |

- 补完字形后 App **仍是 8105 字**，从「纯文字」升级为「图文版」。
- 想扩到中研院 13779 字头规模，是**另一项独立任务**（扩 `characters.json` 文字内容库），与本管线下载无直接依赖。

---

## 2. 字形真实来源（授权清晰，可商用）

| 阶段 | 数据来源 | 许可证 | 覆盖（8105 内） |
|---|---|---|---|
| 字源图 | GlyphWiki 字源体系（dataset.bin） | CC BY-SA 2.1 JP | 100% (8105) |
| 甲骨文 | 中研院/小學堂体系 + cluesurf/mark 字体兜底 | CC BY-SA 2.5 TW / OFL | 10.2% (824) |
| 金文 | 中研院/小學堂体系 + cluesurf/mark 字体兜底 | CC BY-SA 2.5 TW / OFL | 17.3% (1399) |
| 篆书 | 中研院/小學堂体系 + 崇羲篆体字体兜底 | CC BY-SA 2.5 TW / CC-BY-ND-3.0-TW | 56.1% (4547) |
| 简牍帛书 | 中研院/小學堂体系 | CC BY-SA 2.5 TW | 4.0% (327) |
| 隶书 | **缺失，待补** | — | 0% |

> 注：甲骨/金/简帛/篆的「中研院/小學堂体系」指 dataset.bin 内已落地的真迹位图；中研院**在线接口**已不可达（地理封锁），但数据已随 dataset.bin 入库，无需再联网取。

---

## 3. 环境与依赖

- **Python 3.13**（已验证可跑构建）
- 字形数据不依赖任何外部网络：dataset.bin + 字体均随仓库分发，pull 后直接打开 `index.html` 即可。
- 依赖安装（仅重建数据时）：`pip install requests beautifulsoup4 pillow zstandard`（见 `requirements.txt`）。

---

## 4. 部署（接手者）

```bash
git clone https://gitee.com/landlord2003/shuo-wen_-jie-zi.git
# 或已 clone： git pull
# 起本地静态服务（字形数据经 HTTP 加载，不能直接 file:// 双击）
python -m http.server 8765 --bind 127.0.0.1
# 浏览器开 http://127.0.0.1:8765/index.html
```

- `data/dataset.bin` 与 `data/fonts/*.otf` **均已入库**，pull 后无需任何补数据步骤。
- 不要提交：`*.pdf`、`*.bak`、`obsidian/`、`data/sinica_raw/`（中间产物）。

---

## 5. 已废弃：旧 sinica_pipeline（勿跑）

`tools/sinica_pipeline/` 早期设计用于抓中研院 小學堂字形图。因小學堂对本机与海外均返回 **"Access Restricted" 地理封锁**，该管线**当前无法工作**。

- 不要跑 `scrape_sinica.py`（必失败，且会误以为补完图需联网中研院）。
- 若未来中研院可达，管线格式细节见 `tools/sinica_pipeline/README.md`（仅作存档）。
- 字形数据已通过其他渠道落地，**无需复活该管线**。

---

## 6. 授权与合规（重要，别踩红线）

- 字形图主源：GlyphWiki（**CC BY-SA 2.1 JP**，可商用，须署名 + 衍生同授权）。
- 甲骨/金文字体：cluesurf/mark（**OFL**，可商用，须保留版权声明）。
- 篆书字体：崇羲篆体（**CC-BY-ND-3.0-TW**，可商用，须署名，**禁止修改**）。
- 旧 EVOBC（CC BY-NC-SA 4.0）**已下架换源**，本仓库无 NC 残留，可商用。
- App 已内置上述署名，**不要删**。
- 隶书字体待补：须取干净可商用源（首选中研院/崇羲隶书 CC BY-SA 2.5 TW，或逐项核验非 NC 的字体），详见 `tools/rubbing_pipeline/HANDOFF_隶书字体.md`。

---

## 7. 回退方案

若某字体文件损坏：删 `data/fonts/clerical-script.*` 等对应文件，App 自动降级为「该阶段待补全」，其余照常；dataset.bin 字源图不受影响。

---

## 8. 上下文 / 关联文档

- 项目归属：老吴（吴自强）「虚拟经营」课题 **A 线 · 说文解字 App**
- `字形图授权核查报告.md`：授权结论与整改清单（已解除 NC 阻塞）
- `六书终审_P0人工清单再审.md` / `六书终审_声素复核_核对结论.md`：六书人工终审依据
- `tools/glyph_coverage_report.md`：字形阶段覆盖率（含历史基准对比）
- `tools/rubbing_pipeline/HANDOFF_隶书字体.md`：隶书补源操作指南
- `产品化路线图_对标与下阶段.md`：路线图对标与下阶段工作内容
