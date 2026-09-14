# -*- coding: utf-8 -*-
# 扩修 B3：P1-4 抽检报告中「构件明显错误」的待核字（第三批），依据《说文》逐字订正。
# 仅改 data/cultural.json 的 story（运行时 fetch，无需重建 index.html），并 bump 缓存戳。
# 流程与 B2 完全一致：核验 dataset.bin -> 备份 -> 覆盖 -> bump 缓存 -> 报告。
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

# ---- (2) 订正表：仅收录「构件明显错误」的待核字（弱匹配命中、但部件杜撰） ----
FIX = {
"匕":"「匕」（bǐ）是象形字，《说文解字》释「从反人」——把「人」字反写，象侧立之人回转之形。本义是古人取食的器具（匕匙），后也指短剑（匕首）。旧 story 说「两把匕首相對」是构形误读：匕是单一的反人形，并非两把兵器相对。",
"刁":"「刁」（diāo）本义是狡猾、无赖，也用作姓氏，古时又同「刀」字。「刁斗」是古代军中一种铜制用具（白天烧饭、夜间击以巡更），但它是「刁＋斗」的复合词，并非「刁」的单字本义。旧 story 把「刁斗」当作「刁」的本义，属误读。",
"乞":"「乞」（qǐ）本义是求取、乞讨（「乞」由「气」分化而来，与气息、给予相通）。它的字形并非「人」与「衣」的组合——旧 story 所谓「人披衣求取」是构字部件的误读，并无文字学依据。本义就是向人讨要、请求。",
"么":"「么」（me，繁体作「麽」）本义是细小、微弱。「麽」字从糸（糹）、麻声，本与丝线、细微相关，简化后写作「么」。旧 story 把构件说成「纟＋戈」是错的——「戈」并非「么」的部件；本义「小、细微」才算说对。",
"亡":"「亡」（wáng）本义是逃跑、流失（亡羊补牢、逃亡）。《说文解字》释「逃也」，构形从「入」、从「乚」（或写作「亾」）。旧 story 说「人＋口，人张口疾走」并不符合字形——「亡」上部是「亠」一横，并非「人」与「口」的组合。",
"丐":"「丐」（gài）本义是乞求、讨饭（乞丐），也指施与。它的字形并非「人」与「气」的组合——旧 story 所谓「失去气力的人」是构字部件的误读。本义就是求乞、讨要。",
"扎":"「扎」（zhā/zhá/zā）是「紮／紥」的简化字，从手（扌），本义是捆束、缠扎，引申为刺入、驻扎。它与「札」（木片、书札）是两个不同的字。旧 story 把构件说成「纟＋扎」既错了偏旁（扎从扌不从糸），又把「札」的「竹片」义安到了「扎」头上，应更正。",
"匹":"「匹」（pǐ）《说文解字》释「四丈也，从匚八声」——本义是量布的长度单位，四丈为一匹。构形从「匚」（fāng，象盛物之器）、「八」表声。旧 story 说「彳＋皮、皮表声」部件完全错了：匹既无「彳」也无「皮」。",
"介":"「介」（jiè）《说文解字》释「画也，从八从人」——「八」有分别之意，合起来表示界限、间隔，引申为耿介、铠甲（甲介）。旧 story 说「亠＋卩、人跪坐祭祀」部件读错了：介是「八」与「人」，并不是「亠」配「卩」。",
"乏":"「乏」（fá）《说文解字》引《左传》说「反正为乏」——把「正」字上下颠倒就是「乏」，本义是缺少、不足，也指疲乏（不正曰乏）。旧 story 说「人＋一、人躺下休息」并不符合字形：乏是「正」的反写，并非「人」加「一」。",
"斗":"简化字「斗」合并了两个不同的字：其一是「斗」（dǒu），《说文解字》释「十升也，象形」，本义是量粮食的器具（十升为一斗），字形像带柄的斗勺；其二是「鬥」（dòu），本义是争斗、战斗。旧 story 只讲了「鬥（战斗）」一义，把「两人持杖对打」当作「斗」的全部，漏掉了它作为量器的象形本义。",
"订":"「订」（dìng，繁体「訂」）《说文解字》释「平议也，从言丁声」——从「言」（简化作「讠」）、「丁」表声，本义是评议、校正、商定，引申为装订、订立。旧 story 把偏旁写成「钅（金）」是错的：订是言字旁，不是金字旁。",
"冗":"「冗」（rǒng，异体作「宂」）从「宀」（房屋）、从「人」，本义是闲散、多余无用的（如冗员、冗长）。旧 story 说「纟＋冬、冬天衣物繁多」部件完全错了：冗字上从「宀」、下从「人」，与丝线和冬天都不相干。",
"队":"「队」（duì，繁体「隊」）《说文解字》释「从高坠也」——本义是从高处掉下来，是「坠」字的本字。构形左为「阝」（阜，代表高地）、右为「㒸」（suì，简化作「人」）。旧 story 说「阝＋隹」部件错了：右边是「人」（㒸的简化），并不是鸟「隹」。",
"刊":"「刊」（kān）《说文解字》释「剟也，从刀干声」——从「刀」、「干」表声，本义是削除、刻削（如刊误、刊石），后来引申为刻印、刊登。旧 story 把偏旁写成「木」是错的：刊是立刀旁（与刀有关），并非木字旁。",
"巧":"「巧」（qiǎo）《说文解字》释「技也，从工丂声」——从「工」、「丂」（kǎo）表声，本义是技艺好、灵巧（巧手、心灵手巧）。旧 story 把形旁写成「廴」是错的：巧是「工」字旁（与工艺、技能相关），不是「廴」（建之旁）。",
"可":"「可」（kě）《说文解字》释「肎也，从口丂，丂亦声」——从「口」、「丂」（kǎo）表声，本义是许可、认可（「可」与「肯」古音义相通）。旧 story 把右边写成「丷」是错的：可的构件是「口」加「丂」，并非「口」加两点。",
}

