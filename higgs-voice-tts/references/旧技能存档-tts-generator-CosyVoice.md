---
name: "tts-generator"
description: "使用 CosyVoice TTS API 将文本转换为音频。Invoke when user wants to convert text to speech, generate audio from text, or create voice files from written content."
---

# TTS 音频生成器

使用 CosyVoice TTS API 将文本转换为高质量音频文件。

## 何时使用

- 用户需要将文本转换为音频
- 用户想要生成语音文件
- 用户需要为讲稿、文档生成配音
- 用户要求使用 TTS 或语音合成

## 使用方法

### 1. 文本预处理（使用大模型能力）

在调用 API 之前，必须对输入文本进行以下优化：

**规则 1：移除多余换行符**
- 将所有 `\n\n`（段落分隔）替换为句号 `。`
- 将所有单个 `\n` 直接移除，合并为连续文本
- 保持语义连贯，不要在句子中间断开

**规则 2：规范化空格**
- 将多个连续空格合并为单个空格
- 移除文本首尾的空格
- 删除制表符 `\t` 等特殊空白字符

**规则 3：中英文混排处理**
- 确保中文和英文单词之间有且仅有一个空格
- 例如："GraphRAG 课程"（正确）而非 "GraphRAG课程"（错误）
- 数字与中文之间也保持一个空格

**规则 4：标点符号规范化**
- 使用中文标点符号（，。：；？！）
- 将英文引号 `""` 转换为中文引号 `「」`
- 移除连续的重复标点（如 `。。` 改为 `。`）
- 确保每个句子结束都有适当的标点

**规则 5：段落结构优化**
- 将文本组织为流畅的段落
- 避免过长的句子（超过 50 字考虑拆分）
- 保持逻辑段落的完整性

### 2. API 调用参数

```python
API_URL = "https://aigc-api.ynu.edu.cn/api/v1/audio/speech"
API_KEY = os.environ.get("YNU_NEW_API_KEY")  # 旧 CosyVoice 网关密钥，从环境变量读取，勿硬编码

payload = {
    "model": "cosyvoice-v3-plus",  # 可用模型
    "input": optimized_text,        # 优化后的文本
    "voice": "longanyang",          # 默认音色（龙安阳）
    "response_format": "mp3"
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
```

### 3. 可用音色

- `longanyang` - 龙安阳（推荐，男声）
- `longanhuan` - 龙安欢（女声）

### 4. 输出设置

- 输出格式：MP3
- 音质：160 kbps, 24 kHz, 单声道
- 建议文件名：`{prefix}-{page}.mp3`

## 示例

### 输入文本（原始）
```
大家好，我是三分钟。

欢迎来到 GraphRAG 课程。

我是这门课程的导读者。
```

### 优化后文本
```
大家好，我是三分钟。欢迎来到 GraphRAG 课程。我是这门课程的导读者。
```

### 完整调用示例

```python
import requests

def generate_audio(text, output_path, api_key, voice="longanyang"):
    """生成音频文件"""
    
    # 步骤 1: 文本优化（使用大模型能力）
    optimized_text = optimize_text_for_tts(text)
    
    # 步骤 2: 调用 API
    response = requests.post(
        "https://aigc-api.ynu.edu.cn/api/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "cosyvoice-v3-plus",
            "input": optimized_text,
            "voice": voice,
            "response_format": "mp3"
        },
        timeout=60
    )
    
    # 步骤 3: 保存文件
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    else:
        raise Exception(f"API 错误: {response.status_code}")

def optimize_text_for_tts(text):
    """
    使用大模型能力优化文本格式
    
    规则：
    1. 移除多余换行符，合并为连续文本
    2. 规范化空格
    3. 确保中英文之间只有一个空格
    4. 使用中文标点符号
    5. 保持段落流畅
    """
    # 实现文本优化逻辑...
    pass
```

## 注意事项

1. **文本长度**：单次请求建议不超过 1000 字符
2. **API Key**：需要用户提供有效的 API Key
3. **网络超时**：设置合理的超时时间（建议 60 秒）
4. **错误处理**：API 可能返回 500 错误，需要重试机制
5. **文件保存**：确保输出目录存在且有写入权限

## 常见问题

**Q: 音频有卡顿或杂音？**
A: 检查文本是否包含多余换行符或不规范空格，重新优化文本后生成。

**Q: 中英文混读不自然？**
A: 确保中英文之间有且仅有一个空格，使用正确的标点符号。

**Q: 生成失败？**
A: 检查 API Key 是否有效，网络连接是否正常，文本长度是否过长。
