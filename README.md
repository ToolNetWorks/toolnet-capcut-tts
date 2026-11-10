# ToolNet CapCut TTS

**SDK Python và CLI độc lập cho các quy trình Text-to-Speech (TTS), Speech-to-Text (STT), dịch phụ đề và SRT trên CapCut Common Task API.**

[English](README.en.md) · [简体中文](README.zh-CN.md)

---

## Giới thiệu

ToolNet CapCut TTS là một dự án Python độc lập, phát hành theo giấy phép MIT.
Dự án cung cấp:

- thư viện Python để tạo và theo dõi task TTS, tải audio trả về;
- upload media lên VOD, gửi task STT, nhận dạng lời nói;
- dịch phụ đề trong cùng luồng STT nếu dịch vụ hỗ trợ;
- đọc/ghi SRT, tạo audio theo từng cue hoặc một audio gộp;
- catalog giọng đọc và mã ngôn ngữ đi kèm package;
- CLI đầy đủ cho các thao tác thường dùng.

> **Lưu ý:** Đây là dự án độc lập, không phải sản phẩm chính thức của CapCut,
> ByteDance hay bất kỳ bên thứ ba nào. API được sử dụng là endpoint quan sát
> được từ ứng dụng CapCut; dịch vụ có thể thay đổi, giới hạn khu vực hoặc yêu
> cầu thông tin xác thực mà không báo trước. Hãy kiểm tra quyền sử dụng dịch vụ
> và nội dung trước khi triển khai thực tế.

## Tính năng

| Nhóm | Chức năng |
| --- | --- |
| TTS | Tạo task, poll trạng thái, tải artifact MP3 |
| STT | Upload media, nhận dạng, lấy timing câu và từ |
| Dịch | Bật `use_translation`, ghi SRT đã dịch |
| SRT | Đọc SRT, tạo audio từng cue, tạo audio gộp |
| Catalog | Danh sách giọng đọc, resolve voice, danh sách ngôn ngữ |
| SDK | `CapCutClient`, dataclass, exception công khai |
| CLI | 11 chế độ, hỗ trợ `--dry-run`, xuất JSON |
| Tương thích | Giữ import cũ `capcut_tts_api` bên cạnh package mới |

## Yêu cầu

- Python **3.9+**
- `requests>=2.25.0`
- Kết nối mạng tới endpoint CapCut nếu muốn gọi dịch vụ thật
- Không bắt buộc ffmpeg: việc tạo audio gộp do dịch vụ thực hiện

## Cài đặt

### Từ PyPI (khuyến nghị)

```bash
python -m pip install --upgrade pip
python -m pip install toolnet-capcut-tts
```

Bản phát hành chính thức: <https://pypi.org/project/toolnet-capcut-tts/>.

### Từ source

```bash
git clone https://github.com/ToolNetWorks/toolnet-capcut-tts.git
cd toolnet-capcut-tts

python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell

python -m pip install --upgrade pip
python -m pip install -e .
```

### Cài kèm công cụ phát triển

```bash
python -m pip install -e ".[dev]"
```

### Kiểm tra cài đặt

```bash
toolnet-capcut-tts --version
toolnet-capcut-tts --help
python -c "import toolnet_capcut_tts; print(toolnet_capcut_tts.__version__)"
```

## Bắt đầu nhanh

### 1. Tạo client và xem giọng đọc

```python
from toolnet_capcut_tts import CapCutClient

client = CapCutClient(timeout=60)

# Catalog cục bộ, không gọi mạng.
for voice in client.list_voices(lang="vi-VN")[:5]:
    print(voice.voice_type, voice.display_name, voice.resource_id)

voice_type, resource_id = client.resolve_voice("BV421_vivn_streaming")
print(voice_type, resource_id)
```

`list_voices()` đọc `Voice.json` đi kèm package. Catalog có thể cũ; quyền dùng
voice thực tế vẫn do dịch vụ và tài khoản quyết định.

