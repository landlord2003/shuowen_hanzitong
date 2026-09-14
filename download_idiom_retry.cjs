const https = require('https'), fs = require('fs');
const BASE = 'D:/WorkBuddy/projects/说文解字';
const URL = 'https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/idiom.json';
const SRC = BASE + '/data/idioms_whitelist_src.json';
const WL = BASE + '/data/idioms_whitelist.json';
function getOnce() {
  return new Promise((res, rej) => {
    const req = https.get(URL, { timeout: 60000, headers: { 'User-Agent': 'Mozilla/5.0' } }, r => {
      if (r.statusCode !== 200) { req.destroy(); return rej('status ' + r.statusCode); }
      const f = fs.createWriteStream(SRC);
      r.pipe(f);
      f.on('finish', () => res('ok'));
      f.on('error', e => rej('file ' + e.message));
    });
    req.on('error', e => rej('req ' + (e.code || e.message)));
    req.setTimeout(60000, () => { req.destroy(); rej('timeout'); });
  });
}
(async () => {
  for (let i = 0; i < 5; i++) {
    try {
      await getOnce();
      const arr = JSON.parse(fs.readFileSync(SRC, 'utf8'));
      const wl = arr.map(x => (x && x.word) || '').filter(Boolean);
      fs.writeFileSync(WL, JSON.stringify(wl));
      fs.writeFileSync(BASE + '/_dl_done.txt', 'OK total=' + arr.length + ' wl=' + wl.length + ' bytes=' + fs.statSync(SRC).size);
      return;
    } catch (e) {
      fs.writeFileSync(BASE + '/_dl_err.txt', 'try' + i + ' ' + e);
      await new Promise(x => setTimeout(x, 3000 * (i + 1)));
    }
  }
  fs.writeFileSync(BASE + '/_dl_err.txt', 'ALL_RETRY_FAILED');
})();
