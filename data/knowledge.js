/* 知识卡片 · 每日一课 —— 说文解字·汉字通 增值模块
 * ① 今日一课：按日期确定性轮换（同一天稳定不变，可手动上/下翻页）
 * ② 全部知识点：按分类分组、逐条可折叠浏览
 * 单一数据源：内容与样式全部在本文件；index.html 只留一个容器 <div id="kkBlock">
 */
(function () {
  'use strict';
  var LS_KEY = 'swjz_kk_v1';

  /* 分类顺序（同时决定「全部知识点」的分组次序） */
  var CATS = [
    { id: 'liushu', name: '造字之法 · 六书', icon: '🏛️' },
    { id: 'form', name: '汉字形体的演变', icon: '🗿' },
    { id: 'sound', name: '读音与注音', icon: '🔊' },
    { id: 'struct', name: '字形与结构', icon: '🧩' },
    { id: 'book', name: '字书与文献', icon: '📜' },
    { id: 'culture', name: '汉字文化', icon: '🌏' }
  ];

  /* ---------------- 知识点 ---------------- */

  var SIX_SHU_TABLE =
    '<table class="cov-table"><tr><th>六书</th><th>字数</th><th>占比</th></tr>' +
    '<tr><td>形声</td><td>7032</td><td>86.8%</td></tr>' +
    '<tr><td>会意</td><td>636</td><td>7.8%</td></tr>' +
    '<tr><td>象形</td><td>281</td><td>3.5%</td></tr>' +
    '<tr><td>指事</td><td>26</td><td>0.3%</td></tr>' +
    '<tr><td>会意兼形声</td><td>130</td><td>1.6%</td></tr>' +
    '<tr><td><b>合计</b></td><td><b>8105</b></td><td><b>100%</b></td></tr></table>';

  var ITEMS = [
    /* ---------- 造字之法 · 六书 ---------- */
    {
      id: 'six-shu', cat: 'liushu', icon: '📖', title: '「六书」是什么？',
      html:
        '<p><b>「六书」</b>是古人分析汉字<b>造字</b>与<b>用字</b>方法而归纳出的六种条例，由东汉<b>许慎</b>在《说文解字·叙》中系统阐述，并为每一书各举二字为例：</p>' +
        '<ul>' +
        '<li><b>象形</b>——「画成其物，随体诘诎，<b>日月</b>是也」：描摹物体外形，如「日、月、山、水」</li>' +
        '<li><b>指事</b>——「视而可识，察而见意，<b>上下</b>是也」：用抽象符号、或在象形字上加指示符号表示抽象概念，如「上、下、本、末」</li>' +
        '<li><b>会意</b>——「比类合谊，以见指撝，<b>武信</b>是也」：把两个或多个字组合起来表示新意，如「明（日月并照）、休（人倚木而息）」</li>' +
        '<li><b>形声</b>——「以事为名，取譬相成，<b>江河</b>是也」：由表义类的「形旁」与表读音的「声旁」组成，如「江（水形工声）、湖（水形胡声）」</li>' +
        '<li><b>会意兼形声</b>——《说文》称「<b>某亦聲</b>」：会意的两部件中，其一声旁兼表读音，如「眇（从目从少，少亦聲）、字（从宀从子，子亦聲）」</li>' +
        '<li><b>转注</b>——「建类一首，同意相受，<b>考老</b>是也」：部首相同、意义相通、可互相解释的字</li>' +
        '<li><b>假借</b>——「本无其字，依声托事，<b>令长</b>是也」：借用同音字表达新概念，如「令（本义发号，借为县令）、长（本义久远，借为长官）」</li>' +
        '</ul>' +
        '<p><b>本产品 8105 字的六书分布</b>（取自《说文解字》字段）：</p>' + SIX_SHU_TABLE +
        '<p class="kk-note">注：本 App 将常见字归入象形、指事、会意、形声四类，另设「会意兼形声」一类（《说文》「从X从Y，Y亦聲」兼有声符的会意字，共 130 字，自成一类、单独筛选）；转注、假借属用字法，未作为单字主分类。</p>'
    },
    {
      id: 'xiangxing', cat: 'liushu', icon: '🌞', title: '象形：画成其物，随体诘诎',
      html:
        '<p>象形是<b>最古老的造字法</b>——字形直接描摹所指事物的轮廓，「画成其物，随体诘诎」即：画成那个东西，笔画随着物形屈曲。</p>' +
        '<ul>' +
        '<li><b>独体象形</b>：整体像物之形，如「日（太阳）、月（月牙）、山（三峰）、水（流水）、人（侧立之人）、木（树干枝根）」</li>' +
        '<li><b>合体象形</b>：主体之外还画出所依附之物才成形，如「果（木上结子）、眉（目上之毛）、石（山崖下一石）」</li>' +
        '</ul>' +
        '<p>象形字数量不多（本库仅 <b>281 字</b>），却是汉字的<b>基础构件</b>——后起的会意、形声字，多半由象形字拼合而成。也正因为要「像」，字形在甲骨文里最直观，越往后越抽象。</p>' +
        '<p class="kk-note">小技巧：进「字库」页搜「日」「山」「木」，点开详情看「字形演变」，甲骨文一栏最能看出「像什么」。</p>'
    },
    {
      id: 'zhishi', cat: 'liushu', icon: '⬆️', title: '指事：视而可识，察而见意',
      html:
        '<p>指事用于表达<b>看不见、摸不着</b>的抽象概念。它分两类：</p>' +
        '<ul>' +
        '<li><b>纯符号</b>：如「一、二、三」以横画数目表数目；「上、下」在基准线上加一短画指出方位</li>' +
        '<li><b>象形加指示符号</b>：在象形字上添一笔（点、横）指明所要表达的部位——' +
        '「<b>本</b>」在「木」下加一横，指树根；「<b>末</b>」在「木」上加一横，指树梢；「<b>刃</b>」在「刀」上加一点，指刀锋；「<b>亦</b>」在「大（人）」两腋处加两点，即「腋」的本字</li>' +
        '</ul>' +
        '<p>「视而可识」是说一眼能认出所指之物，「察而见意」是说细看才能明白所指之意——这正是指事的特征：<b>形态简单，含义抽象</b>。</p>' +
        '<p class="kk-note">指事只有 <b>26 字</b>，是六书里最少的一类。若把「本、末、刃」硬归会意，就会出现「木下加一横怎么合成『根』」的尴尬——一横并不表义，只起指示作用。</p>'
    },
    {
      id: 'huiyi', cat: 'liushu', icon: '🔗', title: '会意：比类合谊，以见指撝',
      html:
        '<p>会意是<b>拼合两个（或以上）已有之字</b>，用它们的意义组合出新义。「比类合谊」＝并列字类、会合字义，「以见指撝」＝由此看出所指的方向。</p>' +
        '<ul>' +
        '<li><b>明</b>：日 + 月，两光并照为明</li>' +
        '<li><b>休</b>：人 + 木，人倚树而息</li>' +
        '<li><b>武</b>：止 + 戈，「止戈为武」（《说文》引楚庄王语，取「平息干戈」之义）</li>' +
        '<li><b>信</b>：人 + 言，人之言当有信</li>' +
        '<li><b>采</b>：爪 + 木，手在树上摘取</li>' +
        '</ul>' +
        '<p>会意字本库有 <b>636 字</b>。它与会意兼形声的区别在：<b>各部件的读音是否被借用</b>——只取义的是会意，某部件兼表音的是「会意兼形声」。这两类也是最容易被混判的（如「娶」「婚」）。</p>'
    },
    {
      id: 'xingsheng', cat: 'liushu', icon: '🔊', title: '形声：为什么占汉字的 86.8%',
      html:
        '<p>形声字＝<b>形旁（表义类）＋ 声旁（表读音）</b>，如「江」＝水（形旁，说明是水名）＋ 工（声旁，提示读音）。</p>' +
        '<p>它成为汉字主体的原因是<b>能产</b>：语言中新词不断出现，用象形、指事画不出来，用会意又易混淆；而形声只需「取一个现成的字当声旁、再配一个形旁」，造新字几乎不受限制。</p>' +
        '<ul>' +
        '<li>本库 8105 字中形声字达 <b>7032 个（86.8%）</b>——现代汉字绝大多数是形声字</li>' +
        '<li>常用形旁高度集中：<b>氵（水）、木、扌（手）、口、忄（心）、讠（言）、纟（糸）、钅（金）</b></li>' +
        '</ul>' +
        '<p class="kk-note">⚠️ 「读半边」为什么常常不准？因为声旁标注的是<b>造字当时</b>的读音。几千年语音演变后，声旁与整字读音脱节，如「江」从「工」（gōng）而读 jiāng、「础」从「出」（chū）而读 chǔ——这类字称作「声旁失谐」。</p>'
    },
    {
      id: 'jiansheng', cat: 'liushu', icon: '⚖️', title: '会意兼形声：《说文》的「某亦聲」',
      html:
        '<p>《说文》常在释义末尾写「<b>从X从Y，Y亦聲</b>」（某亦声），意思是：这个字既要合 X、Y 二字的义，又取 Y 字的音——<b>一举两得</b>。本库为此单列一类，共 <b>130 字</b>。</p>' +
        '<ul>' +
        '<li><b>眇</b>：从目从少，少亦聲——少目即视力弱</li>' +
        '<li><b>字</b>：从宀从子，子亦聲——屋（宀）中生子，本义为生育、孳乳</li>' +
        '<li><b>娶</b>：从女从取，取亦聲——取女为妻</li>' +
        '<li><b>政</b>：从攴从正，正亦聲——以正教之</li>' +
        '</ul>' +
        '<p>这类字长期在「会意」与「形声」之间摆动：<b>重义则入会意，重音则归形声</b>。本产品采用《说文》字面表述，凡有「亦聲」者独立成类，避免二者互相污染；若字下《说文》只说「从A从B」而无「亦聲」，则判为会意。</p>'
    },
    {
      id: 'zhuanzhu', cat: 'liushu', icon: '🔁', title: '转注与假借：不是造字法',
      html:
        '<p>六书里前四者（象形、指事、会意、形声）是<b>造字法</b>——能造出新字；后二者是<b>用字法</b>——只是现有字的用法，故本产品不把它们作为单字的主分类。</p>' +
        '<ul>' +
        '<li><b>转注</b>：「建类一首，同意相受，考老是也。」部首相同、意义相通、可互相训释的一组字。「<b>考</b>」与「<b>老</b>」同属老部，「老，考也」「考，老也」，互为转注。</li>' +
        '<li><b>假借</b>：「本无其字，依声托事，令长是也。」本来没有这个字，就借用同音字来承载新义。「<b>令</b>」本义是发号令，借作「县令」；「<b>长</b>」本义是久远，借作「长官」。此外「来」本指麦子、借为来往的来；「难」本鸟名、借为困难——都是假借。</li>' +
        '</ul>' +
        '<p class="kk-note">转注与假借在学界解释历来纷歧（尤其转注，异说达数十种）。本产品采取最稳妥的处理：<b>只标注前五类，后二者不予归类</b>，并在「六书」筛选里如实说明。</p>'
    },

    /* ---------- 汉字形体的演变 ---------- */
    {
      id: 'seven-stages', cat: 'form', icon: '🗿', title: '汉字形体演变的七个阶段',
      html:
        '<p>本产品覆盖的七个字形阶段与各自起源：</p>' +
        '<ul>' +
        '<li><b>甲骨文（商代晚期，约前 14—前 11 世纪）</b>：刻于龟甲兽骨上的占卜记事文字，是目前已知最早、成体系的汉字，笔画瘦硬方折。</li>' +
        '<li><b>金文（商中期—秦汉）</b>：铸或刻于青铜礼器、乐器（钟鼎）上的铭文，又称钟鼎文；西周为鼎盛，笔画浑厚圆融。</li>' +
        '<li><b>大篆（先秦）</b>：秦统一前西方秦国及周室所用字体的统称，含籀文、石鼓文等，结构繁复、保留较多象形意味。</li>' +
        '<li><b>小篆（秦代，前 221 年后）</b>：秦始皇「书同文」，李斯等以秦系文字为基础整理推行的标准字体，线条圆匀、字形规整，是古文字的总结阶段。</li>' +
        '<li><b>简牍帛书（战国—汉晋）</b>：书写于竹简、木牍、丝帛上的墨迹，分楚系简帛与秦系简牍，多处于篆隶之间的隶变过渡形态，保留了大量战国文字原貌。</li>' +
        '<li><b>隶书（秦汉，约前 3 世纪起）</b>：由篆书简便化、笔画方折演变而来，标志着「隶变」——古文字向今文字转折的关键节点。</li>' +
        '<li><b>楷书（汉末成熟，魏晋定型）</b>：由隶书进一步笔画化、结构方正规范而来，沿用至今的标准字体（本产品以系统字体呈现，非古文字真迹）。</li>' +
        '</ul>' +
        '<p class="kk-note">本库某字详情页只显示它<b>真实拥有</b>的阶段；未收的阶段会按权威源分两档标注——「有此字形，待补」或「根据权威数据源，未发现有此字形」。</p>'
    },
    {
      id: 'jiaguwen', cat: 'form', icon: '🐢', title: '甲骨文：1899 年的「龙骨」',
      html:
        '<p>1899 年（清光绪二十五年），金石学家<b>王懿荣</b>在中药「龙骨」上发现刻痕，认出那是古文字——甲骨文由此重见天日。出土集中地是河南安阳小屯村，即商代晚期都城<b>殷墟</b>。</p>' +
        '<ul>' +
        '<li><b>性质</b>：主要是商王室<b>占卜</b>的记事刻辞——贞人先在龟腹甲、牛肩胛骨上钻凿，灼烧看裂纹判断吉凶，事后把卜问与应验刻在旁边</li>' +
        '<li><b>体量</b>：已发现带字甲骨约 <b>15 万片</b>，单字约 <b>4000 余个</b>（《甲骨文编》口径），目前能确释的约三分之一</li>' +
        '<li><b>字形特点</b>：笔画瘦硬方折、多直线少弧线（刀刻所致）；同一个字常有多种写法（异体众多），字形方向可左右互换</li>' +
        '</ul>' +
        '<p class="kk-note">本库在 8105 个规范汉字中已收甲骨文真迹 <b>955 字</b>（权威源口径约 1120 字，覆盖 85%+，缺失多为后起字）。很多今天的常用字，当年根本没写进甲骨里。</p>'
    },
    {
      id: 'jinwen', cat: 'form', icon: '🔔', title: '金文：青铜器上的铭文',
      html:
        '<p>金文是铸或刻在<b>青铜器</b>上的文字，因多见于钟（乐器）与鼎（礼器），又称<b>钟鼎文</b>；「金」指青铜（古人称铜为金）。</p>' +
        '<ul>' +
        '<li><b>来源</b>：商代中期已有，西周为鼎盛期。贵族在祭祀、册命、征伐、赏赐后铸器记事，「子子孙孙永宝用」是常见结语</li>' +
        '<li><b>工艺</b>：多先刻在泥范上再浇铸，笔画因此<b>浑厚圆融</b>，比甲骨文饱满得多；行款也趋于整齐</li>' +
        '<li><b>名器</b>：西周<b>毛公鼎</b>铭文约 500 字，是现存最长的青铜器铭文之一；<b>大盂鼎</b>、<b>散氏盘</b>、<b>虢季子白盘</b>同为重器</li>' +
        '<li><b>意义</b>：金文与甲骨文同属商周文字系统，但因载体耐久、铸造精整，成为研究<b>西周历史与文字</b>的第一手史料——许多字在甲骨文中未见的写法，可在金文中找到</li>' +
        '</ul>' +
        '<p class="kk-note">本库在 8105 字中已收金文真迹 <b>2049 字</b>（权威源口径约 2072 字，已近收全）。</p>'
    },
    {
      id: 'dazhuan', cat: 'form', icon: '🪨', title: '大篆与石鼓文',
      html:
        '<p><b>大篆</b>是秦统一之前、通行于周室与秦国的字体统称，与小篆相对。它包含<b>籀文</b>（《史籀篇》字系）与<b>石鼓文</b>等。</p>' +
        '<ul>' +
        '<li><b>石鼓文</b>：唐代出土于陕西的十个鼓形石碣，每鼓刻一首四言诗（记秦国君游猎），故又称「猎碣」。字体介于金文与小篆之间，被推为「<b>篆书之祖</b>」</li>' +
        '<li><b>字体特点</b>：结构繁复、笔画匀圆、象形意味保留较多，字形大小不完全一致</li>' +
        '<li><b>与小篆的关系</b>：秦「书同文」以小篆取代大篆；大篆的繁复笔画被规整、简化，但许多字形结构直接承袭</li>' +
        '</ul>' +
        '<p class="kk-note">大篆（籀文）没有统一总表，学界估算数千字。本库已收 <b>1362 字</b>；汉典「传抄古文字」频道口径为 5055 字，但后者含战国文字、范围宽于本库的籀文口径，两者不可直接对比。</p>'
    },
    {
      id: 'xiaozhuan', cat: 'form', icon: '📐', title: '小篆与「书同文」',
      html:
        '<p>公元前 221 年秦统一六国，随即推行「<b>书同文</b>」——以秦系文字为基础，由李斯等人整理出全国统一的字体，即<b>小篆</b>（秦篆）。</p>' +
        '<ul>' +
        '<li><b>字形特点</b>：线条圆匀匀长、粗细一致、左右对称；字形长方，结构定型，异体字被大幅裁并</li>' +
        '<li><b>整理成果</b>：据《说文解字·叙》，李斯作《仓颉篇》、赵高作《爰历篇》、胡毋敬作《博学篇》，作为学童识字课本与字形标准</li>' +
        '<li><b>历史地位</b>：小篆是<b>古文字的最后阶段</b>——它把此前纷歧的字形归一，汉字从此有了全国通行的规范标准，也使得跨地域交流成为可能</li>' +
        '</ul>' +
        '<p class="kk-note">《说文解字》正是以小篆为字头、按 540 部首编排的，收<b>正篆 9353 字</b>（另有重文 1163 字）。本库已收小篆真迹 <b>2848 字</b>；权威源口径（《说文》字头）9353 字，故本库小篆覆盖仍有明显缺口，多数缺失阶段标注为「有此字形，待补」。</p>'
    },
    {
      id: 'jiandu', cat: 'form', icon: '📜', title: '简牍帛书：战国秦汉的墨迹',
      html:
        '<p>在纸普及之前，古人主要用<b>竹简、木牍</b>书写，贵重者用<b>丝帛</b>。这些出土墨迹是汉字形体演变最直接的实物证据。</p>' +
        '<ul>' +
        '<li><b>楚系简帛（战国）</b>：如郭店楚简、包山楚简、长沙子弹库楚帛书——字形仍在篆书体系内，但因手写而笔画圆转简省</li>' +
        '<li><b>秦系简牍（战国末—秦）</b>：如睡虎地秦简、里耶秦简——已明显向隶书过渡，笔画平直、结构简化</li>' +
        '<li><b>汉简与帛书</b>：如马王堆帛书、银雀山汉简、居延汉简——隶书成熟与向楷书过渡的关键样本</li>' +
        '</ul>' +
        '<p><b>为什么重要</b>：青铜、石刻上的字是「正式字体」；简牍帛书是当时的<b>日常手写体</b>。真正的形体演变（篆→隶的「隶变」）恰恰发生在这些「不登大雅」的实用书写里——正是它们把汉字从古文字带进了今文字。</p>' +
        '<p class="kk-note">简牍帛书出土分散、无统一总表，本库已收 <b>612 字</b>，是本库覆盖最薄弱的阶段之一，缺失多标「有此字形，待补」。</p>'
    },
    {
      id: 'libian', cat: 'form', icon: '✒️', title: '隶变：古今文字的分水岭',
      html:
        '<p><b>隶变</b>指汉字由篆书演变为隶书的过程（秦汉之际）。它是汉字史上<b>最深刻的一次变革</b>，被视为「古文字」与「今文字」的分界线。</p>' +
        '<ul>' +
        '<li><b>写法上</b>：把篆书的圆转弧线改为<b>平直方折</b>的笔画，「蚕头燕尾」成为隶书的标志性笔形；一笔之内有了粗细顿挫</li>' +
        '<li><b>结构上</b>：篆书的对称与象形意味被彻底打破，字形由「长方」趋于「扁平」，笔画可以拆解、可以重新组合</li>' +
        '<li><b>后果</b>：汉字从「<b>象形</b>」彻底转向「<b>符号</b>」。此后楷书、行书、草书都只是在隶书确立的笔画体系内作调整，再没有根本性的形体变革</li>' +
        '</ul>' +
        '<p class="kk-note">隶书另有「<b>八分</b>」之名（取「字有八分相背之势」或「二分篆、八分隶」之说）。本产品隶书阶段以临海隶书＋青柳隶书字体替代呈现，<b>未收汉隶真迹</b>。</p >'
    },
    {
      id: 'kaishu', cat: 'form', icon: '🖌️', title: '楷书：何以为「楷」',
      html:
        '<p>「<b>楷</b>」本是树名（楷木），引申为「<b>楷模、法式</b>」——楷书即「可作范式的书体」。它由隶书进一步笔画化、去除波磔而成。</p>' +
        '<ul>' +
        '<li><b>形成</b>：汉末萌生，经魏晋定型，唐代达到法度严整的高峰</li>' +
        '<li><b>特点</b>：笔画平直、结构方正、一笔一画各自独立（不像行书、草书那样连笔），故最适合刻版印刷与识字教学，沿用一千八百余年至今</li>' +
        '<li><b>唐楷典范</b>：欧阳询（欧体）、颜真卿（颜体）、柳公权（柳体）——结体、笔法各有法度，成为后世临习标准</li>' +
        '</ul>' +
        '<p class="kk-note">本产品「楷书」一栏以系统字体呈现，属<b>现代楷体字形</b>，非古文字真迹，故不与甲骨、金文等阶段同列统计。</p>'
    },

    /* ---------- 读音与注音 ---------- */
    {
      id: 'fanqie', cat: 'sound', icon: '🔤', title: '什么是「反切」？',
      html:
        '<p>「反切」是汉魏以来传统的注音方法：<b>用两个汉字拼注第三个字的读音</b>——<b>上字取声母，下字取韵母与声调</b>。本 App 详情页的「反切」一栏展示该字在《说文》等字书中的音切，「说文音」即据此音切折合出的古读。</p>' +
        '<ul>' +
        '<li><b>怎么拼</b>：如「<b>一</b>」《说文》作「<b>於悉切</b>」——上字「於」取声母 <b>y</b>，下字「悉」取韵母 <b>i</b>，拼得 <b>yī</b>，与今读相同。</li>' +
        '<li><b>为什么不直接等于今读</b>：反切记录的是<b>唐宋以前的语音系统</b>，须经语音演变折合才是今音。如「<b>江</b>」《说文》作「<b>古雙切</b>」——上取声母 g、下取韵母 uang，直拼为 *guāng（* 表示按音切拼出、实际不存在的音节），而今读 <b>jiāng</b>：中古「见母」逢细音后颚化为 j，即「见母颚化」。</li>' +
        '<li><b>古读与今读可以不同</b>：如「<b>缇</b>」《说文》作「<b>他禮切</b>」，折合为 <b>tǐ</b>（古读）；《广韵》作「杜奚切」，折合为 <b>tí</b>，与今读一致。这正是本 App 把读音分作两栏的原因——<b>拼音</b>＝现代规范音，<b>说文音</b>＝据《说文》音切折合的古读（两读相同者标注「与今读同」）。</li>' +
        '</ul>' +
        '<p class="kk-note">说明：「说文音」为按音切规则折合的结果，供溯源参考，不作为现代读音规范；8105 字中有反切者 5378 字，其余多为后起字（字书未收，故无反切）。</p>'
    },
    {
      id: 'zhuyin', cat: 'sound', icon: 'ㄅ', title: '注音符号：拼音的前身',
      html:
        '<p>在汉语拼音之前，中国人用的是<b>注音符号</b>（ㄅㄆㄇㄈ……）。</p>' +
        '<ul>' +
        '<li><b>制定</b>：1913 年「读音统一会」议定，1918 年由北洋政府教育部公布，共 <b>37 个字母</b>（声母 21、韵母 16），另有声调符号</li>' +
        '<li><b>来源</b>：取法章太炎所拟「记音字母」，形体制式借鉴日文假名，多由古字简省而来——如 ㄅ 取自「包」之古字、ㄆ 取自「攵」、ㄇ 取自「冖」、ㄈ 取自「匚」</li>' +
        '<li><b>今天</b>：大陆 1958 年后改用汉语拼音；<b>中国台湾地区</b>至今仍以注音符号作为主要注音工具，小学识字教学亦沿用</li>' +
        '</ul>' +
        '<p class="kk-note">本产品详情页的「拼音」栏右侧会并列显示<b>注音符号</b>（如 yī → ㄧ、ti → ㄊㄧ），方便对照两种注音体系。</p>'
    },
    {
      id: 'pinyin-scheme', cat: 'sound', icon: '🅰️', title: '汉语拼音方案：1958 年',
      html:
        '<p>我们读书、打字用的「拼音」，正式名称是《<b>汉语拼音方案</b>》，用拉丁字母给汉字注音。</p>' +
        '<ul>' +
        '<li><b>研制</b>：1955 年起由中国文字改革委员会主持，周有光等学者参与，广泛征求意见后定稿</li>' +
        '<li><b>颁布</b>：<b>1958 年 2 月 11 日</b>，第一届全国人民代表大会第五次会议批准公布，随即进入小学教学与字典注音</li>' +
        '<li><b>国际标准</b>：1982 年被国际标准化组织采纳为 ISO 7098，成为用拉丁字母拼写汉语的国际标准</li>' +
        '<li><b>构成</b>：23 个声母、24 个韵母、声调符号（阴平 ˉ、阳平 ˊ、上声 ˇ、去声 ˋ，轻声不标）</li>' +
        '</ul>' +
        '<p class="kk-note">拼音与注音符号是<b>两套并行的注音工具</b>，不是「对与错」的关系；本产品的拼音字段采用现代规范读音，用于检索、排序与朗读。</p>'
    },
    {
      id: 'sisheng', cat: 'sound', icon: '🎵', title: '四声与「入声消失」',
      html:
        '<p>普通话有四个声调：<b>阴平（ˉ）、阳平（ˊ）、上声（ˇ）、去声（ˋ）</b>。而中古汉语的声调是<b>四个</b>——平、上、去、<b>入</b>。两者不是一一对应，中间发生了著名的「<b>入声消失</b>」。</p>' +
        '<ul>' +
        '<li><b>平分阴阳</b>：中古「平声」按声母清浊分化，浊音归阳平、清音归阴平——今天普通话的阴平、阳平由此而来</li>' +
        '<li><b>浊上变去</b>：中古的浊声母上声字，今天多读去声</li>' +
        '<li><b>入声消失</b>：中古的<b>入声字</b>（以 -p、-t、-k 收尾的促声字）在官话里<b>声调与韵尾同时脱落</b>，被分别派入阴平、阳平、上声、去声，分布没有统一规律</li>' +
        '</ul>' +
        '<p>因此，读古诗时押韵有时「不押」，往往就是入声造成的——如「独、国、白、石、竹」在古代都是入声字。</p>' +
        '<p class="kk-note">入声在<b>粤语、闽南语、客家话</b>等南方方言中完整保留，这也是用方言读唐诗更「顺口」的原因之一。</p>'
    },
    {
      id: 'duoyinzi', cat: 'sound', icon: '🔀', title: '多音字与「破读」',
      html:
        '<p>一个字有两读或多读，叫<b>多音字</b>。成因主要有两类：</p>' +
        '<ul>' +
        '<li><b>破读（歧音别义）</b>：改变读音以区别<b>词义或词性</b>。如「<b>好</b>」hǎo（形容词，好坏）／hào（动词，爱好）；「<b>长</b>」cháng（长短）／zhǎng（生长）；「<b>王</b>」wáng（名词，君王）／wàng（动词，称王）；「<b>衣</b>」yī（名词）／yì（动词，穿衣）。古注中的「读破」「如字」说的就是这种情况</li>' +
        '<li><b>文白异读</b>：读书音与口语音并存。如「<b>薄</b>」bó（薄弱）／báo（薄纸）；「<b>血</b>」xuè（血压）／xiě（口语）</li>' +
        '</ul>' +
        '<p>本产品把读音以「/」分隔全部列出（如「<b>弹</b>」dàn/tán），检索时任一读音命中即可召回；排序以该字在本次检索中<b>命中的那个读音</b>为准。</p>' +
        '<p class="kk-note">小技巧：在「字库」页搜一个字母（如 <b>t</b>），卡片上高亮的音节就是它凭什么出现在结果里——如「弹」显示为 dàn/<b>tán</b>，说明它是以 tán 这一读命中。</p>'
    },

    /* ---------- 字形与结构 ---------- */
    {
      id: 'bushou', cat: 'struct', icon: '🗂️', title: '部首：检字的钥匙',
      html:
        '<p><b>部首</b>是字典编排与检字的纲目——把同形旁的字归为一部，取该形旁为部首。</p>' +
        '<ul>' +
        '<li><b>《说文》540 部</b>：许慎按<b>字形结构</b>立部，540 部始于「一」、终于「亥」。它是文字学意义的部首，要能统摄该部之字的构形</li>' +
        '<li><b>明代《字汇》214 部</b>：为便于检字，将部首大幅合并调整，此后《康熙字典》沿用 214 部，成为数百年通行的检字体系</li>' +
        '<li><b>现代部首表 201 部</b>：《现代汉语词典》等现代辞书采用，纯为检索便利，与构形关系更松</li>' +
        '</ul>' +
        '<p class="kk-note">正因如此，同一个字在不同体系下的部首可能不同——如「<b>颖</b>」在《说文》从「禾」，现代部首表则归「页」（取楷书字形下方）。本产品详情页给出每字的<b>部首与部首名</b>，供检字与理解构形参考。</p>'
    },
    {
      id: 'pianpang', cat: 'struct', icon: '🧩', title: '偏旁与部件：形旁、声旁各司其职',
      html:
        '<p>「偏旁」原指合体字的左右两部分，后来泛指构成汉字的各个<b>部件</b>。在形声字里，偏旁分两种角色：</p>' +
        '<ul>' +
        '<li><b>形旁（义符）</b>——提示意义类别。如「氵」标示与水有关（江、河、湖、海），「木」标示与树木有关（松、柏、枝、根）</li>' +
        '<li><b>声旁（音符）</b>——提示读音。如「工」在「江、缸、杠」中、「胡」在「湖、糊、蝴」中</li>' +
        '</ul>' +
        '<p><b>为什么「认字认半边」既有用又不靠谱？</b> 形旁的高频集中度很高（氵、木、扌、口、忄、讠、纟、钅这几类就覆盖了大量常用字），因此从形旁往往能猜到字义大类；但声旁记的是造字时的读音，语音演变后多数已失谐（见「形声」一卡）。</p>' +
        '<p class="kk-note">📍 位置不固定也是难点：形旁可在左（江）、可右（鸠）、可上（花）、可下（想）、可外（园）、可内（闷）——同一声旁配不同形旁，就造出一串不同的字。</p>'
    },
    {
      id: 'bishun', cat: 'struct', icon: '✏️', title: '笔画与笔顺',
      html:
        '<p>汉字由<b>笔画</b>构成。现代汉字的五种基本笔形是：<b>横、竖、撇、点、折</b>（其余笔形都由它们组合、变形而来）。</p>' +
        '<p><b>笔顺</b>是书写笔画的先后次序，规则大体是：</p>' +
        '<ul>' +
        '<li>从上到下（三：一、二、三）、从左到右（林：木、木）</li>' +
        '<li>先横后竖（十）、先撇后点／捺（八、文）</li>' +
        '<li>先外后内（月、同）、<b>先外后内再封口</b>（国、回）</li>' +
        '<li>先中间后两边（小、水）、右上有包围先写上（有、布）</li>' +
        '</ul>' +
        '<p class="kk-note">本产品详情页提供<b>笔顺动画</b>（逐笔逐画演示）与<b>笔画数</b>查询，可用来核对自己的书写习惯——笔顺错了，行书连笔时就会别扭。</p>'
    },
    {
      id: 'yiti', cat: 'struct', icon: '👥', title: '异体字与通假字',
      html:
        '<p>这两个概念常被混为一谈，其实完全不同：</p>' +
        '<ul>' +
        '<li><b>异体字</b>——<b>音义完全相同、只是写法不同</b>的一组字。如「峰／峯」「群／羣」「迹／蹟」「泪／淚」。1955 年《第一批异体字整理表》从中选定规范字，其余作为异体字停止使用（古籍中仍会见到）</li>' +
        '<li><b>通假字</b>——古人<b>借用音同或音近的字</b>来代替本字，属「写别字」但约定俗成。如「<b>蚤</b>」通「早」、「<b>畔</b>」通「叛」、「<b>亡</b>」通「无」。读古书遇到讲不通的字，往往就是通假</li>' +
        '</ul>' +
        '<p class="kk-note">另有「<b>古今字</b>」：同一个词在早期用甲字、后来另造乙字（如「莫→暮」「説→悦」）。若古籍里某字的本义与今义不合、字形又相近或音近，多半属以上三种关系之一。</p>'
    },

    /* ---------- 字书与文献 ---------- */
    {
      id: 'shuowen', cat: 'book', icon: '📕', title: '《说文解字》：第一部系统的字书',
      html:
        '<p>《<b>说文解字</b>》由东汉<b>许慎</b>（约 58—147）撰写，是<b>中国第一部系统分析字形、考求字源、辨识读音</b>的字典。</p>' +
        '<ul>' +
        '<li><b>成书</b>：始撰于和帝永元十二年（公元 100 年），至安帝建光元年（121 年）成书进呈，历时二十余年</li>' +
        '<li><b>体例</b>：14 篇正文 ＋ 叙目 1 篇，共 15 篇；收<b>正篆 9353 字</b>，另有重文（异体）1163 字；首创按 <b>540 部首</b>编排的检字体系，是后世字典的范式</li>' +
        '<li><b>意义</b>：它保存了汉代的小篆字形与古义，是解读甲骨、金文的重要桥梁；也是「六书」理论的系统总结</li>' +
        '<li><b>注本</b>：清代<b>段玉裁</b>《说文解字注》最负盛名，另有桂馥、王筠、朱骏声三家名著，合称「说文四大家」</li>' +
        '</ul>' +
        '<p class="kk-note">本产品的「<b>说文原文</b>」「<b>段注</b>」「<b>反切</b>」字段即取自《说文解字》及段玉裁注（公版）。许慎释字有时受当时见闻所限，与今日所见甲骨、金文不合之处，学界已有订正。</p>'
    },
    {
      id: 'later-books', cat: 'book', icon: '📚', title: '《玉篇》《广韵》《康熙字典》',
      html:
        '<p>《说文》之后，历代字书、韵书接力。本产品对「<b>后起字</b>」（《说文》未收之字）的释义溯源，正取自下列三部：</p>' +
        '<ul>' +
        '<li><b>《玉篇》</b>（南朝梁·顾野王，公元 543 年）：继《说文》之后的字书，改以小楷为字头、按部首排列，收字远多于《说文》，注重<b>字义训释</b></li>' +
        '<li><b>《广韵》</b>（北宋·陈彭年等，1008 年）：现存最完整的古代<b>韵书</b>，按四声分类、每韵下按声母排列，字下附<b>反切</b>与释义。研究中古音、《说文》读音，都绕不开它</li>' +
        '<li><b>《康熙字典》</b>（清·张玉书等，1716 年）：集历代字书之大成，收字约 4.7 万，沿用 214 部首；字下罗列历代韵书的反切、释义与书证，是<b>说明字义源流</b>的最重要工具书</li>' +
        '</ul>' +
        '<p class="kk-note">⚠️ <b>音译字提示</b>：部分字古今义差别很大——如「啡」古为「唾声」非「咖啡」、「吨」古为「气相冲」非重量单位、「她」古为「姐」非第三人称。本产品对此类已在溯源中单独标注，避免望文生义。</p>'
    },
    {
      id: 'howmany', cat: 'book', icon: '🔢', title: '汉字一共有多少个？',
      html:
        '<p>答案取决于「怎么数」——历代字书的收字量一路递增，但常用字始终是有限的：</p>' +
        '<ul>' +
        '<li><b>《说文解字》</b>（121 年）：正篆 <b>9353</b> 字（另有重文 1163）</li>' +
        '<li><b>《康熙字典》</b>（1716 年）：约 <b>47035</b> 字，历代字书收字之最</li>' +
        '<li><b>《中华字海》</b>（1994 年）：约 <b>85568</b> 字，收录大量异体、俗字与出土文献用字</li>' +
        '<li><b>《通用规范汉字表》</b>（2013 年，国务院公布）：<b>8105</b> 字，分三级——一级 3500（常用）、二级 3000（次常用）、三级 1605（专业用字）</li>' +
        '</ul>' +
        '<p><b>关键事实</b>：日常阅读写作所用的核心字，其实只有三四千个；但字书里动辄四五万——多出来的绝大部分是异体字、生僻古字与专业用字。</p>' +
        '<p class="kk-note">本产品收录范围即《通用规范汉字表》<b>全部 8105 字</b>——由收字规模决定，凡超出此表的古字、异体字不在库内。</p>'
    },
    {
      id: 'jiantihua', cat: 'book', icon: '✂️', title: '简化字是怎么来的',
      html:
        '<p>今天通行的简化字并非凭空新造，来源主要有几路：</p>' +
        '<ul>' +
        '<li><b>草书楷化</b>：把草书连笔定型为楷书笔画——<b>书、专、为、东、车</b></li>' +
        '<li><b>采录古字／异体</b>：本是古已有之的字或异体字——<b>云（雲）、电（電）、礼（禮）、众（眾）</b></li>' +
        '<li><b>更换声旁</b>：用更易读的声旁替换——<b>态（態）、苹（蘋）、钟（鐘）、忆（憶）</b></li>' +
        '<li><b>符号替代</b>：用一个简单符号代替繁难部件——<b>又</b>（鸡、难、欢）、<b>×</b>（赵、风）、<b>乂</b>（区、冈）</li>' +
        '<li><b>同音替代</b>：借同音字承担多义——<b>后（後）、几（幾）、谷（穀）、里（裏）</b></li>' +
        '<li><b>局部删除</b>：省去部分部件——<b>习（習）、飞（飛）、条（條）、号（號）</b></li>' +
        '</ul>' +
        '<p class="kk-note">《汉字简化方案》1956 年由国务院公布，《简化字总表》1964 年编印、1986 年重新发表，共收简化字 <b>2235</b> 个。本产品字段中的「<b>trad</b>」即对应字的繁体写法，可供简繁对照。</p>'
    },

    /* ---------- 汉字文化 ---------- */
    {
      id: 'ta-word', cat: 'culture', icon: '👩', title: '「她」字的来历',
      html:
        '<p>「<b>她</b>」是不是新造字？答案是：<b>字是老字，用法是新用法</b>。</p>' +
        '<ul>' +
        '<li><b>古已有之</b>：南朝字书《玉篇》收「她」字，训为「<b>姐</b>」（读 jiě），与今天的第三人称代词无关。所以本产品对「她」的古义溯源标注为「姐」</li>' +
        '<li><b>另赋新义</b>：五四时期，白话文需要区分第三人称的性别。1920 年刘半农作文讨论「她」字问题，主张用「她」作女性第三人称，与「他」「它」分工</li>' +
        '<li><b>普及</b>：随新文学与新式教育推广，「她」迅速取代旧有的「伊」等写法，成为现代汉语的规范用法</li>' +
        '</ul>' +
        '<p class="kk-note">这也是本产品要区分「<b>本义／古义</b>」与「<b>今义</b>」的原因——一个字的古代释义与现代常用义，可能毫无关系；只查今义，会误读古籍。</p>'
    },
    {
      id: 'hanzi-circle', cat: 'culture', icon: '🌏', title: '汉字文化圈',
      html:
        '<p>汉字曾长期是东亚的<b>通用书写系统</b>，各国在借用中又发展出各自的路径：</p>' +
        '<ul>' +
        '<li><b>日本</b>：借用汉字（称「漢字」）并据草书、楷书偏旁造出「假名」（平假名、片假名）。1946 年公布《当用汉字表》，1981 年改《常用汉字表》，2010 年增补至 <b>2136 字</b>，并公布了少量「常用汉字表」外的「人名用汉字」</li>' +
        '<li><b>朝鲜半岛</b>：1446 年世宗颁布《训民正音》创制谚文（韩文），与汉字长期并用；韩国现行汉字教育以 <b>1800 个基础汉字</b>为教学基准</li>' +
        '<li><b>越南</b>：长期使用汉字，并仿汉字造字法创制「字喃」（喃字）记录越语；17 世纪起欧洲传教士用拉丁字母拼写越语，1945 年后拉丁化「国语字」成为正式文字</li>' +
        '<li><b>共同遗产</b>：日、韩、越语中至今保留大量<b>汉字词</b>读音层（如「学校」），是历史上汉语借词的活化石</li>' +
        '</ul>' +
        '<p class="kk-note">汉字也是<b>世界上仍在使用的最古老的文字体系</b>之一——甲骨文以来的字形脉络，三千余年未曾中断。</p>'
    }
  ];

  /* ---------------- 样式 ---------------- */

  var CSS = [
    '.kk-today{background:linear-gradient(160deg,rgba(83,74,183,.20),var(--card));border:1px solid var(--accent);border-radius:14px;padding:18px 20px 16px;margin:4px 0 16px}',
    '.kk-head{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:12px}',
    '.kk-badge{font-size:11.5px;font-weight:700;letter-spacing:.6px;padding:3px 10px;border-radius:20px;background:var(--accent);color:#fff}',
    '.kk-cat{font-size:11.5px;color:#c9bfff;border:1px solid var(--accent);border-radius:20px;padding:2px 9px}',
    '.kk-idx{font-size:12px;color:var(--text3);margin-left:auto;white-space:nowrap}',
    '.kk-ttl{font-size:17.5px;font-weight:700;color:#c9bfff;margin:0 0 10px;line-height:1.45}',
    '.kk-body{font-size:13.5px;line-height:1.85;color:var(--text2)}',
    '.kk-body p{margin:0 0 10px}',
    '.kk-body p:last-child{margin-bottom:0}',
    '.kk-body ul{margin:0 0 10px;padding-left:20px}',
    '.kk-body li{margin:3px 0}',
    '.kk-body b{color:var(--text)}',
    '.kk-body table.cov-table{margin:8px 0 12px}',
    '.kk-note{font-size:12.5px;color:var(--text3);line-height:1.75;margin:8px 0 0;padding:8px 11px;border-left:2px solid var(--border);background:rgba(255,255,255,.02);border-radius:0 8px 8px 0}',
    '.kk-foot{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:16px;padding-top:13px;border-top:1px solid var(--border)}',
    '.kk-btn{background:var(--card);border:1px solid var(--border);color:var(--text2);border-radius:9px;padding:7px 15px;font-size:13.5px;cursor:pointer;font-family:inherit;transition:.15s}',
    '.kk-btn:hover{border-color:var(--accent);color:var(--text)}',
    '.kk-btn.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}',
    '.kk-btn.primary:hover{opacity:.9;color:#fff}',
    '.kk-all{margin-top:6px;border:1px solid var(--border);border-radius:12px;background:var(--card);overflow:hidden}',
    '.kk-all>summary{cursor:pointer;list-style:none;padding:13px 17px;font-size:14.5px;font-weight:600;color:var(--text);user-select:none}',
    '.kk-all>summary::-webkit-details-marker{display:none}',
    '.kk-all>summary::after{content:"点击展开 ▾";float:right;font-size:12px;font-weight:400;color:var(--text3)}',
    '.kk-all[open]>summary::after{content:"点击收起 ▴"}',
    '.kk-all[open]>summary{border-bottom:1px solid var(--border)}',
    '.kk-all-in{padding:12px 15px 16px}',
    '.kk-group{margin:0 0 12px;border:1px solid var(--border);border-radius:11px;background:rgba(255,255,255,.02);overflow:hidden}',
    '.kk-group:last-child{margin-bottom:0}',
    '.kk-group>summary{cursor:pointer;list-style:none;padding:10px 14px;font-size:14px;font-weight:600;color:var(--text);user-select:none}',
    '.kk-group>summary::-webkit-details-marker{display:none}',
    '.kk-group>summary::after{content:"▾";float:right;color:var(--text3);font-size:12px}',
    '.kk-group[open]>summary::after{content:"▴"}',
    '.kk-group>summary .kk-cnt{font-size:11.5px;font-weight:400;color:var(--text3);margin-left:6px}',
    '.kk-group-in{padding:2px 12px 12px}',
    '.kk-item{border:1px solid var(--border);border-radius:9px;margin:6px 0;background:var(--card);overflow:hidden}',
    '.kk-item[open]{border-color:var(--accent)}',
    '.kk-item>summary{cursor:pointer;list-style:none;padding:9px 13px;font-size:13.5px;color:var(--text2);user-select:none;display:flex;gap:8px;align-items:baseline}',
    '.kk-item>summary::-webkit-details-marker{display:none}',
    '.kk-item>summary:hover{color:var(--text)}',
    '.kk-item>summary .ic{flex:0 0 auto}',
    '.kk-item>summary .tt{flex:1 1 auto}',
    '.kk-item>summary .ar{flex:0 0 auto;color:var(--text3);font-size:11px}',
    '.kk-item[open]>summary{color:var(--text);font-weight:600;background:rgba(83,74,183,.12)}',
    '.kk-item[open]>summary .ar{color:var(--accent)}',
    '.kk-item-in{padding:12px 14px 4px;border-top:1px solid var(--border)}',
    '.kk-item-in .kk-body{font-size:13px}',
    '.kk-empty{font-size:13px;color:var(--text3);padding:10px 2px}'
  ].join('');

  /* ---------------- 工具 ---------------- */

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function hashStr(s) {
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return h >>> 0;
  }

  function todayKey() {
    var d = new Date();
    var m = d.getMonth() + 1, day = d.getDate();
    return d.getFullYear() + '-' + (m < 10 ? '0' + m : m) + '-' + (day < 10 ? '0' + day : day);
  }

  function catOf(id) {
    for (var i = 0; i < CATS.length; i++) if (CATS[i].id === id) return CATS[i];
    return { id: id, name: id, icon: '•' };
  }

  /* 今天默认展示哪一条：按「日期序数取模」顺次轮换
   * —— 同一天恒定不变；连续 N 天（N＝知识点总数）恰好轮完一遍，不漏不重
   * （不用日期哈希：哈希会伪随机，出现连续两天同一条的概率） */
  function dayOrdinal(d) {
    d = d || new Date();
    return Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000);
  }

  function defaultIndex(d) {
    var n = ITEMS.length;
    return ((dayOrdinal(d) % n) + n) % n;
  }

  function readOff() {
    try {
      var o = JSON.parse(localStorage.getItem(LS_KEY) || 'null');
      if (o && o.d === todayKey() && typeof o.k === 'number') return o.k | 0;
    } catch (e) { }
    return 0;
  }

  function writeOff(k) {
    try { localStorage.setItem(LS_KEY, JSON.stringify({ d: todayKey(), k: k })); } catch (e) { }
  }

  /* ---------------- 渲染 ---------------- */

  var base = 0, off = 0, elBox = null;

  function curIdx() {
    var n = ITEMS.length;
    return ((base + off) % n + n) % n;
  }

  function renderToday() {
    var i = curIdx(), it = ITEMS[i], cat = catOf(it.cat);
    var isToday = (off === 0);
    var host = elBox.querySelector('#kkToday');
    if (!host) return;
    host.innerHTML =
      '<div class="kk-head">' +
      '<span class="kk-badge">📅 今日一课</span>' +
      '<span class="kk-cat">' + esc(cat.icon + ' ' + cat.name) + '</span>' +
      (isToday ? '<span class="kk-cat" style="border-color:#2e9e63;color:#9fe6c8">今日推荐</span>' : '') +
      '<span class="kk-idx">第 ' + (i + 1) + ' / ' + ITEMS.length + ' 条</span>' +
      '</div>' +
      '<h3 class="kk-ttl">' + esc(it.icon + ' ' + it.title) + '</h3>' +
      '<div class="kk-body">' + it.html + '</div>' +
      '<div class="kk-foot">' +
      '<button class="kk-btn" id="kkPrev" type="button">← 上一条</button>' +
      '<button class="kk-btn" id="kkNext" type="button">下一条 →</button>' +
      (isToday ? '' : '<button class="kk-btn primary" id="kkHome" type="button">回到今日推荐</button>') +
      '<span class="kk-idx" style="margin-left:auto">每天自动轮换一条 · 全部 ' + ITEMS.length + ' 条见下方</span>' +
      '</div>';

    var b;
    if ((b = host.querySelector('#kkPrev'))) b.addEventListener('click', function () { off--; writeOff(off); renderToday(); });
    if ((b = host.querySelector('#kkNext'))) b.addEventListener('click', function () { off++; writeOff(off); renderToday(); });
    if ((b = host.querySelector('#kkHome'))) b.addEventListener('click', function () { off = 0; writeOff(0); renderToday(); });
  }

  function renderAll() {
    var host = elBox.querySelector('#kkAllBody');
    if (!host) return;
    var out = [];
    CATS.forEach(function (cat) {
      var list = ITEMS.filter(function (x) { return x.cat === cat.id; });
      if (!list.length) return;
      out.push('<details class="kk-group" open><summary>' + esc(cat.icon + ' ' + cat.name) +
        '<span class="kk-cnt">共 ' + list.length + ' 条</span></summary><div class="kk-group-in">');
      list.forEach(function (it) {
        out.push('<details class="kk-item"><summary>' +
          '<span class="ic">' + esc(it.icon) + '</span>' +
          '<span class="tt">' + esc(it.title) + '</span>' +
          '<span class="ar">展开</span></summary>' +
          '<div class="kk-item-in"><div class="kk-body">' + it.html + '</div></div></details>');
      });
      out.push('</div></details>');
    });
    host.innerHTML = out.length ? out.join('') : '<p class="kk-empty">暂无可显示的知识点。</p>';

    /* 折叠状态同步「展开 / 收起」提示文字 */
    Array.prototype.forEach.call(host.querySelectorAll('.kk-item'), function (d) {
      var ar = d.querySelector('.ar');
      if (!ar) return;
      d.addEventListener('toggle', function () { ar.textContent = d.open ? '收起' : '展开'; });
    });
  }

  function buildShell() {
    return '<h2>📚 知识卡片 · 每日一课</h2>' +
      '<p class="sub" style="margin:0 0 14px">每天一条汉字知识，自动轮换；也可以随时翻页，或在下方展开全部知识点按需查阅。</p>' +
      '<div class="kk-today" id="kkToday"></div>' +
      '<details class="kk-all" id="kkAllBox"><summary>📖 全部知识点 · 共 ' + ITEMS.length + ' 条</summary>' +
      '<div class="kk-all-in" id="kkAllBody"></div></details>';
  }

  function mount() {
    /* 已挂载则只重渲染，避免重复替换容器（脚本被加载两次 / 手工再调用时） */
    var done = document.getElementById('kkBlock');
    if (done) {
      elBox = done;
      base = defaultIndex();
      off = readOff();
      renderToday();
      renderAll();
      return;
    }
    var sec = document.getElementById('page-intro');
    if (!sec) return;
    var blocks = sec.querySelectorAll('.intro-block'), target = null;
    for (var i = 0; i < blocks.length; i++) {
      var h = blocks[i].querySelector('h2');
      if (h && h.textContent.indexOf('知识卡片') >= 0) { target = blocks[i]; break; }
    }
    if (!target) return;

    if (!document.getElementById('kk-style')) {
      var s = document.createElement('style');
      s.id = 'kk-style'; s.textContent = CSS;
      document.head.appendChild(s);
    }

    var box = document.createElement('div');
    box.className = 'intro-block';
    box.id = 'kkBlock';
    box.innerHTML = buildShell();
    target.parentNode.replaceChild(box, target);

    elBox = box;
    base = defaultIndex();
    off = readOff();
    renderToday();
    renderAll();
  }

  /* 供测试与外部调用 */
  window.__kk = {
    items: ITEMS, cats: CATS, defaultIndex: defaultIndex,
    todayKey: todayKey, hashStr: hashStr, mount: mount,
    renderToday: renderToday, renderAll: renderAll,
    state: function () {
      return {
        base: base, off: off, cur: curIdx(),
        hasBox: !!elBox,
        hasTodayHost: !!(elBox && elBox.querySelector('#kkToday')),
        hasAllHost: !!(elBox && elBox.querySelector('#kkAllBody'))
      };
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
