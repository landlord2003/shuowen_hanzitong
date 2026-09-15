# -*- coding: utf-8 -*-
"""对比 App pinyin 与说文源 pinyin_full，确认 177 条疑似错误的来源。"""
import json, io, os, glob, re
from pypinyin import pinyin, Style
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, '.workbuddy', 'charlist', 'shuowen', 'data')
APP = json.load(io.open(os.path.join(ROOT, 'data', 'characters.json'), encoding='utf-8'))['characters']

# 建索引
index_map = {}
for f in glob.glob(os.path.join(DATA_DIR, '*.json')):
    try:
        d = json.load(io.open(f, encoding='utf-8'))
    except Exception:
        continue
    d['__file'] = os.path.basename(f)
    for idx in d.get('indexes', []):
        index_map.setdefault(idx, d)
    index_map.setdefault(d.get('wordhead', ''), d)

def norm(s):
    return (s or '').strip().lower().replace('u:', 'ü').replace('v', 'ü')

rows = []
src_keys = set()
for c in APP:
    ch = c['char']
    app = norm(c['pinyin'])
    try:
        r = pinyin(ch, style=Style.TONE, heteronym=True)
        cand = [norm(x) for x in (r[0] if r else [])]
    except Exception:
        cand = []
    apps = set(norm(x) for sep in ('|/', ',，、;；') for x in re.split('[' + re.escape(sep) + ']', app) if x.strip())
    if not cand or not (apps - set(cand)):
        continue
    e = index_map.get(ch) or index_map.get(c.get('trad', ''))
    if e:
        src_keys.update(k for k in e.keys() if k != '__file')
        rows.append((ch, c['pinyin'], '/'.join(cand), e.get('__file'),
                     e.get('wordhead'), e.get('pinyin'), e.get('pinyin_full'),
                     e.get('pronunciation'), (e.get('explanation') or '')[:20]))
    else:
        rows.append((ch, c['pinyin'], '/'.join(cand), '(NO-SRC)', '', '', '', '', ''))

out = ['char\tapp\tpy_cand\tsrc_file\twordhead\tsrc_pinyin\tsrc_pinyin_full\tsrc_pronunciation\tsrc_expl',
       '源记录字段 keys = ' + ','.join(sorted(src_keys)), '']
for r in rows:
    out.append('\t'.join((x or '') for x in r))
io.open(os.path.join(ROOT, '_l2_src.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('rows=%d' % len(rows))
