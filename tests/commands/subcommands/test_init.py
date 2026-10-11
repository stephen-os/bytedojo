"""Tests for `dojo init`."""

from click.testing import CliRunner

from bytedojo.commands.subcommands.init import init


def test_init_creates_dojo_dir_in_cwd(tmp_path, monkeypatch):
    """Default path is cwd; .dojo lands underneath it."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(init, [])
    assert result.exit_code == 0
    assert (tmp_path / ".dojo").is_dir()
    assert "Initialized empty ByteDojo repository" in result.output


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
    """Second init on the same path exits 1 with an error on stderr."""
    monkeypatch.chdir(tmp_path)
    first = CliRunner().invoke(init, [])
    assert first.exit_code == 0

    second = CliRunner().invoke(init, [])
    assert second.exit_code == 1
    assert "error: .dojo already exists" in second.stderr
    assert "--force" in second.stderr


def test_init_force_re_runs_on_existing(tmp_path, monkeypatch):
    """--force lets the user reinitialise without manual cleanup."""
    monkeypatch.chdir(tmp_path)
    CliRunner().invoke(init, [])
    result = CliRunner().invoke(init, ["--force"])
    assert result.exit_code == 0
    assert "Reinitialized existing ByteDojo repository" in result.output


def test_init_force_on_fresh_dir_says_initialized(tmp_path, monkeypatch):
    """--force on a directory with no .dojo is just a normal init."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(init, ["--force"])
    assert result.exit_code == 0
    assert "Initialized empty ByteDojo repository" in result.output