### 2. Xem danh sách ngôn ngữ

```python
from toolnet_capcut_tts import CapCutClient

client = CapCutClient()
print(client.list_language_categories())
print(client.list_languages(category="tts_catalog_languages"))
print(client.list_languages(category="media_asr_exact_observed"))
```

Các nhóm ngôn ngữ phản ánh phạm vi bằng chứng khác nhau:

- `tts_catalog_languages`: ngôn ngữ có trong catalog TTS;
- `media_asr_exact_observed`: mã ASR quan sát được;
- `media_asr_lowercase_aliases_observed`: alias chữ thường;
- `draft_subtitle_language_examples`: ví dụ ngôn ngữ phụ đề;
- `draft_translate_target_examples`: ví dụ ngôn ngữ đích;
- `ui_locales_observed`: locale giao diện.

Đây không phải danh sách đầy đủ mọi ngôn ngữ mà dịch vụ hỗ trợ.

### 3. Tạo giọng nói và lưu file

```python
from toolnet_capcut_tts import CapCutClient

client = CapCutClient(timeout=60)
result = client.generate_speech(
    "Xin chào từ ToolNet CapCut TTS.",
    voice="BV421_vivn_streaming",
    timeout=180,
)
audio_path = client.download_tts_audio(result, "hello.mp3")
print(f"Đã lưu: {audio_path}")
```

Mặc định `generate_speech()` chờ task hoàn tất. Dùng `wait=False` nếu muốn tự
quản lý polling:

```python
created = client.generate_speech(
    "Task đang chờ",
    voice="BV421_vivn_streaming",
    wait=False,
)
task = created["data"]["tasks"][0]

import time

deadline = time.monotonic() + 180
while time.monotonic() < deadline:
    completed = client.query_tts_task(
        task["id"], task["token"], task.get("bind_id", "")
    )
    status = (completed.get("data", {}).get("tasks") or [{}])[0].get("status", "")
    if status.lower() in {"success", "succeed", "succeeded", "completed", "done"}:
        break
    if status.lower() in {"failed", "failure", "error", "cancelled", "canceled"}:
        raise RuntimeError(f"TTS task lỗi: {completed}")
    time.sleep(1)
else:
    raise TimeoutError("TTS task chưa hoàn thành trong thời hạn")

audio_path = client.download_tts_audio(completed, "queued-task.mp3")
print(status, audio_path)
```

### 4. Nhận dạng file và ghi SRT

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

`transcribe_file()` upload media, tạo task STT, poll và trả response hoàn tất.
Dùng `wait=False` để nhận response tạo task.

### 5. Dịch và ghi SRT đã dịch

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

Bản dịch lấy từ trường `translation_text` do dịch vụ trả về. Nếu dịch vụ không
trả trường này, SDK không tự tạo bản dịch.

### 6. Tạo audio từ SRT

```python
# Một artifact cho mỗi cue không rỗng.
parts = client.generate_speech_from_srt(
    "captions.srt",
    voice="BV421_vivn_streaming",
    output_dir="voice-parts",
    part=True,
)
print(parts["cues"])

# Một request với toàn bộ text, một artifact audio gộp.
combined = client.generate_speech_from_srt(
    "captions.srt",
    voice="BV421_vivn_streaming",
    audio_path="captions.mp3",
    part=False,
)
print(combined["audio_path"])
```

Thời gian bắt đầu/kết thúc của cue được giữ trong metadata trả về. Chế độ
`part=False` gửi text đã gộp cho dịch vụ và không tự ghép từng file MP3 cục bộ;
do đó audio gộp không đảm bảo khớp chính xác timing từng cue. Nếu cần đồng bộ
theo cue, dùng `part=True`.

### 7. TTS rồi STT trên cùng một file

```python
result = client.generate_speech_and_transcribe(
    "Xin chào từ ToolNet CapCut TTS.",
    voice="BV421_vivn_streaming",
    audio_path="roundtrip.mp3",
    srt_path="roundtrip.srt",
    language="vi-VN",
)
print(result["audio_path"], result["srt_path"])
```

