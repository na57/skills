---
name: math-figure-svg
description: 将带数学公式的图形绘制成规范 SVG 的最佳实践与可复用工具。核心方法：图形几何走 SVG 路径（手绘或 AI 生成），数学公式交给 MathJax/TikZ 排版，最后用脚本合成；绝不手动描摹数学符号。当用户要画几何图、函数图像、带公式的示意图，或抱怨 AI 生成的公式符号（∫ ∑ ∂ √ 分式 上下标 极限）不规范时使用。
---

# 数学图形 SVG 绘制（math-figure-svg）

## 何时使用

- 要画几何图、函数图像、带公式的示意图 / 讲义配图
- 用 AI 画图后，公式符号（∫ ∑ ∂ √ 分式 上下标 极限）不规范、显得是"描"出来的
- 需要可无限缩放、可打印、可进资料库的干净 SVG

## 核心原则：两条管道，最后合成

1. **图形几何**：手绘 SVG 的 `path`/`line`/`circle`，或让 AI 只生成几何部分（只画形状，不画公式）
2. **数学公式**：写成 LaTeX，**永远交给排版引擎**（MathJax / KaTeX / TeX）转成 SVG 路径
3. **合成**：用脚本把公式 SVG 按坐标注入几何 SVG
4. ❌ 绝不让模型 / 画图工具去"手绘"数学符号

## 为什么 AI 画公式会翻车（原理）

模型把数学符号当作视觉纹理去拟合，缺乏数学语义，根式高度、分式线居中、极限 `lim` 下标、括号伸缩等版式约束无法保证。这是架构边界，不是 prompt 问题——改进办法是换引擎，不是换提示词。

## 三种落地路径

| 路径 | 适合 | 数学质量 | 成本 |
|---|---|---|---|
| **TikZ + LaTeX** | 几何图（圆/三角/坐标/矩阵） | 最高，数学原生 | 重：需装 TeX |
| **MathJax 合成**（本 skill 内置工具） | 已有 AI 图、只换公式标注 | 高 | 轻：Node + mathjax-full |
| **matplotlib 导出 SVG** | 函数图像 / 统计图 | 高（`usetex` 开真 LaTeX） | 中：pip + 可选 LaTeX |

## 本 skill 工具：`scripts/compose.mjs`

把 MathJax 排版的 LaTeX 标注合成进你提供的几何 SVG。

### 安装（局部，不污染全局）

```bash
cd math-figure-svg          # 含 package.json 的根目录
npm install                 # 装 mathjax-full；如需 PNG 预览再装 @resvg/resvg-js
```

### 用法

```bash
node scripts/compose.mjs --geom geometry.svg --labels labels.json --out out.svg [--png]
```

- `geometry.svg`：你手绘 / AI 生成的几何图（纯形状，不含公式）。脚本会把标注注入到 `</svg>` 前。
- `labels.json`：标注数组，每项 `{ "latex": "...", "x": 100, "y": 200, "size": 18, "color": "#222" }`
  - `x`, `y`：公式基线的锚点坐标（与几何 SVG 同一坐标系）
  - `size`：目标高度（px），默认 18
  - `color`：默认 `#222`
- `--png`：额外渲染一张 PNG 预览（需 `@resvg/resvg-js`）

### 快速开始（自带示例）

```bash
node scripts/compose.mjs --geom scripts/example/geometry.svg \
                         --labels scripts/example/labels.json \
                         --out demo.svg --png
```

## 关键踩坑（复用必读）

1. MathJax `outerHTML()` 输出外层包了 `<mjx-container>`（HTML 标签），嵌入 SVG 前必须正则剥出 `<svg>...</svg>`，否则渲染器不认。
2. MathJax SVG 的宽高单位是 **ex**（不是 pt）；正确做法是从 `viewBox` 反推尺寸，并把 `width`/`height` 重写为 viewBox 数值（纯用户坐标），再靠外层 `scale()` 控制字号。
3. 多个公式嵌进同一文档会撞 glyph id（都叫 `MJX-1-...`），逐个 `replace(/MJX-/g, 'MJX${n}-')` 加唯一前缀。
4. `currentColor` 换成显式颜色，resvg 等渲染器才可靠。
5. 基线对齐：MathJax viewBox 以 `y=0` 为基线（上方为负），放置公式用 `y = baselineY - (0 - minY) * scale`。
6. SVG 上凸半圆弧：从左端点到右端点用 `sweep-flag=1`。

## 进阶：TikZ 方案（几何与数学同源）

完整可跑示例在 `scripts/example/tikz/`（同一张"半圆与几何平均"图，几何和
公式写在**同一份 `.tex`** 里，TeX 同时排版两者，天然同源；改 `\a`/`\b`
两个参数即可换图）：

```bash
bash scripts/example/tikz/build.sh      # 生成 semicircle-mean.svg（顺带 PDF）
```

### 导出 SVG 的关键坑：不要走默认 PostScript 路线

默认 `latex` 用 dvips(PostScript) 驱动，此时 `dvisvgm` 要把 PostScript
special 转成图形，**依赖 Ghostscript**——没装或找不到 `libgs` 时会报
"PostScript specials ignored"，产物只剩文字、几何全丢（本 skill 作者实测踩过）。

更稳的做法：编译时强制 pgf 用**原生 dvisvgm 驱动**，完全不需要 Ghostscript：

```bash
# 在 .tex 前面加一行驱动声明（原文件不动，仍可 pdflatex 出 PDF）
printf '\\def\\pgfsysdriver{pgfsys-dvisvgm.def}\n' | cat - figure.tex > build.tex
latex -interaction=nonstopmode build.tex
dvisvgm -n -o figure.svg build.dvi      # -n：文字转路径，SVG 自包含
```

判别方法：若 dvisvgm 报 "hundreds of PostScript specials ignored" 且
SVG 尺寸只有几十 pt——几何丢了；强制驱动后会降到个位数（颜色等残留，
不影响画面）且尺寸是完整图幅。

只想要 PDF：直接 `pdflatex figure.tex`；PDF 转 SVG 可用
`pdftocairo -svg` / `pdf2svg` / `inkscape --export-type=svg`。

### 何时选 TikZ 而不是 MathJax 合成

图形本身就是几何/坐标类（圆、三角、矩阵、向量）→ TikZ 单源码最省心；
图形是 AI 生成的示意图、只想替换公式 → 用本 skill 的 MathJax 合成更轻量。

## 一句话总结

**数学不是"画"出来的，是"排版"出来的。** 图形与数学分管道、公式交给引擎、脚本合成。
