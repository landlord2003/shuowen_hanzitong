# -*- coding: utf-8 -*-
"""构建飞花令数据 data/feihualing.json

来源分两类：
  1) 简体原文源（直接收录）：宋词 / 元曲 / 诗经 / 楚辞 / 曹操诗集 / 纳兰性德
  2) 繁体原文源（转简后收录）：全唐诗（311,856 首）

繁体源的转换守卫 —— 「双向一致性」：
  只有满足  convert(convert(x,'zh-hans'),'zh-hant') == x  的句子才收录。
  即「繁→简→繁」能原样还原的句子，说明这次简化没有发生多对一歧义
  （如 後/后、幹/乾/干 这类，转回繁体会还原成不同字）——这类句子一律丢弃。
  代价是损失约 13% 的句子，收益是「绝不出现简繁误字」。

配额：每个令字 240 句中，全唐诗占 60%（144 句）、其余源合计 40%（96 句）。
      否则按长度排序取前 240 时，全唐诗（235 万句）会被宋词等（34 万句）挤空。
"""
import os, json, re, random, datetime
from zhconv import convert

BASE = r'D:\WorkBuddy\projects\说文解字'
CB = os.path.join(BASE, 'tools', 'poetry_corpus')
random.seed(20260911)

SPLIT = re.compile(r'[。！？；，、：]')
BAD = re.compile(r'[A-Za-z0-9]|[「」『』（）()\[\]{}<>《》\u3000]|\.\.\.')

SIMP_SOURCES = ['宋词', '元曲', '诗经', '楚辞', '曹操诗集', '纳兰性德']
TRAD_SOURCES = ['全唐诗']
TANG = '全唐诗'
SOURCES = SIMP_SOURCES + TRAD_SOURCES
# ⚠️ 目录名与实际内容不符：tools/poetry_corpus/全唐诗/ 内全部是 poet.song.*.json，
#    实为《全宋诗》（陆游/王十朋/釋印肅…，宋代诗人，311,856 首繁体）。
#    《全唐诗》本体约 5.7 万首，不在本机语料中。对外名称按实际内容标注。
CORPUS_LABEL = {TANG: '全宋诗'}

MAX_CHARS = 48        # 令字池上限（按频次取前 N）
PER_CHAR = 240        # 每令字句子数
TANG_QUOTA = 144      # 其中全唐诗配额（60%）
POOL_SIZE = 2000      # 干扰句池上限
MIN_FREQ = 150        # 入池最低频次

CAND = list('花月风春山水云天日人酒雨江秋雪夜心情白红青千万里来时生家客舟长空明高寒归'
            '梦愁门关思别行飞声老孤远寒清南行书剑')


def is_simp(s):
    return convert(s, 'zh-hans') == s


def t2s_guarded(s):
    """繁体→简体，双向一致性守卫。返回 None 表示该句有简繁歧义、丢弃。"""
    if is_simp(s):
        return s
    x = convert(s, 'zh-hans')
    if convert(x, 'zh-hant') != s:
        return None
    return x


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
    a = (r.get('author') or '').strip()
    if src == '诗经':
        return '《诗经·%s·%s》' % (r.get('section') or '', r.get('title') or '')
    if src == '曹操诗集':
        return '曹操·《%s》' % (r.get('title') or '')
    if src == '元曲':
        return '%s·《%s》' % (a, r.get('title') or '')
    if src == '宋词':
        return '%s·《%s》' % (a, r.get('rhythmic') or r.get('title') or '')
    if src == '楚辞':
        return '%s·《%s》' % (a, r.get('title') or '')
    if src == '纳兰性德':
        return '纳兰性德·《%s》' % (r.get('title') or r.get('rhythmic') or '')
    if src == '全唐诗':
        return '%s·《%s》' % (a or '佚名', r.get('title') or '')
    return a


# ---------------- 收句 ----------------
segments = []          # (句, 出处, 源)
poems = 0
drop_ambig = 0         # 繁体源：简繁歧义丢弃
drop_trad = 0          # 简体源：本身含繁体字（未转）丢弃
for src in SOURCES:
    try:
        rows = load(src)
    except Exception as e:
        print('!! load fail', src, e)
        continue
    if not isinstance(rows, list):
        rows = [rows]
    poems += len(rows)
    n0 = len(segments)
    for r in rows:
        lab = label_of(src, r)
        if src in TRAD_SOURCES:
            lab = convert(lab, 'zh-hans')   # 出处标签同样转简（仅展示用，不参与出题判定）
        for key in ('paragraphs', 'content', 'para'):
            for para in (r.get(key) or []):
                for s in segs_of(para):
                    if src in TRAD_SOURCES:
                        s2 = t2s_guarded(s)
                        if s2 is None:
                            drop_ambig += 1
                            continue
                        s = s2
                    elif not is_simp(s):
                        drop_trad += 1
                        continue
                    segments.append((s, lab, src))
    print('%-8s 篇 %7d  收句 %8d' % (src, len(rows), len(segments) - n0))

