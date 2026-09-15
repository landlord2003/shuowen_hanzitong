# -*- coding: utf-8 -*-
"""生成 pinyin 字段改造映射：pinyin -> 现代规范读音；原值移交 pinyin_sw。
规则（最小改动）：
  A) pypinyin 无读音            -> 保持原值（pinyin_sw 仍存原值）
  B) 原读音集合 ⊆ pypinyin 候选 -> 现代音已具备；仅当库中首音非标准主音时把主音调到首位（不增不减）
  C) 否则（串档 / 古音折合）    -> 换成 pypinyin 全量候选（去重、pypinyin 序）
输出：_pinyin_map.json = { char: {"old":..., "new":...} }（仅列出发生变化的字）
      _pinyin_change.txt = 明细
"""
import json, io, os

ROOT = os.path.dirname(os.path.abspath(__file__))
D = json.load(io.open(os.path.join(ROOT, 'data', 'characters.json'), encoding='utf-8'))
CH = D['characters']

from pypinyin import pinyin, Style

def norm(s):
    s = str(s).strip().lower()
    return s.replace('u:', 'ü').replace('v', 'ü')

def dedup(seq):
    seen, out = set(), []
    for x in seq:
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out

def split_multi(s):
    for sep in ('|', '/', ',', '，', '、', ';', '；'):
        s = s.replace(sep, '/')
    return dedup([norm(x) for x in s.split('/') if x.strip()])

changed = {}
n_keep, n_reorder, n_replace, n_nocand = 0, 0, 0, 0
detail = []
for c in CH:
    ch = c['char']
    old = c.get('pinyin') or ''
    app = split_multi(old)
    try:
        cand = dedup([norm(x) for x in (pinyin(ch, style=Style.TONE, heteronym=True)[0] or [])])
        pri = norm(pinyin(ch, style=Style.TONE)[0][0]) if pinyin(ch, style=Style.TONE) else ''
    except Exception:
        cand, pri = [], ''

    if not cand:
        n_nocand += 1
        continue
    if set(app) <= set(cand):
        # 现代音已具备：原样保留（不动读序——pypinyin 的「主音」常取词内轻声，
        # 如 卜→bo、子→zi、似→shi，对字典类产品是退步；且会改变拼音排序位置）
        n_keep += 1
        continue
    else:
        new_list = list(cand)
        n_replace += 1
        kind = 'REPLACE'
    new = '/'.join([x for x in new_list if x])
    if new != old:
        changed[ch] = {'old': old, 'new': new}
        detail.append('%s\t%s\t%s\t%s' % (kind, ch, old, new))

json.dump(changed, io.open(os.path.join(ROOT, '_pinyin_map.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)

rep = []
rep.append('总字数 = %d' % len(CH))
rep.append('保持原值（读音均为现代规范音）= %d' % n_keep)
rep.append('整体替换为现代规范音（串档/古音折合）= %d' % n_replace)
rep.append('pypinyin 无读音·保持原值 = %d' % n_nocand)
rep.append('实际写入变化条数 = %d' % len(changed))
rep.append('')
rep.append('======== 明细 ========')
rep.extend(detail)
io.open(os.path.join(ROOT, '_pinyin_change.txt'), 'w', encoding='utf-8').write('\n'.join(rep))
print('done changed=%d keep=%d reorder=%d replace=%d nocand=%d' % (len(changed), n_keep, n_reorder, n_replace, n_nocand))
