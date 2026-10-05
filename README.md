# Skills

个人总结的一些 AI Skills，用于各种自动化任务和工具集成。

## Skills 列表

### macOS Calendar Event Creator

**路径**: `macos-calendar-event-creator/SKILL.md`

**功能**: 从自然语言文本中提取日程信息，并生成 AppleScript 代码创建 macOS 日历事件。

**适用场景**:
- 用户用自然语言描述日程（如"明天下午3点开会"）
- 需要将文本转换为 macOS 日历事件
- 自动化日历管理

**核心特性**:
- 智能解析相对时间（明天、下周一、这周末等）
- 自动简化事件标题（提取核心关键词）
- 智能推断默认时间和时长
- 处理已过期日期（自动跨年）
- 生成可直接执行的 AppleScript 代码

**使用要求**:
- 必须提供当前系统日期作为上下文
- 仅适用于 macOS 系统（使用 AppleScript）

**示例**:
```
用户输入: "明天下午3点和张三在会议室A开会讨论项目进度"
系统日期: 2026-03-13

生成 AppleScript:
tell application "Calendar"
    tell calendar "Home"
        make new event with properties {summary:"项目进度会议", start date:date "2026-03-14 15:00:00", end date:date "2026-03-14 16:00:00", description:"与张三讨论项目进度", location:"会议室A"}
    end tell
end tell
```

### make-explainer-video（讲解视频制作流水线）

**路径**: `make-explainer-video/SKILL.md`

**功能**: 把一章/一节的知识点做成「HTML 幻灯片讲解视频」：HTML 课件(PPT) → 抽取旁白 → Higgs 克隆音色配音 → 逐页截图 → 烧入中文字幕 + 推导停顿合成 1080p 视频。

**适用场景**:
- 把一份按页组织的 HTML 课件/讲义做成讲解视频
- 需要**稳定音色**的中文物配音（全片同一把克隆声音）
- 需要**烧入中文字幕**（公式处显示标准记法而非口语稿）
- 需要「暂停推导」类互动（视频真留白，让学生动手）

**核心特性**:
- 阶段化流水线：`extract_narration.py` 抽旁白 → Higgs 批量配音 → Playwright 逐页截图 → `assemble2.py` 拼音频/烧字幕/合成
- 已验证跑通：33 页 / 17.6 分钟 / 1080p25 / 40 段配音 / 7 处推导停顿，全片同一把音色
- 自带模板与示例（`assets/templates/courseware-example.html`、`assets/examples/*`）

**使用要求**:
- 依赖 Python 脚本、Node（Playwright）、ffmpeg、Higgs 配音技能
- 详见 `make-explainer-video/SKILL.md` 的阶段说明与「关键坑速查」

### higgs-voice-tts（Higgs 音色克隆 TTS）

**路径**: `higgs-voice-tts/SKILL.md`

**功能**: 用 Higgs Audio 大模型做中文 TTS，并克隆固定音色（默认样本：云南大学「听力训练」在用的那把男声）。文字转语音、中文配音、生成旁白/讲稿音频、批量合成 mp3。

**适用场景**:
- 中文文字转语音 / 配音 / 旁白
- 需要**稳定统一音色**（多段合成同一把声音，不掉音色）
- 配合 `make-explainer-video` 做讲解视频配音

**核心特性**:
- 音色克隆：传 `ref_audio`（自带 `assets/3-higgs-平台听力训练在用.mp3`）+ `ref_text`，多段之间保持同一把声音
- 批量合成：JSON 输入按 id 落盘，支持 `--force` 重生成、跳过已存在文件断点续跑
- `verify_voice.py` 做 F0 一致性校验（标准差 < 8Hz 判克隆生效）

**使用要求**:
- 依赖 Python、`ffmpeg`/`ffprobe`、Higgs TTS 网关
- **必须设置环境变量 `YNU_NEW_API_KEY`**（网关密钥，不随仓库分发，需自行配置）；可选 `YNU_NEW_API_ENDPOINT` 覆盖网关地址
- 详见 `higgs-voice-tts/SKILL.md`

### wx-miniprogram-page-refresh（微信小程序页面刷新机制）

**路径**: `wx-miniprogram-page-refresh/SKILL.md`

**功能**: 提供微信小程序页面间数据刷新机制的最佳实践——用本地存储标记控制刷新，避免 `onShow` 频繁刷新。

**适用场景**:
- 列表页数据变更后需要刷新
- 详情页数据编辑后需要同步
- 跨页面数据状态同步
- 避免 `onShow` 每次都刷新导致性能浪费

**核心特性**:
- 数据变更页用 `wx.setStorageSync('needRefreshXXX', true)` 打标记，目标页 `onShow` 里检查并立即清除，避免重复刷新
- 标准化命名（`needRefresh` + 驼峰），支持单页 / 多页 / 条件刷新
- 纯小程序原生 API，无额外依赖；自带完整示例与「方案对比」表

**使用要求**:
- 仅适用于微信小程序（JavaScript）
- 详见 `wx-miniprogram-page-refresh/SKILL.md`

## 如何使用

这些 Skills 可以在支持 Skill 系统的 AI 平台上使用，如:
- OpenClaw
- Trae IDE
- 其他兼容的 AI 助手

每个 Skill 都包含在独立的目录中，包含 `SKILL.md` 文件，定义了 Skill 的功能、使用规则和示例。

## 贡献

这些 Skills 是个人工作流的总结，欢迎参考和借鉴。如果你有改进建议，欢迎提交 Issue 或 PR。

## License

MIT License - 自由使用和修改
