#!/usr/bin/env bash
# 说文解字 · Wikimedia index.php 抓取完成后的自动收尾链路
#
#   1) 等待抓取进程退出
#   2) 重打包 dataset.bin (pack_all.py)
#   3) bump 缓存版本串 + 重建 index.html (build_web.py)
#   4) 端到端校验 (verify_dataset.js)
#   5) 提交并推送 Gitee(main)
#
# 幂等：可重复执行；无变更时不产生空提交。
# 用法：auto_repack_push.sh [抓取PID] [缓存版本串]
set -u

# bash 用 POSIX 路径；传给原生 python/node 必须用 Windows 路径（否则 /e/... 会变成 E:\e\...）
PROJ="/e/Workbuddy/说文解字"
PIPE="$PROJ/tools/rubbing_pipeline"
PROJ_W="E:/Workbuddy/说文解字"
PIPE_W="$PROJ_W/tools/rubbing_pipeline"
PY="C:/Users/Lenovo/.workbuddy/binaries/python/versions/3.13.12/python.exe"
NODE="C:/Users/Lenovo/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"

FETCH_PID="${1:-25824}"
VER="${2:-20260911r}"
LOG="$PIPE/_auto_repack.log"
SENT="$PIPE/_auto_repack.done"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

cd "$PROJ" || { echo "无法进入项目目录"; exit 1; }
: > "$LOG"
rm -f "$SENT"

# ---------- 1) 等待抓取结束 ----------
# 主判据 = 抓取日志出现完成标记；兜底 = 进程消失。
# 注意：tasklist CSV 里 PID 带引号（"python.exe","25824",...），模式必须含引号，
#       否则会误判成"进程已退出"并在抓取未完成时提前收尾。
RUNLOG="${WAIT_LOG:-$PIPE/_indexphp_run.log}"
DONE_RE="${WAIT_MARK:-indexphp\] 完成}"

# WAIT_SKIP=1 表示不等待、立即收尾；FETCH_PID=0 表示无进程可查（只看日志标记）。
if [ "${WAIT_SKIP:-0}" != "1" ]; then
  log "等待抓取完成（PID=$FETCH_PID，日志 $(basename "$RUNLOG")）…"
  WAITED=0
  while :; do
    if grep -q "$DONE_RE" "$RUNLOG" 2>/dev/null; then
      log "检测到完成标记，抓取正常结束"
      break
    fi
    if [ "$FETCH_PID" != "0" ] \
       && ! MSYS_NO_PATHCONV=1 tasklist /FI "PID eq $FETCH_PID" /FO CSV 2>/dev/null \
            | grep -qE "\"$FETCH_PID\""; then
      log "⚠️ 抓取进程已消失，但日志中没有完成标记 —— 疑似中途崩溃，链路中止（不推送半成品）"
      tail -5 "$RUNLOG" >> "$LOG" 2>/dev/null
      exit 1
    fi
    sleep 20
    WAITED=$((WAITED + 20))
    if [ "$WAITED" -ge "${WAIT_MAX:-5400}" ]; then
      log "⚠️ 等待超时（${WAIT_MAX:-5400}s）仍无完成标记，链路中止以防挂死"
      exit 8
    fi
    if [ $((WAITED % 300)) -eq 0 ]; then
      log "…仍在抓取（已等待 $((WAITED / 60)) 分钟）：$(tail -1 "$RUNLOG" | sed 's/^ *//')"
    fi
  done
  tail -3 "$RUNLOG" >> "$LOG" 2>/dev/null
fi

# ---------- 2) 重打包 ----------
log "重打包 dataset.bin …"
if ! "$PY" "$PIPE_W/pack_all.py" >> "$LOG" 2>&1; then
  log "❌ pack_all.py 失败，链路中止（dataset.bin 可用 data/dataset.bin.prev 回滚）"
  exit 2
fi
log "pack_all 完成"

