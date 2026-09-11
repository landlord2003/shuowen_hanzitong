#!/usr/bin/env bash
# 说文解字 · 批量枚举（run_intitle_bulk.py）完成后的自动收尾链路
#
#   0) 幂等闸门：若 _bulk_finish_done 已存在且远端已同步，直接退出
#   1) 等待批量下载完成标记 [bulk] 下载完成（主判据）；进程消失=崩溃则中止
#   2) 补跑一次 run_intitle_bulk.py 捞回失败项（幂等，只下载缺失）
#   3) 重打包 dataset.bin (pack_all.py)
#   4) bump 缓存版本串 -> 20260911b + 重建 index.html (build_web.py)
#   5) 端到端校验 (verify_dataset.js)；不通过不提交
#   6) 提交并推送 Gitee (origin/main)
#   7) 写 HANDOFF.md 与完成哨兵
#
# 幂等：可重复执行；无变更时不产生空提交。
# 用法：finish_bulk.sh
set -u

PROJ="/e/Workbuddy/说文解字"
PIPE="$PROJ/tools/rubbing_pipeline"
PROJ_W="E:/Workbuddy/说文解字"
PIPE_W="$PROJ_W/tools/rubbing_pipeline"
PY="C:/Users/Lenovo/.workbuddy/binaries/python/versions/3.13.12/python.exe"
NODE="C:/Users/Lenovo/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"

VER="20260911b"
RUNLOG="$PIPE/_bulk_run.log"
DONE_RE='bulk\] 下载完成'
LOG="$PIPE/_finish_bulk.log"
SENT="$PIPE/_bulk_finish_done"
PUSH_PENDING="$PIPE/_push_pending"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
: > "$LOG"

cd "$PROJ" || { echo "无法进入项目目录"; exit 1; }

# ---------- 0) 幂等闸门 ----------
if [ -f "$SENT" ]; then
  REMOTE=$(timeout 40 git ls-remote origin refs/heads/main 2>/dev/null | cut -c1-7)
  LOCAL=$(git rev-parse --short HEAD 2>/dev/null)
  if [ "$REMOTE" = "$LOCAL" ]; then
    log "已完成且远端同步 ($LOCAL)，跳过"
    exit 0
  fi
  log "本地有提交 $LOCAL 但远端 $REMOTE 未同步，继续推送"
fi

# ---------- 1) 等待下载完成 ----------
log "等待批量下载完成（日志 $(basename "$RUNLOG")）…"
WAITED=0
while :; do
  if grep -q "$DONE_RE" "$RUNLOG" 2>/dev/null; then
    log "检测到完成标记，批量下载正常结束"
    break
  fi
  # 心跳：下载进程每 ~2 分钟写一行「下载 N/2642」；若日志 15 分钟未更新且未见标记，判定崩溃
  NOW=$(date +%s)
  MT=$(stat -c %Y "$RUNLOG" 2>/dev/null || echo 0)
  if [ $((NOW - MT)) -gt 900 ]; then
    log "⚠️ 日志 15 分钟未更新且无完成标记 —— 疑似崩溃，链路中止（不推送半成品）"
    tail -5 "$RUNLOG" >> "$LOG" 2>/dev/null
    exit 1
  fi
  sleep 20
  WAITED=$((WAITED + 20))
  if [ "$WAITED" -ge 7200 ]; then
    log "⚠️ 等待超时（7200s）仍无完成标记，链路中止"
    exit 8
  fi
  if [ $((WAITED % 300)) -eq 0 ]; then
    log "…仍在下载（已等待 $((WAITED / 60)) 分钟）：$(tail -1 "$RUNLOG" | sed 's/^ *//')"
  fi
done
tail -3 "$RUNLOG" >> "$LOG" 2>/dev/null

# ---------- 2) 补跑捞回失败项（幂等） ----------
log "补跑 run_intitle_bulk.py 捞回失败项…"
"$PY" "$PIPE_W/run_intitle_bulk.py" > "$PIPE/_bulk_rerun.log" 2>&1 || \
  log "⚠️ 补跑返回非 0（可能全为 404，忽略继续）"
