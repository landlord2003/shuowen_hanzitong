/**
 * verify_deploy.cjs —— 部署完整性核验（发布前跑一次）
 *
 * 做法：把仓库真克隆一份到临时目录（模拟「另一台电脑 pull 之后」的状态），
 * 起一个临时静态服务，把 index.html 引用的每个资源逐个拉一遍，
 * 校验 HTTP 状态、响应体非空、二进制文件头、JS 语法、内联数据完整度。
 *
 * 用法： node tools/verify_deploy.cjs
 *       node tools/verify_deploy.cjs --keep   （保留临时克隆，便于人工排查）
 * 退出码：0 全部通过；1 存在失败项。
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const vm = require('vm');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const KEEP = process.argv.includes('--keep');
const DST = path.join(os.tmpdir(), 'shuowen_deploy_verify');

// 优先用项目 PortableGit，取不到则退回 PATH 里的 git
function findGit() {
  const cand = 'C:/Users/吴自强/.workbuddy/binaries/PortableGit/versions/1.2.0/cmd/git.exe';
  if (fs.existsSync(cand)) return cand;
  return 'git';
}
const GIT = findGit();
const sh = (args) => execFileSync(GIT, args, { encoding: 'utf8', maxBuffer: 1 << 29 });

const fails = [];
function check(ok, label) {
  console.log('  [' + (ok ? 'OK ' : 'FAIL') + '] ' + label);
  if (!ok) fails.push(label);
}

// ---------- 1. 克隆 ----------
if (fs.existsSync(DST)) fs.rmSync(DST, { recursive: true, force: true });
fs.mkdirSync(path.dirname(DST), { recursive: true });
console.log('=== 1. 全新克隆（模拟另一台电脑 pull 后）===');
const t0 = Date.now();
sh(['clone', '--quiet', '--no-hardlinks', ROOT, DST]);
console.log('  克隆耗时 ' + ((Date.now() - t0) / 1000).toFixed(1) + 's');
console.log('  HEAD: ' + sh(['-C', DST, 'log', '--oneline', '-1']).trim());
const srcHead = sh(['-C', ROOT, 'rev-parse', 'HEAD']).trim();
const dstHead = sh(['-C', DST, 'rev-parse', 'HEAD']).trim();
check(srcHead === dstHead, '克隆 HEAD 与源仓库一致 (' + srcHead.slice(0, 7) + ')');
check(!sh(['-C', DST, 'status', '--short']).trim(), '克隆后工作树 clean');
const nFiles = sh(['-C', DST, 'ls-files']).split(/\r?\n/).filter(Boolean).length;
console.log('  跟踪文件数: ' + nFiles);

// ---------- 2. 抽取所有本地资源引用 ----------
const html = fs.readFileSync(path.join(DST, 'index.html'), 'utf8');
const refs = new Set();
for (const re of [
  /<script[^>]+src\s*=\s*["']([^"']+)["']/gi,
  /<link[^>]+href\s*=\s*["']([^"']+)["']/gi,
  /<img[^>]+src\s*=\s*["']([^"']+)["']/gi,
]) for (const m of html.matchAll(re)) refs.add(m[1]);
// fetch("data/xxx.json?ver") 这类运行时加载
for (const m of html.matchAll(/fetch\s*\(\s*["'`]([^"'`?]+)/g)) refs.add(m[1]);
// 字符串形式的数据路径（字体 FontFace、动态 script）
for (const m of html.matchAll(/["'`]((?:data|assets|tools)\/[A-Za-z0-9._\-\/]+\.(?:js|json|bin|otf|ttf|css|png|jpg|ico))["'`]/g)) refs.add(m[1]);

const targets = [...new Set([...refs]
  .filter(r => !/^(https?:)?\/\//.test(r) && !r.startsWith('data:') && !r.startsWith('#') && !r.startsWith('blob:'))
  .map(r => r.replace(/^\.\//, '').split('?')[0].split('#')[0]))].sort();

// 这些路径是 JS 表达式拼接产物，不是真实路径
const IGNORE = /[+(){}]/;

console.log('\n=== 2. 引用资源逐个实测（' + targets.length + ' 项）===');
const MIME = { '.html': 'text/html;charset=utf-8', '.js': 'application/javascript;charset=utf-8', '.json': 'application/json;charset=utf-8', '.bin': 'application/octet-stream', '.otf': 'font/otf', '.ttf': 'font/ttf', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon' };
const server = http.createServer((req, res) => {
  const p = path.join(DST, decodeURIComponent(req.url.split('?')[0]));
  if (!fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end('404'); }
  const st = fs.statSync(p);
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p).toLowerCase()] || 'application/octet-stream', 'Content-Length': st.size });
  fs.createReadStream(p).pipe(res);
});

server.listen(0, '127.0.0.1', async () => {
  const port = server.address().port;
  // index.html 本身
  for (const t of ['index.html', ...targets]) {
    if (IGNORE.test(t) || !fs.existsSync(path.join(DST, t))) { check(false, t + '  ← 引用路径在仓库中不存在'); continue; }
    try {
      const r = await fetch('http://127.0.0.1:' + port + '/' + t);
      const b = Buffer.from(await r.arrayBuffer());
      const disk = fs.statSync(path.join(DST, t)).size;
      // 状态 200、响应体非空、且长度与磁盘一致（防并发缺陷导致的空体/截断）
      check(r.status === 200 && b.length > 0 && b.length === disk,
        t + '  ' + r.status + '  ' + (b.length / 1048576).toFixed(2) + 'MB');
    } catch (e) { check(false, t + '  ← ' + e.message); }
  }

  // ---------- 3. 二进制文件头 ----------
  console.log('\n=== 3. 字体与二进制文件头 ===');
  for (const f of targets.filter(x => /^data\/fonts\/.*\.(otf|ttf)$/.test(x))) {
    const p = path.join(DST, f);
    const b = Buffer.alloc(4); const fd = fs.openSync(p, 'r'); fs.readSync(fd, b, 0, 4, 0); fs.closeSync(fd);
    const h = b.toString('hex');
    check(h === '4f54544f' || h.startsWith('0001') || h === '74746366', f + '  头=' + h);
  }
  const bin = path.join(DST, 'data/dataset.bin');
  if (fs.existsSync(bin)) {
    const b = Buffer.alloc(15); const fd = fs.openSync(bin, 'r'); fs.readSync(fd, b, 0, 15, 0); fs.closeSync(fd);
    check(b.slice(0, 4).toString('latin1') === 'CEDS', 'data/dataset.bin  容器签名=' + b.slice(0, 11).toString('latin1'));
  }

  // ---------- 4. JSON 大文件可解析 ----------
  console.log('\n=== 4. 大体积 JSON 可解析 ===');
  for (const f of ['data/stroke_data.json', 'data/characters.json', 'data/cultural.json']) {
    const p = path.join(DST, f);
    if (!fs.existsSync(p)) { check(false, f + '  ← 缺失'); continue; }
    try {
      const j = JSON.parse(fs.readFileSync(p, 'utf8'));
      const n = Array.isArray(j) ? j.length : (Array.isArray(j.characters) ? j.characters.length : Object.keys(j).length);
      check(n > 0, f + '  条目=' + n);
    } catch (e) { check(false, f + '  ← JSON 解析失败: ' + e.message); }
  }

  // ---------- 5. 运行时 JS 语法 ----------
  console.log('\n=== 5. 运行时 JS 语法 ===');
  for (const f of targets.filter(x => /^data\/.*\.js$/.test(x))) {
    try { new vm.Script(fs.readFileSync(path.join(DST, f), 'utf8'), { filename: f }); check(true, f); }
    catch (e) { check(false, f + '  ← ' + e.message); }
  }

  // ---------- 6. 内联数据自包含度 ----------
  console.log('\n=== 6. 内联 DATA（无服务时也能用的底线）===');
  try {
    const s = html.indexOf('{', html.indexOf('var DATA'));
    let d = 0, i = s, e2 = -1, inStr = false, esc = false;
    for (; i < html.length; i++) {
      const c = html[i];
      if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; continue; }
      if (c === '"') { inStr = true; continue; }
      if (c === '{') d++; else if (c === '}') { d--; if (d === 0) { e2 = i + 1; break; } }
    }
    const DATA = vm.runInNewContext('(' + html.slice(s, e2) + ')');
    const arr = DATA.characters || [];
    const declared = (DATA.meta && DATA.meta.total_chars) || 0;
    check(arr.length === declared && arr.length > 0, '内联字符数 ' + arr.length + '（meta 声明 ' + declared + '）');
    for (const k of ['pinyin', 'pinyin_sw', 'liushu', 'shuowen']) {
      const n = arr.filter(c => c[k] !== undefined && c[k] !== '' && c[k] !== null).length;
      check(n === arr.length, '字段 ' + k + ' 覆盖 ' + n + '/' + arr.length);
    }
  } catch (e) { check(false, '内联 DATA 求值失败: ' + e.message); }

  // ---------- 7. 运行时绝对路径体检 ----------
  console.log('\n=== 7. 运行时文件不得硬编码本机路径 ===');
  const runtime = ['index.html', ...targets.filter(x => /^data\/.*\.(js|json)$/.test(x))];
  let hard = 0;
  for (const f of runtime) {
    const t = fs.readFileSync(path.join(DST, f), 'utf8');
    const m = t.match(/[A-Z]:[\\/]{1,2}(?:Users|WorkBuddy)[\\/][^"'\s,)]{0,60}/g);
    if (m) { hard++; console.log('     ' + f + ' → ' + [...new Set(m)].slice(0, 3).join(' | ')); }
  }
  check(hard === 0, '运行时文件硬编码绝对路径数 = ' + hard);

  // ---------- 汇总 ----------
  server.close();
  console.log('\n==================== 汇总 ====================');
  console.log('检查项 ' + (fails.length ? '★ 有失败' : '全部通过') + '，失败 ' + fails.length + ' 项');
  for (const f of fails) console.log('  ✗ ' + f);
  if (KEEP) console.log('\n临时克隆保留于: ' + DST);
  else fs.rmSync(DST, { recursive: true, force: true });
  process.exit(fails.length ? 1 : 0);
});
