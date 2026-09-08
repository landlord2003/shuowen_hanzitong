// 说文解字 App · 拼音 -> 注音(bopomofo) 转换工具（纯算法，零外部依赖）
// 输入带声调符号的拼音（如 "yī"/"shí"/"lǘ"），输出注音符号（如 "ㄧ"/"ㄕˊ"/"ㄌㄩˊ"）。
// 一声不标调，二/三/四声分别标 ˊ ˇ ˋ；轻声不标。
(function (global) {
  'use strict';

  // 带声调符号的元音 -> [基础元音, 声调]
  var VOWEL_TONE = {
    'a': ['ā', 'á', 'ǎ', 'à'], 'e': ['ē', 'é', 'ě', 'è'], 'i': ['ī', 'í', 'ǐ', 'ì'],
    'o': ['ō', 'ó', 'ǒ', 'ò'], 'u': ['ū', 'ú', 'ǔ', 'ù'], 'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ']
  };
  var TONE_MAP = {};
  for (var b in VOWEL_TONE) {
    var arr = VOWEL_TONE[b];
    for (var t = 0; t < 4; t++) TONE_MAP[arr[t]] = [b, t + 1];
  }

  // 零声母 y/w 开头音节的标准化（去掉 y/w 并补回真实韵母）
  var ZERO = {
    'yi': 'i', 'ya': 'ia', 'ye': 'ie', 'yao': 'iao', 'you': 'iu', 'yan': 'ian', 'yang': 'iang',
    'ying': 'ing', 'yin': 'in', 'yong': 'iong', 'yu': 'ü', 'yue': 'üe', 'yun': 'ün', 'yuan': 'üan',
    'wu': 'u', 'wa': 'ua', 'wo': 'uo', 'wai': 'uai', 'wei': 'ui', 'wan': 'uan', 'wen': 'un',
    'wang': 'uang', 'weng': 'ueng'
  };

  // 声母：2 字符在前（zh/ch/sh 必须先于 z/c/s 匹配），保证长前缀优先
  var SHENG_LIST = [
    ['zh', 'ㄓ'], ['ch', 'ㄔ'], ['sh', 'ㄕ'],
    ['b', 'ㄅ'], ['p', 'ㄆ'], ['m', 'ㄇ'], ['f', 'ㄈ'], ['d', 'ㄉ'], ['t', 'ㄊ'],
    ['n', 'ㄋ'], ['l', 'ㄌ'], ['g', 'ㄍ'], ['k', 'ㄎ'], ['h', 'ㄏ'],
    ['j', 'ㄐ'], ['q', 'ㄑ'], ['x', 'ㄒ'], ['r', 'ㄖ'], ['z', 'ㄗ'], ['c', 'ㄘ'], ['s', 'ㄙ']
  ];

  // 韵母：按长度降序，长前缀优先匹配
  var YUN_LIST = [
    ['iao', 'ㄧㄠ'], ['iang', 'ㄧㄤ'], ['ian', 'ㄧㄢ'], ['iong', 'ㄩㄥ'], ['uai', 'ㄨㄞ'],
    ['uang', 'ㄨㄤ'], ['uan', 'ㄨㄢ'], ['ueng', 'ㄨㄥ'], ['üan', 'ㄩㄢ'], ['üe', 'ㄩㄝ'],
    ['ang', 'ㄤ'], ['eng', 'ㄥ'], ['ing', 'ㄧㄥ'], ['ong', 'ㄨㄥ'],
    ['ai', 'ㄞ'], ['ei', 'ㄟ'], ['ui', 'ㄨㄟ'], ['ao', 'ㄠ'], ['ou', 'ㄡ'], ['iu', 'ㄧㄡ'],
    ['an', 'ㄢ'], ['en', 'ㄣ'], ['in', 'ㄧㄣ'], ['un', 'ㄨㄣ'], ['ün', 'ㄩㄣ'],
    ['ia', 'ㄧㄚ'], ['ie', 'ㄧㄝ'], ['ua', 'ㄨㄚ'], ['uo', 'ㄨㄛ'], ['er', 'ㄦ'],
    ['i', 'ㄧ'], ['u', 'ㄨ'], ['ü', 'ㄩ'], ['a', 'ㄚ'], ['o', 'ㄛ'], ['e', 'ㄜ']
  ];

  var TONE_SYM = { 1: '', 2: 'ˊ', 3: 'ˇ', 4: 'ˋ' };

  function pinyinToBopomofo(py) {
    if (!py) return '';
    py = String(py).trim().toLowerCase();
    var tone = 0;
    var s = '';
    for (var i = 0; i < py.length; i++) {
      var ch = py[i];
      if (TONE_MAP[ch]) { var info = TONE_MAP[ch]; s += info[0]; tone = info[1]; }
      else s += ch;
    }
    // 多音节（空格/逗号分隔）只取首个音节
    s = s.split(/[\s,，、]/)[0];

    // 零声母 y/w 处理
    if (ZERO.hasOwnProperty(s)) s = ZERO[s];

    // 拆声母（长前缀优先）
    var sheng = '';
    for (var k = 0; k < SHENG_LIST.length; k++) {
      var key = SHENG_LIST[k][0];
      if (s.indexOf(key) === 0) { sheng = SHENG_LIST[k][1]; s = s.slice(key.length); break; }
    }

    // 舌尖元音（zhi/chi/shi/ri/zi/ci/si）：i 不单独标
    if ((sheng==='ㄓ'||sheng==='ㄔ'||sheng==='ㄕ'||sheng==='ㄖ'||sheng==='ㄗ'||sheng==='ㄘ'||sheng==='ㄙ') && s==='i') {
      s = '';
    }
    // j/q/x 后的 u 实为 ü
    if ((sheng === 'ㄐ' || sheng === 'ㄑ' || sheng === 'ㄒ') && s.charAt(0) === 'u') {
      s = 'ü' + s.slice(1);
    }

    // 匹配韵母（舌尖元音已使 s 为空时跳过）
    var yun = '';
    if (s !== '') {
      for (var m = 0; m < YUN_LIST.length; m++) {
        if (s.indexOf(YUN_LIST[m][0]) === 0) { yun = YUN_LIST[m][1]; s = s.slice(YUN_LIST[m][0].length); break; }
      }
      if (!yun) return ''; // 非空却无法解析
    }

    var sym = tone ? (TONE_SYM[tone] || '') : '';
    return sheng + yun + sym;
  }

  global.pinyinToBopomofo = pinyinToBopomofo;
  if (typeof module !== 'undefined' && module.exports) module.exports = pinyinToBopomofo;
})(typeof window !== 'undefined' ? window : this);
