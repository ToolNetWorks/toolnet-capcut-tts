# ToolNet CapCut TTS

**独立的 Python SDK 与 CLI，用于 CapCut 文本转语音（TTS）、语音转文本（STT）、字幕翻译和 SRT 工作流。**

[Tiếng Việt](README.md) · [English](README.en.md)

---

## 简介

ToolNet CapCut TTS 是一个独立的 Python 项目，采用 MIT 许可证。项目提供：

- TTS 任务创建、轮询和音频下载；
- VOD 媒体上传和 STT 识别；
- STT 过程中的可选字幕翻译；
- SRT 读取与写入；
- 按字幕 cue 生成音频，或生成一个合并音频；
- 内置语音和语言目录；
- 完整的命令行工具。

> **声明：** 本项目与 CapCut、ByteDance 或任何第三方均无隶属、授权或赞助
> 关系。使用的接口是从 CapCut 应用观察到的非官方接口，可能随时变化。生产
> 使用前请确认服务条款、内容授权和地区要求。

## 功能

| 模块 | 功能 |
| --- | --- |
| TTS | 创建任务、轮询状态、下载 MP3 |
| STT | 上传媒体、识别语音、提取句子和词级时间 |
| 翻译 | STT 时请求翻译并写入 SRT |
| SRT | 按 cue 输出音频或输出合并音频 |
| 目录 | 语音列表、语音解析、语言代码分组 |
| SDK | `CapCutClient`、数据类、公开异常 |
| CLI | 11 种模式，支持 `--dry-run` 和 JSON 输出 |
| 兼容 | 保留旧版 `capcut_tts_api` 导入路径 |

## 环境要求

- Python **3.9+**
- `requests>=2.25.0`
- 调用真实接口时需要能访问 CapCut 端点
- 不需要 ffmpeg；合并音频由服务端生成

## 安装

### 从 PyPI 安装（推荐）

```bash
python -m pip install --upgrade pip
python -m pip install toolnet-capcut-tts
```

正式发布页：<https://pypi.org/project/toolnet-capcut-tts/>。

### 从源码安装

```bash
git clone https://github.com/ToolNetWorks/toolnet-capcut-tts.git
cd toolnet-capcut-tts

python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

验证：

```bash
toolnet-capcut-tts --version
toolnet-capcut-tts --help
python -c "import toolnet_capcut_tts; print(toolnet_capcut_tts.__version__)"
```

## 快速开始

### 语音和语言

```python
from toolnet_capcut_tts import CapCutClient

client = CapCutClient(timeout=60)

for voice in client.list_voices(lang="vi-VN")[:5]:
    print(voice.voice_type, voice.display_name, voice.resource_id)

voice_type, resource_id = client.resolve_voice("BV421_vivn_streaming")
print(voice_type, resource_id)

print(client.list_language_categories())
print(client.list_languages(category="tts_catalog_languages"))
```

语音目录来自包内 `Voice.json`，可能过期。实际可用性由服务和账号权限决定。
语言分组代表不同的证据范围，不代表服务端支持所有语言。

### 文本转语音

```python
from toolnet_capcut_tts import CapCutClient

client = CapCutClient(timeout=60)
result = client.generate_speech(
    "你好，这是 ToolNet CapCut TTS。",
    voice="BV421_vivn_streaming",
    timeout=180,
)
audio_path = client.download_tts_audio(result, "hello.mp3")
print(audio_path)
```

默认等待任务完成。使用 `wait=False` 可自行调用 `query_tts_task()` 轮询。

### 语音转文本

```python
from toolnet_capcut_tts import CapCutClient

client = CapCutClient(timeout=60)
stt = client.transcribe_file(
    "recording.mp3",
    language="vi-VN",
    timeout=180,
)
subtitles = client.extract_subtitles(stt)
subtitles.write_srt("recording.vi.srt")
print(subtitles.full_text)
```

### 翻译字幕

```python
translated = client.transcribe_file(
    "recording.mp3",
    language="vi-VN",
    translation_language="en-US",
    use_translation=True,
    timeout=180,
)
client.write_srt(translated, "recording.en.srt", use_translation=True)
```

翻译文本来自服务响应。如果服务未返回 `translation_text`，SDK 不会伪造翻译。

### 从 SRT 生成音频

```python
# 每个非空 cue 生成一个音频文件。
parts = client.generate_speech_from_srt(
    "captions.srt",
    voice="BV421_vivn_streaming",
    output_dir="voice-parts",
    part=True,
)

# 发送合并文本，生成一个服务端音频。
combined = client.generate_speech_from_srt(
    "captions.srt",
    voice="BV421_vivn_streaming",
    audio_path="captions.mp3",
    part=False,
)
```

返回的元数据保留 cue 时间。`part=False` 不会在本地拼接文件，也不保证与每个
cue 的时间完全同步；需要精确同步时使用 `part=True`。

### TTS 后再 STT

```python
result = client.generate_speech_and_transcribe(
    "你好，这是 ToolNet CapCut TTS。",
    voice="BV421_vivn_streaming",
    audio_path="roundtrip.mp3",
    srt_path="roundtrip.srt",
    language="vi-VN",
)
```

## Python API

```python
from toolnet_capcut_tts import CapCutClient