tail -3 "$PIPE/_bulk_rerun.log" >> "$LOG" 2>/dev/null

# ---------- 3) 重打包 ----------
log "重打包 dataset.bin …"
if ! "$PY" "$PIPE_W/pack_all.py" >> "$LOG" 2>&1; then
  log "❌ pack_all.py 失败，链路中止（dataset.bin.prev 可回滚）"
  exit 2
fi
log "pack_all 完成"

# 防回退闸门
BASE_BYTES=$(git cat-file -s "HEAD:data/dataset.bin" 2>/dev/null || echo 0)
NEW_BYTES=$(stat -c %s data/dataset.bin 2>/dev/null || echo 0)
log "dataset.bin 基线 $BASE_BYTES -> 新 $NEW_BYTES bytes"
if [ "$NEW_BYTES" -le "$BASE_BYTES" ]; then
  log "❌ 新 dataset.bin 未增长，判定异常，链路中止"
  exit 7
fi

# ---------- 4) bump 缓存版本 + 重建前端 ----------
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

# ---------- 5) 端到端校验 ----------
log "端到端校验 dataset.bin …"
"$NODE" "$PIPE_W/verify_dataset.js" > "$PIPE/_auto_verify.txt" 2>&1
if ! grep -q "验证通过" "$PIPE/_auto_verify.txt"; then
  log "❌ 校验未通过，已停止（不推送）"
  tail -20 "$PIPE/_auto_verify.txt" >> "$LOG"
  exit 4
fi
grep -E "总记录数|脚本分布|覆盖字|验证通过" "$PIPE/_auto_verify.txt" >> "$LOG"
log "校验通过 ✓"

# ---------- 6) 提交数据变更 ----------
git add -A >> "$LOG" 2>&1
if git diff --cached --quiet; then
  log "无数据变更，跳过提交"
else
  MSG="P1-2 续：Wikimedia 批量枚举扩量（intitle 短语搜索，不逐字查）

- 新增 run_intitle_bulk.py：Special:Search 短语式文件名枚举，几十次请求覆盖全站字形（纯度~99%）
- 修正 ACC 编号映射两处 bug：ACC-B(金文) 原被大写漏掉；ACC-L 实为「大篆」误标为「小篆」
- 新增「大篆」书体（bigseal，前缀 D_），数据集/前端/阶段图三处对齐
- pack_all 重打包 dataset.bin，重建 index.html 并 bump 缓存版本 v=$VER
- 端到端校验（verify_dataset.js）通过"
  if git commit -q -m "$MSG" >> "$LOG" 2>&1; then
    log "已提交数据变更 $(git rev-parse --short HEAD)"
  else
    log "❌ 提交失败"
    exit 5
  fi
fi

# ---------- 7) 写 HANDOFF（引用实际新 HEAD）并提交 ----------
HEAD=$(git rev-parse --short HEAD)
DSZ=$(stat -c %s data/dataset.bin)
"$PY" - "$HEAD" "$DSZ" "$VER" <<'PYEOF'
import io, sys
head, dsz, ver = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    v = io.open("tools/rubbing_pipeline/_auto_verify.txt", encoding="utf-8").read()
except Exception:
    v = ""
import re
def grab(pat):
    m = re.search(pat, v)
    return m.group(1).strip() if m else "?"
total = grab(r"总记录数[:：]\s*(\d+)")
cover = grab(r"覆盖字[:：]\s*(\d+)")
script_dist = ""
m = re.search(r"脚本分布[:：]\s*\n((?:\s*.+\n)+?)(?=\s*覆盖字|验证通过)", v)
if m:
    script_dist = "".join("  " + ln.strip() + "\n" for ln in m.group(1).strip().splitlines())
