# -*- coding: utf-8 -*-
"""把 cultural.json 按 HEAD 原格式（ensure_ascii=False, indent=1）重排，让 git diff 只反映真实内容变更。"""
import json, sys

B = 'D:/WorkBuddy/projects/说文解字/'
head = open(B + '_head_cul.json', encoding='utf-8').read()

d = json.loads(head)
out = json.dumps(d, ensure_ascii=False, indent=1)
ok = (out == head) or (out == head.rstrip('\n')) or (out + '\n' == head)
print('HEAD 往返一致:', ok, '| out len', len(out), '| head len', len(head))
if not ok:
    print('尾部差异 out[-24:]=', repr(out[-24:]), ' head[-24:]=', repr(head[-24:]))
    sys.exit(1)

cur = json.load(open(B + 'data/cultural.json', encoding='utf-8'))
with open(B + 'data/cultural.json', 'w', encoding='utf-8') as f:
    json.dump(cur, f, ensure_ascii=False, indent=1)
print('cultural.json 已按 indent=1 重排；条目数', len(cur))