client = CapCutClient(
    device=None,
    session=None,
    base_url=None,
    headers=None,
    timeout=60.0,
)
```

主要方法：

| 方法 | 说明 |
| --- | --- |
| `list_voices` | 读取语音目录 |
| `resolve_voice` | 解析 voice type 和 resource ID |
| `load_language_catalog` | 读取语言目录 |
| `list_language_categories` | 列出语言分组 |
| `list_languages` | 列出指定分组的语言代码 |
| `build_tts_new_request` | 构建 TTS 请求 |
| `create_tts_task` | 创建 TTS 任务 |
| `generate_speech` | 创建并轮询 TTS |
| `query_tts_task` | 查询 TTS 任务 |
| `extract_tts_artifacts` | 提取音频元数据 |
| `download_tts_audio` | 下载音频 |
| `upload_audio` | 上传媒体到 VOD |
| `build_stt_new_request` | 构建 STT 请求 |
| `create_stt_task` | 创建 STT 任务 |
| `transcribe_file` | 上传、创建并轮询 STT |
| `query_stt_task` | 查询 STT 任务 |
| `extract_subtitles` | 解析句子和词级时间 |
| `write_srt` | 写入原文或翻译 SRT |
| `generate_speech_from_srt` | 按 cue 或合并生成音频 |
| `generate_speech_and_transcribe` | TTS 后 STT 往返 |

### 旧版导入

```python
from capcut_tts_api import CapCutClient
from capcut_tts_api.models import SubtitleResult
```

`capcut_tts_api` 是兼容层，公开类名和方法签名保持不变。

## CLI

```bash
toolnet-capcut-tts --help
toolnet-capcut-tts --version
```

旧命令 `capcut-tts-api` 仍作为别名可用。

| 模式 | 用途 |
| --- | --- |
| `list-voices` | 列出语音；省略 `--language` 显示全部 |
| `list-languages` | 按分组列出语言代码 |
| `tts-new` | 从文本创建 TTS 任务 |
| `tts-action` | 构建本地 TTS action |
| `tts-srt` | 从 SRT 生成音频 |
| `tts-query` | 查询 TTS 任务 |
| `upload-audio` | 上传媒体到 VOD |
| `stt-new` | 使用 vid/md5 创建 STT 任务 |
| `stt-query` | 查询 STT 任务 |
| `stt-file` | 上传、创建并轮询 STT |
| `translate` | 上传、识别、翻译并写入 SRT |

示例：

```bash
toolnet-capcut-tts list-voices --language vi-VN
toolnet-capcut-tts list-languages
toolnet-capcut-tts list-languages --language-category media_asr_exact_observed

toolnet-capcut-tts tts-new \
  --text "你好" \
  --voice BV421_vivn_streaming \
  --dry-run

toolnet-capcut-tts tts-srt \
  --srt-file captions.srt \
  --voice BV421_vivn_streaming \
  --part \
  --output-dir voice-parts

toolnet-capcut-tts tts-srt \
  --srt-file captions.srt \
  --voice BV421_vivn_streaming \
  --no-part \
  --audio-out captions.mp3

toolnet-capcut-tts stt-file \
  --audio-file recording.mp3 \
  --language vi-VN \
  --srt-out recording.srt

toolnet-capcut-tts translate \
  --audio-file recording.mp3 \
  --language vi-VN \
  --translation-language en-US \
  --srt-out recording.en.srt
```

## 配置

| 环境变量 | 用途 |
| --- | --- |
| `CAPCUT_BASE_URL` | 覆盖 API origin |
| `CAPCUT_COOKIE` | 可选 Cookie |
| `CAPCUT_BEARER` | 可选 Bearer token |
| `CAPCUT_HEADERS_JSON` | 附加 header 的 JSON 对象 |

同时兼容旧变量 `LYRA_TTS_COOKIE`、`LYRA_TTS_BEARER` 和
`LYRA_TTS_HEADERS_JSON`。

SDK 不读取浏览器 cookie 或 cookie 数据库。请勿提交凭据、cookie 或 API key。

## 错误、超时与重试

- HTTP 错误或 API `ret != 0` 会抛出 `CapCutAPIError`。
- 任务失败或超时会抛出 `CapCutTaskError`。
- 客户端 `timeout` 作用于每次 HTTP 请求。
- 方法级 `timeout` 限制总轮询时间。
- SDK 不会自动重试。请在应用层只重试安全的网络或超时错误。
- `--no-wait` 可立即返回任务标识，适合外部 worker。

```python
from toolnet_capcut_tts import CapCutAPIError, CapCutError, CapCutTaskError

try:
    client.generate_speech("test", voice="BV421_vivn_streaming", timeout=180)
except CapCutTaskError as exc:
    print(f"task failed or timed out: {exc}")
except CapCutAPIError as exc:
    print(f"service error: {exc}")
except CapCutError as exc:
    print(f"client error: {exc}")
```

## 项目结构

```text
toolnet-capcut-tts/
├── toolnet_capcut_tts/   # 主包
├── capcut_tts_api/       # 旧版导入兼容层
├── tests/                # 单元测试
├── pyproject.toml
├── LICENSE
├── NOTICE
└── README.md
```

## 测试

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

离线检查：

```bash
python -m compileall -q toolnet_capcut_tts capcut_tts_api
toolnet-capcut-tts --help
toolnet-capcut-tts list-voices --language vi-VN
toolnet-capcut-tts list-languages
toolnet-capcut-tts tts-new --text "你好" --dry-run
```

真实 TTS/STT 测试需要可用的服务访问、地区网络和账号。结果会随账号、语音和
时间变化。

## 限制

- 非官方接口，可能随时变化。
- 语音和语言目录只是本地参考，不代表账号权限。
- 并非所有账号或地区都能使用所有语音。
- 合并 SRT 音频不保留精确的逐 cue 时间；需要时使用 `part=True`。
- 翻译质量和可用性取决于服务。
- 请勿向第三方服务上传隐私或未授权媒体。
- 遵守服务条款、版权和个人数据保护法律。

## 许可证与署名

本项目使用 **MIT License** 发布。完整条款和版权声明见 [LICENSE](LICENSE)。

原始版权声明、重构说明和品牌化记录见 [NOTICE](NOTICE)。
