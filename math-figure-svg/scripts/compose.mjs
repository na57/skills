#!/usr/bin/env node
// compose.mjs — 把 MathJax 排版的 LaTeX 标注合成进几何 SVG
// 用法: node compose.mjs --geom geometry.svg --labels labels.json --out out.svg [--png]

import { mathjax } from 'mathjax-full/js/mathjax.js';
import { TeX } from 'mathjax-full/js/input/tex.js';
import { SVG } from 'mathjax-full/js/output/svg.js';
import { liteAdaptor } from 'mathjax-full/js/adaptors/liteAdaptor.js';
import { RegisterHTMLHandler } from 'mathjax-full/js/handlers/html.js';
import { AllPackages } from 'mathjax-full/js/input/tex/AllPackages.js';
import { readFileSync, writeFileSync } from 'fs';

const args = process.argv.slice(2);
const get = (flag, def) => {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : def;
};
const geomPath = get('--geom');
const labelsPath = get('--labels');
const outPath = get('--out', 'out.svg');
const doPng = args.includes('--png');

if (!geomPath || !labelsPath) {
  console.error('用法: node compose.mjs --geom geometry.svg --labels labels.json --out out.svg [--png]');
  process.exit(1);
}

// ---- MathJax 初始化（LaTeX → SVG 路径）----
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({ packages: AllPackages });
const svgOut = new SVG({ fontCache: 'local' });
const doc = mathjax.document('', { InputJax: tex, OutputJax: svgOut });

let uid = 0;
function place(latex, cx, baselineY, targetPx = 18, color = '#222') {
  let s = adaptor.outerHTML(doc.convert(latex));
  s = (s.match(/<svg[\s\S]*?<\/svg>/) || [s])[0];   // 剥掉 <mjx-container>
  s = s.replace(/currentColor/g, color);            // 显式颜色
  s = s.replace(/MJX-/g, `MJX${uid++}-`);           // 防止 glyph id 撞车
  const p = ((s.match(/viewBox="([-\d.\s]+)"/) || [])[1] || '0 0 0 0')
    .trim().split(/\s+/).map(Number);
  const [minX, minY, w, h] = p;
  s = s.replace(/width="[^"]*"/, `width="${w}"`)
       .replace(/height="[^"]*"/, `height="${h}"`);
  const scale = h ? targetPx / h : 1;
  const x = cx - (minX + w / 2) * scale;            // 水平居中
  const y = baselineY - (0 - minY) * scale;         // MathJax 以 y=0 为基线，上方为负
  return `<g transform="translate(${x.toFixed(2)},${y.toFixed(2)}) scale(${scale.toFixed(4)})">${s}</g>`;
}

const geom = readFileSync(geomPath, 'utf8');
const labels = JSON.parse(readFileSync(labelsPath, 'utf8'));
const labelSvg = labels
  .map(l => place(l.latex, l.x, l.y, l.size || 18, l.color || '#222'))
  .join('\n  ');

let out = geom.includes('</svg>')
  ? geom.replace('</svg>', `  <g id="math-labels">\n  ${labelSvg}\n  </g>\n</svg>`)
  : geom + `<g id="math-labels">${labelSvg}</g>`;

writeFileSync(outPath, out);
console.log(`✓ 已写出 ${outPath}（含 ${labels.length} 个公式标注）`);

if (doPng) {
  try {
    const { Resvg } = await import('@resvg/resvg-js');
    const pngPath = outPath.replace(/\.svg$/i, '.png');
    writeFileSync(pngPath, new Resvg(out, { background: '#ffffff' }).render().asPng());
    console.log(`✓ 已生成 PNG 预览 ${pngPath}`);
  } catch {
    console.warn('⚠ 未安装 @resvg/resvg-js，跳过 PNG（npm i @resvg/resvg-js）');
  }
}
