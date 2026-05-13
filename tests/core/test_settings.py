"""Tests for SettingsManager and the Settings dataclasses."""

import json

import pytest

from bytedojo.core.settings import LeetCodeSettings, Settings, SettingsManager


# --------------------------------------------------------------------------- #
# Settings / LeetCodeSettings dataclasses                                     #
# --------------------------------------------------------------------------- #

def test_leetcode_settings_default_organization():
    assert LeetCodeSettings().organization == "flat"


def test_settings_default_factory_creates_leetcode_block():
    s = Settings()
    assert isinstance(s.leetcode, LeetCodeSettings)
    assert s.leetcode.organization == "flat"


def test_settings_default_factory_independence():
    """Two fresh Settings shouldn't share their nested leetcode block."""
    a = Settings()
    b = Settings()
    a.leetcode.organization = "difficulty"
    assert b.leetcode.organization == "flat"


def test_settings_to_dict_shape():
    s = Settings()
    d = s.to_dict()
    assert d == {"leetcode": {"organization": "flat"}}


def test_settings_from_dict_roundtrips():
    raw = {"leetcode": {"organization": "difficulty"}}
    s = Settings.from_dict(raw)
    assert s.leetcode.organization == "difficulty"
    assert s.to_dict() == raw


def test_settings_from_dict_missing_leetcode_block_uses_defaults():
    """A partial dict (no leetcode key) still produces a valid Settings."""
    s = Settings.from_dict({})
    assert s.leetcode.organization == "flat"


# --------------------------------------------------------------------------- #
# SettingsManager.load                                                        #
# --------------------------------------------------------------------------- #

def test_load_no_file_returns_defaults(tmp_path):
    mgr = SettingsManager(tmp_path)
    assert not mgr.settings_path.exists()
    assert mgr.load().leetcode.organization == "flat"


def test_load_reads_persisted_settings(tmp_path):
    payload = {"leetcode": {"organization": "difficulty"}}
    (tmp_path / "settings.json").write_text(json.dumps(payload), encoding="utf-8")

    settings = SettingsManager(tmp_path).load()
    assert settings.leetcode.organization == "difficulty"


def test_load_falls_back_to_defaults_on_corrupt_file(tmp_path):
    """Malformed JSON shouldn't crash the CLI — log error, hand back defaults."""
    (tmp_path / "settings.json").write_text("{ not valid", encoding="utf-8")
    settings = SettingsManager(tmp_path).load()
    assert settings.leetcode.organization == "flat"


# --------------------------------------------------------------------------- #
# SettingsManager.save                                                        #
# --------------------------------------------------------------------------- #

def test_save_writes_pretty_printed_json(tmp_path):
    mgr = SettingsManager(tmp_path)
    settings = Settings(leetcode=LeetCodeSettings(organization="difficulty"))
    mgr.save(settings)

    raw = (tmp_path / "settings.json").read_text(encoding="utf-8")
    assert json.loads(raw) == {"leetcode": {"organization": "difficulty"}}
    # `indent=2` pretty-print: a newline between top-level keys.
    assert "\n" in raw


def test_save_creates_parent_directory_if_missing(tmp_path):
    nested = tmp_path / "new" / "deep" / ".dojo"
    mgr = SettingsManager(nested)
    mgr.save(Settings())
    assert mgr.settings_path.exists()


def test_save_then_load_roundtrip(tmp_path):
    mgr = SettingsManager(tmp_path)
    mgr.save(Settings(leetcode=LeetCodeSettings(organization="difficulty")))
    assert mgr.load().leetcode.organization == "difficulty"


# --------------------------------------------------------------------------- #
# SettingsManager.get                                                         #
# --------------------------------------------------------------------------- #

def test_get_dot_notation_returns_nested_value(tmp_path):
    mgr = SettingsManager(tmp_path)
    mgr.save(Settings(leetcode=LeetCodeSettings(organization="difficulty")))
    assert mgr.get("leetcode.organization") == "difficulty"


def test_get_unknown_key_returns_none(tmp_path):
    assert SettingsManager(tmp_path).get("leetcode.nonexistent") is None


def test_get_unknown_root_returns_none(tmp_path):
    assert SettingsManager(tmp_path).get("nonexistent.field") is None


# --------------------------------------------------------------------------- #
# SettingsManager.set                                                         #
# --------------------------------------------------------------------------- #

def test_set_dot_notation_persists_value(tmp_path):
    mgr = SettingsManager(tmp_path)
    ok = mgr.set("leetcode.organization", "difficulty")
    assert ok is True
    assert mgr.load().leetcode.organization == "difficulty"


def test_set_unknown_root_returns_false(tmp_path):
    mgr = SettingsManager(tmp_path)
    assert mgr.set("unknown.org", "x") is False


def test_set_unknown_leaf_returns_false(tmp_path):
    """Existing root, unknown field on it -> False, no write."""
    mgr = SettingsManager(tmp_path)
    assert mgr.set("leetcode.does_not_exist", "x") is False
    # The settings file must not have been written for an invalid set.
    assert mgr.load().leetcode.organization == "flat"


def test_set_single_segment_returns_false(tmp_path):
    """set() requires dot-notation; bare key like 'organization' is invalid."""
    assert SettingsManager(tmp_path).set("organization", "x") is False


# --------------------------------------------------------------------------- #
# SettingsManager.create_default                                              #
# --------------------------------------------------------------------------- #

def test_create_default_writes_file_when_missing(tmp_path):
    mgr = SettingsManager(tmp_path)
    assert not mgr.settings_path.exists()
    mgr.create_default()
    assert mgr.settings_path.exists()


def test_create_default_is_idempotent(tmp_path):
    """An existing file is left alone (caller's customisations preserved)."""
    mgr = SettingsManager(tmp_path)
    mgr.save(Settings(leetcode=LeetCodeSettings(organization="difficulty")))
    mgr.create_default()
    # Existing value preserved, not stomped back to the flat default.
    assert mgr.load().leetcode.organization == "difficulty"