ok = "验证通过" in v
body = """# 说文解字 · P1-2 批量扩量 Handoff（%(head)s）

> 生成时间：自动收尾链 finish_bulk.sh
> 数据版本串（浏览器缓存 key）：v=%(ver)s
> dataset.bin：%(dsz)s bytes

## 一、本轮做了什么
- **通道升级**：从「逐字查分类页（88 分钟）」改为 Commons `Special:Search` 短语式文件名枚举
  （`intitle:"-bigseal.svg"` 等），几十次分页请求覆盖全站字形，纯度 ~99%，耗时大幅缩短。
- **修正两处历史 bug**（一直存在，本轮才发现）：
  1. `ACC-B#####`（金文）使用大写 B，原映射只注册小写 b → 整批金文变体被丢弃。
  2. `ACC-L#####` 实为「大篆 / Great seal」，原映射误标为「小篆」。
- **新增「大篆」书体**（bigseal，数据集前缀 `D_`）：旧数据无大篆维度，本轮补入。
- **界面**：阶段图顺序改为 甲骨→金文→简帛→大篆→小篆→隶书；缺某书体的字不再显示空占位。

## 二、数据增量（相对上一提交 1a4bba8）
- 总记录数：%(total)s
- 覆盖字：%(cover)s
- 脚本分布：
%(script_dist)s- 校验：%(ok)s

## 三、复现命令
```
# 重新抓取（断点续传，只补缺失）
cd tools/rubbing_pipeline
python run_intitle_bulk.py            # 全量枚举+下载
python run_full_ancient.py           # 旧分类反查通道（备用）
# 重打包 + 重建前端
python tools/sinica_pipeline/pack_all.py
python build_web.py
node tools/rubbing_pipeline/verify_dataset.js   # 端到端校验
```

## 四、已知遗留 / 风险
1. **旧误标无法精确回滚**：旧数据里部分 `wa_*_seal.png` 实来自 `-bigseal.svg` 或 `ACC-L`，
   本就被标成小篆。当初未记录"每张图来自哪个文件"，无法逐张识别，影响面有限但确实存在。
   根治需给适配器加 provenance 记录或定向重扫。
2. **少量下载失败**：批量下载有 ~2% 失败（多数为 404 真实缺失，少数为超时），
   finish 脚本已补跑一次捞回超时项；404 项无法恢复。
3. **来源标注未接入界面**：Wikimedia 真迹 vs 字体兜底的来源徽章尚未做（同 P1-2 上轮遗留）。
4. **GitHub 滞后**：本提交仅推 Gitee；如需同步 GitHub 另行 `git push github main`。

## 五、下一步建议
- 评估是否给适配器加 provenance，定向重扫误标小篆的大篆。
- 接入来源徽章（Wikimedia 真迹 / 字体兜底）。
- 视效果决定是否开启 GitHub 同步。
""" % dict(head=head, dsz=dsz, ver=ver, total=total, cover=cover,
           script_dist=script_dist, ok="通过 ✓" if ok else "未通过 ✗")
io.open("HANDOFF.md", "w", encoding="utf-8").write(body)
print("HANDOFF.md written")
PYEOF
log "已写 HANDOFF.md"
git add HANDOFF.md >> "$LOG" 2>&1
if git diff --cached --quiet; then
  log "HANDOFF 无变化，跳过提交"
else
  if git commit -q -m "docs: 新增 P1-2 批量扩量 handoff" >> "$LOG" 2>&1; then
    log "已提交 handoff $(git rev-parse --short HEAD)"
  fi
fi

# ---------- 8) 推送 Gitee ----------
# 后台 bash 沙箱可能读不了 known_hosts 致 push 失败；失败则留 _push_pending 交兜底自动化重推
if git push origin main >> "$LOG" 2>&1; then
  log "✅ 已推送 Gitee origin/main -> $(git rev-parse --short HEAD)"
  date +%s > "$SENT"
  rm -f "$PUSH_PENDING"
  log "🎉 全链路完成"
else
  log "❌ 推送 Gitee 失败（本地已提交 $(git rev-parse --short HEAD)，待兜底自动化重推）"
  date +%s > "$PUSH_PENDING"
  exit 6
fi
