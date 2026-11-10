
import pytest

from toolnet_capcut_tts.action import (
    TTSConfigurationError,
    build_tts_action,
    parse_provider_params,
)


def test_parse_provider_params_accepts_mapping_and_copies():
    source = {"a": 1}
    parsed = parse_provider_params(source)
    assert parsed == {"a": 1}
    assert parsed is not source


def test_parse_provider_params_accepts_json_and_at_file(tmp_path):
    assert parse_provider_params('{"a": 1}') == {"a": 1}

    path = tmp_path / "params.json"
    path.write_text('{"b": 2}', encoding="utf-8")
    assert parse_provider_params("@" + str(path)) == {"b": 2}


@pytest.mark.parametrize("value", ["[]", "not-json", "123"])
def test_parse_provider_params_rejects_non_object(value):
    with pytest.raises(TTSConfigurationError):
        parse_provider_params(value)


def test_build_tts_action_envelope():
    action = build_tts_action(
        text="Xin chào",
        seg_id="seg-1",
        speaker="speaker-1",
        provider_params_json='{"provider": "x"}',
        extension_json={"extension": True},
        emotion="happy",
    )

    params = action["params"]["tts"]["params"]
    assert action["action_name"] == "TTS_ACTION"
    assert action["segment_ids"] == ["seg-1"]
    assert params["segment_id"] == "seg-1"
    assert params["text_segment_id"] == "seg-1"
    assert params["tts_speaker"] == "speaker-1"
    assert params["provider_params"] == {"provider": "x"}
    assert params["extra"] == {"extension": True}
    assert params["emotion"] == "happy"


def test_build_tts_action_rejects_empty_text_and_seg_id():
    with pytest.raises(TTSConfigurationError):
        build_tts_action(text=" ", seg_id="seg")
    with pytest.raises(TTSConfigurationError):
        build_tts_action(text="hello", seg_id=" ")


def test_build_tts_action_rejects_unknown_options():
    with pytest.raises(TTSConfigurationError, match="unknown TTS option"):
        build_tts_action(text="hello", seg_id="seg", not_a_real_option=True)


def test_build_tts_action_allows_tone_prefixed_options():
    action = build_tts_action(
        text="hello", seg_id="seg", tone_custom_option="value"
    )
    assert action["params"]["tts"]["params"]["tone_custom_option"] == "value"
