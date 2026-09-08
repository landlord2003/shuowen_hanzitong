# B 路线海外机器执行交接（wikimedia_seal + scan_trace）

> 目标：在**海外可达网络**的机器上，跑通「说文解字」App 的甲骨 / 金文 / 篆文**真迹**字形采集，
> 产出 `data/dataset_b_route.bin`（B 路线），与本机已有的 A 路线（GlyphWiki「字源」）合并，
> 让 App 演变行从「纯文字 / 字源」升级为「含真迹」。
>
> 本文件给「另一台先试的机器」看，步骤自包含。

---

## 0. 前置条件（务必先确认）

- Python 3.10+（本机 3.13 实测可用）
- **海外网络**：能直连 `upload.wikimedia.org` / `commons.wikimedia.org` 与 `archive.org`
  - ⚠️ 本机沙箱被 GFW 墙了这俩源，所以**必须在海外机器跑**；这不是服务器宕机，是墙
- 🚫 **不要走中研院**：汉字構形資料庫 / 小學堂已证实**双向不可达**（大陆直连 + 海外直连都 block），本管线**不含中研院源**，也无需求

---

## 1. 取代码

```bash
git clone https://gitee.com/landlord2003/shuo-wen_-jie-zi.git
cd shuo-wen_-jie-zi
```

> clone 后请确认 `data/characters.json`（8105 字，含 id/char/trad）在场，
> 以及 `tools/rubbing_pipeline/` 完整（pipeline.py / sources.py / adapters/ / merge_bins.py / requirements.txt）。
> 缺字符表则管线无法跑。

---

## 2. 装依赖

```bash
cd tools/rubbing_pipeline
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 依赖：requests / Pillow / zstandard / resvg_py
# resvg_py 自包含原生库，Windows 无需 GTK/cairo；若缺则用 cairosvg / rsvg-convert / inkscape 自动回退
```

先跑离线自检（不依赖网络，确认打包链路通）：

```bash
python pipeline.py --self-test
```

---

## 3. 跑 B 路线（两种源，可单独或组合）

### 3a. 小篆快速出活（推荐先试 —— Wikimedia 公版 SVG）

```bash
python pipeline.py --chars ../../data/characters.json \
    --sources wikimedia_seal \
    --out ../../data/dataset_b_route.bin
```

- 产出**真·小篆**；覆盖面取决于 Commons 类目（某字取不到属正常，换 glyphwiki 补）
- 这是验证「海外线路是否真通」的最快一步

### 3b. 甲骨 / 金文 / 篆 走公版书影（需先备 bbox_map.json）

```bash
python pipeline.py --chars ../../data/characters.json \
    --sources scan_trace \
    --scan-root /path/to/ia_books \
    --bbox-map bbox_map.json \
    --out ../../data/dataset_b_route.bin
```

- 书影从 Internet Archive 下（罗振玉《殷虚书契》、說文篆書本、金文集古录等，均公版 PD）
- `bbox_map.json` 格式见下「附 A」；可用 IA 的 OCR/文本层半自动生成初版再人工补正

### 组合（覆盖最大化，推荐正式跑）

```bash
python pipeline.py --chars ../../data/characters.json \
    --sources wikimedia_seal glyphwiki scan_trace \
    --scan-root /path/to/ia_books --bbox-map bbox_map.json \
    --out ../../data/dataset_b_route.bin
```

---

## 4. 与 A 路线合并成单一 bin

App 只认**一个** `data/dataset.bin`。合并（A 在前、B 在后，B 真迹补齐甲骨→隶）：

```bash
python tools/rubbing_pipeline/merge_bins.py \
    --bins data/dataset_glyphwiki.bin,data/dataset_b_route.bin \
    --out data/dataset.bin
```

> - 本机已生成 A 路线 bin = `data/dataset.bin`（GlyphWiki 字源，全 8105 字）。
> - 海外机器若只跑了 B：把 `dataset_b_route.bin` 传回本机，与本机 A bin 合并；
>   或海外机器也跑一次 `--sources glyphwiki` 生成 A bin 再合并。

---

## 5. 验证

```bash
cd 项目根
python -m http.server 8931
# 浏览器开 http://localhost:8931 ，点任一字，看演变行是否出现 篆 / 甲骨 / 金文
```

> ⚠️ 必须用 http.server 起服务访问；`file://` 下 fetch bin 受限，App 不显示。
> 确认 bin 非 154B 空包（空包 = 啥都没采到）。

---

## 6. 合规署名（商用前置，务必做）

- `wikimedia_seal`：Commons 各文件按各自许可证（多为公版 / CC），自动写入 `dataset.attribution.json`
- `glyphwiki`（若启用）：CC BY-SA 2.1 JP，**须署名 + 衍生同授权**，App 已固化署名
- 🚫 **严禁**把已下架的 EVOBC（CC BY-NC-SA 4.0 非商业）数据拷回 `dataset.bin`

---

## 7. 排错速查

| 现象 | 对策 |
|---|---|
| `ImportError: resvg_py` | `pip install resvg_py`；或装 `cairosvg`/`librsvg`/`inkscape` 自动回退 |
| Wikimedia 某字取不到 | Commons 该类目本就缺，属正常；换 `glyphwiki` 补 |
| `scan_trace` 全空 | 检查 `bbox_map.json` 的 `book` 与 `--scan-root` 下文件名一致、`page` 从 0 计 |
| bin App 不显示 | 用 `http.server` 起服务（file:// 受限）；确认 bin 非 154B 空包 |
| 海外仍取不到 | 先跑 3a 单源定位是网络问题还是 Commons 缺字；中研院不在范围内 |

---

## 附 A：`bbox_map.json` 格式（scan_trace 用）

```json
{
  "一":  {"book": "yinxu_shuqi", "page": 12, "bbox": [120, 80, 160, 140]},
  "水":  {"book": "yinxu_shuqi", "page": 33, "bbox": [200, 90, 250, 160]},
  "鼎":  {"book": "jigu_lu",     "page": 7,  "bbox": [300, 110, 380, 220]}
}
```

- `book` 对应 `--scan-root` 下的子目录 / 文件名（不含扩展名）
- `page` 为 0 基页码（PDF 渲染后按页取图）
- `bbox` 为 `[x0, y0, x1, y1]` 像素坐标，仅裁剪该区域再二值化

---

完成跑通后，把 `data/dataset_b_route.bin`（或合并后的 `data/dataset.bin`）传回本机即可。
如在某源卡住，保留终端报错文本回传，便于定位是网络还是数据源覆盖问题。
