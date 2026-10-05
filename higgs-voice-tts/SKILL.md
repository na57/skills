---
name: "higgs-voice-tts"
description: "用 Higgs 大模型做中文 TTS 并克隆固定音色（默认样本：云南大学「听力训练」在用的那把男声）。当用户要文字转语音、中文配音、生成旁白/讲稿音频、批量合成 mp3、或抱怨 AI 配音音色每次都不一样、要求音色稳定统一时使用。Trigger: TTS / 文字转语音 / 配音 / 旁白 / 音色克隆 / voice clone / text to speech / 讲稿转音频。"
agent_created: true
---

# Higgs 音色克隆 TTS

把文本合成为**音色固定**的中文 mp3。默认音色样本随技能自带
（`assets/3-higgs-平台听力训练在用.mp3`），拷贝本技能目录到任何机器都能直接用。

## 何时使用

- 用户要「把这段文字转成语音 / 配个音 / 生成旁白 / 讲稿转 mp3」
- 批量生成多段音频，且**要求多段之间是同一个人**（视频配音、课件、有声书）
- 用户反馈「语音音色每次都变」「一句一个声」——这就是 Higgs 没传参考音频的典型症状

## 何时不用

- 需要方言或特定角色音（本网关 Qwen3-TTS 分支有方言音色，见「备选模型」）
- 单句试听、音色无所谓 → 直接调网关即可，不必走本技能

## 快速开始

```bash
SK=~/.workbuddy/skills/higgs-voice-tts

# 1. 冒烟：确认网关 + 音色样本都正常（生成一句，打印时长）
python3 $SK/scripts/tts.py --selftest

# 2. 单句
python3 $SK/scripts/tts.py "欢迎使用 IT 资产中心。" -o out.mp3

# 3. 批量（推荐：长稿拆成多条，出片更稳、时长更好控）
#    script.json = [{"id":"s1","text":"……"}, …]
python3 $SK/scripts/tts.py --batch script.json -d audio/ --timing timing.json

# 4. 客观校验音色有没有真的克隆上
python3 $SK/scripts/verify_voice.py $SK/assets/3-higgs-平台听力训练在用.mp3 audio/*.mp3
```

脚本零第三方依赖（Python 3.9+ 即可，时长探测优先用 ffprobe，没有则走内置
MP3 帧解析）。`verify_voice.py` 需要 numpy 与 ffmpeg。

## 三条硬约束（踩过的坑，别再试错）

1. **必须传参考音频。** Higgs 的 `voice` 只有 `default` 一个值，不给 `ref_audio`
   时每次合成都从分布里采样一个人 → 一批音频里好几个人的声音。
2. **参数名必须是 `ref_audio` / `ref_text`。** 写成 `reference_audio`、
   `speaker_wav`、`audio_prompt` 之类**不会报错**，网关静默忽略并照常返回 200——
   你以为克隆了，其实没有。改完参数务必用 `verify_voice.py` 量一次。
3. **`ref_audio` 必须是 data URI**：`data:audio/mpeg;base64,<base64>`。
   传裸 base64 或本地文件路径 → 400。

批量生成还会偶发 `urlopen error EOF ... _ssl.c` —— 脚本内置 3 次退避重试，
看到「重试 1/3」是正常的，只有连续失败才需要处理。

## 默认音色样本

| 项 | 值 |
| --- | --- |
| 文件 | `assets/3-higgs-平台听力训练在用.mp3`（50 KB，约 6 秒） |
| 来源 | 云南大学信息技术中心「听力训练」应用在用的男声 |
| 样本原文 | 云南大学信息技术中心依托自主研发的三A平台，建成校园网IT资产全息图谱，覆盖全校215个信息系统、7228项资产。 |
| 样本 F0 | 205.1 Hz |

