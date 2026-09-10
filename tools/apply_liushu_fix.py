# -*- coding: utf-8 -*-
"""
六书终审统一修正清单 落地脚本
- 只改「六书统一修正清单.csv」覆盖的 81 字，其余 8024 字不动
- 享：老吴拍板保持会意、只回填 shuowen（不应用 CSV 的"象形"目标）
- 参/曾/学/真：改 liushu 后加 liushu_remark 留痕（现代象形异说 / 段注形声说）
- 臾：整条串档重写（还原为臾本字，剥离误挂的蕢数据）
- 自动探测原文件格式，保持格式写回，避免巨大伪 diff
- 运行前自动备份 characters.json
"""
import json, csv, re, shutil, os, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data', 'characters.json')
CSV = os.path.join(BASE, '六书统一修正清单.csv')

# 1) 备份
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bak = DATA + '.bak_' + ts
shutil.copyfile(DATA, bak)
print('备份 ->', bak)

# 2) 读原文件（探测格式）
raw = open(DATA, encoding='utf-8').read()
obj = json.loads(raw)
chars = obj['characters']
cur = {c['char']: c for c in chars}
indent = 2 if re.search(r'"characters"\s*:\s*\[\s*\n', raw) else None

# 3) 读清单
rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))

liushu_changes = []
refill_changes = []
remark_added = []
yu_rewritten = []
skipped = []

for r in rows:
    ch = r['字'].strip()
    tgt = r['目标liushu'].strip()
    if ch == '享':
        tgt = '会意'  # 老吴拍板：保守，保持会意
    if ch not in cur:
        skipped.append(ch)
        print('⚠️ 跳过(不在库):', ch)
        continue
    c = cur[ch]

    # 臾：整条串档重写
    if ch == '臾':
        old = {k: c.get(k) for k in ('trad', 'pinyin', 'liushu', 'shuowen', 'original', 'modern', 'fanqie')}
        c['trad'] = '臾'
        c['pinyin'] = 'yú'
        c['liushu'] = '会意'
        c['shuowen'] = '束縛捽抴爲臾。从申从乙'
        c['original'] = '束縛捽抴'
        c['modern'] = '须臾；束缚'
        if 'fanqie' in c:
            c['fanqie'] = '羊朱切'
        new = {k: c.get(k) for k in ('trad', 'pinyin', 'liushu', 'shuowen', 'original', 'modern', 'fanqie')}
        yu_rewritten.append((old, new))
        continue

    # 改 liushu
    if c.get('liushu') != tgt:
        liushu_changes.append((ch, c.get('liushu'), tgt))
        c['liushu'] = tgt

    # 回填 shuowen（仅当数据集为后起字缺失）
    sw = c.get('shuowen') or ''
    if sw.lstrip().startswith('（后起') or '后起字' in sw[:8]:
        evi = r['说文依据'].strip()
        if evi:
            refill_changes.append((ch, sw, evi))
            c['shuowen'] = evi

    # 备注留痕（老吴明确要求）
    if ch in ('参', '曾', '学'):
        c['liushu_remark'] = '现代文字学有象形异说（参=星群/曾=甑初文/學有争议），依许慎声符归形声'
        remark_added.append(ch)
    elif ch == '真':
        c['liushu_remark'] = '段注：乚=隱聲，一说形聲；依《說文》本訓歸會意'
        remark_added.append(ch)

# 4) 写回（保持原格式）
out = json.dumps(obj, ensure_ascii=False, indent=indent)
with open(DATA, 'w', encoding='utf-8') as f:
    f.write(out)

# 5) 变更摘要
print('\n=== 变更摘要 ===')
print('改 liushu: %d 字' % len(liushu_changes))
for ch, a, b in liushu_changes:
    print('  %s: %s -> %s' % (ch, a, b))
print('\n回填 shuowen: %d 字' % len(refill_changes))
for ch, a, b in refill_changes:
    print('  %s: [%s] -> [%s]' % (ch, a[:18], b[:18]))
print('\n加 liushu_remark: %s' % remark_added)
print('臾整条重写: %d 字' % len(yu_rewritten))
for old, new in yu_rewritten:
    print('  旧:', old)
    print('  新:', new)
if skipped:
    print('\n跳过(不在库):', skipped)

# 6) 写回后抽样核验
chk = {c['char']: c for c in json.loads(open(DATA, encoding='utf-8'))['characters']}
print('\n=== 抽样核验（写回后）===')
for ch in ('农', '皂', '享', '臾', '参', '曾', '学', '真', '必', '罚', '牟', '芈', '哥'):
    c = chk.get(ch)
    if c:
        print('  %s: liushu=%s | shuowen=%s | remark=%s' % (
            ch, c.get('liushu'), (c.get('shuowen') or '')[:28], c.get('liushu_remark', '-')))
