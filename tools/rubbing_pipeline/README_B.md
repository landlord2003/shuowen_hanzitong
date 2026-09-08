# 字形图 B 路线自动化管线（公版拓片 SVG / 公版书影）

> 这是「说文解字」App 字形图 **B 路线** 的自动化实现：从**公版（Public Domain）或 CC BY-SA** 来源采集甲骨 / 金文 / 篆文等古文字字形，
> 矢量化 / 二值化后打包进 `data/dataset.bin`（CEDS0002 格式，与 App 浏览器端 reader 完全兼容）。
>
> **适用对象**：网络可达海外公共数据源的伙伴（中研院小學堂在本项目已被证实双向不可达，故本管线不走中研院）。
> **目标产物**：`data/dataset.bin` —— 覆盖 App 8105 字的甲骨/金文/篆文等位图，让 App 从「纯文字」升级为「图文版」。

---

## 1. 它能做什么

1. 读取 App 的 `data/characters.json`（8105 字，含 `id` / `char` / `trad`）。
2. 逐个字向一个或多个**数据源适配器**请求古文字字形图（甲骨 / 金文 / 篆文 / 简帛 / 隶）。
3. 把取回的图统一处理成 1 通道灰度二值图（黑字白底），写入中间 `manifest.jsonl`。
4. 复用已验证的 `../sinica_pipeline/pack_dataset.py` 打包为 `data/dataset.bin`。
5. 生成 `data/dataset.attribution.json` 记录各字形的来源与许可证，便于合规署名。

---

## 2. 已内置的数据源适配器

| 适配器 | 来源 | 许可证 | 覆盖脚本 | 说明 |
|---|---|---|---|---|
| `glyphwiki` | GlyphWiki.org | **CC BY-SA 2.1 JP** | **字源**（古形，诚实标注，**非篆文**） | 经 API 取 SVG 并栅格化；**须署名 + 衍生同授权**，自动写入 attribution。App 中显示为「字源」阶段（已接进渲染链路，位于演变行首位） |
| `wikimedia_seal` | Wikimedia Commons 小篆 SVG 类 | **公版（PD）** 或 CC（按文件） | 篆文(seal) | 经 Commons API 拉取 SVG 并栅格化；覆盖面取决于 Commons 类目 |
| `scan_trace` | Internet Archive 公版书影（罗振玉《殷虚书契》、說文篆書本、金文集古录等） | **公版（PD）** | 甲骨 / 金文 / 篆文 | 按 `bbox_map.json`（字→页码+坐标）自动裁剪+二值化 |

> ⚠️ **甲骨文 / 金文** 目前没有可靠的「全字覆盖公版矢量源」，主要走 `scan_trace`（书影裁剪）。
> `bbox_map.json` 可由伙伴用 IA 提供的 OCR/文本层自动生成，或手工补录；格式见第 5 节。

> 📌 **字源 vs 篆文（重要诚实标注）**：GlyphWiki 给出的是该字的标准/旧字形（historical form），**不是**严格的甲骨文/金文/篆文真迹。
> 因此在 App 中它被单独标注为「字源」阶段，绝不冒充实物的「篆文」。真·篆文仍由 `wikimedia_seal` / `scan_trace`（B 路线，需海外网络）补全。

---

## 3. 环境准备（一次性）

```bash
cd tools/rubbing_pipeline
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` 依赖：`requests`、`Pillow`、`zstandard`、`cairosvg`（SVG→PNG；若不可用，脚本自动回退到 `rsvg-convert` / `inkscape`）。

---

## 4. 运行（三选一 / 组合）

```bash
# (A) 仅小篆，走 Wikimedia 公版 SVG（最快出活）
python pipeline.py --chars ../../data/characters.json \
    --sources wikimedia_seal \
    --out ../../data/dataset.bin

# (B) 小篆 + GlyphWiki（CC BY-SA，覆盖面更广，自动署名）
python pipeline.py --chars ../../data/characters.json \
    --sources wikimedia_seal glyphwiki \
    --out ../../data/dataset.bin

# (C) 甲骨/金文/篆文 走公版书影裁剪（需先准备好 bbox_map.json）
python pipeline.py --chars ../../data/characters.json \
    --sources scan_trace \
    --scan-root /path/to/ia_books \
    --bbox-map bbox_map.json \
    --out ../../data/dataset.bin
```

组合多个源（推荐，覆盖最大化）：

```bash
python pipeline.py --chars ../../data/characters.json \
    --sources wikimedia_seal glyphwiki scan_trace \
    --scan-root /path/to/ia_books --bbox-map bbox_map.json \
    --out ../../data/dataset.bin
```

产出校验：

```bash
python pipeline.py --self-test      # 离线合成数据跑通打包，不依赖网络
```

---

## 5. `bbox_map.json` 格式（scan_trace 用）

`scan_trace` 需要一份「字 → 书影页码 + 包围盒」映射。结构：

