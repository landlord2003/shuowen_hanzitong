# -*- coding: utf-8 -*-
"""构建 B 路线交付物：
   1) shuowen_b_route_package.zip  —— 海外伙伴下载即跑的管线包
   2) B路线操作手册.pdf           —— 详细步骤（中文）
"""
import os, shutil, zipfile, datetime

ROOT = r"D:/WorkBuddy/projects/说文解字"
PKG_ROOT = os.path.join(ROOT, "_broute_pkg", "shuowen_broute")
ZIP_PATH = os.path.join(ROOT, "shuowen_b_route_package.zip")
PDF_PATH = os.path.join(ROOT, "B路线操作手册.pdf")

# ---------- 1. 清理并建目录 ----------
if os.path.exists(os.path.join(ROOT, "_broute_pkg")):
    shutil.rmtree(os.path.join(ROOT, "_broute_pkg"))
os.makedirs(PKG_ROOT, exist_ok=True)

# ---------- 2. 拷贝 rubbing_pipeline（剔除中间产物） ----------
src_rp = os.path.join(ROOT, "tools", "rubbing_pipeline")
dst_rp = os.path.join(PKG_ROOT, "tools", "rubbing_pipeline")
os.makedirs(dst_rp, exist_ok=True)
EXCLUDE_DIRS = {"__pycache__", "_glyph_tmp", "_selftest_tmp", ".pytest_cache"}
def _skip_file(name):
    return (name in {"dataset.attribution.json"}
            or name.startswith(("_probe", "_test_", "_selftest_", "_glyph")))
