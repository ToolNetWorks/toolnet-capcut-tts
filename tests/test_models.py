import json

import pytest

from toolnet_capcut_tts.models import (
    DeviceConfig,
    SubtitleResult,
    Utterance,
    VoiceInfo,
    Word,
)


def test_srt_roundtrip_with_multiline_and_translation(tmp_path):
    srt = "\ufeff1\n00:00:00,000 --> 00:00:01,250\nXin chào\nbạn\n\n2\n00:00:02.500 --> 00:00:04.000\nTạm biệt\n"
    input_path = tmp_path / "input.srt"
    input_path.write_text(srt, encoding="utf-8")

    result = SubtitleResult.from_srt(input_path)

    assert len(result.utterances) == 2
    assert result.utterances[0].text == "Xin chào\nbạn"
    assert result.utterances[0].start_time == 0
    assert result.utterances[0].end_time == 1250
    assert result.utterances[1].start_time == 2500
    assert result.full_text == "Xin chào\nbạn Tạm biệt"

    output = result.to_srt()
    assert "1\n00:00:00,000 --> 00:00:01,250\nXin chào\nbạn" in output
    assert "2\n00:00:02,500 --> 00:00:04,000\nTạm biệt" in output
    assert output.endswith("\n")


def test_srt_translation_falls_back_to_source_when_missing():
    result = SubtitleResult(
        utterances=[
            Utterance("Xin chào", 0, 1000, translation_text="Hello"),
            Utterance("Tạm biệt", 1000, 2000),
        ]
    )

    translated = result.to_srt(use_translation=True)
    assert "Hello" in translated
    assert "Tạm biệt" in translated


def test_srt_rejects_invalid_timestamp(tmp_path):
    path = tmp_path / "bad.srt"
    path.write_text("1\n00:00:00,000 --> nope\nHello\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid SRT"):
        SubtitleResult.from_srt(path)


def test_srt_rejects_impossible_timestamp_shape(tmp_path):
    path = tmp_path / "bad2.srt"
    path.write_text("1\n0:00:00 --> 00:00:01,000\nHello\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid SRT"):
        SubtitleResult.from_srt(path)


def test_empty_srt_returns_empty_result(tmp_path):
    path = tmp_path / "empty.srt"
    path.write_text("", encoding="utf-8")

    result = SubtitleResult.from_srt(path)
    assert result.utterances == []
    assert result.to_srt() == ""


def test_write_srt_uses_utf8_and_lf(tmp_path):
    path = tmp_path / "out.srt"
    SubtitleResult(utterances=[Utterance("Xin chào", 0, 1000)]).write_srt(path)
    data = path.read_bytes()
    assert b"\r\n" not in data
    assert "Xin chào".encode("utf-8") in data


def test_from_payload_parses_words_and_translation():
    result = SubtitleResult.from_payload(
        {
            "utterances": [
                {
                    "text": "Xin chào",
                    "start_time": 1,
                    "end_time": 2,
                    "translation_text": "Hello",
                    "words": [
                        {
                            "text": "Xin",
                            "start_time": 1,
                            "end_time": 2,
                            "blank_duration": 0,
                        }
                    ],
                }
            ]
        }
    )

    assert result.full_text == "Xin chào"
    assert result.full_translation_text == "Hello"
    assert result.utterances[0].words == [Word("Xin", 1, 2, 0)]


def test_from_payload_non_dict_is_empty():
    assert SubtitleResult.from_payload("not-a-dict").utterances == []


def test_device_config_merges_defaults_and_ignores_unknown_keys():
    device = DeviceConfig.from_dict({"device_id": "did-1", "unknown": "ignored"})
    assert device.device_id == "did-1"
    assert device.aid == DeviceConfig().aid
    assert "unknown" not in device.to_dict()


def test_device_config_from_json(tmp_path):
    path = tmp_path / "device.json"
    path.write_text(json.dumps({"device_id": "from-file"}), encoding="utf-8")
    assert DeviceConfig.from_json_file(path).device_id == "from-file"


def test_voice_catalog_filters_digital_human_records(tmp_path):
    path = tmp_path / "Voice.json"
    path.write_text(
        json.dumps(
            [
                {
                    "voice_type": "v1",
                    "display_name": "Voice 1",
                    "resource_id": "r1",
                    "lang": "vi-VN",
                    "lan": "vi",
                },
                {
                    "voice_type": "dh1",
                    "display_name": "Digital human",
                    "resource_id": "r2",
                    "lang": "vi-VN",
                    "lan": "vi",
                    "catalog_kind": "digital_human_voice",
                },
            ]
        ),
        encoding="utf-8",
    )

    voices = VoiceInfo.load_catalog(path)
    assert [voice.voice_type for voice in voices] == ["v1"]


def test_voice_catalog_missing_file_returns_empty(tmp_path):
    assert VoiceInfo.load_catalog(tmp_path / "missing.json") == []


def test_srt_timestamp_rounding_and_negative_clamp():
    result = SubtitleResult(
        utterances=[Utterance("x", -50, 999.6)]
    )
    assert "00:00:00,000 --> 00:00:01,000" in result.to_srt()
