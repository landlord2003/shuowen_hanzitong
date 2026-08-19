# -*- coding: utf-8 -*-
import json

PATH = 'data/characters.json'

# A. 化学元素字 81 个
A = '钇氖钋钌氙钍钒钕钚钛钡钨钫钯氡氟砹砷钴钽钼铀铂铈铊铋铌铍氩氦硒铑铒铟铪铬铯铱铷氪铼锂锆锇锑锔锕硼锗锝溴碲锶镁镉镍镓镝镧镭钆钐钔钪钬钷铕铥铹铽锎锘锫锿镄镅镎镤镥镨镱'

# A1. 有实质古义 -> 同名异义（33 个）
A_SAME = {
    '钌': '近代用作化学元素钌，古「钌」为鋌釕（带头饰），同名异义',
    '钒': '近代用作化学元素钒，古「钒」为拂、杯（器名），同名异义',
    '钡': '近代用作化学元素钡，古「钡」为鋌（金属条），同名异义',
    '钨': '近代用作化学元素钨，古「钨」为鎢錥（小釜、温器），同名异义',
    '钫': '近代用作化学元素钫，古「钫」为方钟、镬属，同名异义',
    '钯': '近代用作化学元素钯，古「钯」为兵车、耙，同名异义',
    '钴': '近代用作化学元素钴，古「钴」为鈷䥈（熨斗）、盛黍稷器，同名异义',
    '铂': '近代用作化学元素铂，古「铂」为金薄（金箔），同名异义',
    '铈': '近代用作化学元素铈，古「铈」为剑名，同名异义',
    '铊': '近代用作化学元素铊，古「铊」为短矛，同名异义',
    '铋': '近代用作化学元素铋，古「铋」为矛柄，同名异义',
    '铌': '近代用作化学元素铌，古「铌」为络丝柎（绕丝工具），同名异义',
    '铍': '近代用作化学元素铍，古「铍」为大针、剑，同名异义',
    '铑': '近代用作化学元素铑，古「铑」为大铁钱名，同名异义',
    '铒': '近代用作化学元素铒，古「铒」为钩，同名异义',
    '铪': '近代用作化学元素铪，古「铪」为声、鋋（二尺鋌），同名异义',
    '铬': '近代用作化学元素铬，古「铬」为剃发、钩，同名异义',
    '锑': '近代用作化学元素锑，古「锑」为鎕銻（火齐珠名），同名异义',
    '锔': '近代用作化学元素锔，古「锔」为以铁缚物（锔子），同名异义',
    '锕': '近代用作化学元素锕，古「锕」为鈳䥈（釜属），同名异义',
    '硼': '近代用作化学元素硼，古「硼」为石名、硼砂，同名异义',
    '锗': '近代用作化学元素锗，古「锗」为车𨰓（车上零件），同名异义',
    '溴': '近代用作化学元素溴，古「溴」为水气，同名异义',
    '锶': '近代用作化学元素锶，古「锶」为铁器，同名异义',
    '镉': '近代用作化学元素镉，古「镉」为鼎属（与鬲同），同名异义',
    '镝': '近代用作化学元素镝，古「镝」为箭头，同名异义',
    '镧': '近代用作化学元素镧，古「镧」为金光貌，同名异义',
    '镭': '近代用作化学元素镭，古「镭」为瓶、壶，同名异义',
    '钷': '近代用作化学元素钷，古「钷」为鉕鐸（铜器），同名异义',
    '锘': '近代用作化学元素锘，古「锘」为取，同名异义',
    '锫': '近代用作化学元素锫，古「锫」为錇鏂（钉名），同名异义',
    '镅': '近代用作化学元素镅，古「镅」为大锁（子母环），同名异义',
    '镤': '近代用作化学元素镤，古「镤」为矢名、生铁，同名异义',
}