for name in sorted(os.listdir(src_rp)):
    p = os.path.join(src_rp, name)
    if name in EXCLUDE_DIRS:
        continue
    if os.path.isdir(p):
        shutil.copytree(p, os.path.join(dst_rp, name),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    else:
        if _skip_file(name):
            continue
        shutil.copy2(p, os.path.join(dst_rp, name))

# ---------- 3. 拷贝 sinica_pipeline/pack_dataset.py（管线依赖） ----------
src_sp = os.path.join(ROOT, "tools", "sinica_pipeline")
dst_sp = os.path.join(PKG_ROOT, "tools", "sinica_pipeline")
os.makedirs(dst_sp, exist_ok=True)
for f in ["pack_dataset.py", "README.md"]:
    s = os.path.join(src_sp, f)
    if os.path.exists(s):
        shutil.copy2(s, os.path.join(dst_sp, f))

# ---------- 4. 拷贝字符清单 characters.json（--chars 必需） ----------
os.makedirs(os.path.join(PKG_ROOT, "data"), exist_ok=True)
shutil.copy2(os.path.join(ROOT, "data", "characters.json"),
             os.path.join(PKG_ROOT, "data", "characters.json"))

# ---------- 5. 一键运行脚本 ----------
bat = r'''@echo off
REM ============================================================
REM  说文解字 App 字形图 B 路线（wikimedia_seal）一键运行
REM  作用：自动从 Wikimedia Commons 抓取「小篆」SVG 并打包
REM        成 data/dataset.bin，无需你手动下载任何数据文件。
REM ============================================================
cd /d "%~dp0"

if not exist .venv (
  echo [1/3] 首次运行：创建虚拟环境并安装依赖（需联网）...
  python -m venv .venv
  call .venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)

echo [2/3] 开始抓取小篆字形（约 8105 字，依网络 10~40 分钟）...
python pipeline.py --chars ../../data/characters.json --sources wikimedia_seal --out ../../data/dataset.bin

echo [3/3] 完成！请把 data/dataset.bin 发回给老吴（微信/邮件/网盘均可）。
pause
'''
with open(os.path.join(dst_rp, "run_b_route.bat"), "w", encoding="utf-8") as f:
    f.write(bat)

sh = r'''#!/bin/bash
# ============================================================
#  说文解字 App 字形图 B 路线（wikimedia_seal）一键运行
#  作用：自动从 Wikimedia Commons 抓取「小篆」SVG 并打包成
#        data/dataset.bin，无需你手动下载任何数据文件。
# ============================================================
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "[1/3] 首次运行：创建虚拟环境并安装依赖（需联网）..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

echo "[2/3] 开始抓取小篆字形（约 8105 字，依网络 10~40 分钟）..."
python pipeline.py --chars ../../data/characters.json --sources wikimedia_seal --out ../../data/dataset.bin

echo "[3/3] 完成！请把 data/dataset.bin 发回给老吴（微信/邮件/网盘均可）。"
'''
with open(os.path.join(dst_rp, "run_b_route.sh"), "w", encoding="utf-8") as f:
    f.write(sh)

# ---------- 6. 包内简短说明 ----------
readme = """说文解字 App · 字形图 B 路线管线包
=====================================

本包供「网络可达海外公共数据源」的伙伴运行，用于自动补全 App 的
古文字字形图（当前为「小篆」阶段，源自 Wikimedia Commons 公版 SVG）。

你只需要做三件事：
  1. 安装 Python 3.10+（官网 python.org，勾选 Add to PATH）。
  2. 把本包解压到任意目录，进入 tools/rubbing_pipeline/。
  3. 双击 run_b_route.bat（Windows）或执行 bash run_b_route.sh（Mac/Linux）。

脚本会自动联网从 Wikimedia Commons 抓取小篆字形并打包成
data/dataset.bin —— 你无需手动下载任何数据文件。
跑完后，把 data/dataset.bin 发回给老吴即可。

详细图文步骤见随附的《B路线操作手册.pdf》。
"""
with open(os.path.join(PKG_ROOT, "PARTNER_README.txt"), "w", encoding="utf-8") as f:
    f.write(readme)

# ---------- 7. 打包 zip ----------
if os.path.exists(ZIP_PATH):
    os.remove(ZIP_PATH)
shutil.make_archive(os.path.splitext(ZIP_PATH)[0], "zip", PKG_ROOT)
print("ZIP 已生成:", ZIP_PATH, os.path.getsize(ZIP_PATH), "bytes")

# ============================================================
#  8. 生成 PDF 操作手册（reportlab + 中文 CID 字体）
# ============================================================
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, ListFlowable, ListItem, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# 优先内嵌系统中文字体（确保伙伴任意环境都能显示中文），失败则回退 CID 字体
F = "STSong-Light"
try:
    from reportlab.pdfbase.ttfonts import TTFont
    _candidates = [
        (r"C:/Windows/Fonts/msyh.ttc", 0),
        (r"C:/Windows/Fonts/simhei.ttf", 0),
        (r"C:/Windows/Fonts/simsun.ttc", 0),
        (r"C:/Windows/Fonts/NotoSansSC-VF.ttf", 0),
    ]
    _registered = False
    for _fp, _idx in _candidates:
        if os.path.exists(_fp):
            try:
                pdfmetrics.registerFont(TTFont("CJK", _fp, subfontIndex=_idx))
                F = "CJK"
                _registered = True
                print("内嵌中文字体:", _fp)
                break
            except Exception as _e:
                print("字体加载失败 %s: %s" % (_fp, _e))
    if not _registered:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        F = "STSong-Light"
        print("回退到 CID 字体 STSong-Light")
except Exception:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    F = "STSong-Light"
    print("回退到 CID 字体 STSong-Light")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName=F, fontSize=18,
                    spaceAfter=8, textColor=colors.HexColor("#1a3c6e"))
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName=F, fontSize=13,
                    spaceBefore=10, spaceAfter=5, textColor=colors.HexColor("#245"))
BODY = ParagraphStyle("BODY", parent=styles["BodyText"], fontName=F, fontSize=10,
                      leading=15, alignment=TA_LEFT, spaceAfter=4)
CODE = ParagraphStyle("CODE", parent=styles["BodyText"], fontName="Courier",
                      fontSize=8.5, leading=12, textColor=colors.HexColor("#222"),
                      backColor=colors.HexColor("#f2f2f2"), borderPadding=4,
                      spaceBefore=3, spaceAfter=6)
NOTE = ParagraphStyle("NOTE", parent=BODY, fontSize=9.5, textColor=colors.HexColor("#7a3b00"),
                      backColor=colors.HexColor("#fff5e6"), borderPadding=5, spaceBefore=4)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=8.5, textColor=colors.HexColor("#555"))

def P(t, s=BODY): return Paragraph(t, s)

def code_block(t):
    return Paragraph(t.replace("\n", "<br/>").replace(" ", "&nbsp;"), CODE)

doc = SimpleDocTemplate(PDF_PATH, pagesize=A4,
                        leftMargin=18*mm, rightMargin=18*mm,
                        topMargin=16*mm, bottomMargin=16*mm,
                        title="说文解字 App 字形图 B 路线 · 海外伙伴操作手册")
E = []

