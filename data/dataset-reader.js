/* 精简浏览器端 dataset reader（IIFE，普通 <script> 可加载，file:// 双击可用）
 * 依赖：全局 fzstd（先加载 fzstd.umd.js）
 * 代码库：character-evolution-dataset-1bit（MIT，作者 Leon Si）——仅读取/解码逻辑
 * 数据来源：已切换为「中央研究院漢字構形資料庫 / 小學堂」（CC BY-SA 2.5 TW，可商用，须署名 + 衍生同授权）
 *   旧版非商业授权字形图已下架，禁止再拷入 dataset.bin
 *   新增「字源」阶段：GlyphWiki（CC BY-SA 2.1 JP，可商用，须署名 + 衍生同授权）
 */
(function (global) {
"use strict";
var decompress = (global.fzstd && global.fzstd.decompress) ? global.fzstd.decompress : null;
//#region src/constants.ts
/**
* Binary container format for the character-evolution image dataset.
*
* The dataset ships as a *single* file (`dataset.bin`) that holds every glyph
* image plus a self-describing index, so a consumer downloads one artifact and
* can pull out any individual image at runtime without unpacking the rest.
*
* Why this layout instead of N PNG files or a 2D sprite atlas:
*   - The glyphs are tiny (mostly < 150px) and hugely redundant across each
*     other (vast white margins, repeated stroke shapes, the same modern fonts
*     rendered for thousands of characters). Storing them as separate PNGs hides
*     that redundancy from the compressor and wastes ~36% to filesystem block
*     padding.
*   - Concatenating the *raw* pixels of similar glyphs back-to-back and running
*     a long-window zstd pass over the stream lets the compressor reference
*     matches across many glyphs, which is where the real win comes from
*     (measured ~38% of the original PNG size, fully lossless).
*   - Records are grouped into independently-compressed *blocks*. A reader only
*     decompresses the one block containing the wanted glyph, so random access
*     stays cheap even though the whole dataset is one file.
*
* File layout:
*
*   [ MAGIC (8 bytes) ][ headerLength (u32 LE) ][ header (zstd-compressed) ]
*   [ block 0 (zstd) ][ block 1 (zstd) ] ... [ block N-1 (zstd) ]
*
* The header is a *zstd-compressed* columnar index (see `./types.ts`). It is
* stored columnar — keys in one string, widths/heights/channels in parallel
* typed arrays — and omits anything derivable (a record's block, its offset
* within that block, and its byte length all fall out of the stored order plus
* `width * height * channels`). For ~263k records this shrinks the index from
* ~30 MB of JSON to ~1.3 MB with no loss. Everything needed to extract an image
* is in the header — the blocks are opaque zstd frames.
*/
/**
* File signature. A plain `Uint8Array` (not a Node `Buffer`) so this module —
* and the reader that consumes it — stays free of any Node-only dependency and
* can run in the browser or React Native.
*/
const MAGIC = new Uint8Array([
	67,
	69,
	68,
	83,
	48,
	48,
	48,
	50
]);
//#endregion
//#region src/dataset.ts
/** Chronological rank of each {@link Script}, oldest first. */
const SCRIPT_ORDER = {
	"glyphwiki": 0,
	"oracle-bone": 1,
	"bronze": 2,
	"bamboo-silk": 3,
	"bigseal": 4,
	"seal": 5,
	"clerical": 6,
	"regular": 7,
	"other": 8
};
/**
* Classify a glyph key (or bare filename) into a {@link Script} from its prefix.
* The dataset encodes the script in the filename: `O_*` = oracle-bone, `J_` =
* bronze (金文), `W_` = bamboo/silk slips (简牍帛书), `Z_` =
* seal/Shuowen small-seal (說文/篆), `L_` = clerical (隸), `K_`/`X_` =
* modern regular or Kangxi dictionary forms (楷体/康熙字). Anything else falls
* back to "other".
*/
function parseScript(keyOrFilename) {
	const slash = keyOrFilename.lastIndexOf("/");
	const filename = slash === -1 ? keyOrFilename : keyOrFilename.slice(slash + 1);
	if (filename.startsWith("O_")) return "oracle-bone";
	if (filename.startsWith("J_")) return "bronze";
	if (filename.startsWith("W_")) return "bamboo-silk";
	if (filename.startsWith("D_")) return "bigseal";
	if (filename.startsWith("Z_")) return "seal";
	if (filename.startsWith("L_")) return "clerical";
	if (filename.startsWith("K_")) return "regular";
	if (filename.startsWith("X_")) return "regular";
	if (filename.startsWith("G_")) return "glyphwiki";
	return "other";
}
/**
* Default block decompressor: the pure-JS/WASM-free {@link fzstdDecompress}.
* Works in any JS runtime (browser, React Native, Node) with no native module,
* which is what lets {@link DatasetReader} run out of the box everywhere. It is
* slower than a native zstd binding — supply your own {@link Decompress} (e.g.
* `nodeDecompress` from the `/node` entry) when raw speed matters.
*
* `fzstd` ignores the window log (its second argument is an output buffer, not a
* window), so we deliberately call it with one argument.
*/
const defaultDecompress = (compressed) => decompress(compressed);
const textDecoder = new TextDecoder();
function bytesEqual(a, b) {
	if (a.length !== b.length) return false;
	for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
	return true;
}
/**
* Rebuild the row-shaped {@link DatasetEntry} index from the columnar header.
* The header omits each record's block, within-block offset, and byte length
* because they are derivable: records fill blocks of `blockSize` in stored
* order, a record's length is `width * height * channels`, and its offset is the
* running sum of lengths since the start of its block.
*/
function reconstructEntries(header) {
	const { widths, heights, channels, blockSize } = header;
	const keys = header.keys.length > 0 ? header.keys.split("\n") : [];
	const entries = Array.from({ length: keys.length });
	let blockOffset = 0;
	for (let i = 0; i < keys.length; i++) {
		if (i % blockSize === 0) blockOffset = 0;
		const width = widths[i];
		const height = heights[i];
		const ch = channels[i];
		const length = width * height * ch;
		entries[i] = {
			key: keys[i],
			width,
			height,
			channels: ch,
			block: Math.floor(i / blockSize),
			offset: blockOffset,
			length
		};
		blockOffset += length;
	}
	return entries;
}
/**
* Random-access reader over a single-file character dataset produced by the
* packer. The whole dataset is held as one in-memory `Uint8Array`; image pixels
* are sliced out one decompressed block at a time, so extraction is cheap and
* the reader has **no I/O dependency** — the caller is responsible for getting
* the bytes into memory (read a file on Node, `fetch()` in a browser, bundle an
* asset in React Native) and for supplying a zstd {@link Decompress}.
*/
var DatasetReader = class {
	#bytes;
	#decompress;
	#header;
	#bodyOffset;
	#entries;
	#entryByKey;
	#cache = /* @__PURE__ */ new Map();
	#cacheLimit;
	/** Lazily built character → keys index (see {@link #ensureCharacterIndex}). */
	#keysByCharacter = null;
	/**
	* Build a reader over an in-memory dataset.
	*
	* @param bytes      The entire dataset file as a `Uint8Array`.
	* @param decompress Optional block decompressor (see {@link Decompress}).
	*   Defaults to the bundled `fzstd` ({@link defaultDecompress}); pass a faster
	*   native zstd binding to override. May also be set via `options.decompress`.
	* @param options    Reader tuning (block cache size, decompressor).
	*/
	constructor(bytes, decompress, options = {}) {
		this.#bytes = bytes;
		this.#decompress = decompress ?? options.decompress ?? defaultDecompress;
		this.#cacheLimit = options.blockCacheSize ?? 8;
		const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
		if (bytes.length < MAGIC.length + 4 || !bytesEqual(bytes.subarray(0, MAGIC.length), MAGIC)) throw new Error("Not a character-evolution dataset file (bad magic)");
		const headerLength = view.getUint32(MAGIC.length, true);
		const headerStart = MAGIC.length + 4;
		const headerBytes = this.#decompress(bytes.subarray(headerStart, headerStart + headerLength), 0);
		this.#header = JSON.parse(textDecoder.decode(headerBytes));
		this.#bodyOffset = headerStart + headerLength;
		this.#entries = reconstructEntries(this.#header);
		this.#entryByKey = new Map(this.#entries.map((e) => [e.key, e]));
	}
	/** All keys in the dataset, in stored order. */
	keys() {
		return this.#entries.map((e) => e.key);
	}
	/**
	* The lossy transforms (if any) that were applied when this dataset was
	* packed. All fields absent/false means the stored pixels are bit-exact with
	* the original images — i.e. the file is a lossless source. Used by the packer
	* to refuse re-packing from a lossy input (which would compound loss).
	*/
	get provenance() {
		return {
			quantizeLevels: this.#header.quantizeLevels,
			maxSide: this.#header.maxSide,
			blackWhite: this.#header.blackWhite
		};
	}
	/** Number of images in the dataset. */
	get size() {
		return this.#entries.length;
	}
	/** Whether a key exists. */
	has(key) {
		return this.#entryByKey.has(key);
	}
	/** Metadata for a key, or undefined if absent. */
	entry(key) {
		return this.#entryByKey.get(key);
	}
	/**
	* The modern character for a glyph, e.g. `"㐁"` — or `undefined` if unknown.
	* Accepts either a full key (`"00011/K_楷体"`) or a bare character ID
	* (`"00011"`); the ID is the folder-name prefix of a key. Labels come from the
	* dataset's `Key&Value.json` and may be **partially** present.
	*/
	character(keyOrId) {
		const map = this.#header.characters;
		if (!map) return void 0;
		const slash = keyOrId.indexOf("/");
		return map[slash === -1 ? keyOrId : keyOrId.slice(0, slash)];
	}
	/**
	* The full ID → character map (e.g. `{ "00011": "㐁" }`), or `undefined` if the
	* dataset carries no labels. Coverage may be partial.
	*/
	characters() {
		return this.#header.characters;
	}
	/**
	* Build (once) and return the character → keys index. Requires an embedded
	* character map; without one there is no way to relate a character to its
	* folders, so the index is empty. Keys are grouped by the character of their
	* folder id and kept in stored order.
	*/
	#ensureCharacterIndex() {
		if (this.#keysByCharacter) return this.#keysByCharacter;
		const index = /* @__PURE__ */ new Map();
		const characters = this.#header.characters;
		if (characters) for (const entry of this.#entries) {
			const slash = entry.key.indexOf("/");
			const char = characters[slash === -1 ? entry.key : entry.key.slice(0, slash)];
			if (char === void 0) continue;
			let keys = index.get(char);
			if (!keys) {
				keys = [];
				index.set(char, keys);
			}
			keys.push(entry.key);
		}
		this.#keysByCharacter = index;
		return index;
	}
	/**
	* All glyph keys for a character (e.g. `"㐁"`), in stored order. Empty when the
	* character is unknown or the dataset carries no character map. Pass a key to
	* {@link getRaw} to extract a glyph's pixels.
	*/
	keysForCharacter(character) {
		return this.#ensureCharacterIndex().get(character)?.slice() ?? [];
	}
	/**
	* The glyphs for a character with each key classified into a {@link Script}
	* and assigned a chronological rank, sorted oldest → newest (ties broken by
	* key). This is the shape a consumer renders as an evolution row. Empty when
	* the character is unknown or unlabeled.
	*/
	glyphsForCharacter(character) {
		const keys = this.#ensureCharacterIndex().get(character);
		if (!keys) return [];
		return keys.map((key) => {
			const script = parseScript(key);
			return {
				key,
				script,
				order: SCRIPT_ORDER[script]
			};
		}).sort((a, b) => a.order - b.order || (a.key < b.key ? -1 : a.key > b.key ? 1 : 0));
	}
	/** Decompress (and cache) the block at the given index. */
	#readBlock(blockIndex) {
		const cached = this.#cache.get(blockIndex);
		if (cached) {
			this.#cache.delete(blockIndex);
			this.#cache.set(blockIndex, cached);
			return cached;
		}
		const ref = this.#header.blocks[blockIndex];
		if (!ref) throw new Error(`Block ${blockIndex} out of range`);
		const start = this.#bodyOffset + ref.fileOffset;
		const compressed = this.#bytes.subarray(start, start + ref.compressedLength);
		const raw = this.#decompress(compressed, this.#header.windowLog);
		if (this.#cacheLimit > 0) {
			this.#cache.set(blockIndex, raw);
			while (this.#cache.size > this.#cacheLimit) {
				const oldest = this.#cache.keys().next().value;
				this.#cache.delete(oldest);
			}
		}
		return raw;
	}
	/**
	* Extract the raw pixels for a key. This decompresses one block (cached) and
	* slices out the record — no image re-encoding.
	*/
	getRaw(key) {
		const entry = this.#entryByKey.get(key);
		if (!entry) throw new Error(`Key not found: ${key}`);
		const view = this.#readBlock(entry.block).subarray(entry.offset, entry.offset + entry.length);
		return {
			width: entry.width,
			height: entry.height,
			channels: entry.channels,
			pixels: view.slice()
		};
	}
	/** Drop all cached decompressed blocks. */
	clearCache() {
		this.#cache.clear();
	}
};
//#endregion

var SCRIPT_METADATA = {
  "oracle-bone": { chinese: "甲骨文" },
  "bronze": { chinese: "金文" },
  "bamboo-silk": { chinese: "简牍帛书" },
  "bigseal": { chinese: "大篆" },
  "seal": { chinese: "小篆" },
  "clerical": { chinese: "隶书" },
  "regular": { chinese: "楷书" },
  "glyphwiki": { chinese: "字源" },
  "other": { chinese: "其他" }
};
global.__CDS = {
  DatasetReader: DatasetReader,
  MAGIC: MAGIC,
  parseScript: parseScript,
  SCRIPT_METADATA: SCRIPT_METADATA
};
})(typeof self !== "undefined" ? self : this);
