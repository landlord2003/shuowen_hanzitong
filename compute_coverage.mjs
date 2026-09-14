import fs from 'node:fs';
import vm from 'node:vm';

const ROOT = 'D:/WorkBuddy/projects/说文解字';
const fzsrc = fs.readFileSync(`${ROOT}/data/fzstd.umd.js`, 'utf8');
const drsrc = fs.readFileSync(`${ROOT}/data/dataset-reader.js`, 'utf8');

// Run both scripts in a shared sandbox. dataset-reader expects a global `fzstd`
// (provided by fzstd.umd.js) and sets `global.__CDS`. In a vm top-level, `this`
// is the context object, so passing `self` makes `global` === context.
const ctx = { self: null, TextDecoder, DataView, Uint8Array, Map, Math, Array, JSON, console, Buffer };
ctx.self = ctx;
vm.createContext(ctx);
vm.runInContext(fzsrc, ctx);
vm.runInContext(drsrc, ctx);
const CDS = ctx.__CDS;
if (!CDS) { console.error('CDS missing; fzstd?', !!ctx.fzstd); process.exit(1); }

const buf = fs.readFileSync(`${ROOT}/data/dataset.bin`);
const bytes = new Uint8Array(buf); // ensure byteOffset 0
const reader = new CDS.DatasetReader(bytes);
console.error('dataset size (records):', reader.size);
console.error('has characters map:', !!reader.characters());

// ID -> char from bin header if present, else from characters.json
const idToChar = reader.characters() ? { ...reader.characters() } : {};
if (Object.keys(idToChar).length === 0) {
  const cj = JSON.parse(fs.readFileSync(`${ROOT}/data/characters.json`, 'utf8'));
  for (const c of cj.characters) idToChar[String(c.id)] = c.char;
}

// characters.json: 8105 list + liushu distribution
const cj = JSON.parse(fs.readFileSync(`${ROOT}/data/characters.json`, 'utf8'));
const appChars = cj.characters.map(c => c.char);
const appCharSet = new Set(appChars);
const liushu = {};
for (const c of cj.characters) liushu[c.liushu] = (liushu[c.liushu] || 0) + 1;

// iterate all keys, classify script, map to char via id
const SCRIPT_KEYS = { 'O_':'oracle-bone','J_':'bronze','W_':'bamboo-silk','D_':'bigseal','Z_':'seal','L_':'clerical','K_':'regular','X_':'regular','G_':'glyphwiki' };
const scriptChars = {};      // script -> Set(char)
const scriptImages = {};     // script -> count of images
let unknownScript = 0, unknownId = 0;
for (const key of reader.keys()) {
  const slash = key.lastIndexOf('/');
  const id = slash === -1 ? key : key.slice(0, slash);
  const base = slash === -1 ? key : key.slice(slash + 1);
  let script = 'other';
  for (const p in SCRIPT_KEYS) if (base.startsWith(p)) { script = SCRIPT_KEYS[p]; break; }
  if (script === 'other') unknownScript++;
  const ch = idToChar[id];
  if (ch === undefined) { unknownId++; continue; }
  (scriptChars[script] ||= new Set()).add(ch);
  scriptImages[script] = (scriptImages[script] || 0) + 1;
}

const appScriptCounts = {}; // script -> count of chars in 8105 having that script
for (const s in scriptChars) {
  let n = 0;
  for (const ch of scriptChars[s]) if (appCharSet.has(ch)) n++;
  appScriptCounts[s] = n;
}

// union of ancient real scripts (exclude glyphwiki '字源' which is its own layer)
const ancient = ['oracle-bone','bronze','bamboo-silk','bigseal','seal','clerical','regular'];
const unionSet = new Set();
for (const s of ancient) for (const ch of (scriptChars[s]||[])) if (appCharSet.has(ch)) unionSet.add(ch);

const totalImages = Object.values(scriptImages).reduce((a,b)=>a+b,0);
const realImages = ancient.reduce((a,s)=>a+(scriptImages[s]||0),0);

const out = {
  dataset_records: reader.size,
  total_images: totalImages,
  real_ancient_images: realImages,
  has_characters_map: !!reader.characters(),
  unknown_script_keys: unknownScript,
  unknown_id_keys: unknownId,
  script_images: scriptImages,
  script_distinct_chars: Object.fromEntries(Object.entries(scriptChars).map(([k,v])=>[k,v.size])),
  app_8105_script_counts: appScriptCounts,
  app_chars_total: appChars.length,
  app_chars_with_any_ancient_glyph: unionSet.size,
  liushu_distribution: liushu,
};
console.log(JSON.stringify(out, null, 2));
