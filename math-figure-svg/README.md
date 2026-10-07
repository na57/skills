# math-figure-svg

将**带数学公式的图形**绘制成规范 SVG 的最佳实践与可复用工具。

核心方法：**图形几何走 SVG 路径（手绘或 AI 生成），数学公式交给 MathJax/TikZ 排版，最后用脚本合成**——绝不手动描摹数学符号。

详见 [`SKILL.md`](./SKILL.md)。

## 快速开始

```bash
npm install
node scripts/compose.mjs --geom scripts/example/geometry.svg \
                         --labels scripts/example/labels.json \
                         --out demo.svg --png
```

`demo.svg` 即为一张"以 AB 为直径的半圆、分点 C、垂足 D"的标准几何图，其中
`AB = a + b`、`AC = a`、`CB = b`、`CD = √ab` 全部由 MathJax 从 LaTeX 排版而成。
