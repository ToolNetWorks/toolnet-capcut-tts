# Changelog

## 1.0.1 - 2026-11-10

Bản vá đóng gói và tài liệu; không thay đổi runtime hay API công khai.

- Dọn tài liệu và metadata đóng gói.
- Chỉ đóng gói `LICENSE` trong metadata giấy phép.
- Giữ nguyên TTS, STT, dịch, SRT, catalog giọng đọc, upload VOD và CLI.

## 1.0.0 - 2026-11-10

Bản phát hành độc lập đầu tiên của ToolNet CapCut TTS.

### Đóng gói

- Distribution: `toolnet-capcut-tts`.
- Package chính: `toolnet_capcut_tts`.
- CLI: `toolnet-capcut-tts`.
- README tiếng Việt, tiếng Anh và tiếng Trung.
- Giấy phép MIT và thông báo bản quyền trong `LICENSE`.

### Chức năng

- Giữ nguyên TTS, STT, dịch, SRT, catalog giọng đọc và upload VOD.
- Bổ sung `CapCutClient.list_languages()` và `list_language_categories()`.
- Bổ sung CLI `list-languages`.
- Bổ sung kiểm thử tự động cho model, client, CLI, uploader và package.

### Sửa lỗi

- Nhận diện trạng thái task lỗi không phân biệt hoa/thường.
- Báo lỗi rõ ràng khi response tạo task thiếu `id`/`token`.
- Truyền `base_url` tùy chỉnh vào luồng upload VOD.
- Resolve voice khi người dùng truyền trực tiếp `resource_id`.
- Đồng bộ docstring của helper ký payload với hành vi thực tế.
- Sửa `write_srt()` để tương thích Python 3.9 (không dùng tham số
  `newline` chỉ có từ Python 3.10 của `Path.write_text`).
