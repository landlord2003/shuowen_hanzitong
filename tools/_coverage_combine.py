# -*- coding: utf-8 -*-
# 合并 dataset.bin 真迹阶段 + bundled 字体 cmap fallback，计算"用户实际看到的"字形完整度
import json, sys
from fontTools.ttLib import TTFont

ROOT = "D:/WorkBuddy/projects/说文解字"
PY = sys.executable

# 1) 读逐字 dataset 阶段
stages = json.load(open(f"{ROOT}/data/_dataset_stages.json", encoding="utf-8"))
chars = json.load(open(f"{ROOT}/data/characters.json", encoding="utf-8"))["characters"]
prod = [c["char"] for c in chars]
prod_set = set(prod)

REAL = ["oracle-bone", "bronze", "bamboo-silk", "seal", "clerical"]
FONT_MAP = {  # 字体文件 -> 对应阶段
    "oracle-bone.otf": "oracle-bone",
    "bronze-script.otf": "bronze",
    "chongxi-seal.otf": "seal",
}

def cmap_chars(path):
    f = TTFont(path)
    cm = f.getBestCmap()
    return set(chr(cp) for cp in cm.keys())

font_cmaps = {}
for fn_, stage in FONT_MAP.items():
    try:
        font_cmaps[stage] = cmap_chars(f"{ROOT}/data/fonts/{fn_}") & prod_set
        print(f"  font {fn_} -> stage {stage}: covers {len(font_cmaps[stage])} of {len(prod_set)} product chars")
    except Exception as e:
        print(f"  font {fn_} read error: {e}")
        font_cmaps[stage] = set()

# 2) 有效阶段 = dataset 阶段 ∪ 字体 cmap（字体仅补 pending 的甲骨/金/篆）
eff = {ch: set(stages.get(ch, [])) for ch in prod}
for ch in prod:
    for stage, fset in font_cmaps.items():
        if ch in fset:
            eff[ch].add(stage)

# 3) 统计
stage_count = {s: 0 for s in ["glyphwiki"] + REAL}
for ch in prod:
    for s in eff[ch]:
        if s in stage_count:
            stage_count[s] += 1

# 3.1) 按"拥有真迹阶段数"分桶（分类 8105 字）
from collections import Counter
real_count_dist = Counter(len(eff[ch] & set(REAL)) for ch in prod)

# 仅字源（无真迹阶段）
only_source = [ch for ch in prod if not (set(eff[ch]) & set(REAL))]
# 至少 1 真迹阶段
any_real = [ch for ch in prod if set(eff[ch]) & set(REAL)]

print("\n===== 有效字形完整度（dataset 真迹 + 字体 fallback）=====")
for s in ["glyphwiki"] + REAL:
    print(f"  {s:14s}: {stage_count[s]:5d}/{len(prod)}  ({stage_count[s]/len(prod)*100:.1f}%)")
print(f"  至少1个真迹阶段 : {len(any_real)}/{len(prod)} ({len(any_real)/len(prod)*100:.1f}%)")
print(f"  仅字源(无真迹)  : {len(only_source)}/{len(prod)} ({len(only_source)/len(prod)*100:.1f}%)")

# 4) 写出 refined 缺字清单（仅字源、无真迹、且字体也补不到）
out = {
    "definition": "chars with ONLY 字源图(glyphwiki) and NO real ancient stage (甲骨/金/简帛/篆/隶), even after bundled-font fallback",
    "count": len(only_source),
    "chars": only_source,
}
json.dump(out, open(f"{ROOT}/data/glyph_missing.json", "w", encoding="utf-8"), ensure_ascii=False)