## Python API

### `CapCutClient`

```python
from toolnet_capcut_tts import CapCutClient

client = CapCutClient(
    device=None,          # DeviceConfig, dict, hoặc đường dẫn JSON
    session=None,         # requests.Session tùy chọn
    base_url=None,        # mặc định CAPCUT_BASE_URL hoặc endpoint quan sát được
    headers=None,         # header bổ sung
    timeout=60.0,         # timeout HTTP mặc định (giây)
)
```

Các phương thức chính:

| Phương thức | Mô tả |
| --- | --- |
| `list_voices(lang=None, catalog_path=None)` | Liệt kê voice từ catalog |
| `resolve_voice(voice=None, resource_id=None)` | Resolve voice type và resource ID |
| `load_language_catalog()` | Đọc toàn bộ catalog ngôn ngữ |
| `list_language_categories()` | Liệt kê nhóm ngôn ngữ |
| `list_languages(category=...)` | Liệt kê mã ngôn ngữ theo nhóm |
| `build_tts_new_request(...)` | Tạo request TTS, không gửi |
| `create_tts_task(...)` | Gửi request tạo task TTS |
| `generate_speech(...)` | Tạo task và poll tới khi xong |
| `query_tts_task(...)` | Truy vấn task TTS |
| `extract_tts_artifacts(response)` | Lấy metadata artifact |
| `download_tts_audio(response, path)` | Tải artifact audio |
| `upload_audio(path)` | Upload media lên VOD |
| `build_stt_new_request(...)` | Tạo request STT, không gửi |
| `create_stt_task(...)` | Gửi request tạo task STT |
| `transcribe_file(...)` | Upload + tạo task + poll STT |
| `query_stt_task(...)` | Truy vấn task STT |
| `extract_subtitles(response)` | Parse utterance/word |
| `write_srt(response, path, ...)` | Ghi SRT nguồn hoặc bản dịch |
| `generate_speech_from_srt(...)` | TTS theo cue hoặc audio gộp |
| `generate_speech_and_transcribe(...)` | TTS rồi STT trên cùng file |

### Request builder và worker

```python
created = client.create_tts_task(
    ["Câu thứ nhất", "Câu thứ hai"],
    voice="BV421_vivn_streaming",
)
task = created["data"]["tasks"][0]

tts_result = client.query_tts_task(
    task_id=task["id"],
    token=task["token"],
    bind_id=task.get("bind_id", ""),
)

for artifact in client.extract_tts_artifacts(tts_result):
    print(artifact)
```

```python
upload = client.upload_audio("recording.mp3")
created = client.create_stt_task(
    audio_vid=upload.vid,
    audio_md5=upload.md5,
    duration_ms=upload.duration_ms,
    language="vi-VN",
    translation_language="en-US",
    use_translation=True,
)
task = created["data"]["tasks"][0]
stt_result = client.query_stt_task(task["id"], task["token"], task.get("bind_id", ""))
subtitles = client.extract_subtitles(stt_result)
subtitles.write_srt("recording.en.srt", use_translation=True)
```

### Tương thích import cũ

Package `capcut_tts_api` được giữ làm facade:

```python
from capcut_tts_api import CapCutClient  # vẫn hoạt động
from capcut_tts_api.models import SubtitleResult
```

API công khai và class name không thay đổi. Đường dẫn CLI cũ
`capcut-tts-api` cũng được giữ làm alias.

## CLI

CLI chính:

```bash
toolnet-capcut-tts --help
toolnet-capcut-tts --version
```

Alias tương thích:

```bash
capcut-tts-api --help
```

Chạy không cần cài console script:

```bash
python -m toolnet_capcut_tts --help
python -m capcut_tts_api --help
```

### Các chế độ

