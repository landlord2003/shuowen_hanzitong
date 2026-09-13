# -*- coding: utf-8 -*-
"""Plan2c 定版流水线：汉典金文 SVG -> 白底高清栅格化 -> Otsu 二值化 -> 重打包 dataset.bin。

与 Plan2 的差别（Plan2 的三个缺陷已修正）：
1. **白底渲染**：resvg 传入 background=#ffffff。汉典 SVG 自带近白水印（fill≈#fafbfa），
   透明底渲染时水印会因 alpha 不透明而混进字形；白底后水印并入背景，Otsu 干净分离。
2. **缓存原始 SVG**：_plan2_svg/{char}.svg + _urls.json 落盘，后续调整参数无需再联网。
3. **不做临时文件删除**：避免 WorkBuddy safe-delete shim 拖慢/报错。

产物：_plan2c_cache/{char}.png（0/255 掩码，160px 高，去水印）。
重打包复用 _repack_plan2b.py（基线 dataset.bin.bak6）。
"""
import os, sys, re, json, time, traceback, threading
import urllib.request, urllib.parse, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from PIL import Image
sys.path.insert(0, r"E:\Workbuddy\说文解字")
import img_proc

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
BIN = os.path.join(ROOT, "data", "dataset.bin")
BASE = os.environ.get("SWJ_BASE_BIN") or BIN
SVGDIR = os.path.join(ROOT, "_plan2_svg")
CACHE2 = os.path.join(ROOT, "_plan2c_cache")
OUT = os.path.join(ROOT, "_diag_out")
LOG = os.path.join(OUT, "_plan2c.log")
URLS = os.path.join(SVGDIR, "_urls.json")
NODE = r"C:\Users\Lenovo\.workbuddy\binaries\node\versions\v24.19.0\node.exe"
RS = os.path.join(_HERE, "resvg_render.mjs")
TARGET_H = 160
MAX_WORKERS = 5
MAGIC = b"CEDS0002"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

_lock = threading.Lock()
_url_map = {}

def log(m):
    with _lock:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(str(m) + "\n")

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Referer": "https://www.zdic.net/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()

def jinwen_svgs(ch):
    page_url = "https://www.zdic.net/hans/%s/jinwen" % urllib.parse.quote(ch)
    for attempt in range(3):
        try:
            s, html = fetch(page_url, timeout=20)
            if s != 200:
                return "page_status_%d" % s, []
            break
        except Exception as e:
            if attempt == 2:
                return "page_err", []
            time.sleep(1.0 + attempt)
    text = html.decode("utf-8", "ignore")
    paths = re.findall(r'img\.zdic\.net(/[^\s"\']*?jinwen[^\s"\']*?\.svg)', text)
    seen, out = set(), []
    for p in paths:
        full = "https://img.zdic.net" + p
        if full not in seen:
            seen.add(full); out.append(full)
    return "ok", out

