"""Tests for `dojo settings` (group + every subcommand)."""

import re

from click.testing import CliRunner

from bytedojo.core.errors import RepoNotFoundError
from bytedojo.commands.subcommands.settings import settings
from bytedojo.core.settings import SettingsManager

# Setting rows render as `key<padding>value`. Match the pair, not the bare key —
# the usage footer also mentions the key names.
_ROWS = (
    r"default-language\s+python",
    r"review-frequency\s+7 days",
    r"organize-by-language\s+false",
)


# --------------------------------------------------------------------------- #
# No repo                                                                     #
# --------------------------------------------------------------------------- #


def test_settings_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(settings, [])
    assert result.exit_code != 0
    assert isinstance(result.exception, RepoNotFoundError)


# --------------------------------------------------------------------------- #
# Default view (no subcommand) + `list`                                       #
# --------------------------------------------------------------------------- #


def test_settings_default_view_shows_all(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, [])
    assert result.exit_code == 0
    assert "ByteDojo Settings" in result.output
    for row in _ROWS:
        assert re.search(row, result.output), f"missing settings row: {row}"


def test_settings_list_matches_default_view(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    direct = CliRunner().invoke(settings, []).output
    via_list = CliRunner().invoke(settings, ["list"]).output
    assert "ByteDojo Settings" in via_list
    # Both render the same fields.
    for row in _ROWS:
        assert re.search(row, direct), f"missing from default view: {row}"
        assert re.search(row, via_list), f"missing from `list`: {row}"


# --------------------------------------------------------------------------- #
# default-language                                                            #
# --------------------------------------------------------------------------- #


def test_default_language_persists(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["default-language", "python"])
    assert result.exit_code == 0
    assert SettingsManager(repo.dojo_dir).load().default_language == "python"


def test_default_language_case_insensitive(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["default-language", "PYTHON"])
    assert result.exit_code == 0
    assert SettingsManager(repo.dojo_dir).load().default_language == "python"


def test_default_language_rejects_unsupported(repo, monkeypatch):
    """click.Choice rejects values outside the supported list."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["default-language", "rust"])
    assert result.exit_code != 0


# --------------------------------------------------------------------------- #
# review-frequency                                                            #
# --------------------------------------------------------------------------- #


def test_review_frequency_persists(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["review-frequency", "14"])
    assert result.exit_code == 0
    assert SettingsManager(repo.dojo_dir).load().review_frequency_days == 14


def test_review_frequency_rejects_below_one(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["review-frequency", "0"])
    assert result.exit_code != 0
    assert "at least 1 day" in result.output


def test_review_frequency_rejects_above_year(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["review-frequency", "999"])
    assert result.exit_code != 0
    assert "cannot exceed 365" in result.output


# --------------------------------------------------------------------------- #
# set / get                                                                   #
# --------------------------------------------------------------------------- #


def test_set_organize_by_language(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["set", "organize-by-language", "true"])
    assert result.exit_code == 0
    assert SettingsManager(repo.dojo_dir).load().organize_by_language is True


def test_set_unknown_key_errors_with_key_list(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["set", "no-such-key", "x"])
    assert result.exit_code != 0
    assert "Unknown setting" in result.output
    assert "organize-by-language" in result.output


def test_set_invalid_value_errors(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["set", "organize-by-language", "maybe"])
    assert result.exit_code != 0
    assert "true/false" in result.output


def test_get_known_key(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["get", "review-frequency"])
    assert result.exit_code == 0
    assert "7" in result.output


def test_get_unknown_key_errors(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["get", "nope"])
    assert result.exit_code != 0
    assert "Unknown setting" in result.output
