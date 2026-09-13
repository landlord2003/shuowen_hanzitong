# zdic_pipeline — 汉典金文字形高清化管线

把汉典（zdic.net）的**金文 SVF 矢量**栅格化为 160px 高清位图，替换 `data/dataset.bin`
里的低清金文记录（原始缩略图仅 23x42 / 27x42 px，烤进 bin 后笔画断裂，显示「很虚」）。

## 依赖

- Python：`Pillow`、`zstandard`（受管解释器已具备）
- Node：`@resvg/resvg-js`（Rust/resvg 预编译二进制，**无需 Cairo**）

```bash
# Node 依赖（本目录下）
npm install --prefix . @resvg/resvg-js
```

> 为什么不用 svglib / cairosvg：reportlab 4.x 已移除原生 `_renderPM`，svglib 不可用；
> cairosvg 在 Windows 上需另装 GTK。`@resvg/resvg-js` 是纯预编译二进制，零系统依赖。

## 用法

```bash
# 1) 抓取 + 白底栅格化 + 重打包（一条命令跑完）
python fetch_zdic_jinwen.py all

# 只跑抓取/只跑重打包
python fetch_zdic_jinwen.py fetch
python fetch_zdic_jinwen.py repack

# 2) 单独重打包（换基线 bin 时用）
SWJ_BASE_BIN=/path/to/base.bin python repack_dataset.py
```

- `ROOT` 由 `__file__` 推导（`tools/zdic_pipeline/xxx.py` -> 仓库根），**跨机器可用**
- 基线 bin 默认**当前 `data/dataset.bin`**；要回退到某个备份可设环境变量 `SWJ_BASE_BIN`
- 缓存目录（`_plan2_svg/`、`_plan2c_cache/`、`_diag_out/`）会建在仓库根，均已被 .gitignore 忽略

## 两个必须知道的坑

1. **alpha 通道不可无脑信任**：白底渲染出的 PNG 仍带 alpha 且**全画布不透明**（alpha 恒 255），
   若拿 alpha 当遮罩会把整幅图判成墨迹（`nz = w*h`）。`img_proc.py` 仅在
   `0 < 不透明像素数 < 99.5%` 时才用 alpha，否则回退亮度阈值。
2. **汉典 SVG 自带近白水印**（`fill ≈ #fafbfa`，乞/上/下在左上、丁/七在右下）。
   别用「按 fill 颜色删路径」的正则——部分模板的水印不是自闭合 `<path/>`，正则会漏。
   **正解：resvg 传 `background:"#ffffff"` 白底渲染**，水印并入背景，Otsu 干净分离
   （实测每字只掉 5-29 px，全在角落 bbox，主体笔画一字不少）。
3. **Otsu 在已二值化图上会退化**：把 0/255 掩码再喂一次 `load_image_as_gray`，
   阈值会落在 0、四角判定 `0 < 0` 为假 -> 全部走 `v < t` -> **整批写成空图**。
   `img_proc.py` 已对 `len(uniq) <= 2` 的直方图走四角方向直取。
