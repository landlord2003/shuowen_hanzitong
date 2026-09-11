#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 01110be(P1重写+已含P0) 的 cultural.json 叠加「cultural 三类硬伤修复」：
  ① 10 字六书错标 story：按 data.liushu 权威值精准改写标签（不整文件覆盖，保留其余8095字内容）
  ② 成语字段污染：idioms 仅保留 4 汉字条目
  ③ 诗句出处编造（最高危）：全部 poems[].source 置「待考」，保留 line，剥离假署名
用法：python tools/fix_cultural_01110be.py  -> 写 /tmp/cultural_fixed.json
"""
import json, re, subprocess, sys

BASE = "01110be"

def git_show(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"]).decode("utf-8")

# ---- 载入 ----
cj = json.loads(git_show("data/characters.json"))
lm = {c["char"]: c.get("liushu", "") for c in cj["characters"]}
d = json.loads(git_show("data/cultural.json"))

# ---- ① 10 字六书错标：精准替换（带断言） ----
# 每字：(错误标签词, 正确标签词) 及可选部件修正
REPL = {
    "大":  [("指事字", "象形字")],
    "插":  [("「扌」和「杀」", "「扌」和「臿」（臿兼表声）"), ("会意字", "形声字")],
    "坂":  [("会意字", "形声字")],
    "苷":  [("会意字", "形声字")],
    "唏":  [("会意字", "形声字")],
    "耜":  [("会意字", "形声字")],
    "彀":  [("会意字", "形声字")],
    "彳":  [("会意字", "象形字")],
    "桊":  [("会意字", "形声字")],
    "蛑":  [("会意字", "形声字")],
}
story_fixed = 0
for k, reps in REPL.items():
    v = d.get(k)
    if not isinstance(v, dict):
        print("WARN 缺失字:", k); continue
    st = v.get("story", "")
    for old, new in reps:
        cnt = st.count(old)
        if cnt == 0:
            print(f"WARN {k}: 未找到「{old}」(story前40:{st[:40]})", file=sys.stderr)
            continue
        if cnt > 1:
            print(f"NOTE {k}: 「{old}」出现{cnt}次，全替换", file=sys.stderr)
        st = st.replace(old, new)
    v["story"] = st
    story_fixed += 1

# 复验：冲突应为 0
pat = re.compile(r"(形声|象形|会意|指事)字")
mism = [(k, m.group(1), lm[k]) for k, v in d.items() if isinstance(v, dict)
        for m in [pat.search(v.get("story", ""))]
        if m and lm.get(k, "") and m.group(1) not in lm.get(k, "")]
assert not mism, f"六书冲突未清零: {mism}"

# ---- ② 成语字段污染：仅留4汉字 ----
idiom_removed = 0
for k, v in d.items():
    if not isinstance(v, dict):
        continue
    ids = v.get("idioms")
    if isinstance(ids, list):
        before = len(ids)
        v["idioms"] = [it for it in ids if isinstance(it, dict) and len(it.get("w", "")) == 4]
        idiom_removed += before - len(v["idioms"])

# ---- ③ 诗句出处编造：全部置「待考」 ----
poem_fixed = 0
for k, v in d.items():
    if not isinstance(v, dict):
        continue
    for p in (v.get("poems") or []):
        if isinstance(p, dict) and p.get("source") != "待考":
            p["source"] = "待考"
            poem_fixed += 1

# ---- 写出 ----
out = "/tmp/cultural_fixed.json"
json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"OK 写出 {out}")
print(f"story_fixed={story_fixed} idiom_removed={idiom_removed} poem_fixed={poem_fixed}")
print(f"六书冲突复验={len(mism)}")
