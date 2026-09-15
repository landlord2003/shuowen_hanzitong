# 说文解字 App · 全量拼音声调核查报告

生成日期：2026-09-15　对象：`data/characters.json` 的 `pinyin` 字段（8105 字）

## 一、结论速览

| 项 | 字数 | 占比 |
|---|---|---|
| 总字数 | 8105 | 100% |
| 与标准读音**完全一致** | 5356 | 66.1% |
| App 读音是标准读音的**子集**（仅收了部分读音，不算错） | 2572 | 31.7% |
| **疑似错误** | **177** | **2.18%** |

疑似错误分两类：

- **A 类 · 串档 35 条**：App 的简体/后起字被匹配到了**另一个古字（异体字/通假字）**的说文记录。
  拼音直接照抄了那个古字的音（例：「阵」抄了「敶」读 chén、「肤」抄了「臚」读 lú、「茶」抄了「荼」读 tú）。
- **B 类 · 古音折合 142 条**：字没串，但**拼音取的是《说文》音切折合出来的中古读音，不是现代普通话规范音**。
  例：「义」宜寄切→yí（今 yì）、「曰」王代切→yuè（今 yuē）、「吃」居乙切→jī（今 chī）、「企」去智切→qì（今 qǐ）、「缇」他禮切→tǐ（今 tí）。

## 二、根因

两者的源头都是 `merge_shuowen.py` → `build_from_shuowen.py` 这条链：

```
merge_shuowen.py   :65   "pinyin": entry.get("pinyin_full", "")   ← App 拼音的唯一来源
merge_shuowen.py   :23   for idx in d.get("indexes", []): index_map.setdefault(idx, d)
                           ↑ 说文源的 indexes 混装了「本字」与「关联异体字」，被一律当本字索引
```

- **A 类的因**：`indexes` 里把异体字也登记成本字，于是查「阵」命中了「敶」的整条记录（连 shuowen/fanqie 一起串）。
- **B 类的因**：说文源的 `pinyin_full` 是**依音切折合的中古音**，不是《现代汉语词典》的现代规范音；
  该字本身匹配正确，只是「读音口径」与产品需要（让用户知道现在怎么读）不一致。

> 说明：`fanqie`（反切）字段本来就独立存在、并在详情页展示为「反切：XX切 · 出《说文》」。
> 因此把 `pinyin` 修正为现代读音，**不会丢失古音信息**（古音仍在 fanqie 中）。

## 三、A 类 · 串档明细（35 条）

来源字 = 实际被匹配到的那个古字（≠ App 字）。建议列的箭头指向按标准读音修正后的值。

