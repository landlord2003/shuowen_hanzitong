// 用 zdic_coverage_cache.json 的实测结果，替换 index.html 四列表的「汉典」列。
// 汉典列 = 汉典(zdic.net)在 8105 规范字中"有该字形"的字数。
import fs from 'fs';
import path from 'path';

const ROOT = 'D:/WorkBuddy/projects/说文解字';
const F = path.join(ROOT, 'index.html');
const CACHE = path.join(ROOT, 'zdic_coverage_cache.json');
const CHARS = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/characters.json'), 'utf8')).characters.map(c => c.char);
const N = CHARS.length; // 8105

const cache = JSON.parse(fs.readFileSync(CACHE, 'utf8'));
const CH = ['jiaguwen', 'jinwen', 'xiaozhuan', 'chuwenzi', 'qinwenzi', 'lishu', 'chuanchao'];
const cnt = {}; CH.forEach(c => cnt[c] = 0);
let failed = 0;
for (const ch of CHARS) {
  const r = cache[ch];
  if (!r || r.failed) { failed++; continue; }
  for (const k of CH) if (r[k]) cnt[k]++;
}
// 简牍帛书 = 楚系 或 秦系
let chuOrQin = 0;
for (const ch of CHARS) { const r = cache[ch]; if (r && !r.failed && (r.chuwenzi || r.qinwenzi)) chuOrQin++; }

const pct = (x) => (100 * x / N).toFixed(1) + '%';
// 各书体 -> 汉典实测字数 (label, count, note)
const map = {
  '甲骨文': [cnt.jiaguwen, ''],
  '金文': [cnt.jinwen, ''],
  '大篆': [cnt.chuanchao, '（汉典称"传抄古文字"，含大篆/古文/籀文）'],
  '小篆': [cnt.xiaozhuan, ''],
  '隶书': [cnt.lishu, ''],
  '简牍帛书': [chuOrQin, ''],
};

let s = fs.readFileSync(F, 'utf8');
const CRLF = s.includes('\r\n') ? '\r\n' : '\n';

for (const [label, [count, note]] of Object.entries(map)) {
  const re = new RegExp('(<tr><td>' + label + '</td><td>[^<]*</td><td>[^<]*</td><td>)[^<]*(</td></tr>)');
  const repl = `$1${count} 字（${pct(count)}${note}）$2`;
  if (!re.test(s)) { console.log('WARN 未匹配行:', label); continue; }
  s = s.replace(re, repl);
  console.log('更新', label, '->', count, '字', `(${pct(count)})`);
}

// 同步更新引言句里的口径说明（若仍残留旧"缺口"措辞则改之）
fs.writeFileSync(F, s, 'utf8');
console.log('DONE index.html 字节=', s.length, ' failed/unfetched=', failed, ' 总字数=', N);
