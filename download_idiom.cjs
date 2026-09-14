const https = require('https');
const fs = require('fs');
const BASE = 'D:/WorkBuddy/projects/说文解字';
const URL = 'https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/idiom.json';
const ERR = BASE + '/_dl_err.txt';
const DONE = BASE + '/_dl_done.txt';
const SRC = BASE + '/data/idioms_whitelist_src.json';
const WL = BASE + '/data/idioms_whitelist.json';

function finish(msg) { fs.writeFileSync(DONE, msg); }
const req = https.get(URL, { timeout: 90000, headers: { 'User-Agent': 'Mozilla/5.0' } }, r => {
  if (r.statusCode !== 200) { fs.writeFileSync(ERR, 'status ' + r.statusCode); return; }
  const f = fs.createWriteStream(SRC);
  r.pipe(f);
  f.on('finish', () => {
    try {
      const arr = JSON.parse(fs.readFileSync(SRC, 'utf8'));
      const wl = arr.map(x => (x && x.word) || '').filter(Boolean);
      fs.writeFileSync(WL, JSON.stringify(wl));
      finish('total_entries=' + arr.length + ' whitelist_words=' + wl.length + ' src_bytes=' + fs.statSync(SRC).size);
    } catch (e) { fs.writeFileSync(ERR, 'PARSE_ERR ' + e.message); }
  });
  f.on('error', e => fs.writeFileSync(ERR, 'FILE_ERR ' + e.message));
});
req.on('error', e => fs.writeFileSync(ERR, 'REQ_ERR ' + (e.code || e.message)));
req.setTimeout(90000, () => { req.destroy(); fs.writeFileSync(ERR, 'TIMEOUT'); });