| 字 | App 拼音 | 标准读音 | 来源字 | 源 pinyin_full | 反切 | 建议 |
|---|---|---|---|---|---|---|
| 阵 | `chén` | zhèn | 敶 | chén | 直刃切 | chén→zhèn |
| 吭 | `gāng` | kēng/háng/hàng | 亢 | ɡānɡ | 古郎切 | gāng→kēng |
| 住 | `shù` | zhù | 侸 | shù | 常句切 | shù→zhù |
| 肤 | `lú` | fū | 臚 | lú | 力居切 | lú→fū |
| 朋 | `fèng` | péng | 鳳 | fènɡ | 馮貢切 | fèng→péng |
| 茶 | `tú` | chá | 荼 | tú | 同都切 | tú→chá |
| 栏 | `liàn` | lán | 楝 | liàn | 郎電切 | liàn→lán |
| 鸦 | `yǎ` | yā | 雅 | yǎ | 五下切 | yǎ→yā |
| 眠 | `míng` | mián/miǎn/mǐn | 瞑 | mínɡ | 武延切 | míng→mián |
| 蚣 | `sōng` | gōng/zhōng | 蜙 | sōnɡ | 息恭切 | sōng→gōng |
| 蛇 | `tā` | shé/yí/tuó/chí | 它 | tā | 託何切 | tā→shé |
| 徘 | `péi` | pái | 裵 | péi | 薄回切 | péi→pái |
| 添 | `zhān` | tiān/tiàn | 沾 | zhān | 他兼切 | zhān→tiān |
| 喧 | `huān` | xuān/xuǎn | 讙 | huān | 呼官切 | huān→xuān |
| 慷 | `kàng` | kāng | 忼 | kànɡ | 苦浪切 | kàng→kāng |
| 影 | `jǐng` | yǐng | 景 | jǐnɡ | 居影切 | jǐng→yǐng |
| 鲫 | `zéi` | jì | 鰂 | zéi | 昨則切 | zéi→jì |
| 憔 | `jiāo` | qiáo | 䩌 | jiāo | 即消切 | jiāo→qiáo |
| 瞪 | `chì` | dèng | 眙 | chì | 丑吏切 | chì→dèng |
| 螺 | `luǒ` | luó | 蠃 | luǒ | 郎果切 | luǒ→luó |
| 杻 | `chūn` | chǒu/niǔ | 杶 | chūn | 敕倫切 | chūn→chǒu |
| 茯 | `bèi` | fú | 絥 | bèi | 平袐切 | bèi→fú |
| 娈 | `luǎn` | luán | 𡡗 | luǎn | 力沇切 | luǎn→luán |
| 隼 | `zhuī` | sǔn | 鵻 | zhuī | 思允切 | zhuī→sǔn |
| 颃 | `gāng` | háng | 亢 | ɡānɡ | 古郎切 | gāng→háng |
| 涟 | `lán` | lián | 瀾 | lán | 洛干切 | lán→lián |
| 辍 | `zhuó` | chuò | 罬 | zhuó | 陟劣切 | zhuó→chuò |
| 嗟 | `chā` | jiē/jiè/juē | 差 | chā | 初牙切 | chā→jiē |
| 掣 | `chì` | chè | 𤸪 | chì | 尺制切 | chì→chè |
| 赓 | `xù` | gēng | 續 | xù | 似足切 | xù→gēng |
| 蝈 | `yù` | guō | 蜮 | yù | 于逼切 | yù→guō |
| 簪 | `zēn` | zān/zǎn | 兂 | zēn | 側岑切 | zēn→zān |
| 鸺 | `jiù` | xiū | 舊 | jiù | 巨救切 | jiù→xiū |
| 髢 | `xī` | dí | 鬄 | xī | 先彳切 | xī→dí |
| 彟 | `huò` | yuē | 蒦 | huò | 乙虢切 | huò→yuē |

## 四、B 类 · 古音折合明细（142 条）

来源字与 App 字为同一字（简繁/异体关系），仅为读音口径差异。

