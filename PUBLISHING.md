# Phát hành lên PyPI

Package được phát hành qua **PyPI Trusted Publishing (OIDC)**. Workflow không
lưu token hay mật khẩu PyPI.

## Cấu hình một lần trên PyPI

Tên distribution: `toolnet-capcut-tts`.

Trên PyPI, mở **Publishing** và thêm một *pending trusted publisher* với đúng
các giá trị sau:

| Trường | Giá trị |
| --- | --- |
| PyPI project name | `toolnet-capcut-tts` |
| Owner | `ToolNetWorks` |
| Repository name | `toolnet-capcut-tts` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

Publisher chỉ hợp lệ khi repository là công khai và workflow nằm tại
`.github/workflows/publish.yml`.

Nếu project đã tồn tại trên PyPI, thêm trusted publisher trong phần
**Manage project → Publishing** thay vì tạo pending publisher.

## Cấu hình GitHub

Workflow đã có tại `.github/workflows/publish.yml` và được kích hoạt khi một
GitHub Release được publish. Job publish dùng environment `pypi`; có thể thêm
protection rule cho environment này trong GitHub nếu muốn kiểm duyệt thủ công.

Quyền OIDC cần thiết đã được khai báo trong workflow:

```yaml
permissions:
  id-token: write
  contents: read
```

## Quy trình phát hành

1. Cập nhật version theo Semantic Versioning trong `pyproject.toml` và
   `toolnet_capcut_tts/__init__.py`.
2. Chạy kiểm tra cục bộ:

   ```bash
   python -m pip install -e ".[dev]" build twine
   python -m pytest
   python -m build
   python -m twine check dist/*
   ```

3. Commit, tạo tag annotated và push:

   ```bash
   git tag -a v1.0.1 -m "ToolNet CapCut TTS 1.0.1"
   git push origin main
   git push origin v1.0.1
   ```

4. Tạo GitHub Release từ tag `v1.0.1`. Khi Release được publish, workflow
   `Publish to PyPI` sẽ build lại, chạy test và upload lên PyPI bằng OIDC.
5. Xác nhận bản phát hành tại:

   ```bash
   python -m pip index versions toolnet-capcut-tts
   ```

6. Kiểm tra trên môi trường ảo sạch:

   ```bash
   python -m venv /tmp/toolnet-pypi-check
   /tmp/toolnet-pypi-check/bin/pip install toolnet-capcut-tts
   /tmp/toolnet-pypi-check/bin/toolnet-capcut-tts --version
   /tmp/toolnet-pypi-check/bin/toolnet-capcut-tts list-voices --language vi-VN
   ```

Không dùng `twine upload` với token trong CI và không commit `.pypirc`,
`PYPI_API_TOKEN` hoặc bất kỳ bí mật nào.