E.append(P("说文解字 App · 字形图 B 路线", H1))
E.append(P("海外伙伴操作手册（wikimedia_seal 小篆自动化管线）", BODY))
E.append(P("版本 2026-09-08 ｜ 生成于 %s" % datetime.date.today().isoformat(), SMALL))
E.append(HRFlowable(width="100%", color=colors.HexColor("#1a3c6e"), thickness=1.2, spaceAfter=8))

# §0 一句话结论
E.append(P("0. 先看结论（你最关心的问题）", H2))
E.append(P("你<strong>不需要手动下载任何字形数据文件</strong>。本包里的脚本会<strong>自动联网</strong>从 "
          "Wikimedia Commons（维基共享资源）逐个抓取「小篆」SVG 字形，并打包成 App 能直接用的 "
          "<font name='Courier'>data/dataset.bin</font>。你只需：装好 Python → 解压本包 → 运行一条命令 → "
          "把生成的 bin 文件发回给老吴。", BODY))
E.append(P("（进阶的「甲骨/金文」真迹路线需要额外准备公版书影和坐标映射，<strong>本次不要求</strong>，"
          "后续单独协调。）", NOTE))

# §1 环境准备
E.append(P("1. 环境准备（一次性）", H2))
E.append(P("① 安装 Python 3.10 或更新版本：", BODY))
E.append(ListFlowable([
    ListItem(P("打开 <font name='Courier'>https://www.python.org/downloads/</font> 下载安装包。", BODY)),
    ListItem(P("Windows 安装时<strong>务必勾选 “Add python.exe to PATH”</strong>。", BODY)),
    ListItem(P("装完后打开命令行（Windows 按 Win+R 输入 cmd），执行 <font name='Courier'>python --version</font>"
               " 应能显示版本号（Mac/Linux 用 <font name='Courier'>python3 --version</font>）。", BODY)),
], bulletType="bullet"))
E.append(P("② 把本 ZIP 解压到任意目录（例如桌面 <font name='Courier'>shuowen_broute/</font>）。", BODY))

# §2 运行
E.append(P("2. 运行管线（核心一步）", H2))
E.append(P("进入解压后的 <font name='Courier'>tools/rubbing_pipeline/</font> 目录：", BODY))
E.append(P("Windows：直接<strong>双击</strong> <font name='Courier'>run_b_route.bat</font>。", BODY))
E.append(P("Mac / Linux：在终端执行 <font name='Courier'>bash run_b_route.sh</font>。", BODY))
E.append(P("脚本会自动完成以下事情：", BODY))
E.append(ListFlowable([
    ListItem(P("首次运行创建独立虚拟环境并安装依赖（需联网，约 1~2 分钟）。", BODY)),
    ListItem(P("读取 <font name='Courier'>data/characters.json</font>（8105 个字）。", BODY)),
    ListItem(P("逐字向 Wikimedia Commons 请求「小篆」SVG，栅格化后打包。", BODY)),
    ListItem(P("写出 <font name='Courier'>data/dataset.bin</font> 与 <font name='Courier'>data/dataset.attribution.json</font>。"
               "（部分字 Commons 没有则自动跳过，属正常。）", BODY)),
], bulletType="bullet"))
E.append(P("耗时：依网络状况约 10~40 分钟（8105 字）。请保持联网、命令行窗口不要关。", NOTE))

# §3 产物与回传
E.append(P("3. 产物与回传", H2))
E.append(P("跑完后在 <font name='Courier'>data/</font> 目录下会生成：", BODY))
E.append(ListFlowable([
    ListItem(P("<font name='Courier'>dataset.bin</font> —— 小篆字形数据包（核心交付物）。", BODY)),
    ListItem(P("<font name='Courier'>dataset.attribution.json</font> —— 来源与许可证记录（合规用，一并发回）。", BODY)),
], bulletType="bullet"))
E.append(P("请把这两个文件发回给老吴（微信文件 / 邮件 / 网盘链接均可）。<strong>我们只收这两个文件</strong>，"
          "其余中间产物无需发送。", BODY))

# §4 我们会做什么
E.append(P("4. 老吴这边会做什么（你无需参与）", H2))
E.append(P("收到你的 bin 后，我们会用 <font name='Courier'>merge_bins.py</font> 把你的「小篆」数据与已上线的"
          "「字源」数据合并成 App 最终使用的单一 <font name='Courier'>dataset.bin</font>，App 渲染链路无需改动，"
          "即可在字形演变行看到「字源 → 小篆」两段。", BODY))

