"""
Lớp tương thích ``capcut_tts_api`` cho các dự án đã dùng import cũ.

Package chính của dự án là :mod:`toolnet_capcut_tts`. Module này chỉ
re-export API công khai để việc nâng cấp không làm gãy mã hiện có.
"""

from toolnet_capcut_tts import (
    CapCutAPIError,
    CapCutClient,
    CapCutError,
    CapCutSignError,
    CapCutTaskError,
    CapCutUploadError,
    DeviceConfig,
    SubtitleResult,
    TTSConfigurationError,
    UploadResult,
    Utterance,
    VoiceInfo,
    Word,
    __title__,
    __version__,
    build_tts_action,
    parse_provider_params,
)

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