| Chế độ | Mục đích |
| --- | --- |
| `list-voices` | Liệt kê giọng đọc; bỏ `--language` để xem tất cả |
| `list-languages` | Liệt kê mã ngôn ngữ theo nhóm |
| `tts-new` | Tạo request/task TTS từ text |
| `tts-action` | Tạo envelope TTS action cục bộ |
| `tts-srt` | Tạo audio từ file SRT |
| `tts-query` | Truy vấn task TTS |
| `upload-audio` | Upload media lên VOD |
| `stt-new` | Tạo task STT từ vid/md5 đã có |
| `stt-query` | Truy vấn task STT |
| `stt-file` | Upload + tạo + poll STT từ file |
| `translate` | Upload + STT + dịch + ghi SRT |

### Ví dụ

```bash
# Giọng đọc
toolnet-capcut-tts list-voices --language vi-VN
toolnet-capcut-tts list-voices --out voices.json

# Ngôn ngữ
toolnet-capcut-tts list-languages
toolnet-capcut-tts list-languages --language-category media_asr_exact_observed

# TTS: chỉ xem request
toolnet-capcut-tts tts-new \
  --text "Xin chào" \
  --voice BV421_vivn_streaming \
  --dry-run

# TTS: gửi request
toolnet-capcut-tts tts-new \
  --text "Xin chào" \
  --voice BV421_vivn_streaming \
  --out tts-task.json

# TTS từ SRT: mỗi cue một MP3
toolnet-capcut-tts tts-srt \
  --srt-file captions.srt \
  --voice BV421_vivn_streaming \
  --part \
  --output-dir voice-parts

# TTS từ SRT: một audio gộp
toolnet-capcut-tts tts-srt \
  --srt-file captions.srt \
  --voice BV421_vivn_streaming \
  --no-part \
  --audio-out captions.mp3

# STT từ file
toolnet-capcut-tts stt-file \
  --audio-file recording.mp3 \
  --language vi-VN \
  --srt-out recording.srt

# Dịch
toolnet-capcut-tts translate \
  --audio-file recording.mp3 \
  --language vi-VN \
  --translation-language en-US \
  --srt-out recording.en.srt

# Upload và tạo STT riêng
toolnet-capcut-tts upload-audio --audio-file recording.mp3 --out upload.json
toolnet-capcut-tts stt-new \
  --audio-vid VOD_ID \
  --audio-md5 MD5 \
  --duration-ms 10000 \
  --language vi-VN

# Truy vấn task
toolnet-capcut-tts tts-query --task-id TASK_ID --token TASK_TOKEN
toolnet-capcut-tts stt-query --task-id TASK_ID --token TASK_TOKEN
```

Mọi chế độ gửi request đều hỗ trợ `--dry-run` khi có thể dựng request, và
`--out` để ghi JSON kết quả.

## Xác thực và cấu hình

SDK chỉ đọc thông tin xác thực do người dùng cung cấp qua biến môi trường hoặc
header. Package **không** đọc cookie browser hay cơ sở dữ liệu cookie.

| Biến môi trường | Ý nghĩa |
| --- | --- |
| `CAPCUT_BASE_URL` | Ghi đè API origin |
| `CAPCUT_COOKIE` | Cookie header tùy chọn |
| `CAPCUT_BEARER` | Bearer token tùy chọn |
| `CAPCUT_HEADERS_JSON` | JSON object chứa header bổ sung |

Alias cũ `LYRA_TTS_COOKIE`, `LYRA_TTS_BEARER`, `LYRA_TTS_HEADERS_JSON` vẫn được
hỗ trợ.

Ví dụ:

```bash
export CAPCUT_BASE_URL="https://editor-api-sg.capcutapi.com"
export CAPCUT_BEARER="..."
toolnet-capcut-tts list-voices --language vi-VN
```

Không commit token, cookie, API key hoặc file cấu hình chứa bí mật vào Git.

## Lỗi, timeout và retry

- Lỗi HTTP hoặc `ret != 0` được raise thành `CapCutAPIError` kèm
  `status_code` và `response_data`.
