// 抓汉典(hdic)各字的「說文解字」原文，供人工核对。后台运行。
const https = require('https');
const fs = require('fs');
const OUT = 'D:/WorkBuddy/projects/说文解字/_zw/';
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

// 待核对：勘误 5 字（本字 + 应属的正体）；suspect 9 字
const CHARS = ['匦', '匭', '颃', '頏', '渺', '驭', '馭', '台', '臺',
  '坰', '夯', '皋', '麦', '亟', '尿', '先', '寇', '亘'];

function get(url, depth) {
  return new Promise(res => {
    if (depth > 5) return res({ s: 'TOODEEP', body: '' });
    const req = https.get(url, { headers: { 'User-Agent': UA, 'Referer': 'https://www.zdic.net/' } }, r => {
      if ([301, 302, 303, 307, 308].includes(r.statusCode)) {
        let loc = r.headers.location;
        let next = loc.startsWith('http') ? loc : (new URL(url)).origin + loc;
        try { const u = new URL(next); u.pathname = encodeURI(u.pathname); next = u.toString(); } catch (e) { }
        return res(get(next, depth + 1));
      }
      let b = ''; r.setEncoding('utf8');
      r.on('data', c => b += c);
      r.on('end', () => res({ s: r.statusCode, body: b }));
    });
    req.on('error', e => res({ s: 'ERR:' + (e.code || e.message), body: '' }));
    req.setTimeout(20000, () => { req.destroy(); res({ s: 'TIMEOUT', body: '' }); });
  });
}

// 从页面抽取「說文解字」块：zdic 页面里 <div class="...swjz..."> 或含「說文解字」标题的区块
function extractSwjz(html) {
  if (!html) return null;
  // 去掉脚本/样式
  const txt = html.replace(/<script[\s\S]*?<\/script>/gi, '').replace(/<style[\s\S]*?<\/style>/gi, '');
  const idx = txt.indexOf('說文解字');
  const idx2 = txt.indexOf('说文解字');
  const i = idx >= 0 ? idx : idx2;
  if (i < 0) return null;
  const seg = txt.slice(i, i + 1600);
  return seg.replace(/<[^>]+>/g, ' ').replace(/&[a-z]+;/gi, ' ').replace(/\s+/g, ' ').trim();
}

(async () => {
  const log = [];
  for (const ch of CHARS) {
    const url = 'https://zdic.net/hans/' + encodeURIComponent(ch);
    let r = await get(url, 0);
    if (r.s !== 200) { await new Promise(x => setTimeout(x, 1500)); r = await get(url, 0); }
    fs.writeFileSync(OUT + ch + '.html', r.body || '', 'utf8');
    const sw = extractSwjz(r.body);
    log.push('【' + ch + '】 status=' + r.s + '\n  說文: ' + (sw ? sw.slice(0, 600) : '(未提取到)'));
    await new Promise(x => setTimeout(x, 700));
  }
  fs.writeFileSync(OUT + '_RESULT.txt', log.join('\n\n'), 'utf8');
  fs.writeFileSync(OUT + '_DONE.txt', 'ok ' + new Date().toISOString(), 'utf8');
})();
