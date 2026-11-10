# ToolNet CapCut TTS

**Independent Python SDK and CLI for CapCut Text-to-Speech (TTS), Speech-to-Text (STT), subtitle translation and SRT workflows.**

[Tiếng Việt](README.md) · [简体中文](README.zh-CN.md)

---

## Overview

ToolNet CapCut TTS is a standalone Python project derived from an MIT-licensed
CapCut speech SDK. It includes:

- a high-level Python client for TTS task creation, polling and audio download;
- VOD media upload and STT task workflows;
- optional subtitle translation during STT;
- SRT parsing and writing;
- per-cue audio generation or one combined audio artifact;
- local voice and language catalogs;
- a complete command-line interface.

> **Disclaimer:** This is an independent project. It is not affiliated with,
> endorsed by, or sponsored by CapCut, ByteDance or any third party. The
> endpoint is observed from the CapCut application and may change without
> notice. Verify service terms, content rights and regional requirements
> before production use.

## Features

| Area | Capability |
| --- | --- |
| TTS | Create tasks, poll status, download MP3 artifacts |
| STT | Upload media, transcribe, extract utterance/word timings |
| Translation | Request translation during STT and write translated SRT |
| SRT | Per-cue audio or one combined audio artifact |
| Catalog | Voice list, voice resolution, language code groups |
| SDK | `CapCutClient`, dataclasses, public exceptions |
| CLI | 11 modes, `--dry-run`, JSON output |
| Compatibility | Legacy `capcut_tts_api` imports remain supported |

## Requirements

- Python **3.9+**
- `requests>=2.25.0`
- Network access to the CapCut endpoint for live API calls
- No ffmpeg requirement; combined SRT audio is produced by the service

## Installation

### From PyPI (recommended)

```bash
python -m pip install --upgrade pip
python -m pip install toolnet-capcut-tts
```

Official release: <https://pypi.org/project/toolnet-capcut-tts/>.

### From source

```bash
git clone https://github.com/ToolNetWorks/toolnet-capcut-tts.git
cd toolnet-capcut-tts

python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell

python -m pip install --upgrade pip
python -m pip install -e .
```

With development tools:

```bash
python -m pip install -e ".[dev]"
```

Verify:

```bash
toolnet-capcut-tts --version
toolnet-capcut-tts --help
python -c "import toolnet_capcut_tts; print(toolnet_capcut_tts.__version__)"
```

## Quick start

### Voices and languages

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

Voice data comes from the packaged `Voice.json` catalog and may be stale.
Service-side availability and account permissions always take precedence.

Language groups represent different evidence scopes (TTS catalog, ASR,
translation examples, UI locales). They are not a claim of exhaustive server
support.

### Text to speech

```python
from toolnet_capcut_tts import CapCutClient

client = CapCutClient(timeout=60)
result = client.generate_speech(
    "Hello from ToolNet CapCut TTS.",
    voice="BV421_vivn_streaming",
    timeout=180,
)
audio_path = client.download_tts_audio(result, "hello.mp3")
print(audio_path)
```

`generate_speech()` waits for completion by default. Use `wait=False` to manage
polling yourself, then call `query_tts_task()` until the status succeeds.

### Speech to text

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

### Translation

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

Translation text comes from the service response. If the service does not
return `translation_text`, the SDK does not invent a translation.

### Audio from SRT

```python
# One artifact per non-empty cue.
parts = client.generate_speech_from_srt(
    "captions.srt",
    voice="BV421_vivn_streaming",
    output_dir="voice-parts",
    part=True,
)

# One service-side combined artifact.
combined = client.generate_speech_from_srt(
    "captions.srt",
    voice="BV421_vivn_streaming",
    audio_path="captions.mp3",
    part=False,
)
```

Cue timings are preserved in the returned metadata. `part=False` sends the
combined text to the service; it does not concatenate local files and does not
guarantee exact per-cue timing.

### TTS then STT