# 5) 生成完整报告 markdown
rep = []
rep.append("# 说文解字 App · 字形完整度报告（8105 字）\n")
rep.append("> 生成方式：解码 `data/dataset.bin`（CEDS/zstd 真迹位图库）+ 合并 bundled 古文字体 cmap fallback（甲骨/金/篆）。\n")
rep.append("> 口径：'字源' = GlyphWiki 字源图（溯源参考，非真迹）；'真迹阶段' = 甲骨/金/简帛/篆/隶。\n")
rep.append("\n## 一、各阶段覆盖率（用户实际可见）\n")
rep.append("| 阶段 | 数据来源 | 覆盖字数 | 覆盖率 |")
rep.append("|------|----------|----------|--------|")
rep.append(f"| 字源图 | GlyphWiki（dataset.bin，CC BY-SA 2.1 JP） | {stage_count['glyphwiki']} | 100% |")
rep.append(f"| 甲骨文 | 中研院/小學堂(dataset) + cluesurf/mark(OFL 字体) | {stage_count['oracle-bone']} | {stage_count['oracle-bone']/len(prod)*100:.1f}% |")
rep.append(f"| 金文 | 中研院/小學堂(dataset) + cluesurf/mark(OFL 字体) | {stage_count['bronze']} | {stage_count['bronze']/len(prod)*100:.1f}% |")
rep.append(f"| 简牍帛书 | 中研院/小學堂(dataset) | {stage_count['bamboo-silk']} | {stage_count['bamboo-silk']/len(prod)*100:.1f}% |")
rep.append(f"| 篆文 | 中研院/小學堂(dataset) + 崇羲篆體(CC-BY-ND-3.0-TW 字体) | {stage_count['seal']} | {stage_count['seal']/len(prod)*100:.1f}% |")
rep.append(f"| 隶书 | （缺失，待字体就位） | {stage_count['clerical']} | 0% |")
rep.append("\n## 一之二、按「拥有真迹阶段数」分类 8105 字\n")
rep.append("| 拥有真迹阶段数 | 含义 | 字数 | 占比 |")
rep.append("|------|------|------|------|")
real_meaning = {0:"仅字源图（后起字 / 无古文字形）",1:"有 1 个真迹阶段",2:"有 2 个真迹阶段",3:"有 3 个真迹阶段",4:"有 4 个真迹阶段",5:"5 个全有（甲骨+金+简帛+篆+隶）"}
for k in range(0, 6):
    n = real_count_dist.get(k, 0)
    rep.append(f"| {k} | {real_meaning[k]} | {n} | {n/len(prod)*100:.1f}% |")
rep.append("")
rep.append("> 真迹阶段 = 甲骨 / 金 / 简帛 / 篆 / 隶（共 5 类）。「0」= 完全没有真迹古文字段，仅字源图，即上一轮标注的「后起字·无古文字形」。")
rep.append("")
rep.append("\n## 二、关键结论\n")
rep.append(f"- **字源图：100% 全覆盖**（8105/8105），所有字均有 GlyphWiki 字源溯源图，无完全空白字。")
rep.append(f"- **真迹演变阶段覆盖极低**：仅 {len(any_real)}/{len(prod)}（{len(any_real)/len(prod)*100:.1f}%）的字至少有 1 个真迹古文字段（甲骨/金/简帛/篆/隶）。")
rep.append(f"- **{len(only_source)}/{len(prod)}（{len(only_source)/len(prod)*100:.1f}%）的字只有「字源图」、没有任何真迹古文字形**，其演变行显示：字源 →（空白待补全）→ 楷。这些多为后起字、形声字、简化字，古文字资料本就缺载。")
rep.append(f"- **隶书阶段 0%**：无可用隶书字体（中研院受地理封锁、GitHub 无 OFL 隶书、GlyphWiki 无隶书后缀命名），全 8105 字隶书待补全。")
rep.append("\n## 三、待补充清单（按优先级）\n")
rep.append("1. **隶书字体（最高优先）**：取一版干净可商用隶书字体（中研院/崇羲隶书 CC BY-SA 2.5 TW，或核验过的青柳隶书）→ `data/fonts/clerical-script.ttf` 即自动生效。可一举补满隶书阶段。")
rep.append("2. **甲骨/金/篆真迹扩量**：当前 dataset 真迹仅 395/506/757 字，字体 fallback 已补一部分；若要更高覆盖，需扩充中研院/小學堂抓取或换更全的古文字字体（如更完整的甲骨/金文字体集）。")
rep.append("3. **简牍帛书**：仅 327 字，且无字体兜底，覆盖最薄，优先级低于隶书。")
rep.append("\n## 四、缺字标注（仅字源、无真迹古文字段）\n")
rep.append(f"共 **{len(only_source)}** 字，完整清单见 `data/glyph_missing.json`。示例（前 120）：\n")
rep.append("> " + " ".join(only_source[:120]))
rep.append("\n")
open(f"{ROOT}/tools/glyph_coverage_report.md", "w", encoding="utf-8").write("\n".join(rep))
print("\n[wrote] tools/glyph_coverage_report.md")
print("[wrote] data/glyph_missing.json  refined count=", len(only_source))
