# -*- coding: utf-8 -*-
"""简化本义字段：去掉"从X声/从X从Y/从XY"构形尾巴，保留纯释义。

策略：
1. 手动清单（MANUAL）处理正则难识别的无标记构形、构形在前、后起字空壳等
2. 正则删除形声/会意构形片段（含括号注释），再清理标点
3. dry-run 默认不落盘，加 --apply 落盘
"""
import json, re, sys

APPLY = "--apply" in sys.argv

# ============ 手动清单（正则难处理的情况） ============
MANUAL = {
    # 无标记构形（从X，无"声"无"从"结尾）
    "命": "发号施令",            # 从口令
    "原": "水源（源的本字）",    # 从厂泉
    "哥": "歌声（歌的本字）",    # 从二可
    "后": "后来居后",            # 从彳幺夂
    "局": "局限",                # 从口在尺下
    "光": "人头上火光，表示光亮",  # 从火在人上
    "忘": "心有所失",            # 从心上亡
    # 构形在前
    "神": "天地万物的创造者",    # 从示申声，...
    "草": "栎实（橡子），后借为草木之草",  # 从艸早声，...
    "爱": "行走从容之貌，后假借为仁爱、疼惜",  # 本义为...（从夊㤅声），...
    # 后起字空壳
    "们": "（后起字）表复数",
    "这": "迎也（出《玉篇》）",  # 同时修复 modern
    "她": "（近代新造字）女性第三人称代词",
    # 演变描述混杂
    "风": "空气流动",
    "明": "日月并照，光明",
    # 补充说明冗余
    "美": "羊大则味美",          # 从羊从大，会意甘美
    "年": "谷熟收成，引申为时间单位",
    "头": "首（脑袋）",          # 首也，从页豆声，本义脑袋
    "冰": "水凝结为冰",          # 从冫（冰）从水
    # 构形分散（从牛……勿聲）
    "物": "萬物也",
}

# "这"的今义字段错位修复（原 modern 是古义"迎也"，应改为今义指示代词）
MODERN_FIX = {"这": "这、此（指示代词）"}

# ============ 正则删除构形片段 ============
# 部件字符：汉字（含扩展区），排除标点/括号/空白
PART_SHORT = r"[^\s，。；、,;（）()]{1,4}"
PART_LONG = r"[^\s，。；、,;（）()]{1,6}"

# 形声：从X声/聲（可含"省"），可带括号注释
RE_XINGSHENG = re.compile(
    r"从" + PART_LONG + r"(?:省)?[声聲](?:[（(][^）)]*[）)])?"
)
# 会意：从X从Y[从Z]，可带括号注释
RE_HUIYI = re.compile(
    r"从" + PART_SHORT + r"从" + PART_SHORT + r"(?:从" + PART_SHORT + r")?(?:[（(][^）)]*[）)])?"
)


def clean(t):
    """清理删除构形后的残留标点（分号「；」是文言并列分隔，保留不动）。"""
    # 删空括号
    t = re.sub(r"[（(]\s*[）)]", "", t)
    # 连续逗号
    t = re.sub(r"[，,]{2,}", "，", t)
    # 逗号+句号 / 句号+逗号 -> 句号
    t = re.sub(r"[，,]\s*[。]", "。", t)
    t = re.sub(r"[。]\s*[，,]", "。", t)
    # 连续句号
    t = re.sub(r"[。]{2,}", "。", t)
    # 开头/结尾标点
    t = t.strip("，,。; ")
    return t


def simplify(char, text):
    """返回 (新本义, 是否改动)。"""
    if char in MANUAL:
        return MANUAL[char], True
    if not text:
        return text, False

    t = text
    # 先删会意（双从），再删形声（从X声）
    t = RE_HUIYI.sub("", t)
    t = RE_XINGSHENG.sub("", t)
    t = clean(t)

    if t and t != text:
        return t, True
    return text, False


def main():
    d = json.load(open("data/characters.json", encoding="utf-8"))["characters"]
    targets = [c for c in d if re.search(r"从[一-龥]", c.get("original", ""))]
    print(f"本义含「从」的字: {len(targets)} 字\n")

    changed_list = []
    unchanged_list = []
    for c in targets:
        orig = c.get("original", "")
        new, chg = simplify(c["char"], orig)
        if chg and new != orig:
            changed_list.append((c["char"], orig, new))
        else:
            unchanged_list.append((c["char"], orig))

    print("=" * 60)
    print(f"【将简化】{len(changed_list)} 字")
    print("=" * 60)
    for ch, o, n in changed_list:
        print(f"  {ch}: {o}")
        print(f"     → {n}")

    print()
    print("=" * 60)
    print(f"【不动】{len(unchanged_list)} 字")
    print("=" * 60)
    for ch, o in unchanged_list:
        print(f"  {ch}: {o}")

    if APPLY:
        apply_map = {ch: new for ch, o, new in changed_list}
        data = json.load(open("data/characters.json", encoding="utf-8"))
        n = 0
        for c in data["characters"]:
            if c["char"] in apply_map:
                c["original"] = apply_map[c["char"]]
                n += 1
            if c["char"] in MODERN_FIX:
                c["modern"] = MODERN_FIX[c["char"]]
        json.dump(data, open("data/characters.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n✅ 已落盘 {n} 字本义 + {len(MODERN_FIX)} 字今义修正")
    else:
        print("\n（dry-run 模式，未落盘。确认后加 --apply）")


if __name__ == "__main__":
    main()