```python
result = client.generate_speech_and_transcribe(
    "Hello from ToolNet CapCut TTS.",
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

Key methods:

| Method | Purpose |
| --- | --- |
| `list_voices` | Read the packaged voice catalog |
| `resolve_voice` | Resolve voice type and resource ID |
| `load_language_catalog` | Read the packaged language catalog |
| `list_language_categories` | List language evidence groups |
| `list_languages` | List codes in one language group |
| `build_tts_new_request` | Build a TTS request without sending it |
| `create_tts_task` | Submit a TTS task |
| `generate_speech` | Submit and poll TTS |
| `query_tts_task` | Query a TTS task |
| `extract_tts_artifacts` | Read artifact metadata |
| `download_tts_audio` | Download a TTS artifact |
| `upload_audio` | Upload media to VOD |
| `build_stt_new_request` | Build an STT request |
| `create_stt_task` | Submit an STT task |
| `transcribe_file` | Upload, submit and poll STT |
| `query_stt_task` | Query an STT task |
| `extract_subtitles` | Parse utterances and words |
| `write_srt` | Write source or translated SRT |
| `generate_speech_from_srt` | Per-cue or combined audio |
| `generate_speech_and_transcribe` | Round-trip TTS to STT |

### Low-level worker example

```python
created = client.create_tts_task(
    ["First sentence", "Second sentence"],
    voice="BV421_vivn_streaming",
)
task = created["data"]["tasks"][0]

result = client.query_tts_task(
    task_id=task["id"],
    token=task["token"],
    bind_id=task.get("bind_id", ""),
)

for artifact in client.extract_tts_artifacts(result):
    print(artifact)
```

### Legacy imports

```python
from capcut_tts_api import CapCutClient
from capcut_tts_api.models import SubtitleResult
```

The legacy package is a compatibility facade over `toolnet_capcut_tts`. Public
class names and method signatures are unchanged.

## CLI

```bash
toolnet-capcut-tts --help
toolnet-capcut-tts --version
```

The legacy `capcut-tts-api` command remains available as an alias.

| Mode | Purpose |
| --- | --- |
| `list-voices` | List voices; omit `--language` for all |
| `list-languages` | List language codes by category |
| `tts-new` | Create a TTS task from text |
| `tts-action` | Build a local TTS action envelope |
| `tts-srt` | Generate audio from an SRT file |
| `tts-query` | Query a TTS task |
| `upload-audio` | Upload media to VOD |
| `stt-new` | Create an STT task from vid/md5 |
| `stt-query` | Query an STT task |
| `stt-file` | Upload, create and poll STT |
| `translate` | Upload, transcribe, translate and write SRT |

Examples:

```bash
toolnet-capcut-tts list-voices --language vi-VN
toolnet-capcut-tts list-languages
toolnet-capcut-tts list-languages --language-category media_asr_exact_observed

toolnet-capcut-tts tts-new \
  --text "Hello" \
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

## Configuration

| Variable | Purpose |
| --- | --- |
| `CAPCUT_BASE_URL` | Override the API origin |
| `CAPCUT_COOKIE` | Optional Cookie header |
| `CAPCUT_BEARER` | Optional bearer token |
| `CAPCUT_HEADERS_JSON` | JSON object with extra headers |

Legacy aliases `LYRA_TTS_COOKIE`, `LYRA_TTS_BEARER` and
`LYRA_TTS_HEADERS_JSON` are also supported.

The SDK does not read browser cookies or cookie databases. Never commit
credentials, cookies or API keys.

## Errors, timeouts and retries

- HTTP errors and non-zero API `ret` values raise `CapCutAPIError`.
- Failed or timed-out tasks raise `CapCutTaskError`.
- The client `timeout` applies to each HTTP request.
- Method-level `timeout` limits total polling time.
- The SDK does not retry requests automatically. Wrap calls in application
  logic and only retry network/timeout errors that are safe to repeat.
- `--no-wait` returns task identifiers immediately for external workers.

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

## Project layout

```text
toolnet-capcut-tts/
├── toolnet_capcut_tts/   # Canonical package
├── capcut_tts_api/       # Legacy import facade
├── tests/                # Unit tests
├── pyproject.toml
├── LICENSE
├── NOTICE
└── README.md
```

## Testing

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Offline smoke checks:

```bash
python -m compileall -q toolnet_capcut_tts capcut_tts_api
toolnet-capcut-tts --help
toolnet-capcut-tts list-voices --language vi-VN
toolnet-capcut-tts list-languages
toolnet-capcut-tts tts-new --text "Hello" --dry-run
```

Live TTS/STT checks require service access, a supported region and a usable
account. Results can vary by account, voice and time.

## Limitations

- The endpoint is unofficial and may change without notice.
- Voice and language catalogs are local reference data, not entitlement data.
- Not every voice is available to every account or region.
- Combined SRT audio does not preserve exact per-cue timing; use `part=True`.
- Translation quality and availability depend on the service.
- Do not upload private or unauthorized media to a third-party service.
- Comply with service terms, copyright and data-protection law.

## License and attribution

Released under the **MIT License**. See [LICENSE](LICENSE) for the full terms
and copyright notices.

See [NOTICE](NOTICE) for provenance, the original copyright notice and a
summary of the rebranding and maintenance changes.