def render_mask(svg_path, png_path):
    """白底栅格化 -> 二值掩码。返回 (w,h,px) 或 None。"""
    r = subprocess.run([NODE, RS, svg_path, png_path, str(TARGET_H), "#ffffff"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not os.path.exists(png_path):
        return None
    try:
        return _img_proc.load_image_as_gray(open(png_path, "rb").read())
    except Exception:
        return None

def process_char(ch):
    final = os.path.join(CACHE2, ch + ".png")
    if os.path.exists(final):
        im = Image.open(final).convert("L")
        w, h = im.size
        nz = sum(1 for v in im.tobytes() if v > 0)
        return (ch, "cached", w, h, nz)
    svg_path = os.path.join(SVGDIR, "%s.svg" % ch)
    png_path = os.path.join(CACHE2, "%s_raw.png" % ch)
    png_final = os.path.join(CACHE2, "%s.png" % ch)
    url = None

    if os.path.exists(svg_path):
        w, h, px = render_mask(svg_path, png_path) or (0, 0, b"")
        if w and h:
            nz = sum(1 for v in px if v > 0)
            ratio = nz / float(w * h)
            if 0.0002 < ratio < 0.90:
                Image.frombytes("L", (w, h), px).save(png_final)
                return (ch, "ok_svgcache", w, h, nz)
        return (ch, "svgcache_bad", 0, 0, 0)

    st, urls = jinwen_svgs(ch)
    if st != "ok":
        return (ch, st, 0, 0, 0)
    if not urls:
        return (ch, "no_urls", 0, 0, 0)
    for idx, u in enumerate(urls[:5]):
        try:
            s, svg_bytes = fetch(u, timeout=25)
            if s != 200 or len(svg_bytes) < 100:
                continue
            with open(svg_path, "wb") as f:
                f.write(svg_bytes)
            res = render_mask(svg_path, png_path)
            if res is None:
                os.remove(svg_path)
                continue
            w, h, px = res
            nz = sum(1 for v in px if v > 0)
            ratio = nz / float(w * h) if w * h else 0
            if 0.0002 < ratio < 0.90 and w >= 10 and h >= 10:
                Image.frombytes("L", (w, h), px).save(png_final)
                with _lock:
                    _url_map[ch] = u
                return (ch, "ok", w, h, nz)
            else:
                os.remove(svg_path)
        except Exception:
            continue
    return (ch, "no_good", 0, 0, 0)

def read_bin(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == MAGIC
    hl = __import__("struct").unpack("<I", data[8:12])[0]
    return json.loads(__import__("zstandard").decompress(data[12:12 + hl]))

def phase1():
    os.makedirs(SVGDIR, exist_ok=True)
    os.makedirs(CACHE2, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    open(LOG, "w", encoding="utf-8").write("START\n")
    header = read_bin(BASE)
    keys = header["keys"].split("\n")
    characters = header.get("characters", {})
    chars = sorted({characters[k.rsplit("/", 1)[0]] for k in keys
                    if k.endswith("/J_bronze") and characters.get(k.rsplit("/", 1)[0])})
    log("bronze chars to fetch: %d" % len(chars))

    results, t0 = [], time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(process_char, ch): ch for ch in chars}
        for f in as_completed(futs):
            try:
                results.append(f.result())
            except Exception as e:
                results.append((futs[f], "future_exc:%r" % e, 0, 0, 0))
            if len(results) % 100 == 0:
                log("progress %d/%d  %.1fs" % (len(results), len(chars), time.time() - t0))
    log("phase1 done %d chars in %.1fs" % (len(results), time.time() - t0))

    cnt = Counter(r[1] for r in results)
    log("status summary: " + repr(dict(cnt)))
    ok = [r for r in results if r[1] in ("ok", "ok_svgcache", "cached")]
    log("usable: %d / %d" % (len(ok), len(results)))
    if ok:
        nzs = [r[4] for r in ok]
        log("nonzero min/median/max: %d / %d / %d" % (min(nzs), sorted(nzs)[len(nzs)//2], max(nzs)))
    bad = [r for r in results if r[1] not in ("ok", "ok_svgcache", "cached")]
    if bad:
        log("failed samples: " + repr(bad[:25]))
    with open(URLS, "w", encoding="utf-8") as f:
        json.dump(_url_map, f, ensure_ascii=False, indent=1)
    log("url map saved: %d entries" % len(_url_map))

def phase2():
    r = subprocess.run([sys.executable, os.path.join(_HERE, "repack_dataset.py"),
                        CACHE2, BASE], capture_output=True, text=True)
    log("repack rc=%s" % r.returncode)
    log("repack stdout:\n" + r.stdout)
    if r.stderr.strip():
        log("repack stderr:\n" + r.stderr)

if __name__ == "__main__":
    try:
        only = sys.argv[1] if len(sys.argv) > 1 else "all"
        if only in ("all", "p1"):
            phase1()
        if only in ("all", "p2"):
            phase2()
        log("=== plan2c END ===")
    except Exception:
        log("FATAL:\n" + traceback.format_exc())
        raise
