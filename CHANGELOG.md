# Changelog

## 1.0.0 - 2026-11-10

Bản phát hành độc lập đầu tiên của ToolNet CapCut TTS.

### Thương hiệu và đóng gói

- Đổi tên distribution thành `toolnet-capcut-tts`.
- Package chính mới: `toolnet_capcut_tts`.
- Giữ package tương thích `capcut_tts_api` cho mã nguồn hiện có.
- CLI mới: `toolnet-capcut-tts`; giữ alias `capcut-tts-api`.
- Viết lại README tiếng Việt, bổ sung README tiếng Anh và tiếng Trung.
- Bổ sung LICENSE, NOTICE và metadata giấy phép MIT.

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
