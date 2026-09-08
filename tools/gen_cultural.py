# -*- coding: utf-8 -*-
"""
Sprint 2 文化内容生成器：用本地 Ollama（默认 qwen3:14b）为单字生成
「字源小故事 / 相关成语 / 诗词引用」，输出 data/cultural.json。

零外部 API 成本（本地推理）。成语/诗词须真实存在（公版优先），宁缺毋滥。
用法:
  python tools/gen_cultural.py --limit 200 --workers 4        # 试跑 200 字
  python tools/gen_cultural.py --resume --workers 6           # 全量（断点续跑）
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS_JSON = os.path.join(ROOT, 'data', 'characters.json')
OUT = os.path.join(ROOT, 'data', 'cultural.json')
OLLAMA = 'http://127.0.0.1:11434/api/generate'


def build_prompt(c):
    return (
        "你是一位严谨的汉字文化学者。请为汉字「%s」（拼音 %s，六书：%s，本义：%s）"
        "生成文化内容。严格只输出一个 JSON 对象，不要任何解释、不要代码块标记。\n"
        "JSON 格式：\n"
        "{\n"
        '  "story": "一句60字内的字源小故事，紧扣其六书构形与本义，通俗有趣，不杜撰",\n'
        '  "idioms": [{"w": "含该字的真实四字成语", "meaning": "8-15字释义"}],\n'
        '  "poems": [{"line": "该字所在的经典诗词名句（须公版，1900年前作品）", "source": "作者·篇名"}]\n'
        "}\n"
        "若某类无合适且真实的内容，对应字段用空数组 [] 或空字符串 \"\"。成语与诗词务必真实存在，宁缺毋滥。"
    ) % (c.get('char', ''), c.get('pinyin', ''), c.get('liushu', ''), (c.get('original', '') or '')[:40])


def _one_try(char_obj, model):
    prompt = build_prompt(char_obj)
    payload = json.dumps({
        'model': model,
        'prompt': prompt,
        'format': 'json',
        'stream': False,
        'think': False,
        'options': {'temperature': 0.3, 'num_ctx': 2048}
    }).encode('utf-8')
    req = urllib.request.Request(OLLAMA, data=payload,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.loads(r.read().decode('utf-8'))
        text = resp.get('response', '') or ''
        return parse_json(text)
    except Exception as e:
        sys.stderr.write('ERR %s: %s\n' % (char_obj.get('char'), repr(e)[:80]))
        return None


def call_ollama(char_obj, model, retries=2):
    """带重试：qwen3 关闭思考后仍偶发返回空 {}，重试可恢复。"""
    for attempt in range(retries + 1):
        d = _one_try(char_obj, model)
        if d is None:
            continue
        if d.get('story') or d.get('idioms') or d.get('poems'):
            return d
        if attempt < retries:
            sys.stderr.write('EMPTY %s (retry %d)\n' % (char_obj.get('char'), attempt + 1))
    return d


def parse_json(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.strip('`')
        text = text[text.find('{') if '{' in text else 0:]
    s, e = text.find('{'), text.rfind('}')
    if s == -1 or e == -1:
        return None
    blob = text[s:e + 1]
    try:
        d = json.loads(blob)
    except Exception:
        return None
    # 规范化
    out = {'story': str(d.get('story', '') or '').strip(),
           'idioms': [], 'poems': []}
    for it in (d.get('idioms') or []):
        if isinstance(it, dict) and it.get('w'):
            out['idioms'].append({'w': str(it['w']), 'meaning': str(it.get('meaning', '') or '')})
    for p in (d.get('poems') or []):
        if isinstance(p, dict) and p.get('line'):
            out['poems'].append({'line': str(p['line']), 'source': str(p.get('source', '') or '')})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='仅处理前 N 字（0=全部）')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--model', default='qwen3:14b')
    ap.add_argument('--resume', action='store_true', help='保留已有 cultural.json 结果')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()

    data = json.load(open(CHARS_JSON, encoding='utf-8'))
    chars = data['characters']
    if args.limit:
        chars = chars[:args.limit]

    existing = {}
    if args.resume and os.path.exists(args.out):
        try:
            existing = json.load(open(args.out, encoding='utf-8'))
            print('[resume] 已有 %d 字' % len(existing))
        except Exception:
            existing = {}

    def _has_content(d):
        return d and (d.get('story') or d.get('idioms') or d.get('poems'))
    todo = [c for c in chars if not _has_content(existing.get(c['char']))]
    print('待生成 %d 字（共 %d）' % (len(todo), len(chars)))

    result = dict(existing)
    done = 0
    t0 = time.time()

    def work(c):
        return c['char'], call_ollama(c, args.model)

    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for ch, d in ex.map(work, todo):
            done += 1
            if d is not None:
                result[ch] = d
            if done % 50 == 0:
                json.dump(result, open(args.out, 'w', encoding='utf-8'),
                          ensure_ascii=False, separators=(',', ':'))
                dt = time.time() - t0
                print('  进度 %d/%d  成功 %d  用时 %.0fs' % (done, len(todo), len(result), dt), flush=True)

    json.dump(result, open(args.out, 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    print('完成：成功 %d 字（共 %d）输出：%s' % (len(result), len(chars), args.out))


if __name__ == '__main__':
    main()
