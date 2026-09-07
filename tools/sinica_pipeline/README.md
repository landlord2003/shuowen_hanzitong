# 中研院字形图「换源落地」管线（说文解字 App）

> 目的：把 App 的字形演变图从 **EVOBC（CC BY-NC-SA 4.0 非商业，禁止商用）** 换成
> **台湾中央研究院 漢字構形資料庫 / 小學堂（CC-BY-SA 2.5 TW，可商用）**，
> 消除上架侵权风险，并保留完整字形图体验。

## 一、授权结论（已核实）

- 中研院《漢字部件檢字系統／漢字構形資料庫》释出声明（cdp.sinica.edu.tw/cdphanzi/declare.htm）明确：
  「漢字字型」以 **CC-BY-SA 2.5 TW** 或 GFDL 1.2 释出，**允许商业使用**，
  条件：**①署名中央研究院；②衍生作品以相同授权（CC-BY-SA）释出**。
- 这意味着我们可以在产品中**商用**这些字形图，只要：
  1. 在 App 与产品页**署名「字形图：中央研究院漢字構形資料庫（CC BY-SA 2.5 TW）」**；
  2. 字形数据集（dataset.bin 及其来源）以 **CC-BY-SA 2.5 TW** 发布（与 App 代码的其他自有内容分离授权）。
- 注意：**CC-BY-SA 是「相同方式分享」**，不要求整个 App 开源，但要求**字形数据本身**保持该授权。
  这比 EVOBC 的「非商业」宽松且合规。

## 二、目录结构

```
tools/sinica_pipeline/
├── scrape_sinica.py   # 步骤1：从中研院小學堂抓取字形图 + 现代字映射 -> manifest.jsonl
├── pack_dataset.py    # 步骤2：将 manifest 打包为 CEDS0002 dataset.bin（与 App Reader 兼容）
├── gen_empty_bin.py   # 生成合规空 dataset.bin（154B，降级态用）
├── test_pack.py       # 格式自检：合成像素 -> 打包 -> 用 npm Reader 还原验证（需 npm 包，可选）
└── README.md
```

## 三、运行步骤（须在「可访问小學堂」的网络环境执行）

> ⚠️ 当前（2026-09-07）部分网络出口对小學堂有地理访问限制（返回 Access Restricted）。
> 若本机/服务器在该限制内，请在可访问环境运行本管线；产物 dataset.bin 与 App 均不依赖中研院网络。

### 步骤 1：抓图
```bash
pip install requests beautifulsoup4 pillow zstandard
python tools/sinica_pipeline/scrape_sinica.py --out-dir data/sinica_raw --max-order 14000
# 输出 data/sinica_raw/manifest.jsonl
#   每行: {"id":"<kaiOrder>","char":"<现代字>","script":"<oracle-bone|bronze|seal...>","img":"<png路径>"}
```
- 小學堂库段名：`jiaguwen`(甲骨文) / `jinwen`(金文) / `xiaozhuan`(小篆)；
  简牍帛书段名需实测（jiandu / chujian / boshu 候选）。
- 页面为 SPA，字形图由 JS/XHR 加载；若初始 HTML 无 `<img>`，需按 README「接口嗅探」
  章节改为调用其数据接口（见 scrape_sinica.py 注释）。

### 步骤 2：打包
```bash
python tools/sinica_pipeline/pack_dataset.py --manifest data/sinica_raw/manifest.jsonl --out data/dataset.bin
# 生成 data/dataset.bin（CEDS0002，App 直接 fetch 加载）
```

### 步骤 3：替换并验证
- 新 `data/dataset.bin` 直接生成到仓库内 `data/dataset.bin`（覆盖空包即可）；
- 本地起服务 `python -m http.server` 打开 index.html，点字查看「字形演变」应显示
  甲骨文/金文/小篆图（缺失的字自动降级为楷/繁文字）。

## 四、App 署名需同步修改（build_web.py / index.html）

将以下 EVOBC / CC BY-NC-SA 字样全部替换为：
- 副标题：`8105字·甲骨文到简体演变·字形来源·中央研究院漢字構形資料庫（CC BY-SA 2.5 TW）`
- 资料来源：`字形演变图：中央研究院漢字構形資料庫（CC BY-SA 2.5 TW，可商用，须署名）`
- 页脚：`字形来源：中央研究院漢字構形資料庫（CC BY-SA 2.5 TW）`

## 五、接口嗅探（当 SPA 初始 HTML 无图时）

小學堂后端为 ASP.NET，字形图经 XHR 返回。嗅探方法：
1. 浏览器开发者工具 → Network，过滤 `kaiOrder` / `img` / `.png` / `ashx` / `svc`；
2. 找到形如 `GetGlyph?kaiOrder=1&type=xiaozhuan` 的接口后用 requests 直连批量抓；
3. 或将 scrape_sinica.py 改为 requests 调用该接口返回 JSON 中的图片 URL。

## 六、回退方案（本环境无法取数时）

若暂时无法取得中研院数据，App 以「文字版」上线：
- 移除/清空 dataset.bin（App 自动降级为楷/繁文字 + AI 生成的演变文字说明，零侵权风险）；
- 待在可达网络跑通本管线后，一键补入真实字形图。