# B. 口旁字 147 个
B = '叵叱呋呒呖呃吡呗吽吣吲咂呸咔咀呷呱呤咆咛呶呣呦咎哂咴咦哓哔呲咣哕咻咿哌哙咯咩咤哝咫哧哽唏唑啬啧喏啉唵啭啁啕唿啐唼唷啖唳唰啜喋嗒喃喈喁喟啾嗖喑嗟喽嗞喀喔喙啻喾嗷嗉嘟嗑嗫嗔嗝嗄嗣嗳嗌嗍嗐嗤嘈嘌嘁嘎嘘嘤嘚嗾嘭噎噶嘬噍噢噜噌噔嚄嚆噤噱噬噫嚅嚯吒呙㕮呇咉咇咍咡咺哒咥哃哢唝哳哱哿唪啴喆喤𫫇嘏噇噂噀亸嚚冁嚭'

# B2. 拟声词（26 个）
B_ONO = '呖呸咔呣咴咣咻咿咯咩哧唰嘟嘎嘚嘭噔噌哒哱唷嗖嗒喀噢嚯'

# B2. 音译字（10 个）
B_TRANS = '呋吡吲唑嘌𫫇啉哌哔噶'

NOTE_ONO = '拟声词，近代新造'
NOTE_TRANS = '音译字，古字书无此字'
NOTE_NEW = '化学元素字（近代新造），古字书无此字'

# 校验：A 集合 81 个，A_SAME 是子集
setA = set(A)
assert len(setA) == 81, f'A 集合数量 {len(setA)} != 81'
assert set(A_SAME.keys()) <= setA, 'A_SAME 有不在 A 中的字'
A_NEW = setA - set(A_SAME.keys())

setB = set(B)
assert len(setB) == 147, f'B 集合数量 {len(setB)} != 147'
setB_ONO = set(B_ONO)
setB_TRANS = set(B_TRANS)
assert setB_ONO <= setB, 'B_ONO 有不在 B 中的字'
assert setB_TRANS <= setB, 'B_TRANS 有不在 B 中的字'
assert not (setB_ONO & setB_TRANS), 'B_ONO 与 B_TRANS 有交集'
B_KEEP = setB - setB_ONO - setB_TRANS

# 构建最终映射
mapping = {}
for ch in A_SAME:
    mapping[ch] = A_SAME[ch]
for ch in A_NEW:
    mapping[ch] = NOTE_NEW
for ch in setB_ONO:
    mapping[ch] = NOTE_ONO
for ch in setB_TRANS:
    mapping[ch] = NOTE_TRANS

assert len(mapping) == 81 + len(setB_ONO) + len(setB_TRANS), 'mapping 数量不对'

# 读取、遍历、写回
with open(PATH, encoding='utf-8') as f:
    data = json.load(f)

cnt_elem_same = 0
cnt_elem_new = 0
cnt_ono = 0
cnt_trans = 0
cnt_keep = 0
found = set()

for c in data['characters']:
    ch = c.get('char')
    if ch in mapping:
        c['trace_note'] = mapping[ch]
        found.add(ch)
        if ch in A_SAME:
            cnt_elem_same += 1
        elif ch in A_NEW:
            cnt_elem_new += 1
        elif ch in setB_ONO:
            cnt_ono += 1
        elif ch in setB_TRANS:
            cnt_trans += 1
    elif ch in B_KEEP:
        # 正常古字，保持空（不添加字段）
        cnt_keep += 1
        found.add(ch)

# 校验所有目标字都被处理
all_target = setA | setB
assert found == all_target, f'有未处理的字: {all_target - found}'

with open(PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

print('=== 统计 ===')
print(f'化学元素字标注：{cnt_elem_same + cnt_elem_new} 个（同名异义 {cnt_elem_same}，新造 {cnt_elem_new}）')
print(f'拟声/音译字标注：{cnt_ono + cnt_trans} 个（拟声 {cnt_ono}，音译 {cnt_trans}）')
print(f'口旁古字保持空：{cnt_keep} 个')
print(f'合计处理：{len(all_target)} 个')