| 字 | App 拼音 | 标准读音 | 来源字 | 源 pinyin_full | 反切 | 建议 |
|---|---|---|---|---|---|---|
| 义 | `yí` | yì | 義 | yí | 宜寄切 | yí→yì |
| 曰 | `yuè` | yuē | 曰 | yuè | 王代切 | yuè→yuē |
| 队 | `zhuì` | duì | 隊 | zhuì | 徒對切 | zhuì→duì |
| 厌 | `yā` | yàn | 厭 | yā | 於輒切 | yā→yàn |
| 页 | `xié` | yè | 頁 | xié | 胡結切 | xié→yè |
| 吃 | `jī` | chī/qī | 吃 | jī | 居乙切 | jī→chī |
| 企 | `qì` | qǐ | 企 | qì | 去智切 | qì→qǐ |
| 闯 | `chèn` | chuǎng | 闖 | chèn | 丑禁切 | chèn→chuǎng |
| 尬 | `jiè` | gà | 尬 | jiè | 公八切 | jiè→gà |
| 县 | `xuán` | xiàn | 縣 | xuán | 胡涓切 | xuán→xiàn |
| 钉 | `xié` | dīng/dìng | 钉 | xié | — | xié→dīng |
| 妙 | `yāo` | miào/miǎo | 玅 | yāo | 於霄切 | yāo→miào |
| 厕 | `cì` | cè/si | 廁 | cì | 初吏切 | cì→cè |
| 欧 | `ǒu` | ōu | 歐 | ǒu | 烏后切 | ǒu→ōu |
| 顷 | `qīng` | qǐng | 頃 | qīnɡ | 去營切 | qīng→qǐng |
| 净 | `chéng` | jìng/chēng | 淨 | chénɡ | 士耕切 | chéng→chēng |
| 闸 | `yā` | zhá | 閘 | yā | 烏甲切 | yā→zhá |
| 哑 | `è` | yǎ/yā | 啞 | è | 於革切 | è→yǎ |
| 俘 | `fū` | fú | 俘 | fū | 芳無切 | fū→fú |
| 捡 | `liǎn` | jiǎn | 撿 | liǎn | 良冉切 | liǎn→jiǎn |
| 唠 | `chāo` | láo/lào | 嘮 | chāo | 敕交切 | chāo→láo |
| 颂 | `róng` | sòng | 頌 | rónɡ | 余封切 | róng→sòng |
| 涝 | `láo` | lào | 澇 | láo | 魯刀切 | láo→lào |
| 剧 | `jí` | jù | 劇 | jí | 渠力切 | jí→jù |
| 探 | `tān` | tàn/xián | 探 | tān | 他含切 | tān→tàn |
| 勘 | `kàn` | kān | 勘 | kàn | 苦紺切 | kàn→kān |
| 梦 | `méng` | mèng | 夢 | ménɡ | 莫忠切 | méng→mèng |
| 综 | `zòng` | zōng/zèng | 綜 | zònɡ | 子宋切 | zòng→zōng |
| 蒋 | `jiāng` | jiǎng | 蔣 | jiānɡ | 子良切 | jiāng→jiǎng |
| 嵌 | `qiān` | qiàn/hǎn/kàn | 嵌 | qiān | 口銜切 | qiān→qiàn |
| 链 | `lián` | liàn | 鏈 | lián | 力延切 | lián→liàn |
| 湿 | `tà` | shī | 濕 | tà | 他合切 | tà→shī |
| 缘 | `yuàn` | yuán | 緣 | yuàn | 以絹切 | yuàn→yuán |
| 腥 | `xìng` | xīng | 腥 | xìnɡ | 穌佞切 | xìng→xīng |
| 溶 | `yǒng` | róng | 溶 | yǒnɡ | 余隴切 | yǒng→róng |
| 雌 | `cī` | cí | 雌 | cī | 此移切 | cī→cí |
| 颗 | `kě` | kē | 顆 | kě | 苦惰切 | kě→kē |
| 煽 | `shàn` | shān | 煽 | shàn | 式戰切 | shàn→shān |
| 醋 | `zuó` | cù/zuò | 醋 | zuó | 在各切 | zuó→zuò |
| 磕 | `kài` | kē/kě | 磕 | kài | 口太切 | kài→kē |
| 缭 | `liǎo` | liáo | 繚 | liǎo | 盧鳥切 | liǎo→liáo |
| 濒 | `pín` | bīn | 瀕 | pín | 符眞切 | pín→bīn |
| 镶 | `ráng` | xiāng | 鑲 | ránɡ | 汝羊切 | ráng→xiāng |
| 钋 | `yīng` | pō | 钋 | yīnɡ | 於陵切 | yīng→pō |
| 炀 | `yàng` | yáng | 煬 | yànɡ | 余亮切 | yàng→yáng |
| 忾 | `xì` | kài/qì | 愾 | xì | 許旣切 | xì→kài |
| 纰 | `bǐ` | pī | 紕 | bǐ | 卑履切 | bǐ→pī |
| 帙 | `zhí` | zhì | 帙 | zhí | 直質切 | zhí→zhì |
| 剀 | `gāi` | kǎi | 剴 | ɡāi | 五來切 | gāi→kǎi |
| 钍 | `zhì` | tǔ | 钍 | zhì | 支義切 | zhì→tǔ |
| 侉 | `kuā` | kuǎ/huá/è/wú | 侉 | kuā | 苦瓜切 | kuā→kuǎ |
| 侩 | `guì` | kuài | 儈 | ɡuì | 古外切 | guì→kuài |
| 䏝 | `zhuǎn` | zhuān | 膞 | zhuǎn | 市沇切 | zhuǎn→zhuān |
| 绉 | `bí` | zhòu | 绉 | bí | 彼及切 | bí→zhòu |
| 荠 | `cí` | jì/qí | 薺 | cí | 疾咨切 | cí→jì |
| 荨 | `tán` | xún/qián | 蕁 | tán | 徒含切 | tán→xún |
| 哕 | `yuē` | huì/yuě | 噦 | yuē | 於月切 | yuē→yuě |
| 钯 | `bā` | bǎ/pá | 鈀 | bā | 伯加切 | bā→bǎ |
| 俦 | `dào` | chóu | 儔 | dào | 直由切 | dào→chóu |
| 俪 | `lí` | lì | 儷 | lí | 呂支切 | lí→lì |
| 阂 | `ài` | hé | 閡 | ài | 五漑切 | ài→hé |
| 洙 | `shū` | zhū | 洙 | shū | 市朱切 | shū→zhū |
| 浍 | `guì` | huì/kuài | 澮 | ɡuì | 古外切 | guì→huì |
| 娆 | `niǎo` | ráo/rǎo | 嬈 | niǎo | 奴鳥切 | niǎo→ráo |
| 莼 | `tuán` | chún | 蓴 | tuán | 常倫切 | tuán→chún |
| 桡 | `nào` | ráo | 橈 | nào | 女教切 | nào→ráo |
| 蚬 | `xiàn` | xiǎn | 蜆 | xiàn | 胡典切 | xiàn→xiǎn |
| 钺 | `huì` | yuè | 鉞 | huì | 呼會切 | huì→yuè |
| 铊 | `shī` | tā/tuó | 鉈 | shī | 食遮切 | shī→tā |
| 诹 | `jū` | zōu | 諏 | jū | 子于切 | jū→zōu |
| 绥 | `suī` | suí | 綏 | suī | 息遺切 | suī→suí |
| 掸 | `dàn` | dǎn/shàn | 撣 | dàn | 徒旱切 | dàn→dǎn |
| 梿 | `liǎn` | lián | 槤 | liǎn | 里典切 | liǎn→lián |
| 铬 | `luò` | gè | 鉻 | luò | 盧各切 | luò→gè |
| 羟 | `qiān` | qiǎng | 羥 | qiān | 口莖切 | qiān→qiǎng |
| 锑 | `tí` | tī | 銻 | tí | 杜兮切 | tí→tī |
| 傧 | `bìn` | bīn | 儐 | bìn | 必刃切 | bìn→bīn |
| 颌 | `hàn` | hé/gé | 頜 | hàn | 胡感切 | hàn→hé |
| 痨 | `lào` | láo | 癆 | lào | 郎到切 | lào→láo |
| 颏 | `hái` | kē/ké | 頦 | hái | 戶來切 | hái→kē |
| 谥 | `yì` | shì | 謚 | yì | 伊昔切 | yì→shì |
| 缇 | `tǐ` | tí | 緹 | tǐ | 他禮切 | tǐ→tí |
| 趑 | `cī` | zī/cì | 趑 | cī | 取私切 | cī→cì |
| 蓥 | `yìng` | yíng | 鎣 | yìnɡ | 烏定切 | yìng→yíng |
| 酰 | `xī` | xiān | 醯 | xī | 呼雞切 | xī→xiān |
| 蜉 | `liè` | fú | 蜉 | liè | 力輟切 | liè→fú |
| 锜 | `yǐ` | qí | 錡 | yǐ | 魚綺切 | yǐ→qí |
| 敫 | `yuè` | jiǎo/qiāo/jiào | 敫 | yuè | 以灼切 | yuè→jiǎo |
| 腼 | `tiǎn` | miǎn | 靦 | tiǎn | 他典切 | tiǎn→miǎn |
| 滫 | `xiū` | xiǔ | 滫 | xiū | 息流切 | xiū→xiǔ |
| 蔷 | `sè` | qiáng | 薔 | sè | 所力切 | sè→qiáng |
| 龇 | `chái` | zī | 齜 | chái | 仕街切 | chái→zī |
| 睾 | `yì` | gāo/hào | 睪 | yì | 羊益切 | yì→gāo |
| 麽 | `mǒ` | mó/má/ma/me | 麽 | mǒ | 亡果切 | mǒ→mó |
| 樗 | `huà` | chū | 樗 | huà | 乎化切 | huà→chū |
| 踔 | `zhào` | chuō/diào/zhuō/tiào/chuò | 踔 | zhào | 知教切 | zhào→zhuō |
| 缲 | `zǎo` | qiāo/sāo | 繰 | zǎo | 親小切 | zǎo→qiāo |
| 缳 | `xuàn` | huán | 缳 | xuàn | 胡畎切 | xuàn→huán |
| 髀 | `bǐ` | bì | 髀 | bǐ | 并弭切 | bǐ→bì |
| 镣 | `liáo` | liào | 鐐 | liáo | 洛蕭切 | liáo→liào |
| 镫 | `dēng` | dèng | 鐙 | dēnɡ | 都滕切 | dēng→dèng |
| 鲽 | `tà` | dié | 鰈 | tà | 土盍切 | tà→dié |
| 鳟 | `zùn` | zūn | 鱒 | zùn | 慈損切 | zùn→zūn |
| 鹳 | `huān` | guàn | 鸛 | huān | 呼官切 | huān→guàn |
| 戋 | `cán` | jiān | 戔 | cán | 昨千切 | cán→jiān |
| 仝 | `quán` | tóng | 仝 | quán | 疾緣切 | quán→tóng |
| 朸 | `lè` | lì | 朸 | lè | 盧則切 | lè→lì |
| 轪 | `dì` | dài | 軑 | dì | 特計切 | dì→dài |
| 呙 | `kuā` | guō | 咼 | kuā | 苦媧切 | kuā→guō |
| 玟 | `méi` | wén/mín | 玟 | méi | 莫桮切 | méi→mín |
| 钐 | `yáo` | shān/shàn | 钐 | yáo | 余招切 | yáo→shān |
| 肭 | `nǜ` | nà/nù | 肭 | nǜ | 女六切 | nǜ→nà |
| 肸 | `xì` | xī/bì | 肸 | xì | 羲乙切 | xì→xī |
| 䌹 | `jiōng` | jiǒng | 絅 | jiōnɡ | 古熒切 | jiōng→jiǒng |
| 昫 | `xū` | xù/xiǒng | 昫 | xū | 火于切 | xū→xù |
| 𬬱 | `yǐn` | jīn | 釿 | yǐn | 宜引切 | yǐn→jīn |
| 朏 | `pěi` | fěi/kū | 朏 | pěi | 普乃切 | pěi→fěi |
| 恔 | `xiáo` | jiǎo/xiào | 恔 | xiáo | 下交切 | xiáo→xiào |
| 莶 | `liǎn` | xiān | 薟 | liǎn | 良冉切 | liǎn→xiān |
| 莙 | `jùn` | jūn | 莙 | jùn | 渠殞切 | jùn→jūn |
| 剟 | `zhuō` | duō/chì | 剟 | zhuō | 陟劣切 | zhuō→duō |
| 琎 | `jīn` | jìn | 璡 | jīn | 將鄰切 | jīn→jìn |
| 𬟽 | `dòng` | dōng | 蝀 | dònɡ | 多貢切 | dòng→dōng |
| 𪣻 | `lǒu` | lóu | 塿 | lǒu | 洛矦切 | lǒu→lóu |
| 溇 | `lǚ` | lóu | 漊 | lǚ | 力主切 | lǚ→lóu |
| 愃 | `xuǎn` | xuān | 愃 | xuǎn | 況晚切 | xuǎn→xuān |
| 稙 | `zhí` | zhī/zhì | 稙 | zhí | 常職切 | zhí→zhī |
| 鲏 | `pī` | pí | 鮍 | pī | 𢾭羈切 | pī→pí |
| 裛 | `yè` | yì | 裛 | yè | 於業切 | yè→yì |
| 𫘬 | `xī` | xí | 騱 | xī | 胡雞切 | xī→xí |
| 𫚖 | `jì` | cǐ | 鮆 | jì | 徂礼切 | jì→cǐ |
| 鲒 | `jí` | jié | 鮚 | jí | 巨乙切 | jí→jié |
| 瘕 | `xiá` | jiǎ/xiā | 瘕 | xiá | 乎加切 | xiá→xiā |
| 皛 | `xiào` | xiǎo/jiǎo/pò | 皛 | xiào | 烏皎切 | xiào→xiǎo |
| 觭 | `qī` | jī/qǐ/qí | 觭 | qī | 去奇切 | qī→qǐ |
| 翯 | `xué` | hè/hào | 翯 | xué | 胡角切 | xué→hè |
| 𨱔 | `zùn` | zūn | 鐏 | zùn | 徂寸切 | zùn→zūn |
| 髃 | `ǒu` | yú | 髃 | ǒu | 午口切 | ǒu→yú |
| 酂 | `zuǎn` | cuó/zàn | 酇 | zuǎn | 作管切 | zuǎn→cuó |
| 鳒 | `qiàn` | jiān | 鰜 | qiàn | 古甜切 | qiàn→jiān |
| 𬙋 | `rǎng` | xiāng | 纕 | rǎnɡ | 汝羊切 | rǎng→xiāng |
| 鳠 | `huà` | hù | 鳠 | huà | 胡化切 | huà→hù |

