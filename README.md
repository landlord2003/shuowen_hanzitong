# 说文解字 · 汉字知识库

一个本地离线可用的汉字知识工具，收录 **3500 个常用汉字**（《通用规范汉字表》一级字表），提供字形演变、说文原文、段玉裁注、六书、本义今义、后起字溯源等完整信息。

## ✨ 功能特性

- **3500 常用字**：拼音、部首、笔画、六书、繁体对照
- **字形演变**：甲骨文 → 金文 → 简牍帛书 → 篆书 → 隶书 → 楷书，6 书体本地离线渲染
- **说文原文**：2763 字精确《说文解字》原文 + 反切
- **段玉裁注**：2631 字段玉裁《说文解字注》全文
- **异体重文**：古文、籀文等异体字形
- **后起字溯源**：《玉篇》（543年）、《广韵》（1008年）、《康熙字典》（1716年）三源对照
- **来源标注**：每个字段标注出处，权威数据与 AI 生成内容明确区分
- **音译字甄别**：明确标注"啡=唾声≠咖啡"等同名异义陷阱

## 🚀 快速开始

### 方式一：一键启动（推荐）

双击 `start.bat`，自动启动本地服务器并打开浏览器。

### 方式二：手动启动

```bash
# 需要 Python 3（仅起静态服务器）
python -m http.server 8765 --bind 127.0.0.1
# 浏览器打开 http://127.0.0.1:8765
```

> ⚠️ 字形数据（`data/dataset.bin`，35MB）需通过 HTTP 加载，**不能直接双击 `index.html`**（`file://` 协议会被浏览器拦截）。

## 📦 目录结构

```
├── index.html              # 最终产物（单文件，内嵌 3500 字数据 + 字形渲染）
├── start.bat               # 一键启动脚本
├── data/
│   ├── characters.json     # 3500 字完整数据（含反切/段注/溯源）
│   ├── dataset.bin         # 字形数据集（EVOBC，35MB）
│   ├── dataset-reader.js   # 浏览器端读取器（IIFE）
│   └── fzstd.umd.js        # 纯 JS zstd 解压器
├── build_web.py            # 主构建脚本：生成 index.html
├── build_enrich.py         # 补全反切/段注/异体
├── build_trace.py          # 补后起字溯源（玉篇/广韵/康熙）
├── build_trace_note.py     # 音译字/新造字甄别标注
├── build_final.py          # 合并数据源
├── build_from_shuowen.py   # 从说文推导六书/本义
├── build_assets.py         # 生成 dataset-reader.js
├── merge_shuowen.py        # 说文数据库匹配
└── requirements.txt        # 数据重建依赖
```

## 📚 数据来源与许可

| 数据 | 来源 | 许可证 | 说明 |
|---|---|---|---|
| 说文原文 / 反切 / 段注 / 异体 | [shuowenjiezi/shuowen](https://github.com/shuowenjiezi/shuowen) | Apache 2.0 | 2763 字精确原文 |
| 字形图 | [EVOBC](https://github.com/RomanticGodVAN/character-Evolution-Dataset) | **CC BY-NC-SA 4.0** | 甲骨文/金文/篆书等古字形，经 [character-evolution-dataset-1bit](https://github.com/leonsilicon/character-evolution-dataset-1bit) 封装 |
| 后起字溯源 | 《玉篇》《广韵》《康熙字典》 | 公版古籍 | 来源 [mengzhiwu/chtxt](https://github.com/mengzhiwu/chtxt)、[omnilingual/han-chem](https://github.com/omnilingual/han-chem) |
| 六书 / 本义 / 今义 / 演变 | AI 生成 | 自有 | 页面已标注"待核验" |

> **⚠️ 重要许可说明**：字形图底层为 EVOBC 数据集（**CC BY-NC-SA 4.0**），其中 **NC = 非商业用途**。本项目整体受此约束，**不可用于商业用途**；衍生作品需以相同协议（CC BY-NC-SA 4.0）发布并署名 EVOBC。商业化需先获得 EVOBC 作者授权或更换字形数据源。

## 🔧 数据重建（可选）

仅"查看页面"无需重建。如需修改/扩展数据：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 重建页面
python build_web.py
```

完整重建流程（从零生成 3500 字数据）需准备数据源（说文数据库、字书数据），详见各构建脚本头部注释。

## 📄 许可证

本项目（含代码与数据）整体采用 **CC BY-NC-SA 4.0**（署名-非商业-相同方式共享）发布，受 EVOBC 字形数据的许可证约束。详见 [LICENSE](LICENSE)。