换样本时：`--ref-audio 新样本.mp3 --ref-text "新样本的逐字原文"`。
**ref_text 必须给且与音频内容逐字对应**，克隆质量高度依赖它；不传也能出声，
但音色相似度和稳定性都下降。样本要求：3–10 秒、单人、无背景音乐、无噪声。

## 网关与参数

| 项 | 值 |
| --- | --- |
| endpoint | `https://new-api-itc.ynu.edu.cn/v1/audio/speech`（环境变量 `YNU_NEW_API_ENDPOINT` 覆盖，可选） |
| key | 必填，环境变量 `YNU_NEW_API_KEY`（本机已配置于 `~/.zshrc`） |
| model | `bosonai/higgs-audio-v3-tts-4b` |
| voice | `default`（唯一有效值） |
| 输出 | mp3，`response_format: "mp3"` |

请求体：

```json
{
  "model": "bosonai/higgs-audio-v3-tts-4b",
  "input": "要合成的文本",
  "voice": "default",
  "response_format": "mp3",
  "ref_audio": "data:audio/mpeg;base64,....",
  "ref_text": "样本音频的逐字原文"
}
```

## 校验标准（verify_voice.py）

比较各条音频的基频中位数：

- 标准差 **< 8 Hz** → 克隆生效，音色统一（实测成片 3–6 Hz）
- 标准差 **> 15 Hz** → 音色在随机漂移，检查 ref_audio 是否真的传上去了
- 成片整体比样本低 **5–20 Hz 属正常**（语速语调不同），不代表音色变了

## 备选模型（同网关）

- `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`：`voice=dylan` 北京普通话男声、
  `uncle_fu` 成熟男声；**`eric` 是四川话，做普通话配音别用**。
  这个分支不需要 ref_audio，音色本身就固定，但自然度不如 Higgs 克隆。
- 同网关另一个 `aigc-api.ynu.edu.cn`（CosyVoice）历史上有 502，优先用 new-api-itc。

## 文本预处理（影响自然度）

- 合并换行与多余空格为连续文本；单条建议 ≤ 800 字，超过按句号拆成多条批量生成
- 中英文、数字与中文之间留一个空格（`IT 资产中心`、`覆盖 215 个系统`）
- 用中文标点，删重复标点；不要写括号注释、列表符号（会被念出来）

## 故障排查

| 现象 | 原因 / 处理 |
| --- | --- |
| HTTP 400 | ref_audio 不是 data URI，或字段名拼错 |
| 音色每句都变 | ref_audio 没传上去（字段名错会静默忽略），或误加了 `--no-ref` |
| 音色不像样本 | ref_text 缺失或与音频不符；样本有背景音/噪音/多人声 |
| 文本被截断 | 单条太长，拆句批量生成 |
| `EOF occurred in violation of protocol` | 网关偶发 SSL 断连，脚本自动重试 |
| 测不出 F0 | 音频太短或几乎无声，换一条更长的测 |

## 文件

- `scripts/tts.py` —— 合成主脚本（单句 / 批量 / 文本件 / `--selftest` / `--probe`）
- `scripts/verify_voice.py` —— F0 一致性校验（需 numpy + ffmpeg）
- `assets/3-higgs-平台听力训练在用.mp3` —— 默认音色样本
- `references/网关探明记录.md` —— 当初试错过程（含 F0 实验数据），改脚本前建议先看

## 相关技能

- 做「HTML 演示稿 + 录屏 + 旁白 + 合成视频」的完整片子，用 `narrated-demo-video`；
  本技能只负责其中的 TTS 环节，两者配合。
- **中文 TTS 一律用本技能，不要再建/用别的 TTS 技能。** 原 `tts-generator`
  （CosyVoice / `aigc-api.ynu.edu.cn` / 音色 longanyang、longanhuan）已于 2026-10-04
  废弃：该网关长期 502，音色也不如 Higgs 克隆。其原文存档在
  `references/旧技能存档-tts-generator-CosyVoice.md`，仅作历史参考。
