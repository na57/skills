#!/usr/bin/env bash
# 把 semicircle-mean.tex 编译成自包含的 SVG（几何与数学同源）。
#
# 用法： bash build.sh
# 依赖：TeX Live 的 latex + dvisvgm（不需要 Ghostscript）。
#   macOS: `brew install --cask mactex`（或轻量的 basictex）
#   Linux: `apt install texlive-latex-base texlive-pictures texlive-latex-extra dvisvgm`
#
# 原理（重要，绕开 Ghostscript 依赖）：
#   默认 `latex` 走 dvips(PostScript) 驱动，dvisvgm 需要 Ghostscript
#   才能把 PostScript special 转成图形。这里在编译时强制 pgf 使用
#   原生 dvisvgm 驱动（pgfsys-dvisvgm.def），dvisvgm 直接消费这些
#   special，完全不需要 Ghostscript。原 .tex 不做改动，仍可 pdflatex。
set -euo pipefail

cd "$(dirname "$0")"
name=semicircle-mean

# 1) 生成强制 dvisvgm 驱动的临时副本（原 .tex 保持引擎无关）
tmp=svgbuild.tex
printf '\\def\\pgfsysdriver{pgfsys-dvisvgm.def}\n' | cat - "$name.tex" > "$tmp"

# 2) latex -> DVI
latex -interaction=nonstopmode -halt-on-error "$tmp" >/dev/null

# 3) DVI -> SVG（-n：文字转路径，SVG 自包含、不依赖外部字体）
dvisvgm -n -o "$name.svg" svgbuild.dvi

# 4) 顺手出一份 PDF（想要 PDF 终态时）
pdflatex -interaction=nonstopmode -halt-on-error "$name.tex" >/dev/null

# 清理中间文件
rm -f "$tmp" svgbuild.dvi svgbuild.log svgbuild.aux \
      "$name.dvi" "$name.log" "$name.aux" "$name.out"

echo "wrote $name.svg"