- Task thất bại hoặc quá hạn được raise thành `CapCutTaskError`.
- `CapCutClient(timeout=...)` áp dụng cho từng request HTTP.
- `generate_speech(timeout=...)`, `transcribe_file(timeout=...)` và
  `generate_speech_from_srt(timeout=...)` giới hạn tổng thời gian polling.
- SDK hiện không tự retry request. Nếu cần, bọc lời gọi trong vòng lặp của ứng
  dụng và chỉ retry các lỗi mạng/timeout có thể thử lại an toàn.
- `--no-wait` cho phép nhận task ID ngay và tự quản lý polling sau đó.

```python
from toolnet_capcut_tts import CapCutAPIError, CapCutError, CapCutTaskError

try:
    client.generate_speech("test", voice="BV421_vivn_streaming", timeout=180)
except CapCutTaskError as exc:
    print(f"Task lỗi hoặc quá hạn: {exc}")
except CapCutAPIError as exc:
    print(f"Dịch vụ trả lỗi: {exc}")
except CapCutError as exc:
    print(f"Lỗi client: {exc}")
```

## Cấu trúc dự án

```text
toolnet-capcut-tts/
├── toolnet_capcut_tts/      # Package chính
│   ├── action.py            # Envelope TTS action cục bộ
│   ├── cli.py               # CLI
│   ├── client.py            # CapCutClient
│   ├── config.py            # Endpoint và device profile
│   ├── exceptions.py        # Exception công khai
│   ├── models.py            # Dataclass, SRT, catalog voice
│   ├── signer.py            # Header và helper ký request
│   ├── uploader.py          # Upload VOD
│   ├── Voice.json           # Catalog giọng đọc
│   └── language.json        # Catalog ngôn ngữ
├── capcut_tts_api/          # Facade tương thích import cũ
├── tests/                   # Unit test
├── pyproject.toml
├── LICENSE
├── NOTICE
└── README.md
```

## Kiểm thử

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Kiểm tra nhanh không cần dịch vụ:

```bash
python -m compileall -q toolnet_capcut_tts capcut_tts_api
toolnet-capcut-tts --help
toolnet-capcut-tts list-voices --language vi-VN
toolnet-capcut-tts list-languages
toolnet-capcut-tts tts-new --text "Xin chào" --dry-run
```

Các kiểm thử TTS/STT thật cần quyền truy cập dịch vụ và vùng mạng phù hợp.
Kết quả có thể khác nhau theo tài khoản, voice và thời điểm.

## Giới hạn và lưu ý

- Đây là API không chính thức, được quan sát từ ứng dụng; có thể thay đổi.
- Catalog voice/ngôn ngữ chỉ là dữ liệu tham khảo, không đảm bảo quyền truy cập.
- Không phải mọi tài khoản/khu vực đều dùng được mọi voice.
- Audio gộp từ SRT không tự đồng bộ timing từng cue; dùng `part=True` nếu cần.
- Chất lượng dịch phụ thuộc dịch vụ; SDK không tự dịch khi thiếu dữ liệu.
- Không upload nội dung riêng tư hoặc media không có quyền lên dịch vụ bên thứ ba.
- Luôn tuân thủ điều khoản dịch vụ và pháp luật về nội dung, bản quyền, dữ liệu
  cá nhân tại khu vực sử dụng.

## Giấy phép và ghi công

Dự án phát hành theo giấy phép **MIT**. Xem [LICENSE](LICENSE) để biết toàn văn
điều kiện cấp phép và thông báo bản quyền.

Thông tin về tác phẩm gốc, các thay đổi khi tái cấu trúc thương hiệu và việc bảo
toàn thông báo bản quyền được ghi trong [NOTICE](NOTICE).

MIT cho phép sử dụng, sao chép, sửa đổi và phân phối, với điều kiện giữ lại
thông báo bản quyền và điều kiện giấy phép trong bản sao hoặc phần quan trọng
của phần mềm.
