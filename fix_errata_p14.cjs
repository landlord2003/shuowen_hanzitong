// P1-4 收尾：数据勘误 4 字（characters.json 字段）+ suspect 9 字（cultural.json story）
const fs = require('fs');
const B = 'D:/WorkBuddy/projects/说文解字/data/';
const CJP = B + 'characters.json', CULP = B + 'cultural.json';

const cjRaw = fs.readFileSync(CJP, 'utf8');
const culRaw = fs.readFileSync(CULP, 'utf8');
const cj = JSON.parse(cjRaw), cul = JSON.parse(culRaw);

// 先验证：round-trip 是否与原文件字节一致（确保可安全回写）
const rtCj = JSON.stringify(cj) === cjRaw;
const rtCul = JSON.stringify(cul) === culRaw;
console.log('round-trip characters.json 字节一致:', rtCj, ' cultural.json 字节一致:', rtCul);
if (!rtCj || !rtCul) { console.log('⚠️ 往返不一致，改用定向字符串替换更安全——中止。'); process.exit(1); }

// 备份
fs.copyFileSync(CJP, CJP + '.bak_pre_errata4');
fs.copyFileSync(CULP, CULP + '.bak_pre_suspect9');

const by = {}; for (const c of cj.characters) by[c.char] = c;

// ── A. 数据勘误 4 字（trad 原本指向了别的字，连带 radical/shuowen 也错）
const FIELD_FIX = {
  '匦': { trad: '匭', radical: '匚', radical_name: '匚部', shuowen: '古文簋。从匚軌。', original: '匣也' },
  '颃': { trad: '頏', radical: '頁', radical_name: '頁部', shuowen: '亢或从頁。从頁亢聲。', original: '人頸也' },
  '渺': { trad: '渺', radical: '水', radical_name: '水部', shuowen: '（后起字，从水眇声，《说文》未收。）', original: '水面辽阔' },
  '驭': { trad: '馭', radical: '馬', radical_name: '馬部', shuowen: '（《说文》御之或体，从馬从又。）', original: '使馬也' },
};
const aLog = [];
for (const ch in FIELD_FIX) {
  const c = by[ch];
  if (!c) { aLog.push('MISSING ' + ch); continue; }
  const rec = [];
  for (const k in FIELD_FIX[ch]) { rec.push(k + ': ' + JSON.stringify(c[k]) + ' -> ' + JSON.stringify(FIELD_FIX[ch][k])); c[k] = FIELD_FIX[ch][k]; }
  aLog.push('【' + ch + '】\n   ' + rec.join('\n   '));
}

// ── B. suspect 9 字 story（逐条对照《说文》原文重写构形句，保留文化引申）
const STORY_FIX = {
  '坰': '「坰」从「土」从「冋」（声），指远离城邑的郊野，本义为遥远的郊野。《说文》训「冂」为「林外谓之冂，象远界也」，「坰」即其孳乳字。引申指野外、远郊。',
  '夯': '「夯」从「大」从「力」，本义为用力砸实、打夯（《说文》未收，为后起字）。引申为夯实、填实，又指夯土的工具。',
  '皋': '「皋」从「夲」从「白」，「夲」表疾进，「白」表光明洁白，本义为「气皋白之进也」（雾气升腾而洁白）。引申指水边高地、沼泽之岸。',
  '麦': '「麦」从「來」从「夊」，「來」象麦株之形，「夊」象其根，本义为麦类作物。《说文》：「芒谷，秋穜厚薶，故谓之麦。」引申专指小麦。',
  '亟': '「亟」从「人」从「口」，从「又」从「二」（二表天地），本义为「敏疾也」（急速）。引申为急迫、屡次。',
  '尿': '「尿」从「尾」从「水」，「尾」表人体下部，「水」表排泄之液，本义为「人小便也」（小便）。',
  '先': '「先」从「儿」（人）从「之」（前往），本义为「前进也」。引申为时间或次序在前，又指祖先、首要。',
  '寇': '「寇」从「攴」（手持器械）从「完」（兼表音），本义为「暴也」（劫掠侵犯）。引申为盗匪、侵略者。',
  '亘': '「亘」从「二」从「囘」（回），「二」表上下，「囘」象回旋之形，本义为「求亘也」。引申为延续不断、横贯。',
};
const bLog = [];
for (const ch in STORY_FIX) {
  const e = cul[ch];
  if (!e) { bLog.push('MISSING ' + ch); continue; }
  bLog.push('【' + ch + '】旧: ' + e.story + '\n   新: ' + STORY_FIX[ch]);
  e.story = STORY_FIX[ch];
}

fs.writeFileSync(CJP, JSON.stringify(cj), 'utf8');
fs.writeFileSync(CULP, JSON.stringify(cul), 'utf8');

console.log('\n=== A. characters.json 勘误 ' + Object.keys(FIELD_FIX).length + ' 字 ===\n' + aLog.join('\n'));
console.log('\n=== B. cultural.json suspect story ' + Object.keys(STORY_FIX).length + ' 字 ===\n' + bLog.join('\n'));
console.log('\n条目数 characters=' + cj.characters.length + ' cultural=' + Object.keys(cul).length);
