#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""六书交叉校验（dry-run）：精确识别说文构形的声符，找出误判"""
import json
import re

auth = json.load(open('.workbuddy/charlist/authoritative_fields.json', encoding='utf-8'))
chars = json.load(open('data/characters.json', encoding='utf-8'))['characters']
cur = {c['char']: c for c in chars}

def precise_liushu(sw):
    """精确六书推导（排除"五聲八音""聲也"等词义干扰）"""
    # 1. 构形声符：从...X聲/X声（"从"之后到句号之间含"聲/声"且前面是声符字）
    if re.search(r'从[^。]*[一-龥](?:亦|省)?(?:聲|声)', sw):
        return '形声'
    # 2. 指事（明确标注）
    if '指事' in sw:
        return '指事'
    # 3. 象形
    if '象形' in sw or re.search(r'象[^。]{0,6}之?形', sw):
        return '象形'
    # 4. 会意：从X从Y / 从X、Y
    if re.search(r'从[一-龥][^。]*从', sw):
        return '会意'
    return ''

# 找出当前是会意/象形，但精确推导是形声的字
to_xingsheng = []
for ch, a in auth.items():
    if not a.get('matched'):
        continue
    c = cur.get(ch)
    if not c or c.get('liushu') not in ('会意', '象形'):
        continue
    precise = precise_liushu(a.get('shuowen', ''))
    if precise == '形声':
        to_xingsheng.append((ch, c['liushu'], a.get('shuowen', '')[:35]))

print(f'=== 应改回形声的字: {len(to_xingsheng)} ===')
for ch, from_, sw in to_xingsheng:
    print(f'{ch}[{from_}]: {sw}')

# 找出当前是形声，但精确推导是会意/象形的字（derive_liushu 误判，如"乐""哥"）
print()
print('=== 当前形声，但精确推导不是形声（derive 误判） ===')
for ch, a in auth.items():
    if not a.get('matched'):
        continue
    c = cur.get(ch)
    if not c or c.get('liushu') != '形声':
        continue
    precise = precise_liushu(a.get('shuowen', ''))
    if precise in ('会意', '象形', ''):
        label = precise or '?'
        print(f'{ch}[形声→{label}]: {a.get("shuowen","")[:35]}')