# 去重（同句保留首次出现的源）
seen = set(); uniq = []
for s, lab, src in segments:
    if s in seen:
        continue
    seen.add(s); uniq.append((s, lab, src))
segments = uniq
print('\n合计诗篇 %d 首，去重后可用句 %d（歧义丢弃 %d，简体源含繁体丢弃 %d）'
      % (poems, len(segments), drop_ambig, drop_trad))

# ---------------- 令字频次（一次遍历） ----------------
candset = set(CAND)
cnt = {ch: 0 for ch in CAND}
for s, _, _ in segments:
    for ch in set(s) & candset:
        cnt[ch] += 1

POOL = [ch for ch in sorted(cnt, key=lambda c: -cnt[c]) if cnt[ch] >= MIN_FREQ][:MAX_CHARS]
pset = set(POOL)
print('\n入池令字 %d 个：%s' % (len(POOL), ''.join(POOL)))

# ---------------- 分桶（一次遍历） ----------------
buckets = {ch: [] for ch in POOL}
rest = []
for s, lab, src in segments:
    hit = set(s) & pset
    if not hit:
        rest.append((s, lab, src))
        continue
    for ch in hit:
        buckets[ch].append((s, lab, src))

# ---------------- 每令字：按源配额取样 ----------------
key = lambda x: (abs(len(x[0]) - 7), len(x[0]))
chars = {}
for ch in POOL:
    hits = buckets[ch]
    a = sorted([x for x in hits if x[2] == TANG], key=key)
    b = sorted([x for x in hits if x[2] != TANG], key=key)
    picked = a[:TANG_QUOTA] + b[:PER_CHAR - TANG_QUOTA]
    if len(picked) < PER_CHAR:                       # 某一源不足时互补
        extra = a[TANG_QUOTA:] + b[PER_CHAR - TANG_QUOTA:]
        picked += extra[:PER_CHAR - len(picked)]
    random.shuffle(picked)
    chars[ch] = [[s, lab] for s, lab, _ in picked[:PER_CHAR]]
    if ch == POOL[0]:
        print('  ▸ 抽样令字「%s」：候选 %d 条（%s %d / 其他 %d）→ 取 %d'
              % (ch, len(hits), CORPUS_LABEL[TANG], len(a), len(b), len(chars[ch])))

# ---------------- 干扰句池：全量随机采样（天然按语料比例混合） ----------------
pool = [[s, lab] for s, lab, _ in random.sample(rest, min(POOL_SIZE, len(rest)))]
print('干扰句候选 %d 条，取 %d 条' % (len(rest), len(pool)))

out = {
    'meta': {
        'built': datetime.date.today().isoformat(),
        'corpus': [CORPUS_LABEL.get(s, s) for s in SOURCES],
        'corpus_note': '语料目录 tools/poetry_corpus/全唐诗/ 内实为《全宋诗》（poet.song.*.json，311,856 首，繁体）；'
                       '《全唐诗》本体（约 5.7 万首）不在本机语料中。',
        'poems': poems,
        'segments': len(segments),
        'chars': len(POOL),
        'trad_converted': TANG,
        'tang_quota': TANG_QUOTA,
        'note': '简体源（宋词/元曲/诗经/楚辞/曹操/纳兰性德）直接收录；全唐诗经「繁→简→繁」双向一致性守卫转换，'
                '凡转回繁体与原句不符（简繁多对一歧义）者丢弃，确保无一误字。'
                '每令字 %d 句中全唐诗占 %d 句，其余源合计 %d 句。' % (PER_CHAR, TANG_QUOTA, PER_CHAR - TANG_QUOTA)
    },
    'chars': chars,
    'pool': pool,
}
dst = os.path.join(BASE, 'data', 'feihualing.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('写出 %s  %.1f KB' % (dst, os.path.getsize(dst) / 1024))
