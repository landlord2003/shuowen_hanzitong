# -*- coding: utf-8 -*-
"""生成拼音声调核查报告（md + json）。
对照源：pypinyin（基于《现代汉语词典》/Unihan 等综合字表）的现代普通话规范读音。
"""
import json, io, os, glob, re
from pypinyin import pinyin, Style
ROOT = os.path.dirname(os.path.abspath(__file__))
APP = json.load(io.open(os.path.join(ROOT, 'data', 'characters.json'), encoding='utf-8'))['characters']
DATA_DIR = os.path.join(ROOT, '.workbuddy', 'charlist', 'shuowen', 'data')
try:
    from opencc import OpenCC
    s2t = OpenCC('s2t'); t2s = OpenCC('t2s')
except Exception:
    s2t = t2s = None

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

def split_multi(s):
    for sep in ('|', '/', ',', '，', '、', ';', '；'):
        s = s.replace(sep, '/')
    return [norm(x) for x in s.split('/') if x.strip()]

def same(back, wh, trad):
    if not wh: return False
    if wh == back or wh == trad: return True
    if s2t and s2t.convert(back) == wh: return True
    if t2s and t2s.convert(wh) == back: return True
    return False

ok = subset = 0
rows = []
for c in APP:
    ch = c['char']
    app_list = split_multi(c['pinyin'])
    app_set = set(app_list)
    try:
        r = pinyin(ch, style=Style.TONE, heteronym=True)
        cand = [norm(x) for x in (r[0] if r else [])]
    except Exception:
        cand = []
    seen = set(); cand2 = []
    for x in cand:
        if x not in seen: seen.add(x); cand2.append(x)
    cand = cand2
    if not cand:
        rows.append({'char': ch, 'app': c['pinyin'], 'cand': [], 'kind': 'unknown',
                     'src': '', 'full': '', 'fq': '', 'suggest': ''}); continue
    bad = [p for p in app_list if p not in cand]
    if not bad:
        if set(app_list) < set(cand): subset += 1
        else: ok += 1
        continue
    e = index_map.get(ch) or index_map.get(c.get('trad', '')) or {}
    wh = e.get('wordhead', '')
    kind = 'same_char_古音' if same(ch, wh, c.get('trad', '')) else 'cross_ref_串档'
    # 建议音：错误音 -> 候选中「声母韵母相同仅声调不同」者优先，否则取首选
    def base(p): return re.sub(u'[\u0100-\u01dc]', lambda m: '', p)
    sug = []
    for b in bad:
        pick = ''
        for x in cand:
            if x != b and x[:1] == b[:1] and len(x) == len(b):
                pick = x; break
        if not pick: pick = cand[0]
        sug.append(b + u'\u2192' + pick)
    rows.append({'char': ch, 'app': c['pinyin'], 'cand': cand, 'bad': bad, 'kind': kind,
                 'src': wh, 'full': e.get('pinyin_full', ''), 'fq': e.get('pronunciation', ''),
                 'suggest': ' , '.join(sug)})

bad_rows = [r for r in rows if r['kind'] != 'unknown']
A = [r for r in bad_rows if r['kind'] == 'cross_ref_串档']
B = [r for r in bad_rows if r['kind'] == 'same_char_古音']

io.open(os.path.join(ROOT, 'data', 'pinyin_audit.json'), 'w', encoding='utf-8').write(
    json.dumps({'total': len(APP), 'ok': ok, 'subset': subset, 'suspect': len(bad_rows),
                'cross_ref': len(A), 'same_char': len(B), 'rows': rows},
               ensure_ascii=False, indent=1))

