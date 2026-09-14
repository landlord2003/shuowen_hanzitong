// 下载权威简繁映射表（OpenCC + Unihan），后台联网
const fs = require('fs');
const https = require('https');
const path = require('path');
const OUT = 'D:/WorkBuddy/projects/说文解字/.cache/s2t';
fs.mkdirSync(OUT, { recursive: true });

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

const TARGETS = [
  ['TSCharacters.txt', 'https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/TSCharacters.txt'],
  ['STCharacters.txt', 'https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/STCharacters.txt'],
  ['TSPhrases.txt', 'https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/TSPhrases.txt'],
  ['Unihan.zip', 'https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip'],
  ['UnihanVariants.txt', 'https://raw.githubusercontent.com/unicode-org/unicodetools/main/unicodetools/data/ucd/dev/Unihan_Variants.txt'],
];

function get(url, redirects = 0) {
  return new Promise(resolve => {
    if (redirects > 6) return resolve({ err: 'TOODEEP' });
    let req;
    try {
      req = https.get(url, { timeout: 30000, headers: { 'User-Agent': UA } }, res => {
        if ([301, 302, 303, 307, 308].includes(res.statusCode)) {
          let loc = res.headers.location;
          let next = loc.startsWith('http') ? loc : new URL(url).origin + loc;
          return resolve(get(next, redirects + 1));
        }
        if (res.statusCode !== 200) { res.resume(); return resolve({ err: 'HTTP ' + res.statusCode }); }
        const chunks = [];
        res.on('data', c => chunks.push(c));
        res.on('end', () => resolve({ buf: Buffer.concat(chunks) }));
        res.on('error', e => resolve({ err: e.code || e.message }));
      });
    } catch (e) { return resolve({ err: e.message }); }
    req.on('error', e => resolve({ err: e.code || e.message }));
    req.on('timeout', () => { req.destroy(); resolve({ err: 'TIMEOUT' }); });
  });
}

(async () => {
  const log = [];
  for (const [name, url] of TARGETS) {
    let ok = false;
    for (let a = 0; a < 4 && !ok; a++) {
      const r = await get(url);
      if (r.buf && r.buf.length > 100) {
        fs.writeFileSync(path.join(OUT, name), r.buf);
        log.push(`OK   ${name}  ${r.buf.length} bytes  (attempt ${a + 1})`);
        ok = true;
      } else {
        log.push(`FAIL ${name}  ${r.err}  (attempt ${a + 1})`);
        await new Promise(x => setTimeout(x, 800 * (a + 1)));
      }
    }
  }
  fs.writeFileSync('D:/WorkBuddy/projects/说文解字/_s2t_dl.txt', log.join('\n'), 'utf8');
  console.log(log.join('\n'));
})();
