---
name: "make-explainer-video"
description: "把一章/一节的知识点做成「HTML 幻灯片讲解视频」：HTML 课件(PPT) → 抽取旁白 → Higgs 克隆音色配音 → 逐页截图 → 烧入中文字幕+推导停顿合成 1080p 视频。适用于学科复习讲解、微课、知识地图类视频。Trigger: 讲解视频 / 复习视频 / 微课 / 课件转视频 / 知识讲解 / 公式推导视频 / 带字幕教学视频。"
agent_created: true
---

# 讲解视频制作流水线

把一份「按页组织的 HTML 幻灯片」变成一支**带配音、带中文字幕、含互动暂停**的 1080p 讲解视频。
已验证跑通：33 页 / 17.6 分钟 / 1080p25 / 40 段配音 / 7 处推导停顿，全片同一把克隆音色。

## 何时用

- 用户要「把这份课件/讲义做成讲解视频」
- 要带**稳定音色**的中文物配音（视频类，不能一句一个声）
- 要**烧入字幕**（尤其念到公式时字幕显示标准记法而非口语稿）
- 需要「暂停推导」类互动（视频真留白，让学生动手）

## 何时不用

- 录屏式演示视频（系统操作/产品 Demo）→ 用 `narrated-demo-video` 技能
- 纯音频、不需画面

## 总览

```
课件 HTML(每页 data-narration)
   │  extract_narration.py
   ▼
script.json(旁白文本) + meta.json(分页/拆分/停顿)
   │  higgs-voice-tts 批量合成（引用该 skill）
   ▼
audio/*.mp3 + timing.json(每段时长)
   │  playwright 逐页截图（shoot.js / shoot3.js）
   ▼
shots/slide_NN.png
   │  assemble2.py（拼音频+烧字幕+合成）
   ▼
final.mp4（1080p）
```

## 阶段 0 — 课件 HTML 规范（最重要，决定后续顺不顺）

参考 `assets/templates/courseware-example.html`（一份真实 33 页物理讲解课件）。
每页必须是一个 `<section class="slide" data-narration="...">`，且：

- **`data-narration` 是旁白稿的唯一来源**，后续全部自动抽取。写稿时直接写「口语版」（如 `v 零`、`x t`），别写 LaTeX。
- **`data-narration` 里禁止半角双引号 `"`**——会提前截断 HTML 属性。用中文引号「」或『』。本流程真踩过坑。
- 用 `MathJax`（CDN 加载 `tex-chtml`）渲染公式；同一 display 公式块里**不能有两个 `\tag{}`**（报 "Multiple \tag"），改用 `\;\;(1)` 内联标号。
- 加 `?slide=N&autohide=1` 直达参数：截图脚本用它逐页打开并隐藏导航/进度条。
- 固定 16:9 舞台 + 页脚 ~40px；内容 bottom 超过舞台高减 ~44px 会被页脚盖住——推导页用 `\text{}` 把引导句并进公式块省高度。可写个无头脚本逐页测 `getBoundingClientRect` bottom 是否越界。
- 图片用相对路径 `images/`，截图前确认图片已落盘。

## 阶段 1 — 抽取旁白

`scripts/extract_narration.py`（**先改脚本顶部的 `SRC` 和 `OUT_DIR` 两个常量**为你自己的路径）：

- 正则抓全部 `data-narration` → `script.json`（TTS 输入）。
- 同时产出 `meta.json`：每页一个对象，`parts` 给出该页音频段列表，`pause` 给出停顿秒数。
- **推导互动页自动拆分**：用正则 `你?(推出来了吗|证明了吧|发现了吧|算出来了吗)[？?]?` 把该页拆成 `a`(下达暂停指令前) + `b`(核对答案) 两段，中间由组装脚本插静音停顿。
- `clean()` 做口语化：`v0→v 零`、`x1→x 一`、`x-t→x t` 等，让 TTS 念得自然。

## 阶段 2 — Higgs 配音

加载 `higgs-voice-tts` 技能，用它的 `tts.py --batch script.json -d audio/ --timing timing.json` 批量合成。
要点：

- 自带克隆样本，多段之间**同一把声音**；合成后用 `verify_voice.py` 做 F0 一致性校验（标准差 < 8Hz 即稳定）。
- 40 条批量建议在**后台**跑（`run_in_background`），几分钟。

## 阶段 3 — 逐页截图

`scripts/shoot.js`（`node shoot.js <课件html绝对路径> <输出目录>`）。要点（真踩坑）：

- `page.goto(url, {waitUntil:'load'})` + 等 `MathJax.startup.document.state()==='ready'`（超时 15s 就放行，图片页无公式）。
- **不要用 `networkidle`**：MathJax CDN 会让它永远等不到而超时。
- 视口 1920×1080，`deviceScaleFactor:1`，文件名 `slide_01.png`…（与 `assemble2.py` 的 `slide_{sid[1:]}.png` 对应）。
- **单页图变了只重截那页**（图片页不等 MathJax，用 `shoot3.js` 只截第 3 页：`domcontentloaded` + 等 `<img>` 的 `complete&&naturalWidth>0`）。之前全量重截 33 页卡死在逐页等 CDN，被超时 SIGTERM——别重蹈。

## 阶段 4 — 组装（核心）

`scripts/assemble2.py`（**先改顶部的 `SRC`、`OUT` 路径常量**）。它做四件事：

