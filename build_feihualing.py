# -*- coding: utf-8 -*-
"""构建飞花令数据 data/feihualing.json
仅取「本身即简体」的诗句（zhconv 守卫，零转换风险），来源排除繁体源（全唐诗/四书五经/蒙学）。
"""
import os, json, re, random
from zhconv import convert

BASE = r'D:\WorkBuddy\projects\说文解字'
CB = os.path.join(BASE, 'tools', 'poetry_corpus')
random.seed(20260911)

SPLIT = re.compile(r'[。！？；，、：]')
BAD = re.compile(r'[A-Za-z0-9]|[「」『』（）()\[\]{}<>《》\u3000]|\.\.\.')


def is_simp(s):
    return convert(s, 'zh-hans') == s


def clean(s):
    return s.strip().strip('“”"\'‘’ ')


def segs_of(text):
    out = []
    for p in SPLIT.split(text):
        p = clean(p)
        if 4 <= len(p) <= 18 and not BAD.search(p):
            out.append(p)
    return out


def load(name):
    p = os.path.join(CB, name)
    if os.path.isdir(p):
        rows = []
        for f in sorted(os.listdir(p)):
            if not f.endswith('.json'):
                continue
            try:
                j = json.load(open(os.path.join(p, f), encoding='utf-8'))
            except Exception:
                continue
            rows.extend(j if isinstance(j, list) else [j])
        return rows
    return json.load(open(p, encoding='utf-8'))


def label_of(src, r):
    a = r.get('author') or ''
    if src == '诗经':
        return '《诗经·%s·%s》' % (r.get('section') or '', r.get('title') or '')
    if src == '曹操诗集':
        return '曹操·《%s》' % (r.get('title') or '')
    if src == '元曲':
        return '%s·《%s》' % (a, r.get('title') or '')
    if src in ('宋词',):
        return '%s·《%s》' % (a, r.get('rhythmic') or r.get('title') or '')
    if src == '楚辞':
        return '%s·《%s》' % (r.get('author') or '', r.get('title') or '')
    if src == '纳兰性德':
        return '纳兰性德·《%s》' % (r.get('title') or r.get('rhythmic') or '')
    return a


SOURCES = ['宋词', '元曲', '诗经', '楚辞', '曹操诗集', '纳兰性德']

segments = []          # (句, 出处)
poems = 0
dropped_trad = 0
for src in SOURCES:
    try:
        rows = load(src)
    except Exception as e:
        print('!! load fail', src, e)
        continue
    if not isinstance(rows, list):
        rows = [rows]
    poems += len(rows)
    for r in rows:
        lab = label_of(src, r)
        for key in ('paragraphs', 'content', 'para'):
            for para in (r.get(key) or []):
                for s in segs_of(para):
                    if not is_simp(s):
                        dropped_trad += 1
                        continue
                    segments.append((s, lab))
    print('%-8s 累计诗句 %d' % (src, len(segments)))

# 去重
seen = set(); uniq = []
for s, lab in segments:
    if s in seen:
        continue
    seen.add(s); uniq.append((s, lab))
segments = uniq
print('\n诗篇 %d，可用简体句 %d（丢弃含繁体字句 %d）' % (poems, len(segments), dropped_trad))

# 令字候选
CAND = list('花月风春山水云天日人酒雨江秋雪夜心情白红青千万里来时生家客舟长空明高寒归')
cnt = {}
for ch in CAND:
    cnt[ch] = sum(1 for s, _ in segments if ch in s)
print('\n令字频次:')
for ch in sorted(cnt, key=lambda c: -cnt[c]):
    print('  %s %d' % (ch, cnt[ch]))

POOL = [ch for ch in CAND if cnt[ch] >= 150]
print('\n入池令字 %d 个' % len(POOL))

random.shuffle(segments)
chars = {}
chosen = set()
for ch in POOL:
    hits = [x for x in segments if ch in x[0]]
    # 优先长度 5~12 的短句，去掉过长
    hits.sort(key=lambda x: (abs(len(x[0]) - 7), len(x[0])))
    chars[ch] = [[s, lab] for s, lab in hits[:240]]
    chosen.update(s for s, _ in chars[ch])
    print('  %s → %d 句' % (ch, len(chars[ch])))

# 干扰句池（不含任何入池令字的句子，避免与正确答案冲突）
rest = [x for x in segments if not any(c in x[0] for c in POOL)]
pool = [[s, lab] for s, lab in rest[:1800]]

out = {
    'meta': {
        'built': '2026-09-11',
        'corpus': SOURCES,
        'poems': poems,
        'segments': len(segments),
        'chars': len(POOL),
        'note': '仅收录简体原文诗句（排除繁体源 全唐诗/四书五经/蒙学，避免简繁转换误字）；每令字最多 240 句。'
    },
    'chars': chars,
    'pool': pool,
}
dst = os.path.join(BASE, 'data', 'feihualing.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('\n写出 %s  %.1f KB' % (dst, os.path.getsize(dst) / 1024))
