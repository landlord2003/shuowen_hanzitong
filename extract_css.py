# -*- coding: utf-8 -*-
"""从 index.html 提取 .char-card / .fav-dot / .daily-card / .bopo 的 CSS 规则。"""
import io, os, re
ROOT = os.path.dirname(os.path.abspath(__file__))
h = io.open(os.path.join(ROOT, 'index.html'), encoding='utf-8', errors='replace').read()
out = []
for sel in ['.char-card', '.fav-dot', '.daily-card', '.bopo', '.pinyin']:
    for m in re.finditer(re.escape(sel) + r'[^{}]*\{[^{}]*\}', h):
        s = m.group(0).strip()
        if len(s) < 600:
            out.append(s)
    out.append('')
out.append('==== charCardHTML 源码 ====')
m = re.search(r'function charCardHTML[\s\S]{0,600}?\n\}', h)
out.append(m.group(0) if m else '(not found)')
io.open(os.path.join(ROOT, '_css.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('rules=%d' % len(out))
