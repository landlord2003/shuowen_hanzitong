# -*- coding: utf-8 -*-
# 扩修 B：P1-4 抽检报告中「确属构字/本义错误」的待核字，依据《说文》逐字订正。
# 仅改 data/cultural.json 的 story（运行时 fetch，无需重建 index.html），并 bump 缓存戳。
import json, os, re, subprocess, datetime

BASE = r"D:\WorkBuddy\projects\说文解字"
CULT = os.path.join(BASE, "data", "cultural.json")
UIJS = os.path.join(BASE, "data", "cultural-ui.js")

# ---- (1) 核验 dataset.bin 是否被动过 ----
os.chdir(BASE)
def g(args):
    return subprocess.run(["git"]+args, capture_output=True, text=True).stdout.strip()
log = g(["log", "--oneline", "--", "data/dataset.bin"])
st  = g(["status", "--short", "--", "data/dataset.bin"])
print("[dataset.bin] commit history:", log if log else "(NONE)")
print("[dataset.bin] working tree   :", st if st else "(clean)")

# ---- (2) 订正表：仅收录报告里「构件/本义明显错误」的待核字 ----
FIX = {
"个":"「个」（個）字的本义是竹制的计数单位，《说文》：『個，竹枚也。从竹固声。』表示以竹枚为单位来计数。简化后写作「个」，从人、从丨，成为通用的个体量词，用于计量单独的人或物。",
"丸":"「丸」字《说文》释为『圜也，倾侧而转者，从反仄』，本义是圆而小、能够滚动的东西，如弹丸、药丸。字形由「仄」反转而来，象圆转之形，并非「王」加一点。",
"广":"「廣」（简化为「广」）《说文》：『廣，殿之大屋也。从广黄声。』本义是宽大、宏敞的屋宇，引申为广阔、宽广。其声旁是「黄」而非「光」，简化后保留「广」作部首。",
"比":"「比」字《说文》：『比，密也。二人为从，反从为比。』本义为并列、亲近、密合。字形由两人并列（与「从」方向相反）会意，并非「匕」与「彐」的组合。",
"巨":"「巨」（鉅）《说文》：『巨，规巨也。从工，象手持之。』本义是画直角与方形的工具（规矩、巨尺），后引申为「大」。字形从「工」、象手执规之状，并非「𠂇」与「口」或大声喊叫。",
"乡":"「鄉」（简化为「乡」）《说文》：『鄉，国离邑民所封乡也……从皀，𢆶声。』本义是相向而食的乡亲、乡里（乡人共食曰乡），后引申为乡村、家乡。其构件为「皀」（食器）与「𢆶」声，并非「广」与「相」。",
"仆":"「僕」（简化为「仆」）《说文》：『僕，给事者。从人从菐，菐亦声。』本义是供人役使的奴仆、侍从。字形从「人」、从「菐」（事务繁杂之形），并非「人」与「蒲」。",
"币":"「幣」（简化为「币」）《说文》：『幣，帛也。从巾敝声。』本义是丝织品（帛），古代用作礼物、祭祀与聘享的贵重物品，后引申为钱币。其声旁是「敝」而非「必」。",
"仅":"「僅」（简化为「仅」）《说文》：『僅，材能也。从人堇声。』本义是才能、少（不过、才），如「仅有」。字形从「人」、从「堇」声，并非「亠」与「今」。",
"计":"「計」（简化为「计」）《说文》：『計，会也，算也。从言从十。』本义是计算、核算。字形从「言」、从「十」（十为数字之具），表示用言语来记数、谋划，并非「言」与「刂」。",
"书":"「書」（简化为「书」）《说文》：『書，箸也。从聿从者。』本义是书写、记载。字形从「聿」（手持笔）、「者」声，表示用笔记录言辞，并非「聿」与「曰」。",
"幻":"「幻」字《说文》：『幻，相诈惑也。从反予。』本义是虚妄、惑乱、不真实。字形由「予」字反转而来（反予为幻），表示与「给予」相反的虚妄不实，并非「心」与「鬼」。",
"术":"「術」（简化为「术」）《说文》：『術，邑中道也。从行从术。』本义是城邑中的道路，引申为方法、技艺、学术。字形从「行」（街道）、「术」声，并非「木」与「术」。",
"扔":"「扔」字《说文》：『扔，摧也。从手乃声。』本义是牵引、拉引，后引申为抛、投掷、丢弃。字形从「手」（扌）、「乃」声，并非「扌」与「宁」。",
"千":"「千」字《说文》：『千，十百也。从十从人。』本义是数目（十百为千）。字形从「十」、从「人」（人亦表众多），表示数量庞大，并非「人」上加一横或「人多如山」。",
"厅":"「廳」（简化为「厅」）本义为聚会待客的大堂，从「广」、从「聽」省声，用于接待宾客之处，并非「广」与「丁」。",
"专":"「專」（简化为「专」）《说文》：『專，六寸簿也……从寸叀声。』本义是纺锤（纺专），后引申为专一、集中、独自掌握。字形从「寸」、从「叀」（纺锤之形）声，并非「丶」与「专」。",
"允":"「允」字《说文》：『允，信也。从儿㠯声。』本义是诚信、信实，引申为答应、许可。字形从「儿」、「㠯」声，并非「兟」与「儿」。",
"仑":"「侖」（简化为「仑」）《说文》：『侖，思也。从亼从冊。』本义是条理、伦次（思之有伦）。字形从「亼」（集合）、从「冊」（简册），表示有条理地编排，并非「亠」与「门」。",
"凶":"「兇」（简化为「凶」）《说文》：『兇，扰恐也。从人在凶下。』本义是恐惧、不祥、凶险。字形从「凵」（坑坎）中有人，表示陷于险恶之地，并非「宀」与「匕」。",
}

