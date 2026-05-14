"""Tests for `dojo stats`."""

from click.testing import CliRunner

from bytedojo.commands.subcommands.stats import stats

from tests.services.conftest import insert_registered_problem


# --------------------------------------------------------------------------- #
# No repo                                                                     #
# --------------------------------------------------------------------------- #

def test_stats_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(stats, [])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


# --------------------------------------------------------------------------- #
# Summary mode (default)                                                      #
# --------------------------------------------------------------------------- #

def test_stats_empty_summary(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(stats, [])
    assert result.exit_code == 0
    assert "Repository Statistics" in result.output
    assert "Total problems: 0" in result.output


def test_stats_summary_with_problems(repo, monkeypatch):
    insert_registered_problem(repo, pid=1, slug="a", title="A")
    insert_registered_problem(repo, pid=2, slug="b", title="B")
    monkeypatch.chdir(repo.root_dir)

    result = CliRunner().invoke(stats, [])
    assert result.exit_code == 0
    assert "Total problems: 2" in result.output
    assert "By difficulty:" in result.output
    assert "By source:" in result.output


# --------------------------------------------------------------------------- #
# --list mode                                                                 #
# --------------------------------------------------------------------------- #

def test_stats_list_empty_shows_friendly_message(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(stats, ["--list"])
    assert result.exit_code == 0
    assert "No problems found" in result.output


def test_stats_list_renders_per_problem_rows(repo, monkeypatch):
    insert_registered_problem(repo, pid=1, slug="a", title="Two Sum")
    insert_registered_problem(repo, pid=2, slug="b", title="Add Two Numbers")
    monkeypatch.chdir(repo.root_dir)

    result = CliRunner().invoke(stats, ["--list"])
    assert result.exit_code == 0
    assert "Found 2 problem(s)" in result.output
    assert "Two Sum" in result.output
    assert "Add Two Numbers" in result.output


def test_stats_list_difficulty_filter(repo, monkeypatch):
    insert_registered_problem(repo, pid=1, slug="a", title="A",
                              difficulty="Easy")
    insert_registered_problem(repo, pid=2, slug="b", title="B",
                              difficulty="Hard")
    monkeypatch.chdir(repo.root_dir)

    result = CliRunner().invoke(stats, ["--list", "-d", "easy"])
    assert result.exit_code == 0
    assert "Found 1 problem(s)" in result.output
    assert "Two Sum" not in result.output


def test_stats_list_verbose_shows_attempt_placeholder(repo, monkeypatch):
    insert_registered_problem(repo, pid=1, slug="a", title="A")
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(stats, ["--list", "--verbose"])
    assert result.exit_code == 0
    assert "attempts:" in result.output


def test_stats_invalid_difficulty_rejected(repo, monkeypatch):
    """click.Choice validates the value before the command body runs."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(stats, ["--list", "-d", "wizard"])
    assert result.exit_code != 0
    assert "Invalid value" in result.output or "wizard" in result.output
