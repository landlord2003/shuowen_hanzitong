# -*- coding: utf-8 -*-
"""全量拼音声调核查：App 的 pinyin 字段 vs pypinyin 标准读音表。
输出三层：
  L1 通过（App 读音 ⊆ pypinyin 候选）
  L2 疑似错误（App 有读音完全不在 pypinyin 候选中）
  L3 待定（pypinyin 无候选）
"""
import json, io, os

ROOT = os.path.dirname(os.path.abspath(__file__))
APP = json.load(io.open(os.path.join(ROOT, 'data', 'characters.json'), encoding='utf-8'))['characters']

from pypinyin import pinyin, Style

def norm(s):
    s = s.strip().lower()
    s = s.replace('u:', 'ü').replace('v', 'ü').replace('ü', 'ü')
    return s

def split_multi(s):
    for sep in ('|', '/', ',', '，', '、', ';', '；'):
        s = s.replace(sep, '/')
    return [norm(x) for x in s.split('/') if x.strip()]

def dedup(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

ok, subset, mismatch, unknown = 0, [], [], []
for c in APP:
    ch = c['char']
    app_py = dedup(split_multi(c['pinyin']))
    try:
        r = pinyin(ch, style=Style.TONE, heteronym=True)
        cand = dedup([norm(x) for x in (r[0] if r else [])])
    except Exception:
        cand = []
    if not cand:
        unknown.append((ch, c['pinyin']))
        continue
    missing = [p for p in app_py if p not in cand]
    if missing:
        mismatch.append((ch, c['pinyin'], app_py, cand, missing))
    elif set(app_py) < set(cand):
        subset.append((ch, c['pinyin'], cand))
    else:
        ok += 1

lines = []
lines.append('App 字数 = %d' % len(APP))
lines.append('L1 通过（App 读音集合 == pypinyin 候选集合）= %d' % ok)
lines.append('L1b 通过（App 读音是 pypinyin 候选的真子集，即 App 只收录部分读音）= %d' % len(subset))
lines.append('L2 疑似错误（App 有读音不在 pypinyin 候选里）= %d' % len(mismatch))
lines.append('L3 待定（pypinyin 无候选，多为生僻/异体字）= %d' % len(unknown))
lines.append('')
lines.append('======== L2 疑似错误明细（App 拼音 | pypinyin 候选 | 冲突读音）========')
for ch, ap, apl, cand, missing in mismatch:
    lines.append('%s\t%s\t%s\t%s' % (ch, ap, '/'.join(cand), '/'.join(missing)))
lines.append('')
lines.append('======== L3 待定（pypinyin 无候选）========')
for ch, ap in unknown:
    lines.append('%s\t%s' % (ch, ap))
lines.append('')
lines.append('======== L1b 样例（App 单音，pypinyin 多音；前 60 条）========')
for ch, ap, cand in subset[:60]:
    lines.append('%s\t%s\t%s' % (ch, ap, '/'.join(cand)))

io.open(os.path.join(ROOT, '_pinyin_audit.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
print('done mismatch=%d unknown=%d subset=%d ok=%d' % (len(mismatch), len(unknown), len(subset), ok))
