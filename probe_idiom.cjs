const https = require('https');
const fs = require('fs');
const OUT = 'D:/WorkBuddy/projects/说文解字/_probe_idiom.txt';
const urls = [
  'https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/idiom.json',
  'https://raw.githubusercontent.com/fighting41love/funNLP/master/data/%E6%88%90%E8%AF%AD.json',
  'https://raw.githubusercontent.com/kdjlyy/idioms/master/idioms.json',
];
const lines = [];
function save() { fs.writeFileSync(OUT, lines.join('\n') + '\n'); }
function probe(u) {
  return new Promise(res => {
    const req = https.get(u, { timeout: 15000, headers: { 'User-Agent': 'Mozilla/5.0' } }, r => {
      let n = 0, buf = '';
      r.on('data', d => { n += d.length; if (buf.length < 400) buf += d.toString('utf8', 0, 400); if (n >= 2000) r.destroy(); });
      r.on('end', () => res({ u, s: r.statusCode, n, buf }));
      r.on('error', e => res({ u, err: e.code || e.message }));
    });
    req.on('error', e => res({ u, err: e.code || e.message }));
    req.setTimeout(15000, () => { req.destroy(); res({ u, err: 'TIMEOUT' }); });
  });
}
(async () => {
  for (const u of urls) {
    const r = await probe(u);
    if (r.err) lines.push('ERR ' + r.err + '  ' + u.slice(0, 58));
    else lines.push('OK status=' + r.s + ' bytes>=' + r.n + '  ' + u.slice(0, 58) + '\n   preview: ' + r.buf.slice(0, 220));
    save();
  }
  lines.push('ALL_DONE');
  save();
})();
