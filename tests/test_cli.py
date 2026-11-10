import json

import pytest

from toolnet_capcut_tts.cli import main


def test_help_and_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "toolnet-capcut-tts" in output
    assert "list-languages" in output

    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert "1.0.0" in capsys.readouterr().out


def test_list_voices(capsys):
    main(["list-voices", "--language", "vi-VN"])
    data = json.loads(capsys.readouterr().out)

    assert data["voices"]
    assert all(item["lang"] == "vi-VN" for item in data["voices"])


def test_list_voices_all_when_language_omitted(capsys):
    main(["list-voices"])
    data = json.loads(capsys.readouterr().out)
    assert len(data["voices"]) > 10


def test_list_languages(capsys):
    main(["list-languages"])
    data = json.loads(capsys.readouterr().out)

    assert data["category"] == "tts_catalog_languages"
    assert "vi-VN" in data["languages"]
    assert "tts_catalog_languages" in data["categories"]


def test_list_languages_custom_category(capsys):
    main(["list-languages", "--language-category", "media_asr_exact_observed"])
    data = json.loads(capsys.readouterr().out)
    assert "auto" in data["languages"]


def test_tts_new_dry_run(capsys):
    main(["tts-new", "--text", "Xin chào", "--dry-run"])
    data = json.loads(capsys.readouterr().out)

    assert "/lv/v1/common_task/new" in data["url"]
    assert data["body"]["tasks"][0]["req_key"] == "sami_text_to_speech"
    assert "sign" in data["headers"]


def test_tts_action(capsys):
    main(["tts-action", "--text", "Xin chào", "--seg-id", "seg-1"])
    data = json.loads(capsys.readouterr().out)
    assert data["action_name"] == "TTS_ACTION"
    assert data["params"]["tts"]["params"]["segment_id"] == "seg-1"


def test_tts_srt_dry_run(tmp_path, capsys):
    srt = tmp_path / "captions.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nXin chào\n\n"
        "2\n00:00:02,000 --> 00:00:03,000\nTạm biệt\n",
        encoding="utf-8",
    )

    main(["tts-srt", "--srt-file", str(srt), "--dry-run"])
    data = json.loads(capsys.readouterr().out)

    assert data["cue_count"] == 2
    assert data["texts"] == ["Xin chào", "Tạm biệt"]
    assert data["sent"] is False


def test_out_file_is_written(tmp_path, capsys):
    out = tmp_path / "languages.json"
    main(["list-languages", "--out", str(out)])
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8"))["category"] == "tts_catalog_languages"


def test_missing_audio_file_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["upload-audio"])
    assert exc_info.value.code == 1
    assert "--audio-file is required" in capsys.readouterr().err


def test_legacy_cli_facade_is_same_main():
    import capcut_tts_api.cli as legacy_cli
    import toolnet_capcut_tts.cli as new_cli

    assert legacy_cli.main is new_cli.main
