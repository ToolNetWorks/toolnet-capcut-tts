import base64
import hashlib
import json

import pytest

from toolnet_capcut_tts.config import TTS_SIGN_PUBLIC_KEY_PEM
from toolnet_capcut_tts.exceptions import CapCutSignError
from toolnet_capcut_tts.models import DeviceConfig
from toolnet_capcut_tts.signer import (
    aws4_authorization,
    base_headers,
    compact_json,
    common_query,
    escape_xml,
    file_md5,
    make_sign_header,
    make_tts_payload_sign,
    make_x_ss_stub,
    rsa_public_numbers_from_pem,
)
from toolnet_capcut_tts.uploader import VODUploader


def test_compact_json_and_escaping():
    assert compact_json({"b": 1, "a": "ế"}) == '{"b":1,"a":"ế"}'
    assert escape_xml('<a & "b">') == "&lt;a &amp; &quot;b&quot;&gt;"


def test_make_sign_header_is_deterministic():
    first = make_sign_header(
        "https://example.test/lv/v1/common_task/new?a=1",
        "8.7.0",
        "1700000000",
        "did-1",
    )
    second = make_sign_header(
        "https://example.test/lv/v1/common_task/new?a=2",
        "8.7.0",
        "1700000000",
        "did-1",
    )
    assert first == second
    assert len(first) == 32
    assert make_x_ss_stub("abc") == hashlib.md5(b"abc").hexdigest()


def test_rsa_public_key_parses():
    modulus, exponent = rsa_public_numbers_from_pem(TTS_SIGN_PUBLIC_KEY_PEM)
    assert modulus.bit_length() >= 2048
    assert exponent == 65537


def test_rsa_payload_sign_is_base64_and_randomized():
    first = make_tts_payload_sign("ssml", "{}", "did", "359289")
    second = make_tts_payload_sign("ssml", "{}", "did", "359289")
    assert first != second
    assert len(base64.b64decode(first)) == 256
    assert len(base64.b64decode(second)) == 256


def test_rsa_rejects_invalid_pem():
    with pytest.raises(CapCutSignError):
        rsa_public_numbers_from_pem("not a pem")


def test_base_headers_and_common_query():
    device = DeviceConfig(device_id="did-1", iid="did-1", tdid="did-1")
    headers = base_headers(device.to_dict(), "{}", appid=True)
    query = common_query(device.to_dict(), {"x": 1})

    assert headers["x-ss-dp"] == device.aid
    assert headers["appid"] == device.aid
    assert headers["x-ss-stub"] == hashlib.md5(b"{}").hexdigest()
    assert query["device_id"] == "did-1"
    assert json.loads(query["babi_param"]) == {"x": 1}


def test_aws4_authorization_shape():
    authorization = aws4_authorization(
        "GET",
        "https://vod.example.test/upload?b=2&a=1",
        b"",
        "AKID",
        "SECRET",
        "SESSION",
        "20260101T000000Z",
    )
    assert authorization.startswith("AWS4-HMAC-SHA256 Credential=AKID/20260101/")
    assert "SignedHeaders=x-amz-date;x-amz-security-token" in authorization
    assert "Signature=" in authorization


def test_file_md5(tmp_path):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"hello")
    assert file_md5(str(path)) == hashlib.md5(b"hello").hexdigest()


def test_vod_signed_headers_contain_required_fields():
    uploader = VODUploader(DeviceConfig(), session=None)
    headers = uploader._vod_signed_headers(
        "GET",
        "https://vod.example.test/upload",
        b"",
        {
            "access_key_id": "AKID",
            "secret_access_key": "SECRET",
            "session_token": "SESSION",
        },
    )
    assert headers["Authorization"].startswith("AWS4-HMAC-SHA256")
    assert headers["X-Amz-Security-Token"] == "SESSION"
    assert "Date" in headers
