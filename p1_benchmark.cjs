const https = require('https'), fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字';
const cand = JSON.parse(fs.readFileSync(ROOT + '/data/p1_candidates.json', 'utf8'));
const cf = ROOT + '/data/p1_benchmark_cache.json';
let cache = fs.existsSync(cf) ? JSON.parse(fs.readFileSync(cf, 'utf8')) : {};
const N = Math.min(200, cand.length);
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

function get(url, d) {
  return new Promise(res => {
    if (d > 5) return res(null);
    const req = https.get(url, { headers: { 'User-Agent': UA, 'Referer': 'https://www.zdic.net/' } }, r => {
      if ([301, 302, 303, 307, 308].includes(r.statusCode)) {
        let loc = r.headers.location;
        let n = loc.startsWith('http') ? loc : (new URL(url)).origin + loc;
        try { n = new URL(n); n.pathname = encodeURI(n.pathname); n = n.toString(); } catch (e) {}
        return res(get(n, d + 1));
      }
      let b = ''; r.on('data', c => b += c); r.on('end', () => res(b));
    });
    req.on('error', e => res(null));
    req.setTimeout(15000, () => { req.destroy(); res(null); });
  });
}
function explain(html) {
  if (!html) return '';
  // 汉典解释区块
  let m = html.match(/<div class="js-info">([\s\S]*?)<\/div>/);
  let t = m ? m[1] : '';
  if (!t) { m = html.match(/基本解释([\s\S]*?)(详细解释|常用词组|<\/div>)/); t = m ? m[1] : ''; }
  t = t.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
  return t.slice(0, 400);
}
function save() { fs.writeFileSync(cf, JSON.stringify(cache)); }
(async () => {
  let done = 0;
  for (const c of cand.slice(0, N)) {
    if (cache[c.ch]) { done++; continue; }
    const enc = encodeURIComponent(c.ch);
    let html = null;
    for (let a = 0; a < 3; a++) { html = await get('https://zdic.net/hans/' + enc, 0); if (html) break; await new Promise(x => setTimeout(x, 500 * (a + 1))); }
    if (html) { cache[c.ch] = { explain: explain(html), story: c.story, liushu: c.liushu }; done++; }
    if (done % 15 === 0) save();
  }
  save();
  fs.writeFileSync(ROOT + '/_p1_bench.txt', 'benchmark done: ' + done + '/' + N + ' (cache=' + Object.keys(cache).length + ')');
})();
