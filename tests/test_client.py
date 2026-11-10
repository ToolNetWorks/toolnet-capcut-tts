import json
from pathlib import Path

import pytest

from toolnet_capcut_tts import CapCutClient
from toolnet_capcut_tts.exceptions import CapCutAPIError, CapCutTaskError, CapCutUploadError
from toolnet_capcut_tts.models import DeviceConfig, UploadResult
from toolnet_capcut_tts.uploader import VODUploader

from conftest import (
    FakeResponse,
    FakeSession,
    completed_stt_response,
    completed_tts_response,
    completed_tts_response_multi,
    create_task_response,
)


def make_client(session):
    return CapCutClient(
        device=DeviceConfig(device_id="did-test", iid="did-test", tdid="did-test"),
        session=session,
        timeout=5,
    )


def test_build_tts_request_contains_escaped_ssml_and_signature():
    client = make_client(FakeSession())
    url, headers, body = client.build_tts_new_request(
        ["Xin chào <b> & \"bạn\""], voice="BV421_vivn_streaming"
    )

    assert url.startswith("https://editor-api-sg.capcutapi.com/lv/v1/common_task/new?")
    assert "sign" in headers
    assert headers["x-ss-stub"]
    payload = json.loads(body)
    task = payload["tasks"][0]
    assert task["req_key"] == "sami_text_to_speech"
    inner = json.loads(task["payload"])
    assert "&lt;b&gt;" in inner["ssml"]
    assert "&amp;" in inner["ssml"]
    assert inner["sign"]


def test_build_stt_request_and_query_modes():
    client = make_client(FakeSession())
    url, headers, body = client.build_stt_new_request(
        "vid-1", "md5-1", duration_ms=1234, language="vi-VN",
        translation_language="en-US", use_translation=True,
    )
    inner = json.loads(json.loads(body)["tasks"][0]["payload"])["cap_json"]
    assert url.startswith("https://editor-api-sg.capcutapi.com/lv/v1/common_task/new?")
    assert inner["audio"] == "vid-1"
    assert inner["duration"] == 1234
    assert inner["use_translation"] is True

    query_url, query_headers, query_body = client.build_query_request(
        "task", "token", mode="stt", bind_id="bind"
    )
    assert "/lv/v1/common_task/query?" in query_url
    assert json.loads(query_body)["tasks"][0]["req_key"] == "cc_audio_subtitle_asr"
    assert "sign" in query_headers


def test_resolve_voice_by_type_name_and_resource_id():
    client = make_client(FakeSession())

    assert client.resolve_voice("BV421_vivn_streaming")[0] == "BV421_vivn_streaming"
    assert client.resolve_voice("Nhỏ Ngọt Ngào")[0] == "BV421_vivn_streaming"
    voice_type, resource_id = client.resolve_voice("7252594014782755330")
    assert voice_type == "BV421_vivn_streaming"
    assert resource_id == "7252594014782755330"


def test_generate_speech_polls_and_downloads(tmp_path):
    session = FakeSession(
        post_responses=[create_task_response(), completed_tts_response()],
        get_responses=[FakeResponse(content=b"ID3-audio")],
    )
    client = make_client(session)

    response = client.generate_speech("Xin chào", timeout=5, poll_interval=0)
    output = client.download_tts_audio(response, tmp_path / "out.mp3")

    assert output.read_bytes() == b"ID3-audio"
    assert len(session.posts) == 2
    assert session.gets[0]["url"] == "https://cdn.example/audio.mp3"
    assert session.gets[0]["timeout"] == 5


def test_generate_speech_failed_status_is_case_insensitive():
    session = FakeSession(
        post_responses=[
            create_task_response(),
            completed_tts_response(status="FAILED"),
        ]
    )
    client = make_client(session)

    with pytest.raises(CapCutTaskError, match="failed"):
        client.generate_speech("Xin chào", timeout=5, poll_interval=0)


def test_generate_speech_missing_task_credentials():
    session = FakeSession(
        post_responses=[
            FakeResponse({"ret": 0, "data": {"tasks": [{"id": "id-only"}]}})
        ]
    )
    client = make_client(session)

    with pytest.raises(CapCutTaskError, match="id/token"):
        client.generate_speech("Xin chào", timeout=5)


def test_api_level_error_raises_api_error():
    session = FakeSession(
        post_responses=[FakeResponse({"ret": 1014, "errmsg": "busy"})]
    )
    client = make_client(session)

    with pytest.raises(CapCutAPIError, match="ret=1014"):
        client.create_tts_task("Xin chào")


def test_http_error_raises_api_error_with_response_data():
    session = FakeSession(
        post_responses=[FakeResponse({"error": "bad"}, status_code=500)]
    )
    client = make_client(session)

    with pytest.raises(CapCutAPIError) as exc_info:
        client.create_tts_task("Xin chào")
    assert exc_info.value.status_code == 500
    assert exc_info.value.response_data == {"error": "bad"}


