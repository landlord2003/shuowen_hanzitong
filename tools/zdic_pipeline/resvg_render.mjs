// resvg_render.mjs  用法: node resvg_render.mjs <in.svg> <out.png> [h] [background]
// 金文字形栅格化：@resvg/resvg-js（Rust/resvg 预编译，零系统依赖，无需 Cairo）
// 注意：务必传 background="#ffffff" —— 汉典 SVG 自带近白水印，白底渲染可让水印并入背景
import { Resvg } from '@resvg/resvg-js';
import { readFileSync, writeFileSync } from 'fs';
const [, , inPath, outPath, hArg, bgArg] = process.argv;
const opts = { fitTo: { mode: 'height', value: parseInt(hArg || '160', 10) } };
if (bgArg && bgArg !== 'none') opts.background = bgArg;   // 传 "#ffffff"
writeFileSync(outPath, new Resvg(readFileSync(inPath, 'utf8'), opts).render().asPng());
