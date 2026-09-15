// 将 feihualing.js 挂载到 index.html（幂等）
const fs = require('fs');
const B = 'D:/WorkBuddy/projects/说文解字/';
const P = B + 'index.html';
let H = fs.readFileSync(P, 'utf8');
const TAG = '<script src="data/feihualing.js"></script>';
if (H.indexOf('data/feihualing.js') >= 0) { console.log('已挂载，跳过'); process.exit(0); }

const anchor = '<script src="data/app-features.js">';
const i = H.indexOf(anchor);
if (i < 0) { console.log('⚠️ 未找到锚点 app-features.js'); process.exit(1); }
const j = H.indexOf('</script>', i);
if (j < 0) { console.log('⚠️ 未找到 </script>'); process.exit(1); }
const at = j + '</script>'.length;

// 保持原有换行风格
const nl = H.slice(at, at + 2) === '\r\n' ? '\r\n' : '\n';
fs.copyFileSync(P, B + 'index.html.bak_pre_fhl');
H = H.slice(0, at) + nl + TAG + H.slice(at);
fs.writeFileSync(P, H, 'utf8');
console.log('已插入 <script src="data/feihualing.js"> @' + at);
console.log('出现次数:', (H.match(/data\/feihualing\.js/g) || []).length);
console.log('新大小(MB):', (H.length / 1048576).toFixed(2));
