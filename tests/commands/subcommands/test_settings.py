"""Tests for `dojo settings` (group + every subcommand)."""

from click.testing import CliRunner

from bytedojo.commands.subcommands.settings import settings


# --------------------------------------------------------------------------- #
# No repo                                                                     #
# --------------------------------------------------------------------------- #

def test_settings_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(settings, [])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


# --------------------------------------------------------------------------- #
# Default view (no subcommand) + `list`                                       #
# --------------------------------------------------------------------------- #

def test_settings_default_view_shows_all(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, [])
    assert result.exit_code == 0
    assert "BYTEDOJO SETTINGS" in result.output
    assert "language:" in result.output
    assert "frequency:" in result.output
    assert "organization:" in result.output


def test_settings_list_matches_default_view(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    direct = CliRunner().invoke(settings, []).output
    via_list = CliRunner().invoke(settings, ["list"]).output
    assert "BYTEDOJO SETTINGS" in via_list
    # Both render the same fields.
    for key in ("language:", "source:", "frequency:", "organization:"):
        assert key in direct
        assert key in via_list


# --------------------------------------------------------------------------- #
# default-language                                                            #
# --------------------------------------------------------------------------- #

def test_default_language_persists(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["default-language", "java"])
    assert result.exit_code == 0
    with repo.open_db() as db:
        assert db.get_config("default_language") == "java"


def test_default_language_case_insensitive(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["default-language", "CPP"])
    assert result.exit_code == 0
    with repo.open_db() as db:
        assert db.get_config("default_language") == "cpp"


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
    with repo.open_db() as db:
        assert db.get_config("review_frequency_days") == "14"


def test_review_frequency_rejects_below_one(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["review-frequency", "0"])
    assert result.exit_code != 0
    assert "at least 1 day" in result.output


def test_review_frequency_rejects_above_365(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["review-frequency", "366"])
    assert result.exit_code != 0
    assert "365" in result.output


def test_review_frequency_rejects_non_int(repo, monkeypatch):
    """click validates the type before the command body runs."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["review-frequency", "many"])
    assert result.exit_code != 0


# --------------------------------------------------------------------------- #
# set / get                                                                   #
# --------------------------------------------------------------------------- #

def test_set_known_setting_persists(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(
        settings, ["set", "leetcode.organization", "difficulty"],
    )
    assert result.exit_code == 0

    from bytedojo.core.settings import SettingsManager
    mgr = SettingsManager(repo.dojo_dir)
    assert mgr.load().leetcode.organization == "difficulty"


def test_set_unknown_key_errors(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["set", "made.up.key", "x"])
    assert result.exit_code != 0
    assert "Unknown setting" in result.output


def test_set_invalid_value_errors(repo, monkeypatch):
    """Known key, value outside the whitelist -> error."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(
        settings, ["set", "leetcode.organization", "spiral"],
    )
    assert result.exit_code != 0
    assert "Invalid value" in result.output


def test_get_known_setting_succeeds(repo, monkeypatch):
    """get exits 0 for a known key.

    The displayed value goes through the logger handler, which is bound
    to the real sys.stdout at module-load time and isn't captured by
    CliRunner. Exit-code is the contract we can verify here; the actual
    persisted value is exercised by the set tests above.
    """
    monkeypatch.chdir(repo.root_dir)
    # Persist a non-default so there's something to read.
    CliRunner().invoke(settings, ["set", "leetcode.organization", "difficulty"])
    result = CliRunner().invoke(settings, ["get", "leetcode.organization"])
    assert result.exit_code == 0


def test_get_unknown_key_errors(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(settings, ["get", "made.up.key"])
    assert result.exit_code != 0
    assert "Unknown setting" in result.output