```json
{
  "一":  {"book": "yinxu_shuqi", "page": 12, "bbox": [120, 80, 160, 140]},
  "水":  {"book": "yinxu_shuqi", "page": 33, "bbox": [200, 90, 250, 160]},
  "鼎":  {"book": "jigu_lu",     "page": 7,  "bbox": [300, 110, 380, 220]}
}
```

- `book` 对应 `--scan-root` 下的子目录 / 文件名（不含扩展名）。
- `page` 为 0 基页码（PDF 渲染后按页取图）。
- `bbox` 为 `[x0, y0, x1, y1]`，像素坐标，仅裁剪该区域再二值化。

伙伴可用 IA 下载书籍后，用我们提供的 `helpers/build_bbox_from_ocr.py`（占位模板，按 IA OCR XML 自动对齐）生成初版映射，再人工补正。

---

## 6. 合规与署名（重要）

- **公版源**（Wikimedia PD / IA 公版书影）：自由商用，建议保留来源说明（自动写入 `dataset.attribution.json`）。
- **GlyphWiki（CC BY-SA 2.1 JP）**：可商用，但**必须署名 + 衍生同授权**。App 已在 `data/dataset-reader.js` 与页面 footer 固化「中央研究院漢字構形資料庫（CC BY-SA 2.5 TW）」署名；
  启用 `glyphwiki` 源时，请额外在 App「数据来源」说明中追加 GlyphWiki 署名，并确保衍生包以 CC BY-SA 发布。
- **严禁**：把已下架的 EVOBC（CC BY-NC-SA 4.0 非商业）数据拷回 `dataset.bin`。

---

## 7. 与 A 路线的关系（已重订）

> ⚠️ **重要更正（2026-09-08）**：原计划 A 路线使用 **BabelStone 字体**渲染古文字。实测发现 BabelStone **PUA 字体没有任何「标准字 → 古字形」映射表**（cmap 仅含 6024 个 PUA 码位，普通汉字码位无对应字形），因此**无法**从正常汉字文本渲染出甲骨/金文/篆文。A 路线已**停用 BabelStone 方案**。

- **A 路线（现行·GlyphWiki「字源」阶段）**：本机沙箱即可直连 GlyphWiki（HTTP 200 可达），逐字拉取 SVG → `resvg` 栅格化 → 打包进 `dataset.bin`，显示为「字源」阶段。**零真迹、即时可用、可商用（CC BY-SA 2.1 JP，须署名+同授权）**。这是当前已落地的「图文版」第一步。
- **B 路线（本管线）**：产出真迹拓片 / 公版书影位图（甲骨/金文/篆文），质量最高，但需海外可达网络（Wikimedia / Internet Archive 在本机沙箱被墙，需伙伴环境运行）。
- 二者**不冲突、互补**：A 先交付「字源」覆盖；B 后续补全甲骨→隶真迹。合并方式见第 9 节 `merge_bins.py`。

### A 路线（GlyphWiki 字源）本地运行命令

```bash
# 生成含「字源」阶段的 dataset.bin（已实测：沙箱直连 GlyphWiki 可用）
python tools/rubbing_pipeline/pipeline.py \
    --chars data/characters.json \
    --sources glyphwiki \
    --out data/dataset.bin
```

---

## 8. 故障排查

| 现象 | 原因 / 对策 |
|---|---|
| `ImportError: No module named cairosvg` | 装 `cairosvg`；或系统装 `librsvg`/`inkscape` 后脚本自动回退 |
| Wikimedia 某字取不到 | Commons 该类目本就缺该字，属正常；换 `glyphwiki` 补 |
| `scan_trace` 全空 | 检查 `bbox_map.json` 的 `book` 是否与 `--scan-root` 下文件名一致、`page` 是否从 0 计 |
| 生成的 bin App 不显示 | 用 `python -m http.server` 起服务访问（file:// 下 fetch 受限）；确认 `dataset.bin` 含记录（非 154B 空包） |

---

## 9. A + B 合并（最终交付单一 bin）

A 路线先产出「字源」bin，B 路线后续产出甲骨/金文/篆真迹 bin。App 只认**一个** `data/dataset.bin`，故用 `merge_bins.py` 合并：

```bash
# 假设 A 已产出 data/dataset_glyphwiki.bin，B 已产出 data/dataset_b_route.bin
python tools/rubbing_pipeline/merge_bins.py \
    --bins data/dataset_glyphwiki.bin,data/dataset_b_route.bin \
    --out data/dataset.bin
```

- 合并按 key（`id/前缀脚本名`）去重，先出现的优先（建议 A 在前、B 在后，B 的真迹补齐甲骨→隶）。
- `characters` 映射取并集。
- 合并后用相同方式起本地服务验证 App 演变行是否同时出现「字源 / 甲骨 / 金文 / 篆 / 隶 / 楷」。

> 💡 当前（2026-09-08）`data/dataset.bin` 已是 A 路线（GlyphWiki 字源）产物；B 路线海外跑通后，再执行一次合并即可补全真迹，无需改动 App 代码。