def test_transcribe_file_uploads_creates_and_parses(monkeypatch):
    session = FakeSession(
        post_responses=[create_task_response(), completed_stt_response()]
    )
    client = make_client(session)

    monkeypatch.setattr(
        client,
        "upload_audio",
        lambda path: UploadResult(
            vid="vid-1", md5="md5-1", local_md5="md5-1", duration_ms=5000
        ),
    )

    response = client.transcribe_file("recording.mp3", timeout=5, poll_interval=0)
    subtitles = client.extract_subtitles(response)

    assert subtitles.full_text == "Xin chào"
    assert subtitles.utterances[0].translation_text == "Hello"
    assert len(session.posts) == 2


def test_download_rejects_empty_file(tmp_path):
    session = FakeSession(
        post_responses=[create_task_response(), completed_tts_response()],
        get_responses=[FakeResponse(content=b"")],
    )
    client = make_client(session)
    response = client.generate_speech("Xin chào", timeout=5, poll_interval=0)

    with pytest.raises(Exception, match="empty file"):
        client.download_tts_audio(response, tmp_path / "empty.mp3")


def test_download_requires_observed_url():
    client = make_client(FakeSession())
    response = {
        "data": {
            "tasks": [
                {"payload": json.dumps({"audio_subtitles": [{"vid": "only-vid"}]})}
            ]
        }
    }

    with pytest.raises(Exception, match="no observed download URL"):
        client.download_tts_audio(response, "unused.mp3")


def test_list_languages_and_categories():
    client = make_client(FakeSession())
    categories = client.list_language_categories()
    assert "tts_catalog_languages" in categories
    assert "vi-VN" in client.list_languages()
    with pytest.raises(ValueError, match="Unknown language category"):
        client.list_languages("missing")


def test_custom_base_url_is_used_by_uploader():
    uploader = VODUploader(
        DeviceConfig(device_id="did", iid="did", tdid="did"),
        session=FakeSession(),
        base_url="https://custom.example.test",
    )
    url, headers, body = uploader._upload_sign_request()
    assert url.startswith("https://custom.example.test/lv/v1/upload_sign?")
    assert "sign" in headers


def test_upload_audio_missing_file_raises():
    client = make_client(FakeSession())
    with pytest.raises(CapCutUploadError, match="File not found"):
        client.upload_audio("/path/does/not/exist.mp3")


def test_generate_speech_from_srt_part_mode(tmp_path):
    srt = tmp_path / "captions.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,500\nCâu một\n\n"
        "2\n00:00:02,000 --> 00:00:04,000\nCâu hai\n",
        encoding="utf-8",
    )
    session = FakeSession(
        post_responses=[
            create_task_response(),
            completed_tts_response_multi(
                ["https://cdn.example/1.mp3", "https://cdn.example/2.mp3"]
            ),
        ],
        get_responses=[
            FakeResponse(content=b"audio-1"),
            FakeResponse(content=b"audio-2"),
        ],
    )
    client = make_client(session)

    result = client.generate_speech_from_srt(
        srt, output_dir=tmp_path / "parts", timeout=5
    )

    assert result["part"] is True
    assert len(result["cues"]) == 2
    assert result["cues"][0]["start_time"] == 0
    assert result["cues"][0]["end_time"] == 1500
    assert Path(result["cues"][0]["audio_path"]).read_bytes() == b"audio-1"
    assert Path(result["cues"][1]["audio_path"]).read_bytes() == b"audio-2"
    assert [call["url"] for call in session.gets] == [
        "https://cdn.example/1.mp3",
        "https://cdn.example/2.mp3",
    ]


def test_generate_speech_from_srt_combined_mode(tmp_path):
    srt = tmp_path / "captions.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,500\nCâu một\n\n"
        "2\n00:00:02,000 --> 00:00:04,000\nCâu hai\n",
        encoding="utf-8",
    )
    session = FakeSession(
        post_responses=[create_task_response(), completed_tts_response()],
        get_responses=[FakeResponse(content=b"combined")],
    )
    client = make_client(session)

    result = client.generate_speech_from_srt(
        srt, part=False, audio_path=tmp_path / "combined.mp3", timeout=5
    )

    assert result["part"] is False
    assert result["text"] == "Câu một Câu hai"
    assert result["cues"][0]["start_time"] == 0
    assert result["cues"][0]["end_time"] == 4000
    assert Path(result["audio_path"]).read_bytes() == b"combined"


def test_generate_speech_from_empty_srt_raises(tmp_path):
    srt = tmp_path / "empty.srt"
    srt.write_text("", encoding="utf-8")
    client = make_client(FakeSession())

    with pytest.raises(Exception, match="no non-empty subtitle cues"):
        client.generate_speech_from_srt(srt)
