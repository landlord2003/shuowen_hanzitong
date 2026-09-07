# 说文解字 App — 交接文档（字形图「换源落地」补全）

> 写给接手的机器 / 同事。**目标**：把甲骨 / 金文 / 篆 / 隶等位图补进 App，让「字形演变」区从纯文字降级态变成完整字形图。
> 当前仓库已可合规商用（文字版），只差这一步。

---

## 0. TL;DR（一句话）

原字形图来自 **EVOBC（CC BY-NC-SA 4.0 非商业，禁止商用）**，已下架；换成 **台湾中研院 漢字構形资料库 / 小學堂（CC BY-SA 2.5 TW，可商用）** 后，因本机网络取不到数据，`data/dataset.bin` 现为 **154B 空包**（App 自动降级为纯文字）。

**你只需做一件事**：在**可联网环境**跑 `tools/sinica_pipeline/` 抓中研院字形图 → 打包 → 覆盖 `dataset.bin` → 验证 → 提交推送。

---

## 1. 当前仓库状态

- 主分支：`main`，已连 Gitee：`https://gitee.com/landlord2003/shuo-wen_-jie-zi.git`
- 本次已提交（换源合规化）：`build_assets.py` / `build_final.py` / `build_web.py` / `data/characters.json` / `data/dataset-reader.js` / `data/dataset.bin`(空包) / `index.html`
- 字形图：**缺失**（dataset.bin = 154B 空包）。App 正常工作，仅「字形演变」区只显示「繁→简」文字，无位图。
- 授权署名：已在 App（副标题 / 数据来源 / 页脚 / 详情）内置「中央研究院漢字構形资料庫（CC BY-SA 2.5 TW）」，**勿删**。
- 全仓 NC 残留扫描：`index.html` / `dataset-reader.js` / `characters.json` / `build_web.py` 均为 0 命中。

---

## 1.1 两个数据文件 —— 别混为一谈（关键）

App 的「数据」其实分**两类**，本管线只处理其中一类。**务必区分**，否则会误以为补完图会自动变成 13779 字：

| 文件 | 性质 | 来源 | 本管线是否改 |
|---|---|---|---|
| `data/characters.json` | **文字内容库**（8105 字，含 modern / liushu / shuowen / duan_note 等释义文本） | 通用规范汉字表 + 说文整理 | ❌ 不改 |
| `data/dataset.bin` | **字形图库**（甲骨/金文/篆/隶位图，现为 154B 空包） | 中研院 小學堂 | ✅ 本管线填它 |

- 跑完 `scrape + pack` 后，**只覆盖 `dataset.bin`**，`characters.json` 一字不动。
- 因此补完图后，App **仍是 8105 字**，只是从「纯文字」升级为「图文版」。
- 想扩到中研院 13779 字头规模，是**另一项独立任务**：须先把 `characters.json` 文字内容扩到 13779 字（需释义文本源，如《汉语大字典》/中研院字头表）；**注意中研院只给字形图、不给释义文本，故扩字内容库不依赖本管线下载**，但扩完之后本管线才能为新字匹配图形。

## 2. 你要做的事（目标）

补全甲骨 / 金文 / 小篆 / 简帛 / 隶书位图，让 App 显示完整字形演变（**字数仍是 8105，字形图变完整**）。

---

## 3. 环境与依赖

- **Python 3.10+**（3.13 已验证可跑管线）
- **关键网络要求**：运行 `scrape_sinica.py` 的机器必须能访问 `https://xiaoxue.iis.sinica.edu.tw`（台湾中研院 小學堂）。
  - ⚠️ **部分网络出口对台湾小學堂有地理限制（返回 "Access Restricted"）**。务必在**可达环境**运行抓图步骤。
  - 产物 `dataset.bin` 与 App 本身**不依赖**中研院网络，打包后随便哪台机器用。
- 依赖安装：`pip install requests beautifulsoup4 pillow zstandard`

---

## 4. 执行步骤（在仓库根目录 `说文解字/` 下）

```bash
# ① 抓图（可联网环境，耗时依数据量，数分钟~数十分钟）
python tools/sinica_pipeline/scrape_sinica.py --out-dir data/sinica_raw --max-order 14000
#   输出 data/sinica_raw/manifest.jsonl
#   每行: {"id":"<kaiOrder>","char":"<现代字>","script":"<oracle-bone|bronze|seal...>","img":"<png路径>"}

# ② 打包（覆盖空包）
python tools/sinica_pipeline/pack_dataset.py --manifest data/sinica_raw/manifest.jsonl --out data/dataset.bin
#   生成 data/dataset.bin（CEDS0002，App 直接 fetch 加载）

# ③ 验证
python -m http.server 8099
#   浏览器开 http://127.0.0.1:8099/index.html ，点任意字
#   「字形演变」应显示 甲骨/金文/小篆 图；
#   中研院没收录的字会自动降级为楷/繁文字，属正常。
```

---

## 5. SPA 接口嗅探（若步骤①抓不到图）

小學堂后端是 ASP.NET，字形图经 **XHR** 返回，初始 HTML 可能无 `<img>`。详见 `tools/sinica_pipeline/README.md` 第五节：

1. 浏览器 DevTools → Network，过滤 `kaiOrder` / `img` / `.png` / `ashx` / `svc`；
2. 找到形如 `GetGlyph?kaiOrder=1&type=xiaozhuan` 的接口后，把 `scrape_sinica.py` 改为 requests 直连该接口取图；
3. 库段名：`jiaguwen`(甲骨文) / `jinwen`(金文) / `xiaozhuan`(小篆)；简牍帛书段名候选 `jiandu` / `chujian` / `boshu`。

---

## 6. 授权与合规（重要，别踩红线）

- 字形图来源：中研院 漢字構形资料库 / 小學堂，**CC BY-SA 2.5 TW**（可商用，条件：①署名中央研究院 ②衍生作品同授权）。
- App 已内置署名，**不要删**。
- **`dataset.bin` 须以 CC BY-SA 2.5 TW 发布**（与 App 自有代码分离授权，不要求整个 App 开源）。
- 🚫 **禁止**把旧 EVOBC（CC BY-NC-SA 4.0）数据拷回 `dataset.bin`：
  - `build_assets.py` 的「拷 bin」步骤**已加固**，重建时不会自动回灌 NC 数据；
  - 手动也不要加回去。

---

## 7. 提交与推送

```bash
git add data/dataset.bin          # 完整字形版（产品资源，必须提交）
git commit -m "补全中研院字形图(CC BY-SA 2.5 TW)，dataset.bin 接入甲骨/金文/小篆"
git push origin main
```

- **不要提交**：`fonts/`（方正字体版权）、`*.pdf`、`*.bak`、`obsidian/`、`data/sinica_raw/`（中间产物，已 gitignore）。
- `data/dataset.bin` **必须提交**（是产品资源，空包时也要在）。
- 若修改了管线脚本，连同 `tools/sinica_pipeline/` 一起提交。

---

## 8. 回退方案

若暂时无法取得中研院数据，**保持空包即可**——App 文字版零侵权可上线；将来在可达网络跑通管线，一键补入真实字形图。

---

## 9. 上下文 / 关联文档

- 项目归属：老吴（吴自强）「虚拟经营」课题 **A 线 · 说文解字 App**
- `字形图授权核查报告.md`：授权结论与整改清单（结论已由 🔴 改为 🟢）
- `tools/sinica_pipeline/README.md`：管线格式细节、SPA 嗅探、回退
