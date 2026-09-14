// 扫描汉典(zdic.net)对全部8105规范字各书体"有无字形"的真实覆盖。
// 用法: node scan_zdic_coverage.mjs
// 输出: zdic_coverage_cache.json (每字各通道布尔) + 完成后打印统计
import fs from 'fs';
import https from 'https';
import path from 'path';

const ROOT = 'D:/WorkBuddy/projects/说文解字';
const CHARS = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/characters.json'), 'utf8')).characters.map(c => c.char);
const CACHE = path.join(ROOT, 'zdic_coverage_cache.json');
const CHANNELS = ['jiaguwen', 'jinwen', 'xiaozhuan', 'chuwenzi', 'qinwenzi', 'lishu', 'chuanchao'];
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

const cache = fs.existsSync(CACHE) ? JSON.parse(fs.readFileSync(CACHE, 'utf8')) : {};

function get(url, depth = 0) {
  return new Promise((resolve) => {
    if (depth > 5) return resolve({ s: 'TOODEEP' });
    const req = https.get(url, { headers: { 'User-Agent': UA, 'Referer': 'https://www.zdic.net/' } }, (r) => {
      if ([301, 302, 303, 307, 308].includes(r.statusCode)) {
        let loc = r.headers.location;
        let next;
        if (loc.startsWith('http')) next = loc;
        else { const u = new URL(url); next = u.origin + loc; }
        try { next = new URL(next); next.pathname = encodeURI(next.pathname); next = next.toString(); } catch (e) {}
        return resolve(get(next, depth + 1));
      }
      let d = '';
      r.on('data', (c) => d += c);
      r.on('end', () => resolve({ s: r.statusCode, body: d }));
    });
    req.on('error', (e) => resolve({ s: 'ERR', body: e.message }));
    req.setTimeout(12000, () => { req.destroy(); resolve({ s: 'TO', body: '' }); });
  });
}

function detect(body) {
  const svgs = [...body.matchAll(/img\.zdic\.net([^\s"']*?\.svg)/g)].map(m => m[1]);
  const res = {};
  for (const ch of CHANNELS) res[ch] = svgs.some(s => s.includes(ch));
  return res; // 仅记录"有无"
}

async function scanOne(ch) {
  if (cache[ch] && Object.keys(cache[ch]).length) return cache[ch];
  const enc = encodeURIComponent(ch);
  for (let attempt = 0; attempt < 3; attempt++) {
    const r = await get('https://zdic.net/hans/' + enc, 0);
    if (r.s === 200 && r.body) {
      cache[ch] = detect(r.body);
      return cache[ch];
    }
    await new Promise(r => setTimeout(r, 600 * (attempt + 1)));
  }
  cache[ch] = { failed: true };
  return cache[ch];
}

const WORKERS = 10;
let idx = 0, done = 0, failed = 0;
const t0 = Date.now();

async function worker() {
  while (idx < CHARS.length) {
    const i = idx++;
    const ch = CHARS[i];
    const r = await scanOne(ch);
    done++;
    if (r.failed) failed++;
    if (done % 200 === 0) {
      fs.writeFileSync(CACHE, JSON.stringify(cache));
      const el = (Date.now() - t0) / 1000;
      console.log(`progress ${done}/${CHARS.length}  failed=${failed}  ${(done / el).toFixed(0)}/s`);
    }
  }
}

await Promise.all(Array.from({ length: WORKERS }, worker));
fs.writeFileSync(CACHE, JSON.stringify(cache));

// 统计"汉典有该字形的字数(8105内)"
const counts = { jiaguwen: 0, jinwen: 0, xiaozhuan: 0, chuwenzi: 0, qinwenzi: 0, lishu: 0, chuanchao: 0 };
let fcount = 0;
for (const ch of CHARS) {
  const r = cache[ch];
  if (!r || r.failed) { fcount++; continue; }
  for (const k of CHANNELS) if (r[k]) counts[k]++;
}
console.log('=== 汉典覆盖(8105内, 有该字形字数) ===');
console.log('甲骨文(jiaguwen):', counts.jiaguwen);
console.log('金文(jinwen):', counts.jinwen);
console.log('小篆(xiaozhuan):', counts.xiaozhuan);
console.log('楚系简帛(chuwenzi):', counts.chuwenzi);
console.log('秦系简牍(qinwenzi):', counts.qinwenzi);
console.log('简牍帛书(chu+qin):', counts.chuwenzi + counts.qinwenzi - 0); // 并集需去重, 下面算
console.log('隶书(lishu):', counts.lishu);
console.log('传抄古文字(chuanchao,含大篆/古文):', counts.chuanchao);
console.log('failed/unfetched:', fcount);

// 简牍帛书并集(楚系 或 秦系)
let chuOrQin = 0;
for (const ch of CHARS) { const r = cache[ch]; if (r && !r.failed && (r.chuwenzi || r.qinwenzi)) chuOrQin++; }
console.log('简牍帛书并集(chuwenzi||qinwenzi):', chuOrQin);
