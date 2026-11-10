"""
ToolNet CapCut TTS - Python SDK cho CapCut TTS, STT và quy trình upload VOD.

Package cung cấp client Python thuần cho các tác vụ:
- Text-to-Speech (TTS) và tải artifact audio.
- Speech-to-Text (STT), nhận dạng và dịch phụ đề.
- Đọc/ghi SRT, tạo audio theo từng cue hoặc audio gộp.
- Tra cứu catalog giọng đọc và ngôn ngữ đi kèm package.
"""

from toolnet_capcut_tts.client import CapCutClient
from toolnet_capcut_tts.exceptions import (
    CapCutAPIError,
    CapCutError,
    CapCutSignError,
    CapCutTaskError,
    CapCutUploadError,
)
from toolnet_capcut_tts.models import (
    DeviceConfig,
    SubtitleResult,
    UploadResult,
    Utterance,
    VoiceInfo,
    Word,
)
from toolnet_capcut_tts.action import TTSConfigurationError, build_tts_action, parse_provider_params

__title__ = "ToolNet CapCut TTS"
__version__ = "1.0.0"

__all__ = [
    "CapCutClient",
    "DeviceConfig",
    "UploadResult",
    "SubtitleResult",
    "Utterance",
    "Word",
    "VoiceInfo",
    "CapCutError",
    "CapCutAPIError",
    "CapCutUploadError",
    "CapCutSignError",
    "CapCutTaskError",
    "TTSConfigurationError",
    "build_tts_action",
    "parse_provider_params",
    "__title__",
    "__version__",
]
