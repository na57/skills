# TikZ 方案示例：以 AB 为直径的半圆与几何平均

这是 `math-figure-svg` skill 的 **路径 A（TikZ + LaTeX）** 示例。

与 `../`（MathJax 合成）方案不同，这里**几何与数学来自同一份 LaTeX 源码**：
半圆、直径、垂线、直角标记、各点，连同 `AB = a + b`、`CD = √ab` 等公式，
全部由 TeX 排版，二者天然同源、永远不会「画歪」。

## 文件

- `semicircle-mean.tex` — 单文件图形源码（改 `\a` / `\b` 两个参数即可换图）
- `build.sh` — 一键编译成自包含 SVG

## 编译

需要 TeX Live（`latex` + `dvisvgm`）：

```bash
bash build.sh          # 生成 semicircle-mean.svg（文字已转路径，自包含）
```

如果你只想出 PDF，直接 `pdflatex semicircle-mean.tex`；再把 PDF 转 SVG 可用
`pdftocairo -svg`、`pdf2svg` 或 `inkscape --export-type=svg`。

## 何时选 TikZ 而不是 MathJax 合成

- 图形本身就是几何 / 坐标类（圆、三角、矩阵、向量）—— 单一源码最省心，零合成步骤。
- 图形是 AI 生成的示意图、只想替换里面的公式 —— 改用上层目录的 MathJax 合成更轻量。
