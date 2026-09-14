import fs from 'fs';

const F = 'D:/WorkBuddy/projects/说文解字/index.html';
let s = fs.readFileSync(F, 'utf8');

const rep = (oldS, newS, label) => {
  const n = s.split(oldS).length - 1;
  if (n !== 1) throw new Error(`[${label}] 匹配数=${n}（期望1），中止以免误改`);
  s = s.replace(oldS, newS);
  console.log(`OK  ${label}  (matched 1)`);
};

// 0) 折叠面板标题 -> 三张知识卡片
rep(
  '<summary>&#128218; 数据来源与说明（点击展开/收起）</summary>',
  '<summary>&#128218; 产品说明 · 知识卡片（六书 / 数据来源 / 统计，点击展开/收起）</summary>',
  '面板标题'
);

// 1) 六书卡片：在说明后追加 8105 字六书分布表
rep(
  '<p style="margin:8px 0 0;font-size:12px;color:var(--text3)">注：本 App 将常见字归入象形、指事、会意、形声四类；转注、假借更多是用字法，未作为单字主分类。</p></div>',
  `<p style="margin:10px 0 6px;font-size:13px;line-height:1.7"><b>本产品 8105 字六书分布</b>（取自《说文解字》字段）：</p>
<table class="cov-table"><tr><th>六书</th><th>字数</th><th>占比</th></tr>
<tr><td>形声</td><td>7189</td><td>88.7%</td></tr>
<tr><td>会意</td><td>588</td><td>7.3%</td></tr>
<tr><td>象形</td><td>292</td><td>3.6%</td></tr>
<tr><td>指事</td><td>30</td><td>0.4%</td></tr>
<tr><td>会意兼形声</td><td>6</td><td>0.1%</td></tr>
<tr><td><b>合计</b></td><td><b>8105</b></td><td><b>100%</b></td></tr></table>
<p style="margin:8px 0 0;font-size:12px;color:var(--text3)">注：本 App 将常见字归入象形、指事、会意、形声四类；转注、假借更多是用字法，未作为单字主分类。「会意兼形声」为少量边界字单独标注。</p></div>`,
  '六书分布表'
);

// 2) 数据来源卡片：追加汉典不接入声明
rep(
  '约 44% 字（人体、动作、抽象、虚词等）无明确归属</li></ul></div>',
  `约 44% 字（人体、动作、抽象、虚词等）无明确归属</li>
<li class="warn">⚠️ <b>汉典（zdic.net）数据不接入本商用产品</b>：汉典对古文字形采用 CC0 与 CC BY-NC-ND 2.5 两种冲突口径，且其无权处分《甲骨文编》《说文》陈昌治本等底本权利；汉典字形仅作<b>内部研究与缺口索引</b>使用，不在产品内以任何形式呈现。</li></ul></div>`,
  '汉典不接入声明'
);

// 3) 统计卡片：甲骨行数字更新
rep(
  '758 字<br>（真迹）</td><td>—</td><td>9.4%',
  '955 字<br>（真迹）</td><td>—</td><td>11.8%',
  '甲骨行'
);
// 4) 金文行数字更新
rep(
  '1056 字<br>（真迹）</td><td>—</td><td>13.0%',
  '2049 字<br>（真迹）</td><td>—</td><td>25.3%',
  '金文行'
);
// 5) 篆书行拆为 大篆 + 小篆
rep(
  '<tr><td>篆书</td><td>9353 字头<br>（《说文解字》小篆）</td><td>2903 字<br>（真迹：大篆1362＋小篆2848 去重）</td><td>—</td><td>35.8%</td></tr>',
  `<tr><td>大篆</td><td>籀文，无精确总表<br>（石鼓文等，学界估数千）</td><td>1362 字<br>（真迹）</td><td>—</td><td>16.8%</td></tr>
<tr><td>小篆</td><td>9353 字头<br>（《说文解字》）</td><td>2848 字<br>（真迹）</td><td>—</td><td>35.1%</td></tr>`,
  '篆书拆分为大篆+小篆'
);
// 6) 统计卡片引言：补充历史可考总字形图 15,931
rep(
  '<p style="margin:0 0 10px;line-height:1.7">下表对比「各古文字阶段历史上能写的字数（学界基准）」与「本产品在 8105 个规范汉字中实际收录展示的字数」：</p>',
  '<p style="margin:0 0 10px;line-height:1.7">本产品历史可考字形图共 <b>15,931 张</b>（古文字真迹 7,826 张 ＋ 字源图 8,105 张）。下表对比「各古文字阶段历史上能写的字数（学界基准）」与「本产品在 8105 个规范汉字中实际收录展示的字数（解码 dataset.bin 实测）」：</p>',
  '统计引言'
);
// 7) 插入汉典针对8105统计表（在第一个 </table> 与 口径说明 之间）
rep(
  '</table>\r\n<p>口径说明：',
  `</table>\r\n<h3 style="margin:16px 0 8px">汉典（zdic.net）针对本产品 8105 字的覆盖</h3>\r\n<p style="margin:0 0 10px;line-height:1.7;font-size:12px;color:var(--text3)">汉典为内部研究缺口索引，<b>不接入本商用产品</b>。下表为其三书体重建针对本 8105 字的实际覆盖（字形数为单字下摹写矢量数）：</p>\r\n<table class="cov-table">\r\n<tr><th>书体</th><th>覆盖字数（∈8105）</th><th>字形数</th><th>占 8105</th></tr>\r\n<tr><td>甲骨文</td><td>452 字</td><td>4977</td><td>5.6%</td></tr>\r\n<tr><td>简牍帛书</td><td>1832 字</td><td>20379</td><td>22.6%</td></tr>\r\n<tr><td>小篆</td><td>2821 字</td><td>3295</td><td>34.8%</td></tr>\r\n<tr><td><b>三体去重并集</b></td><td><b>3832 字</b></td><td>—</td><td><b>47.3%</b></td></tr>\r\n</table>\r\n<p>口径说明：`,
  '汉典针对8105表'
);
// 8) 口径说明 ② 注明实算 + ⑤ 汉典不入统计
rep(
  '（甲骨/金文/简帛/大篆/小篆 真迹已基本完备）',
  '（甲骨/金文/简帛/大篆/小篆 真迹已基本完备，数字解码 dataset.bin 实算）',
  '口径②实算'
);
rep(
  '余约 9% 简体字无隶书字形回退楷体。</p>',
  '余约 9% 简体字无隶书字形回退楷体；⑤ 汉典三体（甲骨/简帛/小篆）覆盖基于其公开摹写，仅作内部缺口参考，未计入本产品真迹统计。</p>',
  '口径⑤汉典'
);

s = s.replace(/\r\n/g, '\n').replace(/\n/g, '\r\n');
fs.writeFileSync(F, s, 'utf8');
console.log('DONE index.html 字节数=', s.length);
