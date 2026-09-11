#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1-4 字源 story 抽检（沙箱可执行版）
===================================
对 cultural.json 中 200 个代表字（Unicode 顺序前 200，覆盖高频常用字），
拉取汉典「基本解释」作为权威本义标杆，与 App 内 AI 生成的 story 字段做对照，
产出「汉典本义 vs App story」对照表 + 弱标记（本义核心义项是否出现在 story 中），
供人工/AI 复核 story 是否偏离本义。

不修改 App 任何数据，纯产出抽检报告。

用法：
  python tools/story_audit_200.py            # 抽前200字，写报告
  python tools/story_audit_200.py --n 50     # 抽前50字（快速自测）
"""
import json, urllib.request, ssl, re, os, time, sys, urllib.parse

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CULT = os.path.join(ROOT, "data", "cultural.json")
OUT_MD = os.path.join(ROOT, "tools", "story_audit_200.md")
OUT_JSON = os.path.join(ROOT, "tools", "story_audit_200.json")


def fetch(ch):
    enc = urllib.parse.quote(ch)
    u = "https://www.zdic.net/hans/" + enc
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception:
        return ""


def strip_tags(s):
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", s))


def basic_explanation(html):
    if not html:
        return ""
    poses = [m.start() for m in re.finditer("基本解释", html)]
    if len(poses) >= 2:
        seg = html[poses[1]:poses[1] + 1600]
        txt = strip_tags(seg)
        for kw in ["详细解释", "國語辭典", "康熙字典", "说文解字", "字源字形"]:
            j = txt.find(kw)
            if j > 0:
                txt = txt[:j]
                break
        txt = re.sub(r"^基本解释", "", txt)
        # 从「●」后截取真实义项（跳过 字+拼音+注音 前缀）
        i = txt.find("●")
        if i > 0:
            txt = txt[i + 1:]
        # 去掉注音符号（Bopomofo）
        txt = re.sub(r"[\u3105-\u312f]", "", txt)
        return txt[:200]
    return ""


def first_sense(bexp):
    """取「●」后第一个义项（到第一个句读），作为本义核心。"""
    if not bexp:
        return ""
    m = re.search(r"●(.+?)(?:。|；|，)", bexp)
    if m:
        return m.group(1).strip()
    return bexp[:24].strip()


def core_keywords(sense):
    """取义项中的 2-4 字中文词组，作为弱匹配词。"""
    if not sense:
        return []
    # 去掉标点，取连续汉字片段
    parts = re.findall(r"[一-鿿]{2,5}", sense)
    return parts[:3]


def main():
    n = 200
    for i, a in enumerate(sys.argv[1:]):
        if a == "--n" and i + 1 < len(sys.argv[1:]):
            n = int(sys.argv[i + 2])
    d = json.load(open(CULT, encoding="utf-8"))
    chars = [ch for ch, v in d.items() if v.get("story")][:n]

    rows = []
    for idx, ch in enumerate(chars):
        html = fetch(ch)
        bexp = basic_explanation(html)
        sense = first_sense(bexp)
        kws = core_keywords(sense)
        story = d[ch]["story"]
        hit = bool(kws) and any(kw in story for kw in kws)
        rows.append({
            "char": ch,
            "basic": bexp,
            "sense": sense,
            "story": story,
            "hit": hit,
            "keywords": kws,
        })
        if (idx + 1) % 20 == 0:
            print(f"  ... {idx+1}/{len(chars)} done", flush=True)
        time.sleep(0.08)

    json.dump(rows, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 生成 Markdown 对照表
    hit_n = sum(1 for r in rows if r["hit"])
    lines = []
    lines.append(f"# 字源 story 抽检对照表（{len(rows)} 字）\n")
    lines.append(f"> 数据源：汉典 zdic.net「基本解释」为权威本义标杆；App story 为 AI 生成综合描述。\n")
    lines.append(f"> 弱标记：**🟢 命中** = 本义核心词出现在 story；**🟡 待核** = 未直接命中，需人工/AI 判读（故事化描述未必逐字包含义项词，不代表错误）。\n")
    lines.append(f"> 命中统计：{hit_n}/{len(rows)} 直接命中；{len(rows)-hit_n} 待人工核。\n")
    lines.append("")
    lines.append("| # | 字 | 汉典本义（基本解释首义项） | App story（截取） | 标记 |")
    lines.append("|---|---|---|---|---|")
    for i, r in enumerate(rows):
        basic = (r["basic"][:60] + "…") if len(r["basic"]) > 60 else r["basic"]
        story = (r["story"][:70] + "…") if len(r["story"]) > 70 else r["story"]
        basic = basic.replace("|", "／").replace("\n", "")
        story = story.replace("|", "／").replace("\n", "")
        tag = "🟢命中" if r["hit"] else "🟡待核"
        lines.append(f"| {i+1} | {r['char']} | {basic} | {story} | {tag} |")
    lines.append("")
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(lines))

    print(f"DONE rows={len(rows)} hit={hit_n} pending={len(rows)-hit_n}")
    print(f"  -> {OUT_MD}")
    print(f"  -> {OUT_JSON}")


if __name__ == "__main__":
    main()