# §5 进阶（可不看）
E.append(P("5. 进阶：甲骨 / 金文真迹路线（本次不做）", H2))
E.append(P("若日后要补全甲骨文、金文，会改用 <font name='Courier'>scan_trace</font> 适配器：从 Internet Archive "
          "公版书影（如罗振玉《殷虚书契》）按页码+坐标裁剪。该路线需要额外的书影图片与 "
          "<font name='Courier'>bbox_map.json</font> 坐标映射，准备成本较高，<strong>本次不要求</strong>，"
          "待我们另行协调后再启动。", BODY))

# §6 合规
E.append(P("6. 合规与署名（自动处理）", H2))
E.append(P("本路线使用的 Wikimedia Commons 小篆 SVG 多为<strong>公版（Public Domain）</strong>或 CC 授权，"
          "可自由商用；脚本会把每条来源与许可证自动写入 <font name='Courier'>dataset.attribution.json</font>，"
          "App 发布时会一并署名。请勿把任何标注 “CC BY-NC（非商业）” 的来源混入。", BODY))

# §7 故障排查
E.append(P("7. 故障排查", H2))
tbl_data = [
    [P("<b>现象</b>", SMALL), P("<b>原因 / 对策</b>", SMALL)],
    [P("命令行不认 <font name='Courier'>python</font>", SMALL),
     P("Python 未加入 PATH；重装并勾选 Add to PATH，或改用 <font name='Courier'>py</font> / 完整路径。", SMALL)],
    [P("<font name='Courier'>pip install</font> 卡住/失败", SMALL),
     P("检查联网；依赖仅 requests/Pillow/zstandard/resvg_py，无需系统 cairo。", SMALL)],
    [P("某字没有小篆图", SMALL),
     P("Commons 该类目本就缺该字，属正常；合并后该字仅显示「字源」阶段。", SMALL)],
    [P("bin 文件只有约 154 字节", SMALL),
     P("抓取全部失败（多为网络被限）。检查能否浏览器打开 commons.wikimedia.org，再重跑。", SMALL)],
    [P("想只试跑少量字", SMALL),
     P("命令行加 <font name='Courier'>--limit 20</font> 参数先验证流程。", SMALL)],
]
t = Table(tbl_data, colWidths=[55*mm, 110*mm])
t.setStyle(TableStyle([
    ("FONTNAME", (0,0), (-1,-1), F),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#bbb")),
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a3c6e")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f5f7fb")]),
    ("LEFTPADDING", (0,0), (-1,-1), 5),
    ("RIGHTPADDING", (0,0), (-1,-1), 5),
    ("TOPPADDING", (0,0), (-1,-1), 3),
    ("BOTTOMPADDING", (0,0), (-1,-1), 3),
]))
E.append(t)

# §8 命令速查
E.append(P("8. 命令速查（备用 / 手动）", H2))
E.append(code_block(
    "# 进入管线目录\n"
    "cd tools/rubbing_pipeline\n\n"
    "# 建环境 + 装依赖（首次）\n"
    "python -m venv .venv && source .venv/Scripts/activate   # Windows\n"
    "pip install -r requirements.txt\n\n"
    "# 跑小篆抓取并打包\n"
    "python pipeline.py --chars ../../data/characters.json \\\n"
    "    --sources wikimedia_seal --out ../../data/dataset.bin\n\n"
    "# 只试前 20 字验证流程\n"
    "python pipeline.py --chars ../../data/characters.json \\\n"
    "    --sources wikimedia_seal --out ../../data/dataset.bin --limit 20\n\n"
    "# 离线自测（不联网，验证打包链路）\n"
    "python pipeline.py --self-test"
))
E.append(P("附录 · 包内目录结构", H2))
E.append(code_block(
    "shuowen_broute/\n"
    "├─ PARTNER_README.txt\n"
    "├─ data/\n"
    "│   └─ characters.json        # 8105 字清单（--chars 输入）\n"
    "└─ tools/\n"
    "    ├─ rubbing_pipeline/\n"
    "    │   ├─ pipeline.py\n"
    "    │   ├─ run_b_route.bat    # Windows 一键\n"
    "    │   ├─ run_b_route.sh     # Mac/Linux 一键\n"
    "    │   ├─ adapters/          # wikimedia_seal / glyphwiki / scan_trace\n"
    "    │   ├─ sources.py  merge_bins.py  pack_existing.py\n"
    "    │   ├─ requirements.txt\n"
    "    │   └─ README_B.md\n"
    "    └─ sinica_pipeline/\n"
    "        └─ pack_dataset.py    # 打包器（管线依赖）"
))

doc.build(E)
print("PDF 已生成:", PDF_PATH, os.path.getsize(PDF_PATH), "bytes")
print("DONE")
