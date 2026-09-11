# 说文解字 App · P1-2 古文字扩量交接文档（2026-09-11 版）

> 本文件记录 P1-2「甲骨/金文/古文字字形扩量」两轮的完整变更与复现方法。
> 项目整体合规/授权/六书交接见 `HANDOFF.md`（2026-09-10 版，内容仍有效，勿删）。
> 数据版本串（浏览器缓存 key）：`v=20260911b`（见 `build_web.py` 中 `dataset.bin?v=...`）。

## 0. TL;DR

两轮扩量把古文字真迹字形从 **10063 → 14741 条（+46.5%）**，覆盖字始终 8105/8105。

- **轮1**（9-10 晚，`1a4bba8`）：逐字查 Commons 分类页反查，命中 703 字、新增 1435 真迹。
- **轮2**（9-11，`6dfad28`）：改用 `Special:Search` 短语式文件名枚举（效率数量级提升）+ 修正两处历史 bug + **新增「大篆」书体**。

---

## 1. 数据集演进（三提交对比）

| 指标 | 起点 `438b9f4` | 轮1 `1a4bba8` | 轮2 `6dfad28` |
|---|---|---|---|
| 总记录数 | 10063 | 11513（+1450） | **14741（+3228）** |
| dataset.bin 字节 | 9.67 MB | 10.91 MB | **13.96 MB** |
| 覆盖字 | 8105 | 8105 | 8105 |
| glyphwiki 字源 | 8105 | 8105 | 8105 |
| 甲骨文 oracle-bone | 390 | 633 | **758** |
| 金文 bronze | 500 | 865 | **1056** |
| 简帛 bamboo-silk | 321 | 486 | **612** |
| 小篆 seal | 747 | 1424 | **2848** |
| **大篆 bigseal（新书体）** | 0 | 0 | **1362** |

> 小篆从 747→2848 暴增，是因为 `Special:Search` 枚举挖出了大量此前逐字查漏掉的 `-seal.svg`（全站约 2097 个，之前只抓到 1424）。

---

## 2. 轮2 具体改动（commit `6dfad28`）

### 2.1 通道升级：逐字 → 批量枚举
- 旧（`run_indexphp.py`）：逐字查 `index.php?title=Category:{汉字}&action=render`，7403 字耗时 88 分钟。
- 新（`run_intitle_bulk.py`）：Commons `Special:Search` 短语式文件名搜索（`intitle:"-bigseal.svg"` 等），纯度 ~99%、支持分页，**几十次请求覆盖全站字形**，约 47 分钟跑完 2642 个下载。
- 实测可用查询式：
  - `intitle:"-bigseal.svg"` → 大篆全集（~500+，纯度 99.8%）
  - `intitle:"-hanjian.svg"` → 汗簡（11，纯度 100%）
  - `intitle:"-oracle.svg"` → 甲骨（含英文命名漏网文件，~500+）
  - `deepcat:"Seal script"` → 篆书分类树（1172）

### 2.2 修正两处一直存在的 bug（本轮才发现）
1. **`ACC-B#####`（金文）整批被丢弃**：实物文件名用**大写 `B`**，原映射只注册小写 `b`。读文件页模板确认 `ACC-B00001` → `一｜bronze｜我方鼎(early Western Zhou)`。单「一」字就有 15 个金文变体曾被扔掉。
2. **大篆被当成小篆**：`ACC-L#####` 模板明写 `bigseal|Great seal`，原映射误标为 `seal`。现已独立成「大篆」书体。

### 2.3 新增「大篆」书体（bigseal）
- `tools/sinica_pipeline/pack_dataset.py`：脚本前缀映射加 `"bigseal": "D_"`
- `data/dataset-reader.js`：SCRIPT_ORDER 加 `bigseal`、文件名前缀 `D_` 解析、SCRIPT_METADATA 加中文名「大篆」
- `build_web.py`：六阶段顺序改为 `甲骨→金文→简帛→大篆→小篆→隶书`；**无某书体的字不显示空占位**（否则 84% 的字会多一个空槽）

---

## 3. 最终数据状态（`6dfad28`，端到端校验通过 ✓）

```
总记录数: 14741
覆盖字:   8105
脚本分布:
  glyphwiki:    8105   (字源，GlyphWiki 体系)
  seal:         2848   (小篆)
  bigseal:      1362   (大篆 / 籀文，本轮新增书体)
  bronze:       1056   (金文)
  oracle-bone:   758   (甲骨文)
  bamboo-silk:   612   (简牍帛书)
总字节: 13956587 (13.96 MB)
```

校验工具：`node tools/rubbing_pipeline/verify_dataset.js`（CI 级端到端，不通过不推送）。

---

## 4. 复现命令

```bash
# 重新抓取（断点续传，只补缺失）—— 走 run_intitle_bulk 批量枚举通道
cd tools/rubbing_pipeline
python run_intitle_bulk.py              # 全量枚举 + 下载（~47 分钟，2642 个）

# 旧分类反查通道（备用，已并入 ACC-B/ACC-L 修正）
python run_indexphp.py --workers 4      # 逐字分类页反查

# 重打包 + 重建前端 + 校验
python tools/sinica_pipeline/pack_all.py
python build_web.py                     # 顺带 bump 缓存版本（data/dataset.bin?v=...）
node tools/rubbing_pipeline/verify_dataset.js

# 提交推送
git add -A && git commit -m "..." && git push origin main
```

收尾自动化脚本（已验证幂等）：
- `tools/rubbing_pipeline/finish_bulk.sh`：等下载完成 → 补跑捞回失败项 → 重打包 → bump 版本 → 重建前端 → 校验 → 提交 → 推送 Gitee → 写 HANDOFF
- `tools/rubbing_pipeline/wait_finish_push.sh`：监控兜底（主链被沙箱拦 push 时补推；主链崩溃才重跑）

---

## 5. 已知遗留 / 风险（诚实上报）

1. **旧误标无法精确回滚**：旧数据中部分 `wa_{id}_seal.png` 实来自 `-bigseal.svg` 或 `ACC-L`（大篆），却被标成小篆。当初未记录"每张图来自哪个文件"，无法逐张识别，影响面有限但确实存在。根治需给适配器加 provenance 记录，或对受影响字定向重扫。
2. **少量下载失败**：批量下载首轮失败 47/2642（≈1.8%，多为 404 真缺失），补跑捞回 35 个、剩 39 个为 404 不可恢复。
3. **来源标注未接入界面**：Wikimedia 真迹 vs 字体兜底（临海/青柳隶书、甲骨/金文字体）的来源徽章尚未做（同 P1-2 上轮遗留）。用户明确要求"改 A 线前先拉起本地预览服务亲眼过目"——此功能上线前需走该流程。
4. **GitHub 滞后**：`6dfad28` 仅推 Gitee；如需同步 GitHub 另行 `git push github main`。
5. **运行日志污染**：`6dfad28` 误将 `_finish_bulk.log` / `_wait_finish.log` 提交进仓库（当时 .gitignore 未覆盖）。后续已加进 .gitignore 并从跟踪移除。

---

## 6. 下一步建议

- [ ] 评估给适配器加 provenance，定向重扫"误标小篆的大篆"
- [ ] 接入来源徽章（Wikimedia 真迹 / 字体兜底）—— 上线前拉本地预览给老吴过目
- [ ] 视效果决定是否开启 GitHub 同步
- [ ] 汗簡（hanjian，仅 11 字）是否值得做成一个独立书体维度
