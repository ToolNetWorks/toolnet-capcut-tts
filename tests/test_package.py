from pathlib import Path

import capcut_tts_api
import capcut_tts_api.client as legacy_client
import capcut_tts_api.models as legacy_models
import capcut_tts_api.signer as legacy_signer
import toolnet_capcut_tts
import toolnet_capcut_tts.client as new_client
import toolnet_capcut_tts.models as new_models
import toolnet_capcut_tts.signer as new_signer

ROOT = Path(__file__).resolve().parents[1]


def test_public_metadata():
    assert toolnet_capcut_tts.__title__ == "ToolNet CapCut TTS"
    assert toolnet_capcut_tts.__version__ == "1.0.1"
    assert capcut_tts_api.__version__ == toolnet_capcut_tts.__version__


def test_legacy_facade_reexports_public_api():
    assert capcut_tts_api.CapCutClient is toolnet_capcut_tts.CapCutClient
    assert legacy_models.SubtitleResult is new_models.SubtitleResult
    assert legacy_client.CapCutClient is new_client.CapCutClient
    assert legacy_signer.make_sign_header is new_signer.make_sign_header
    assert callable(legacy_client._checked_json_response)


def test_legacy_catalog_data_is_identical():
    for name in ("Voice.json", "language.json"):
        assert (ROOT / "capcut_tts_api" / name).read_bytes() == (
            ROOT / "toolnet_capcut_tts" / name
        ).read_bytes()


def test_license_preserved():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    assert "MIT License" in license_text
    assert "CapCut API Contributors" in license_text
    assert "ToolNetWorks" in license_text


def test_no_promotional_source_links_in_text_files():
    forbidden = (
        "K07" + "VN",
        "k07" + "vn",
        "star-" + "history.com",
        "tnk" + "re.dev",
        "forked" + " from",
    )
    suffixes = {".md", ".py", ".toml", ".json", ".txt", ".yml", ".yaml", ".cfg", ".ini"}
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if path == Path(__file__):
            continue
        if any(part in {".git", "__pycache__", ".venv", "build", "dist"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in forbidden:
            if needle in text:
                offenders.append((str(path.relative_to(ROOT)), needle))
    assert offenders == []


def test_pyproject_uses_toolnet_distribution():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "toolnet-capcut-tts"' in text
    assert 'version = "1.0.1"' in text
    assert 'toolnet-capcut-tts = "toolnet_capcut_tts.cli:main"' in text
    assert 'capcut-tts-api = "capcut_tts_api.cli:main"' in text
    assert 'license = "MIT"' in text
    assert 'license-files = ["LICENSE"]' in text


def test_release_workflow_uses_trusted_publishing():
    text = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    assert "release:" in text
    assert "id-token: write" in text
    assert "pypa/gh-action-pypi-publish@release/v1" in text
    assert "environment:" in text
    assert "password:" not in text
    assert "PYPI_API_TOKEN" not in text


def test_changelog_and_pypi_version_agree():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## 1.0.0" in changelog
    assert "## 1.0.1" in changelog
    assert toolnet_capcut_tts.__version__ == "1.0.1"