# 防回退闸门：新 dataset.bin 必须大于已提交版本，否则视为异常，不推送
BASE_BYTES=$(git cat-file -s "HEAD:data/dataset.bin" 2>/dev/null || echo 0)
NEW_BYTES=$(stat -c %s data/dataset.bin 2>/dev/null || echo 0)
log "dataset.bin 基线 $BASE_BYTES bytes -> 新 $NEW_BYTES bytes"
if [ "$NEW_BYTES" -le "$BASE_BYTES" ]; then
  log "❌ 新 dataset.bin 未增长（$NEW_BYTES <= $BASE_BYTES），判定异常，链路中止"
  exit 7
fi

# ---------- 3) bump 缓存版本 + 重建前端 ----------
log "bump 缓存版本 -> $VER 并重建 index.html …"
"$PY" - "$VER" <<'PYEOF' >> "$LOG" 2>&1
import io, re, sys
ver = sys.argv[1]
p = "build_web.py"
s = io.open(p, encoding="utf-8", newline="").read()
s2, n = re.subn(r'(fetch\("data/dataset\.bin\?v=)[^"]*(")', r"\g<1>" + ver + r"\g<2>", s)
io.open(p, "w", encoding="utf-8", newline="").write(s2)
print("[bump] dataset.bin?v=%s (%d 处)" % (ver, n))
PYEOF
if ! "$PY" build_web.py >> "$LOG" 2>&1; then
  log "❌ build_web.py 失败，链路中止"
  exit 3
fi
grep -E "Total:|non-ASCII" "$LOG" | tail -2

# ---------- 4) 端到端校验 ----------
log "端到端校验 dataset.bin …"
"$NODE" "$PIPE_W/verify_dataset.js" > "$PIPE/_auto_verify.txt" 2>&1
if ! grep -q "验证通过" "$PIPE/_auto_verify.txt"; then
  log "❌ 校验未通过，已停止（不推送）"
  tail -20 "$PIPE/_auto_verify.txt" >> "$LOG"
  exit 4
fi
grep -E "总记录数|脚本分布|覆盖字|验证通过" "$PIPE/_auto_verify.txt" >> "$LOG"
log "校验通过 ✓"

# ---------- 5) 提交并推送 Gitee ----------
if [ "${DRY_RUN:-0}" = "1" ]; then
  log "DRY_RUN=1 —— 跳过提交与推送。当前 git status："
  git status --short >> "$LOG" 2>&1
  exit 0
fi

git add -A >> "$LOG" 2>&1
if git diff --cached --quiet; then
  log "无变更，跳过提交与推送"
else
  MSG="P1-2 甲骨/金文扩量：Wikimedia index.php 分类反查补真迹字形

- 新增 run_indexphp.py：走 index.php 页面渲染（不受 api.php 限流），ACC 编号 + 汉字命名双解析，断点续传 + 软限流退避
- pack_all 重打包 dataset.bin，重建 index.html 并 bump 缓存版本 v=$VER
- 端到端校验（verify_dataset.js）通过
- .gitignore 补充 indexphp/auto_repack 运行日志"

  if git commit -q -m "$MSG" >> "$LOG" 2>&1; then
    log "已提交 $(git rev-parse --short HEAD)"
  else
    log "❌ 提交失败"
    exit 5
  fi

  if git push origin main >> "$LOG" 2>&1; then
    log "✅ 已推送 Gitee origin/main -> $(git rev-parse --short HEAD)"
  else
    log "❌ 推送 Gitee 失败（本地已提交，可手动重推）"
    exit 6
  fi
fi

echo "SUMMARY_BEGIN" >> "$LOG"
echo "head=$(git rev-parse --short HEAD)" >> "$LOG"
echo "dataset_bytes=$(stat -c %s data/dataset.bin)" >> "$LOG"
echo "SUMMARY_END" >> "$LOG"

date +%s > "$SENT"
log "🎉 全链路完成"