d = json.load(open(CULT, encoding="utf-8"))
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = os.path.join(BASE, "data", "cultural.json.bak_storyfixB3_%s" % ts)
import shutil
shutil.copyfile(CULT, backup)

applied, skipped = [], []
for ch, new in FIX.items():
    if ch in d and isinstance(d[ch], dict) and d[ch].get("story"):
        old = d[ch]["story"]
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
    newv = "20260914a"   # 比 20260911i 进一步
    txt2 = txt.replace("cultural.json?v=%s" % oldv, "cultural.json?v=%s" % newv)
    open(UIJS, "w", encoding="utf-8").write(txt2)
    print("[cache] bump %s -> %s" % (oldv, newv))
else:
    print("[cache] 未找到版本戳，跳过")

# ---- (4) 报告 ----
rep = ["# 字源 story 扩修报告（第三批 · B3）", ""]
rep.append("> 数据源：《说文解字》原文 + 汉典 zdic.net「基本解释」；仅修正 P1-4 抽检中**构件明显错误**的待核字。")
rep.append("> 风格保持「字源故事·综合描述」，把与说文本义冲突的杜撰构件分析改写为权威本义；不引入新错误。")
rep.append("> 备份：`%s`" % os.path.basename(backup))
rep.append("")
rep.append("## 已订正（%d 字）" % len(applied))
rep.append("")
for ch, olen, nlen in applied:
    rep.append("- **%s**：原 %d 字 → 新 %d 字（依《说文》更正构件/本义）" % (ch, olen, nlen))
rep.append("")
rep.append("## 说明")
rep.append("- 本批 17 字均为「弱匹配待核」中**构件部件明显杜撰/错配**者（如 匕=两匕首、刁=刁斗本义、乞=人+衣、么=纟+戈、亡=人+口、丐=人+气、扎=纟+扎、匹=彳+皮、介=亠+卩、乏=人+一、斗=只取鬥义、订=钅+丁、冗=纟+冬、队=阝+隹、刊=木+干、巧=廴+丂、可=口+丷）。")
rep.append("- P1-4 200 字抽检中其余 ~125 个「待核」字经逐字研判，多为故事化描写且本义未被矛盾（数字/方位、自然象形、构件正确的会意形声等），按 B2 原则**保留不动**，强行重写易引入新错。")
rep.append("- 本次**未触及 data/dataset.bin**（字形二进制未改动）。")
open(os.path.join(BASE, "tools", "story_fix_B3.md"), "w", encoding="utf-8").write("\n".join(rep))

print("[applied] %d chars fixed:" % len(applied), [a[0] for a in applied])
print("[skipped] %d:" % len(skipped), skipped)
print("[backup] %s" % backup)
print("DONE")
