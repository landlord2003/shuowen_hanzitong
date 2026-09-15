"""生成含 medians 的笔顺库：从 hanzi-writer-data(_vendor) 抽取 App 实际用到的字。
输出 data/stroke_data.json = {char: {strokes:[...], medians:[[...]]}}
格式直接兼容 HanziWriter 的 charDataLoader。"""
import json, os, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
chars_path = os.path.join(ROOT, 'data', 'characters.json')
vendor_dir = os.path.join(ROOT, '_vendor', 'package')
out_path = os.path.join(ROOT, 'data', 'stroke_data.json')

data = json.load(open(chars_path, encoding='utf-8'))
want = set(c['char'] for c in data['characters'])
print('App 用字:', len(want))

out = {}
missing = 0
for fp in glob.glob(os.path.join(vendor_dir, '*.json')):
    name = os.path.splitext(os.path.basename(fp))[0]
    if name == 'package':
        continue
    if name not in want:
        continue
    try:
        d = json.load(open(fp, encoding='utf-8'))
    except Exception:
        continue
    if isinstance(d, dict) and d.get('strokes') and d.get('medians'):
        out[name] = {'strokes': d['strokes'], 'medians': d['medians']}
    else:
        missing += 1

json.dump(out, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False)
sz = os.path.getsize(out_path)
print('生成笔顺库:', len(out), '字 | 缺 medians 跳过:', missing)
print('文件大小: %.2f MB' % (sz / 1024 / 1024))
# 抽样核对
for ch in ['马', '永', '一', '字']:
    if ch in out:
        print('  抽样', ch, 'strokes=', len(out[ch]['strokes']), 'medians=', len(out[ch]['medians']))
