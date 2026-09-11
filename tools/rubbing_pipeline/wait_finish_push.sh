#!/usr/bin/env bash
# wait_finish_push.sh —— P1-2 批量扩量收尾的「监控+保险」脚本
# 不重打包、不碰 dataset.bin。只做两件事：
#   1) 主链 finish_bulk.sh 若推送 Gitee 被沙箱拦（known_hosts）→ 这里补推
#   2) 主链若中途崩溃 → 这里重跑 finish_bulk.sh 收尾
set -u
PIPE_W="E:/Workbuddy/说文解字/tools/rubbing_pipeline"
PROJ="E:/Workbuddy/说文解字"
LOG="$PIPE_W/_wait_finish.log"
RUNLOG="$PIPE_W/_finish_bulk.log"
DONE="$PIPE_W/_bulk_finish_done"
PUSH_PENDING="$PIPE_W/_push_pending"
DEADLINE=$(( $(date +%s) + 90*60 ))   # 最多等 90 分钟（到 ~09:30）

log(){ echo "[$(date +%H:%M:%S)] $*" >> "$LOG"; }

finish_running(){
  # 用 PowerShell 精确判断是否有 finish_bulk.sh 进程在跑（tasklist/FO CSV 不含命令行，不可靠）
  local n
  n=$(powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='bash.exe'\" | Where-Object { \$_.CommandLine -match 'finish_bulk' } | Measure-Object | Select-Object -ExpandProperty Count" 2>/dev/null | tr -d '\r\n ')
  # 空值/非数字 → 保守当「仍存活」（避免误判崩溃而重跑造成并发）
  case "$n" in
    ''|*[!0-9]*) return 0 ;;
  esac
  [ "$n" != "0" ]
}

cd "$PROJ" || { log "无法进入项目目录"; exit 1; }
: > "$LOG"
log "监控启动（等待主链 finish_bulk.sh 收尾）"

while :; do
  # 情形 A：已完成并推送
  if grep -q "🎉 全链路完成" "$RUNLOG" 2>/dev/null; then
    log "检测到「🎉 全链路完成」，收尾成功"
    break
  fi
  # 情形 B：主链推送失败 → 这里补推
  if grep -q "❌ 推送 Gitee 失败" "$RUNLOG" 2>/dev/null || [ -f "$PUSH_PENDING" ]; then
    log "检测到主链推送失败，尝试补推 Gitee…"
    if git push origin main >> "$LOG" 2>&1; then
      log "✅ 补推 Gitee 成功"
      rm -f "$PUSH_PENDING"
      break
    else
      log "❌ 补推仍失败，60s 后重试"
      sleep 60
      continue
    fi
  fi
  # 情形 C：主链进程没了，但也没完成标记 → 崩溃，重跑收尾
  if [ -f "HANDOFF.md" ] && grep -q "已完成且远端同步" "$RUNLOG" 2>/dev/null; then
    log "已同步，结束"
    break
  fi
  if ! finish_running; then
    if grep -q "下载完成" "$PIPE_W/_bulk_run.log" 2>/dev/null; then
      log "⚠️ 主链进程已消失且无完成标记 —— 重跑 finish_bulk.sh 收尾"
      ( cd "$PIPE_W" && bash finish_bulk.sh ) >> "$LOG" 2>&1 &
      # 重跑后重置循环等待
    fi
  fi
  if [ "$(date +%s)" -gt "$DEADLINE" ]; then
    log "⚠️ 超过 90 分钟仍未完成，停止监控（请人工介入）"
    break
  fi
  sleep 30
done

log "监控结束"
