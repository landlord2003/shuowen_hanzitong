#!/bin/bash
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