## 五、修复建议

1. **改 `pinyin` 为现代规范读音**（建议音见上两表），保留 `fanqie` 作为古音展示——两不耽误。
2. **A 类需连带复核**：串档的字其 `shuowen`/`original`/`duan_note`/`variant` 也可能是别人家的，建议一并核。
3. **治本**：`merge_shuowen.py` 的 `indexes` 索引应只登记「本字」（`wordhead` 及其简繁对应），
   把异体/通假关系拆到单独的关联表，避免后续再串档。
4. 修正后重跑本报告，目标：疑似错误 ≈ 0。

---

## 六、已实施修正（2026-09-15，方案 B）

采纳「**另开 `pinyin_sw` 存说文音、`pinyin` 改现代音、详情页并列展示**」：

| 字段 | 内容 | 覆盖 |
|---|---|---|
| `pinyin` | **现代规范读音**（依 pypinyin 标准读音表逐字核对；多音用 `/` 分隔） | 8105 |
| `pinyin_sw` | 原字段值，即源数据依《说文》音切**折合的古读**（《说文》音） | 8105 |

- **仅改动 177 字**（第 L2 疑似错误层），其余 7928 字原值本身已是现代规范音，**一字未动**（零回归）。
- 未做「读音排序」（pypinyin 的「主音」常取词内轻声：卜→bo、子→zi、似→shi，对字典类产品是退步，且会改变拼音排序位置）。
- 修正后 `pinyin !== pinyin_sw` 的字共 **177**（= 串档 35 + 古音折合 142）。

### 详情页展示

- `拼音: zhèn` ＋ `说文音: chén　依《说文》音切折合`
- 两读相同的字（7928 字）标 `与今读同`。
- **A 类 35 串档字**额外标 **`源字串档·待复核`**：其 `pinyin_sw` 取自被错配的关联异体/通假字（如「阵」取到「敶」的音），与该字自身反切（阵·直刃切）自相矛盾，故明确标注待复核，不冒充实为本字说文音。

### 连带待办（未擅动）

- A 类 35 字的 `shuowen` / `original` / `duan_note` / `variant` 亦可能取自错配源字（例：「肤」的反切「力居切」实为「臚」的），建议随 `merge_shuowen.py` 索引表整改一并复核（见第 234 行「治本」条）。
- `data/s2t_loose_assoc.json` 165 条宽松关联仍待人工复核。

