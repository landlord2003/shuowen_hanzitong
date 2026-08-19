# -*- coding: utf-8 -*-
"""多音字专项：给现代常用多音字补注多个读音（手动维护的常用多音字表）。
只补注"确实有多个现代常用读音"的字，不补古音/生僻异读。
"""
import json

BASE = r"D:\WorkBuddy\projects\说文解字"
CHARS = BASE + r"\data\characters.json"

# 常用多音字表：char -> "读音1/读音2[/读音3]"
MULTI = {
    "行": "xíng/háng", "重": "zhòng/chóng", "长": "cháng/zhǎng", "乐": "lè/yuè",
    "觉": "jué/jiào", "校": "xiào/jiào", "调": "tiáo/diào", "得": "dé/de/děi",
    "地": "dì/de", "的": "de/dí/dì", "着": "zhe/zháo/zhuó", "参": "cān/shēn",
    "差": "chà/chā/cī", "数": "shù/shǔ", "朝": "cháo/zhāo", "盛": "shèng/chéng",
    "传": "chuán/zhuàn", "假": "jiǎ/jià", "冠": "guān/guàn", "几": "jī/jǐ",
    "了": "le/liǎo", "大": "dà/dài", "少": "shǎo/shào", "都": "dōu/dū",
    "和": "hé/hè/huó/huò", "省": "shěng/xǐng", "强": "qiáng/qiǎng/jiàng",
    "应": "yīng/yìng", "处": "chǔ/chù", "种": "zhǒng/zhòng", "奇": "qí/jī",
    "间": "jiān/jiàn", "弹": "dàn/tán", "藏": "cáng/zàng", "空": "kōng/kòng",
    "降": "jiàng/xiáng", "解": "jiě/jiè", "载": "zǎi/zài", "转": "zhuǎn/zhuàn",
    "卡": "kǎ/qiǎ", "佛": "fó/fú", "率": "lǜ/shuài", "恶": "è/wù/ě",
    "吓": "xià/hè", "咽": "yān/yàn/yè", "宿": "sù/xiǔ", "累": "lèi/lěi",
    "量": "liáng/liàng", "难": "nán/nàn", "磨": "mó/mò", "喝": "hē/hè",
    "薄": "báo/bó", "落": "luò/là", "露": "lù/lòu", "更": "gēng/gèng",
    "给": "gěi/jǐ", "蒙": "méng/mēng", "塞": "sāi/sài/sè", "倒": "dǎo/dào",
    "当": "dāng/dàng", "看": "kàn/kān", "发": "fā/fà", "干": "gān/gàn",
    "教": "jiāo/jiào", "便": "biàn/pián", "铺": "pū/pù", "折": "zhé/shé",
    "漂": "piāo/piào", "扇": "shàn/shān", "撒": "sā/sǎ", "相": "xiāng/xiàng",
    "担": "dān/dàn", "涨": "zhǎng/zhàng", "钻": "zuān/zuàn", "曲": "qǔ/qū",
    "缝": "féng/fèng", "笼": "lóng/lǒng", "圈": "quān/juàn", "背": "bèi/bēi",
    "尽": "jìn/jǐn", "好": "hǎo/hào", "要": "yào/yāo", "吐": "tǔ/tù",
    "切": "qiè/qiē", "划": "huá/huà", "为": "wéi/wèi", "兴": "xīng/xìng",
    "结": "jié/jiē", "会": "huì/kuài", "还": "hái/huán", "没": "méi/mò",
    "只": "zhǐ/zhī", "中": "zhōng/zhòng", "作": "zuò/zuō", "鲜": "xiān/xiǎn",
    "血": "xiě/xuè", "嚼": "jiáo/jué", "乐": "lè/yuè", "数": "shù/shǔ",
    # 生僻字多音
    "陂": "bēi/pí", "泌": "mì/bì", "泌": "mì/bì", "拗": "ào/niù",
    "拓": "tuò/tà", "拓": "tuò/tà", "蚌": "bàng/bèng", "臂": "bì/bei",
    "扁": "biǎn/piān", "屏": "píng/bǐng", "澄": "chéng/dèng", "冲": "chōng/chòng",
    "臭": "chòu/xiù", "畜": "chù/xù", "创": "chuàng/chuāng", "答": "dá/dā",
    "逮": "dài/dǎi", "单": "dān/chán/shàn", "的": "de/dí/dì", "度": "dù/duó",
    "囤": "dùn/tún", "佛": "fó/fú", "杆": "gān/gǎn", "骨": "gǔ/gū",
    "还": "hái/huán", "巷": "xiàng/hàng", "荷": "hé/hè", "核": "hé/hú",
    "横": "héng/hèng", "糊": "hú/hù/hū", "华": "huá/huà", "晃": "huǎng/huàng",
    "混": "hùn/hún", "豁": "huō/huò", "济": "jì/jǐ", "系": "xì/jì",
    "夹": "jiā/jiá/gā", "贾": "jiǎ/gǔ", "渐": "jiàn/jiān", "将": "jiāng/jiàng",
    "浆": "jiāng/jiàng", "角": "jiǎo/jué", "剿": "jiǎo/chāo", "禁": "jìn/jīn",
    "劲": "jìn/jìng", "经": "jīng/jìng", "卷": "juàn/juǎn", "隽": "juàn/jùn",
    "壳": "ké/qiào", "勒": "lè/lēi", "俩": "liǎ/liǎng", "撩": "liáo/liāo",
    "淋": "lín/lìn", "令": "lìng/líng", "溜": "liū/liù", "搂": "lǒu/lōu",
    "陆": "lù/liù", "率": "lǜ/shuài", "绿": "lǜ/lù", "论": "lùn/lún",
    "抹": "mǒ/mā/mò", "吗": "ma/má/mǎ", "埋": "mái/mán", "蔓": "màn/wàn/mán",
    "眯": "mī/mí", "模": "mó/mú", "摩": "mó/mā", "泥": "ní/nì",
    "宁": "níng/nìng", "拧": "níng/nǐng/nìng", "弄": "nòng/lòng", "胖": "pàng/pán",
    "刨": "páo/bào", "炮": "pào/páo/bāo", "泡": "pào/pāo", "喷": "pēn/pèn",
    "劈": "pī/pǐ", "片": "piàn/piān", "撇": "piē/piě", "朴": "pǔ/piáo/pō",
    "期": "qī/jī", "抢": "qiǎng/qiāng", "悄": "qiāo/qiǎo", "翘": "qiào/qiáo",
    "亲": "qīn/qìng", "圈": "quān/juàn", "任": "rèn/rén", "散": "sàn/sǎn",
    "丧": "sàng/sāng", "扫": "sǎo/sào", "色": "sè/shǎi", "刹": "chà/shā",
    "煞": "shà/shā", "稍": "shāo/shào", "舍": "shè/shě", "甚": "shèn/shén",
    "什": "shén/shí", "识": "shí/zhì", "拾": "shí/shè", "说": "shuō/shuì",
    "似": "sì/shì", "伺": "sì/cì", "遂": "suì/suí", "缩": "suō/sù",
    "踏": "tà/tā", "台": "tái/tāi", "汤": "tāng/shāng", "趟": "tàng/tāng",
    "提": "tí/dī", "挑": "tiāo/tiǎo", "帖": "tiē/tiě/tiè", "通": "tōng/tòng",
    "同": "tóng/tòng", "吐": "tǔ/tù", "褪": "tuì/tùn", "瓦": "wǎ/wà",
    "尾": "wěi/yǐ", "尉": "wèi/yù", "系": "xì/jì", "吓": "xià/hè",
    "巷": "xiàng/hàng", "削": "xuē/xiāo", "熏": "xūn/xùn", "燕": "yàn/yān",
    "叶": "yè/xié", "遗": "yí/wèi", "殷": "yīn/yān", "饮": "yǐn/yìn",
    "应": "yīng/yìng", "佣": "yōng/yòng", "与": "yǔ/yù", "吁": "xū/yù",
    "员": "yuán/yùn", "晕": "yūn/yùn", "攒": "zǎn/cuán", "脏": "zàng/zāng",
    "择": "zé/zhái", "曾": "céng/zēng", "扎": "zhā/zā/zhá", "轧": "zhá/yà/gá",
    "粘": "zhān/nián", "召": "zhào/shào", "正": "zhèng/zhēng", "症": "zhèng/zhēng",
    "只": "zhǐ/zhī", "赚": "zhuàn/zuàn", "着": "zhe/zháo/zhuó", "种": "zhǒng/zhòng",
}

data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]
n = 0
for c in chars:
    ch = c["char"]
    if ch in MULTI:
        c["pinyin"] = MULTI[ch]
        n += 1

json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"多音字补注: {n} 字")
for ch in ["行", "重", "长", "乐", "和", "血", "薄", "着", "给", "教"]:
    c = next((x for x in chars if x["char"] == ch), None)
    if c:
        print(f"  {ch}: {c['pinyin']}")
