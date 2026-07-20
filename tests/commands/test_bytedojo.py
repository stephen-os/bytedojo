"""Tests for the top-level `dojo` Click group."""

from click.testing import CliRunner

from bytedojo import __author__, __version__
from bytedojo.commands.bytedojo import bytedojo


# --------------------------------------------------------------------------- #
# Group structure                                                             #
# --------------------------------------------------------------------------- #

def test_dojo_help_lists_every_subcommand():
    """Every command registered via add_command shows up in --help."""
    result = CliRunner().invoke(bytedojo, ["--help"])
    assert result.exit_code == 0
    for cmd in (
        "fetch", "grade", "init", "pick", "query",
        "review", "settings",
    ):
        assert cmd in result.output, f"{cmd!r} missing from --help"


def test_dojo_no_args_shows_usage_with_exit_2():
    """Bare `dojo` is a Click group with required subcommand — exits 2 with usage.

    Standard Click behaviour for groups invoked without a subcommand.
    """
    result = CliRunner().invoke(bytedojo, [])
    assert result.exit_code == 2
    assert "Usage" in result.output


# --------------------------------------------------------------------------- #
# Eager flags: --version / --author / --desc                                  #
# --------------------------------------------------------------------------- #

def test_version_flag_prints_version_and_exits():
    result = CliRunner().invoke(bytedojo, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_author_flag_prints_author_and_exits():
    result = CliRunner().invoke(bytedojo, ["--author"])
    assert result.exit_code == 0
    assert __author__ in result.output


def test_desc_flag_prints_description_and_exits():
    result = CliRunner().invoke(bytedojo, ["--desc"])
    assert result.exit_code == 0
    assert "ByteDojo" in result.output
    assert "LeetCode" in result.output


def test_eager_flag_skips_subcommand_invocation():
    """--version short-circuits before the registered subcommand runs."""
    result = CliRunner().invoke(bytedojo, ["--version", "query"])
    assert result.exit_code == 0
    assert __version__ in result.output
    # If query had run we'd see its output or a "not inside a repository" error.
    assert "repository" not in result.output.lower()


# --------------------------------------------------------------------------- #
# --debug toggles the logger level                                            #
# --------------------------------------------------------------------------- #

def test_debug_flag_initialises_debug_logger(monkeypatch):
    """The --debug flag flows through to setup_logger(debug=True)."""
    captured = {"debug": None}

    def fake_setup(debug: bool = False):
        captured["debug"] = debug

    monkeypatch.setattr("bytedojo.commands.bytedojo.setup_logger", fake_setup)
    # Re-initialise via a noop subcommand path: --help exits before the
    # subcommand body, but the group callback still runs first.
    CliRunner().invoke(bytedojo, ["--debug", "init", "--help"])
    assert captured["debug"] is True


def test_no_debug_flag_initialises_info_logger(monkeypatch):
    captured = {"debug": None}

    def fake_setup(debug: bool = False):
        captured["debug"] = debug

    monkeypatch.setattr("bytedojo.commands.bytedojo.setup_logger", fake_setup)
    CliRunner().invoke(bytedojo, ["init", "--help"])
    assert captured["debug"] is False
