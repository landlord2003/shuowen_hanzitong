# -*- coding: utf-8 -*-
"""为 4605 新增字补充 trace_note：化学元素字、音译/拟声字甄别。"""
import json

BASE = r"D:\WorkBuddy\projects\说文解字"
CHARS = BASE + r"\data\characters.json"

# 化学元素字（118元素，古字书无此义或同名异义）
ELEMENTS = set("氢氦锂铍硼碳氮氧氟氖钠镁铝硅磷硫氯氩钾钙钪钛钒铬锰铁钴镍铜锌镓锗砷硒溴氪铷锶钇锆铌钼锝钌铑钯银镉铟锡锑碲碘氙铯钡镧铈镨钕钷钐铕钆铽镝钬铒铥镱镥铪钽钨铼锇铱铂金汞铊铅铋钋砹氡钫镭锕钍镤铀镎钚镅锔锫锎锿镄钔锘铹氘氚")

# 同名异义的元素字（古字书有古义，如铊=短矛、钴=熨斗、砷=砒、钋=金朴）
ELEMENT_HOMONYM = {
    "铊": "近代用作化学元素铊(Tl)，古「鉈」为短矛，同名异义",
    "钴": "近代用作化学元素钴(Co)，古「鈷」为熨斗，同名异义",
    "砷": "近代用作化学元素砷(As)，古「砷」为砒（砒霜），同名异义",
    "钋": "近代用作化学元素钋(Po)，古「釙」为金朴，同名异义",
    "铈": "近代用作化学元素铈(Ce)，古「鈰」为剑名，同名异义",
    "钽": "近代用作化学元素钽(Ta)，古「鉭」为锡块，同名异义",
    "铍": "近代用作化学元素铍(Be)，古「鈹」为长矛，同名异义",
    "钡": "近代用作化学元素钡(Ba)，古「鋇」为铁杖，同名异义",
}

# 明确拟声/音译字（古字书无实质古义，纯拟声/音译）
ONOMATOPOEIA = set("咔咣咚哐噼啪嚓啵唧嗡嘎嘭噔噜噌嘣嘁嘚噼咪唛唦嘀咚呛啷噼啦哐当")

data = json.load(open(CHARS, encoding="utf-8"))
chars = data["characters"]

n_elem = 0
n_elem_hom = 0
n_ono = 0
for c in chars:
    ch = c["char"]
    if c.get("trace_note"):
        continue  # 已标注的跳过
    if ch in ELEMENTS:
        if ch in ELEMENT_HOMONYM:
            c["trace_note"] = ELEMENT_HOMONYM[ch]
            n_elem_hom += 1
        else:
            c["trace_note"] = "化学元素字（近代新造），古字书无此字"
            n_elem += 1
    elif ch in ONOMATOPOEIA:
        c["trace_note"] = "拟声词/音译字，近代新造"
        n_ono += 1

json.dump(data, open(CHARS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"元素字(新造): {n_elem}, 元素字(同名异义): {n_elem_hom}, 拟声/音译: {n_ono}")
total = sum(1 for c in chars if c.get("trace_note"))
print(f"trace_note 总覆盖: {total}")