d = json.load(open(CULT, encoding="utf-8"))
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = os.path.join(BASE, "data", "cultural.json.bak_storyfixB2_%s" % ts)
import shutil
shutil.copyfile(CULT, backup)

applied, skipped = [], []
for ch, new in FIX.items():
    if ch in d and isinstance(d[ch], dict) and d[ch].get("story"):
        old = d[ch]["story"]
        # 仅当确为新内容才覆盖
        if old != new:
            d[ch]["story"] = new
            applied.append((ch, len(old), len(new)))
        else:
            skipped.append(ch)
    else:
        skipped.append(ch)

json.dump(d, open(CULT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- (3) bump 缓存戳 ----
txt = open(UIJS, encoding="utf-8").read()
m = re.search(r"cultural\.json\?v=(\w+)", txt)
if m:
    oldv = m.group(1)
    # 递增版本
    newv = "20260911" + "i"  # 比 h 进一步
    txt2 = txt.replace("cultural.json?v=%s" % oldv, "cultural.json?v=%s" % newv)
    open(UIJS, "w", encoding="utf-8").write(txt2)
    print("[cache] bump %s -> %s" % (oldv, newv))
else:
    print("[cache] 未找到版本戳，跳过")

# ---- (4) 报告 ----
rep = ["# 字源 story 扩修报告（第二批 · B2）", ""]
rep.append("> 数据源：《说文解字》原文；仅修正 P1-4 抽检中**构字部件或本义明显错误**的待核字。")
rep.append("> 风格保持「字源故事·综合描述」，但删去与说文本义冲突的杜撰构件分析。")
rep.append("> 备份：`%s`" % os.path.basename(backup))
rep.append("")
rep.append("## 已订正（%d 字）" % len(applied))
rep.append("")
for ch, olen, nlen in applied:
    rep.append("- **%s**：原 %d 字 → 新 %d 字（依《说文》重写构件/本义）" % (ch, olen, nlen))
rep.append("")
rep.append("## 说明：以下待核字**未改动**（属故事化描写，本义未被矛盾，强行重写易引入新错）")
rep.append("- 数字/方位类（一、二、三、十、上、下、小、千之外）：多为象形/指事的通俗比喻，本义不冲突。")
rep.append("- 自然类（日、月、水、火、山、木、土、人、口）：象形如实，无错。")
rep.append("- 会意/形声凡构件正确者（公=八+厶背私、分=刀+八、仁=人+二、正=一+止、本=木+根、末=木+端、友=二又、从=二人、心=心形等）：均正确，保留。")
rep.append("")
rep.append("> 本次**未触及 data/dataset.bin**（字形二进制未改动）。")
open(os.path.join(BASE, "tools", "story_fix_B2.md"), "w", encoding="utf-8").write("\n".join(rep))

print("[applied] %d chars fixed:" % len(applied), [a[0] for a in applied])
print("[skipped] %d:" % len(skipped), skipped)
print("[backup] %s" % backup)
print("DONE")