L = []
L.append(u'# 说文解字 App · 全量拼音声调核查报告')
L.append(u'')
L.append(u'生成日期：2026-09-15　对象：`data/characters.json` 的 `pinyin` 字段（8105 字）')
L.append(u'')
L.append(u'## 一、结论速览')
L.append(u'')
L.append(u'| 项 | 字数 | 占比 |')
L.append(u'|---|---|---|')
L.append(u'| 总字数 | %d | 100%% |' % len(APP))
L.append(u'| 与标准读音**完全一致** | %d | %.1f%% |' % (ok, ok * 100.0 / len(APP)))
L.append(u'| App 读音是标准读音的**子集**（仅收了部分读音，不算错） | %d | %.1f%% |' % (subset, subset * 100.0 / len(APP)))
L.append(u'| **疑似错误** | **%d** | **%.2f%%** |' % (len(bad_rows), len(bad_rows) * 100.0 / len(APP)))
L.append(u'')
L.append(u'疑似错误分两类：')
L.append(u'')
L.append(u'- **A 类 · 串档 %d 条**：App 的简体/后起字被匹配到了**另一个古字（异体字/通假字）**的说文记录。' % len(A))
L.append(u'  拼音直接照抄了那个古字的音（例：「阵」抄了「敶」读 chén、「肤」抄了「臚」读 lú、「茶」抄了「荼」读 tú）。')
L.append(u'- **B 类 · 古音折合 %d 条**：字没串，但**拼音取的是《说文》音切折合出来的中古读音，不是现代普通话规范音**。' % len(B))
L.append(u'  例：「义」宜寄切→yí（今 yì）、「曰」王代切→yuè（今 yuē）、「吃」居乙切→jī（今 chī）、「企」去智切→qì（今 qǐ）、「缇」他禮切→tǐ（今 tí）。')
L.append(u'')
L.append(u'## 二、根因')
L.append(u'')
L.append(u'两者的源头都是 `merge_shuowen.py` → `build_from_shuowen.py` 这条链：')
L.append(u'')
L.append(u'```')
L.append(u'merge_shuowen.py   :65   "pinyin": entry.get("pinyin_full", "")   ← App 拼音的唯一来源')
L.append(u'merge_shuowen.py   :23   for idx in d.get("indexes", []): index_map.setdefault(idx, d)')
L.append(u'                           ↑ 说文源的 indexes 混装了「本字」与「关联异体字」，被一律当本字索引')
L.append(u'```')
L.append(u'')
L.append(u'- **A 类的因**：`indexes` 里把异体字也登记成本字，于是查「阵」命中了「敶」的整条记录（连 shuowen/fanqie 一起串）。')
L.append(u'- **B 类的因**：说文源的 `pinyin_full` 是**依音切折合的中古音**，不是《现代汉语词典》的现代规范音；')
L.append(u'  该字本身匹配正确，只是「读音口径」与产品需要（让用户知道现在怎么读）不一致。')
L.append(u'')
L.append(u'> 说明：`fanqie`（反切）字段本来就独立存在、并在详情页展示为「反切：XX切 · 出《说文》」。')
L.append(u'> 因此把 `pinyin` 修正为现代读音，**不会丢失古音信息**（古音仍在 fanqie 中）。')
L.append(u'')

def table(rs, title, note):
    L.append(u'## %s（%d 条）' % (title, len(rs)))
    L.append(u'')
    L.append(u'%s' % note)
    L.append(u'')
    L.append(u'| 字 | App 拼音 | 标准读音 | 来源字 | 源 pinyin_full | 反切 | 建议 |')
    L.append(u'|---|---|---|---|---|---|---|')
    for r in rs:
        L.append(u'| %s | `%s` | %s | %s | %s | %s | %s |' % (
            r['char'], r['app'], '/'.join(r['cand']), r.get('src') or '—',
            r.get('full') or '—', r.get('fq') or '—', r['suggest']))
    L.append(u'')

table(A, u'三、A 类 · 串档明细', u'来源字 = 实际被匹配到的那个古字（≠ App 字）。建议列的箭头指向按标准读音修正后的值。')
table(B, u'四、B 类 · 古音折合明细', u'来源字与 App 字为同一字（简繁/异体关系），仅为读音口径差异。')

L.append(u'## 五、修复建议')
L.append(u'')
L.append(u'1. **改 `pinyin` 为现代规范读音**（建议音见上两表），保留 `fanqie` 作为古音展示——两不耽误。')
L.append(u'2. **A 类需连带复核**：串档的字其 `shuowen`/`original`/`duan_note`/`variant` 也可能是别人家的，建议一并核。')
L.append(u'3. **治本**：`merge_shuowen.py` 的 `indexes` 索引应只登记「本字」（`wordhead` 及其简繁对应），')
L.append(u'   把异体/通假关系拆到单独的关联表，避免后续再串档。')
L.append(u'4. 修正后重跑本报告，目标：疑似错误 ≈ 0。')
L.append(u'')
io.open(os.path.join(ROOT, 'tools', 'pinyin_audit_report.md'), 'w', encoding='utf-8').write(u'\n'.join(L))
print('ok ok=%d subset=%d suspect=%d A=%d B=%d' % (ok, subset, len(bad_rows), len(A), len(B)))
