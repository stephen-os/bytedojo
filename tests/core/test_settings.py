"""Tests for Settings + SettingsManager (.dojo/settings.json)."""

import json

import pytest

from bytedojo.core.settings import SETTING_KEYS, Settings, SettingsManager

# --------------------------------------------------------------------------- #
# Settings dataclass                                                          #
# --------------------------------------------------------------------------- #


def test_defaults():
    s = Settings()
    assert s.default_language == "python"
    assert s.review_frequency_days == 7
    assert s.organize_by_language is False


def test_to_dict_from_dict_roundtrip():
    s = Settings(
        default_language="python", review_frequency_days=14, organize_by_language=True
    )
    assert Settings.from_dict(s.to_dict()) == s


def test_from_dict_ignores_unknown_keys():
    """Old settings files with retired keys must still load."""
    s = Settings.from_dict(
        {"leetcode": {"organization": "flat"}, "review_frequency_days": 3}
    )
    assert s.review_frequency_days == 3
    assert s.default_language == "python"


# --------------------------------------------------------------------------- #
# SettingsManager — load / save                                               #
# --------------------------------------------------------------------------- #


def test_load_missing_file_returns_defaults(tmp_path):
    assert SettingsManager(tmp_path).load() == Settings()


def test_load_malformed_file_returns_defaults(tmp_path):
    (tmp_path / "settings.json").write_text("{ nope", encoding="utf-8")
    assert SettingsManager(tmp_path).load() == Settings()


def test_save_writes_pretty_printed_json(tmp_path):
    mgr = SettingsManager(tmp_path)
    mgr.save(Settings(review_frequency_days=14))

    raw = (tmp_path / "settings.json").read_text(encoding="utf-8")
    assert json.loads(raw) == {
        "default_language": "python",
        "review_frequency_days": 14,
        "organize_by_language": False,
    }
    assert "\n" in raw  # indent=2 pretty-print


def test_save_creates_parent_directory_if_missing(tmp_path):
    nested = tmp_path / "new" / "deep" / ".dojo"
    SettingsManager(nested).save(Settings())
    assert (nested / "settings.json").exists()


def test_create_default_does_not_overwrite(tmp_path):
    mgr = SettingsManager(tmp_path)
    mgr.save(Settings(review_frequency_days=3))
    mgr.create_default()
    assert mgr.load().review_frequency_days == 3


# --------------------------------------------------------------------------- #
# SettingsManager — get / set by CLI key                                      #
# --------------------------------------------------------------------------- #


def test_get_known_keys(tmp_path):
    mgr = SettingsManager(tmp_path)
    assert mgr.get("default-language") == "python"
    assert mgr.get("review-frequency") == 7
    assert mgr.get("organize-by-language") is False


def test_get_unknown_key_returns_none(tmp_path):
    assert SettingsManager(tmp_path).get("nope") is None


@pytest.mark.parametrize(
    "key, raw, expected",
    [
        ("default-language", "PYTHON", "python"),
        ("review-frequency", "14", 14),
        ("organize-by-language", "true", True),
        ("organize-by-language", "False", False),
    ],
)
def test_set_parses_and_persists(tmp_path, key, raw, expected):
    mgr = SettingsManager(tmp_path)
    assert mgr.set(key, raw) == expected
    assert mgr.get(key) == expected


def test_set_unknown_key_raises_keyerror(tmp_path):
    with pytest.raises(KeyError):
        SettingsManager(tmp_path).set("nope", "1")


@pytest.mark.parametrize(
    "key, raw, msg",
    [
        ("default-language", "rust", "Unsupported language"),
        ("review-frequency", "abc", "must be a number"),
        ("review-frequency", "0", "at least 1 day"),
        ("review-frequency", "999", "cannot exceed 365"),
        ("organize-by-language", "maybe", "true/false"),
    ],
)
def test_set_rejects_invalid_values(tmp_path, key, raw, msg):
    with pytest.raises(ValueError, match=msg):
        SettingsManager(tmp_path).set(key, raw)


def test_setting_keys_cover_all_fields():
    """Every Settings field is reachable from the CLI."""
    from dataclasses import fields

    assert set(SETTING_KEYS.values()) == {f.name for f in fields(Settings)}
