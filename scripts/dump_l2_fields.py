# -*- coding: utf-8 -*-
import json, io, os
from pypinyin import pinyin, Style
ROOT = os.path.dirname(os.path.abspath(__file__))
APP = json.load(io.open(os.path.join(ROOT, 'data', 'characters.json'), encoding='utf-8'))['characters']

def norm(s):
    return s.strip().lower().replace('u:', 'ü').replace('v', 'ü')

out = []
for c in APP:
    ch = c['char']
    app = norm(c['pinyin'])
    try:
        r = pinyin(ch, style=Style.TONE, heteronym=True)
        cand = [norm(x) for x in (r[0] if r else [])]
    except Exception:
        cand = []
    appset = set()
    for sep in ('|', '/', ',', '，', '、', ';', '；'):
        for x in app.replace(sep, '/').split('/'):
            if x.strip(): appset.add(norm(x))
    if not cand or not (appset - set(cand)):
        continue
    def cut(s, n):
        s = (s or '').replace('\t', ' ').replace('\n', ' ')
        return s[:n]
    out.append('\t'.join([
        ch,
        c['pinyin'],
        '/'.join(cand),
        cut(c.get('fanqie'), 20),
        cut(c.get('shuowen'), 34),
        cut(c.get('duan_note'), 40),
        cut(c.get('trad'), 4),
        cut(c.get('variant'), 30),
        str(c.get('strokes', '')),
    ]))

io.open(os.path.join(ROOT, '_l2_fields.txt'), 'w', encoding='utf-8').write(
    'char\tapp_pinyin\tpy_cand\tfanqie\tshuowen\tduan_note\ttrad\tvariant\tstroke\n' + '\n'.join(out))
print('rows=' + str(len(out)))
