"""Tests for `dojo init`."""

import pytest
from click.testing import CliRunner

from bytedojo.commands.subcommands.init import init


def test_init_creates_dojo_dir_in_cwd(tmp_path, monkeypatch):
    """Default path is cwd; .dojo lands underneath it."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(init, [])
    assert result.exit_code == 0
    assert (tmp_path / ".dojo").is_dir()
    assert "initialized" in result.output.lower()


def test_init_respects_path_flag(tmp_path):
    """--path is honoured (regression test for the hard-coded Path.cwd() bug)."""
    target = tmp_path / "elsewhere"
    target.mkdir()

    result = CliRunner().invoke(init, ["--path", str(target)])
    assert result.exit_code == 0
    assert (target / ".dojo").is_dir()
    # Output mentions the actual path so users can see where it landed.
    assert str(target) in result.output


def test_init_short_path_flag(tmp_path):
    """-p is the documented short form of --path."""
    target = tmp_path / "via-short"
    target.mkdir()
    result = CliRunner().invoke(init, ["-p", str(target)])
    assert result.exit_code == 0
    assert (target / ".dojo").is_dir()


def test_init_fails_when_already_exists_without_force(tmp_path, monkeypatch):
    """Second init on the same path exits 1 with a failure message."""
    monkeypatch.chdir(tmp_path)
    first = CliRunner().invoke(init, [])
    assert first.exit_code == 0

    second = CliRunner().invoke(init, [])
    assert second.exit_code == 1
    assert "failed" in second.output.lower()


def test_init_force_re_runs_on_existing(tmp_path, monkeypatch):
    """--force lets the user reinitialise without manual cleanup."""
    monkeypatch.chdir(tmp_path)
    CliRunner().invoke(init, [])
    result = CliRunner().invoke(init, ["--force"])
    assert result.exit_code == 0
    assert "initialized" in result.output.lower()
