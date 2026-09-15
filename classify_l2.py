# -*- coding: utf-8 -*-
"""对 177 条疑似错误分类：串档(A) vs 古音折合(B)。"""
import json, io, os, glob, re
from pypinyin import pinyin, Style
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, '.workbuddy', 'charlist', 'shuowen', 'data')
APP = json.load(io.open(os.path.join(ROOT, 'data', 'characters.json'), encoding='utf-8'))['characters']

try:
    from opencc import OpenCC
    s2t = OpenCC('s2t'); t2s = OpenCC('t2s')
    CV = 'opencc'
except Exception:
    s2t = None; t2s = None; CV = 'none'

index_map = {}
for f in glob.glob(os.path.join(DATA_DIR, '*.json')):
    try:
        d = json.load(io.open(f, encoding='utf-8'))
    except Exception:
        continue
    for idx in d.get('indexes', []):
        index_map.setdefault(idx, d)
    index_map.setdefault(d.get('wordhead', ''), d)

def norm(s):
    return (s or '').strip().lower().replace('u:', 'ü').replace('v', 'ü')

def is_same_char(back, wh, trad):
    if not wh:
        return False
    if wh == back or wh == trad:
        return True
    if s2t and (s2t.convert(back) == wh or wh == trad):
        return True
    if t2s and t2s.convert(wh) == back:
        return True
    return False

A, B, C = [], [], []   # A=串档, B=同字(古音), C=无源
for c in APP:
    ch = c['char']
    app = c['pinyin']
    try:
        r = pinyin(ch, style=Style.TONE, heteronym=True)
        cand = [norm(x) for x in (r[0] if r else [])]
    except Exception:
        cand = []
    appset = set(norm(x) for x in re.split('[/|,，、;；]', app) if x.strip())
    if not cand or not (appset - set(cand)):
        continue
    e = index_map.get(ch) or index_map.get(c.get('trad', ''))
    if not e:
        C.append((ch, app, '/'.join(cand), '', '', '')); continue
    wh = e.get('wordhead', '')
    row = (ch, app, '/'.join(cand), wh, e.get('pinyin_full', ''), e.get('pronunciation', ''),
           (e.get('explanation') or '')[:22])
    if is_same_char(ch, wh, c.get('trad', '')):
        B.append(row)
    else:
        A.append(row)

def dump(name, rows):
    L = ['char\tapp\tpy_cand\tsrc_wordhead\tsrc_full\tfanqie\tsrc_expl'] + \
        ['\t'.join((x or '') for x in r) for r in rows]
    io.open(os.path.join(ROOT, name), 'w', encoding='utf-8').write('\n'.join(L))

dump('_cls_A.txt', A)
dump('_cls_B.txt', B)
dump('_cls_C.txt', C)
print('converter=%s  A(串档)=%d  B(同字古音)=%d  C(无源)=%d  total=%d' % (CV, len(A), len(B), len(C), len(A) + len(B) + len(C)))
