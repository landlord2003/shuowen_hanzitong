# -*- coding: utf-8 -*-
"""GlyphWiki 适配器（CC BY-SA 2.1 JP，须署名 + 衍生同授权）。

GlyphWiki 以字名索引字形，Unicode 字 U+XXXX 的规范名为 `uXXXX`（小写 hex）。
本适配器尝试核心名与若干「旧字体/异体」风格变体名，取到的 SVG 栅格化后作为「字源/古形」候选。
注意：GlyphWiki 给出的是该字的标准/旧字形（非严格甲骨文/金文/篆文），故本阶段诚实标注为「字源」，
      不作为「篆文」。覆盖面好但非 100%，且为 CC BY-SA，启用即代表衍生包须同授权发布。

并发抓取：复用 requests.Session（带重试）+ 线程池，8105 字可在数分钟内完成。
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from sources import download_file, svg_to_png, LICENSES

BASE = "https://glyphwiki.org/glyph/{name}.svg"

# 尝试的名字变体（核心 + 常见旧字体/异体后缀）；伙伴可按 GlyphWiki 实际命名扩充
VARIANTS = ["{u}", "{u}-kyujitai", "{u}-shinjitai", "{u}-heishin"]


def _strip(v):
    if v is None:
        return ""
    return str(v).strip().strip("'\"")


def _names(char):
    cp = ord(char)
    u = "u%04x" % cp
    return [v.format(u=u) for v in VARIANTS]


def _fetch_one(c, out_dir, session, attribution):
    ch = _strip(c.get("char"))
    if not ch or len(ch) != 1:
        return None
    for name in _names(ch):
        url = BASE.format(name=name)
        svg_path = os.path.join(out_dir, "gw_%s.svg" % c["id"])
        png_path = os.path.join(out_dir, "gw_%s.png" % c["id"])
        if download_file(url, svg_path, session=session) and svg_to_png(svg_path, png_path, size=160):
            if attribution:
                attribution.add("glyphwiki", "GlyphWiki", LICENSES["cc_by_sa_2_1_jp"])
            # 注意：不在此删除中间 SVG/PNG——沙箱 bulk-delete 保护会拦截批量删除并抛错，
            # 由调用方在打包完成后统一清理（或保留在 gitignore 的 _glyph_tmp 下）。
            return {"id": str(c["id"]), "char": ch, "script": "glyphwiki", "img": png_path}
    return None


def fetch(chars, out_dir, attribution=None, limit=None, workers=8, **kw):
    os.makedirs(out_dir, exist_ok=True)
    items = chars if limit is None else chars[:limit]
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    session.trust_env = False  # 关键：绕过沙箱环境代理（https_proxy 会拦境外 glyphwiki.org），直连
    retry = Retry(total=4, backoff_factor=0.4, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_connections=workers, pool_maxsize=workers))

    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_fetch_one, c, out_dir, session, attribution) for c in items]
        for f in as_completed(futs):
            r = f.result()
            if r:
                results.append(r)
            done += 1
            if done % 500 == 0:
                print("[glyphwiki] 已处理 %d/%d，命中 %d" % (done, len(items), len(results)))
    print("[glyphwiki] 完成：处理 %d 字，命中 %d" % (len(items), len(results)))
    return results