1. 把 `SRC` 的 shots/audio 拷到 `OUT`；读 script/timing/meta。
2. **互动页音频**：`a.mp3` + `anullsrc`(PAUSE 秒静音) + `b.mp3` → `concat` 成整段。PAUSE 默认 2.0s（用户原话「停 1-2 秒就行」；留白是提示性一拍，推导靠学生自己暂停。早期用 20s 太啰嗦）。
3. **逐页字幕 SRT + 分段视频**：
   - 长旁白**必须按标点切成 ≤36 字短句**，再按字数比例分摊每条字幕的起止时间。否则单条长字幕在 1920 宽下左右被裁（libass 对无空格中文**不自动换行**）。`MAXLEN` 早期 24→36：含公式长句（如 `√[(v₀²+v²)⁄2]`）在 24 字会被硬切两行。
   - **公式显示版（本流程关键优化）**：旁白念口语（`v 减 v 零`），但字幕在念到公式处显示标准记法（`v = v₀ + at`、`v² − v₀² = 2ax`、`Δx = aT²`、`v₁∶v₂∶v₃ = 1∶2∶3`）。实现是脚本里的 `DISPLAY` 字典，按 part-id 覆盖**含公式的段落**。新视频请按自己的旁白改写或清空该字典，逻辑不变。
   - 停顿窗口插一条提示字幕 `（暂停视频，拿出纸笔推导，推完再继续播放）`。
   - **字体**：libass 需要含中文 glyph 的字体。macOS 只有 `.ttc`（PingFang 在 `/System/Library/AssetsV2/.../AssetData/PingFang.ttc`，不在 `/System/Library/Fonts` 根目录，`fc-list` 才找得到）。先 `pip install fonttools`，从 ttc 抽**单字重** `.ttf`（避免 libass 字重歧义）：

     ```python
     from fontTools.ttLib import TTCollection
     col = TTCollection("/System/Library/AssetsV2/.../PingFang.ttc")
     # 选 family=='PingFang SC' 且 style 含 Regular/Medium 的 face
     col.fonts[i].save("/tmp/.../fonts/PingFangSC.ttf")
     ```
     抽前用 `getBestCmap()` 核对要用到的符号（₀₁₂₃ ² √ ⁄ − ×·÷ ½ ∶）确实在字形集里，否则出方块。
   - **烧录滤镜**（路径别有空格，放 `/tmp` 下；filtergraph 空格转义坑）：

     ```
     subtitles=<srt>:fontsdir=<字体目录>:force_style='FontName=PingFang SC,FontSize=40,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=3,Shadow=1,Alignment=2,MarginV=70,PlayResX=1920,PlayResY=1080'
     ```
     **必须显式 `PlayResX/Y=1920,1080`**：libass 默认脚本分辨率低，否则字号被异常放大。`scale=1920:1080:flags=lanczos` 前置。
4. `concat -c copy` 所有分段 → `final.mp4`。每段统一 `libx264 -crf 18 -preset medium` + `aac 192k`。

## 阶段 5 — 质检（必做）

```bash
FF=.../ffmpeg; FP=.../ffprobe
$FP -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height -of default=nw=1 final.mp4
# 停顿数 = 设计的交互页数（本片 7）：
$FF -i final.mp4 -af "silencedetect=noise=-40dB:d=1.5" -f null - 2>&1 | grep -c "silence_start"
```
- 规格应 1080p、预期时长、停顿数恰好 = 交互页数、无其他 >2.2s 静音（查漏配）。
- 抽几帧（`-ss` + `-frames:v 1`）目检公式页、字幕、暂停提示画面。
- 之前还逐页用无头浏览器测过溢出/控制台报错，正式交付前可复跑。

## 配套资源（本技能自带）

- `assets/templates/courseware-example.html` — 真实 33 页讲解课件，看 `data-narration`/`autohide`/MathJax/溢出控制怎么写。
- `assets/examples/script.json` `meta.json` `timing.json` — 三种中间 JSON 的格式范本。
- `assets/examples/subtitle-example.srt` — 切句后的字幕格式范本（多 cue、按字数分摊时长）。
- `assets/examples/knowledge_map.svg` — 知识地图的**手写 SVG 源稿**范本（见下）。

## 关键坑速查

| 坑 | 现象 | 解法 |
|---|---|---|
| `data-narration` 内半角 `"` | 属性提前截断，整页旁白丢失 | 用中文引号；抽取后 `grep` 一下确保 33 段都在 |
| MathJax 同块两个 `\tag` | "Multiple \tag" | 改用 `\;\;(1)` 内联标号 |
| 截图 `networkidle` | 永远超时 | 改 `load` + 等 MathJax ready（15s 兜底） |
| 全量重截 33 页 | 卡死/被超时杀掉 | 单页改了只重截那页（图片页用 `shoot3.js`） |
| 长字幕被裁 | libass 不自动换行中文 | 按标点切 ≤36 字短句；`PlayResX/Y=1920,1080` |
| 字幕字体缺中文/字重乱 | 方块或字形错 | fonttools 从 PingFang.ttc 抽单字重 ttf |
| 滤镜路径含空格 | filtergraph 转义失败 | 素材放 `/tmp` 无空格目录 |
| 知识地图用 mermaid | 箭头压框、斜线穿框 | 弃 mermaid **手写 SVG 逐坐标控制**（直角走线+侧边汇流线，箭头离框 6px），playwright `deviceScaleFactor:2` 渲染 PNG |
