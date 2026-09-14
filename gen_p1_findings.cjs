// 生成 P1-4 抽检发现清单 + 报告（人工判决结果固化）
const fs = require('fs');
const ROOT = 'D:/WorkBuddy/projects/说文解字';
const v4 = JSON.parse(fs.readFileSync(ROOT + '/data/p1_judge_v4.json', 'utf8'));

// 人工核验·判为「假阳性」：现代结构正确 / 《说文》仅列篆体义符，story 无误
const FP = new Set(['帽','创','域','生','凝','法','划','集','蛊','甘','直','涉','炙','古','明','国','卧','采','或','旦','牧','军','逐','束','尾','乔']);
// 人工核验·判为「真错」（story 构件自造/张冠李戴）；其余高置信默认 suspect
const REAL = new Set(['冒','舍','香','紧','弱','兜','印','竞','兴','退','觋','辔','玄','庆','局','恒','沓','耐','肱','燮','页','具','匦','丙','攸','邑','兽','联','刈','桀','出','奏','尊','毳','匠','幸','濒','青','最','频','熏','氐','乂','嗣','佩','赞','史','敖','扫','危','肘','芈','析','筋','酋','戎','台','别','定','今','申','乍','承','些','审','麻','寡','泅','涎','市','罚','祝','射','善','图','茧','威','素','祟','竟','普','驭','颃','败','宦','只','处','须','晋','卮','埽','协','向','坚','利','寅','渺','算','谷','昌','质','伏','规','委','詹','会','合','甚','毋','奄','绝','衔','支','设','妻','飨','全','躬','庸','詈','平','制','肥','簋','章','翟','赤','胤','龠','枚','致','悉']);

const decorate = r => ({ ...r, verdict: FP.has(r.ch) ? 'FP' : (REAL.has(r.ch) ? 'REAL' : 'suspect') });
const high = v4.highConf.map(decorate);
const mid = v4.midConf.map(r => ({ ...r, verdict: 'mid' }));
const nReal = high.filter(r => r.verdict === 'REAL').length;
const nFP = high.filter(r => r.verdict === 'FP').length;
const nSus = high.filter(r => r.verdict === 'suspect').length;

const out = {
  meta: {
    generated: new Date().toISOString().slice(0, 10),
    method: '逐字比对 story 的强构形断言(从X从Y / 由X与Y组成) 与《说文》原文构件；偏旁异体+简繁归一；剔除否证语境',
    basis: 'data/characters.json 的 shuowen 字段（《说文》原文，权威）',
    highConf: high.length, real: nReal, falsePositive: nFP, suspect: nSus, midConf: mid.length
  },
  highConf: high, midConf: mid
};
fs.writeFileSync(ROOT + '/data/p1_audit_findings.json', JSON.stringify(out, null, 1));

// 报告
const L = [];
L.push('# P1-4 字源 story · 余量扩展抽检报告');
L.push('');
L.push('- 生成日期：' + out.meta.generated);
L.push('- 抽检范围：`data/p1_candidates.json`（' + v4.highConf.length + ' 高置信 + ' + v4.midConf.length + ' 中置信，已排除此前 B/B2/B3 已修 48 字）');
L.push('- 方法：' + out.meta.method);
L.push('- 基准：' + out.meta.basis);
L.push('');
L.push('## 一、结论');
L.push('');
L.push('| 判定 | 数量 | 说明 |');
L.push('|---|---:|---|');
L.push('| ✅ 真错(REAL) | ' + nReal + ' | story 构件与《说文》冲突，确属生成错误 |');
L.push('| ⚪ 假阳性(FP) | ' + nFP + ' | story 属现代结构分析、《说文》列篆体义符，story 无误 |');
L.push('| 🟡 待复核(suspect) | ' + nSus + ' | 高置信但需人工终审 |');
L.push('| 中置信(mid) | ' + mid.length + ' | 《说文》仅列单一义符，噪声大，仅备查 |');
L.push('');
L.push('## 二、错误模式（REAL 类）');
L.push('');
L.push('1. **凭空造构件**：story 拆分出《说文》完全没有的部件。');
L.push('   - 肘「月+舟」→《说文》从肉从寸（应为寸，非舟）');
L.push('   - 泅「氵+酉」→《说文》从水从子（应为子，非酉）');
L.push('   - 兴「八+井」→《说文》从舁从同');
L.push('   - 竞「彐+攴」→《说文》从誩从二人');
L.push('   - 图「囗+余」→《说文》从囗从啚');
L.push('2. **张冠李戴声旁**：以为某字是声旁，实为另一形符。');
L.push('   - 耐「肉+耏」→《说文》从而从彡');
L.push('   - 设「言+市」→《说文》从言从殳');
L.push('   - 致「至+辵」→《说文》从夊从至');
L.push('3. **自指/自我复制**：story 用本字自身当部件。');
L.push('   - 乍「女+乍」、麻「麻+木」、市「市+買」');
L.push('');
L.push('## 三、假阳性说明（诚实披露）');
L.push('');
L.push('以下 story 经人工核验**无误**，属自动筛查误报，勿改：');
L.push([...FP].join('、'));
L.push('');
L.push('误报主因：①story 用简体/偏旁形（氵扌纟），《说文》用本字（水手糸）——同义；②《说文》只给篆体义符（如「集」从雥从木），story 的「隹+木」是现代通行分析，正确。');
L.push('');
L.push('## 四、REAL 清单（' + nReal + ' 字，建议纳入下一批修正）');
L.push('');
for (const r of high.filter(x => x.verdict === 'REAL'))
  L.push('- **' + r.ch + '**（' + r.liushu + '）story[' + r.badParts.join('/') + '] ≠ 说文[' + r.swParts.join('/') + ']');
L.push('');
L.push('## 五、待复核 suspect（' + nSus + ' 字）');
L.push('');
L.push(high.filter(x => x.verdict === 'suspect').map(x => x.ch).join('、'));
L.push('');
L.push('## 六、下一步建议');
L.push('');
L.push('1. REAL 清单 ' + nReal + ' 字，按《说文》原文重写 story 的构形句（去杜撰、保留文化引申）。');
L.push('2. suspect ' + nSus + ' 字人工终审后再定。');
L.push('3. mid ' + mid.length + ' 字噪声大，暂不动。');
fs.writeFileSync(ROOT + '/tools/P1-4_余量抽检报告.md', L.join('\n'));
console.log('REAL', nReal, 'FP', nFP, 'suspect', nSus, 'mid', mid.length);
