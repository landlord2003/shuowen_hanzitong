# -*- coding: utf-8 -*-
"""
文化内容(cultural.json)质检：统计覆盖率、字段完整度、空值清单，并抽样打印供人工抽检。
用法：
  python tools/check_cultural.py [--sample 5] [--empty-list 50]
"""
import json, os, sys, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CULT = os.path.join(ROOT, 'data', 'cultural.json')
CHARS = os.path.join(ROOT, 'data', 'characters.json')


def load(p):
    if not os.path.exists(p):
        print('[ERROR] 文件不存在:', p)
        sys.exit(2)
    return json.load(open(p, encoding='utf-8'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sample', type=int, default=5)
    ap.add_argument('--empty-list', type=int, default=50)
    args = ap.parse_args()

    cult = load(CULT)
    chars = load(CHARS)['characters']
    total_chars = len(chars)

    print('=' * 60)
    print('文化内容质检报告')
    print('=' * 60)
    print('characters.json 总字数 :', total_chars)
    print('cultural.json 已生成   :', len(cult))

    # 覆盖率
    covered = len(cult)
    print('覆盖率                 : %.1f%%' % (covered / total_chars * 100 if total_chars else 0))

    # 字段完整度
    have_story = have_idiom = have_poem = 0
    nonempty = 0
    empty_chars = []
    for ch, v in cult.items():
        s = bool(v.get('story'))
        i = bool(v.get('idioms'))
        p = bool(v.get('poems'))
        if s: have_story += 1
        if i: have_idiom += 1
        if p: have_poem += 1
        if s or i or p:
            nonempty += 1
        else:
            empty_chars.append(ch)

    print('-' * 60)
    print('非空条目(有 story/idioms/poems 任一): %d (%.1f%%)' %
          (nonempty, nonempty / covered * 100 if covered else 0))
    print('  含 字源故事 : %d' % have_story)
    print('  含 成语     : %d' % have_idiom)
    print('  含 诗词     : %d' % have_poem)
    print('空壳条目     : %d' % len(empty_chars))

    if empty_chars:
        print('  空壳字样本 :', ''.join(empty_chars[: args.empty_list]))
        # 是否大量空壳（警惕超时事故）
        if len(empty_chars) > covered * 0.1:
            print('  ⚠️ 警告：空壳比例 >10%，疑似生成质量事故（参考此前 8 并发超时）')

    # 抽样打印
    print('-' * 60)
    print('抽样打印（前 %d 个非空条目）:' % args.sample)
    shown = 0
    for ch, v in cult.items():
        if not (v.get('story') or v.get('idioms') or v.get('poems')):
            continue
        print('  【%s】' % ch)
        if v.get('story'):
            print('    故事:', v['story'][:80])
        if v.get('idioms'):
            print('    成语:', [x.get('w') for x in v['idioms'][:3]])
        if v.get('poems'):
            print('    诗词:', [x.get('line') for x in v['poems'][:2]])
        shown += 1
        if shown >= args.sample:
            break

    print('=' * 60)
    print('结论: %s' % ('OK' if len(empty_chars) <= covered * 0.1 else '需排查'))


if __name__ == '__main__':
    main()
