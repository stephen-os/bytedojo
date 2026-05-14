"""Tests for `dojo fetch`."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from bytedojo.commands.subcommands.fetch import fetch
from bytedojo.services.fetch_service import FetchBatchResult, FetchResult

from tests.conftest import make_problem


# --------------------------------------------------------------------------- #
# Pre-flight                                                                  #
# --------------------------------------------------------------------------- #

def test_fetch_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(fetch, ["1"])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


def test_fetch_requires_problem_ids(repo, monkeypatch):
    """Click marks `arguments` as required — no IDs means a usage error."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, [])
    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Usage" in result.output


# --------------------------------------------------------------------------- #
# Mode validation                                                             #
# --------------------------------------------------------------------------- #

def test_version_and_path_are_mutually_exclusive(repo, monkeypatch, tmp_path):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(
        fetch, ["1", "--version", "1", "--path", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_force_with_version_errors(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1", "--force", "--version", "1"])
    assert result.exit_code != 0
    assert "--force" in result.output and "--version" in result.output


def test_force_with_path_errors(repo, monkeypatch, tmp_path):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1", "--force", "--path", str(tmp_path)])
    assert result.exit_code != 0
    assert "scratch" in result.output.lower()


# --------------------------------------------------------------------------- #
# Service wiring (mocked)                                                     #
# --------------------------------------------------------------------------- #

@pytest.fixture
def captured(monkeypatch):
    """Replace FetchService.fetch_and_place_batch and capture the call."""
    state = {"calls": []}

    def fake_batch(self, repo, ids, lang, *, force, version, custom_path):
        state["calls"].append({
            "ids": ids, "lang": lang, "force": force,
            "version": version, "custom_path": custom_path,
        })
        return FetchBatchResult(results=[
            FetchResult(
                problem_id=pid, success=True,
                problem=make_problem(pid=pid, slug=f"p{pid}", title=f"Problem {pid}"),
                target_path=repo.root_dir / "problems" / f"{pid:04d}-x" / "python3" / "v001" / "solution.py",
                version=1,
            )
            for pid in ids
        ])

    monkeypatch.setattr(
        "bytedojo.services.fetch_service.FetchService.fetch_and_place_batch",
        fake_batch,
    )
    return state


def test_fetch_default_mode_dispatches_to_service(repo, monkeypatch, captured):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1"])
    assert result.exit_code == 0
    assert len(captured["calls"]) == 1
    call = captured["calls"][0]
    assert call["ids"] == [1]
    assert call["force"] is False
    assert call["version"] is None
    assert call["custom_path"] is None


def test_fetch_parses_id_range(repo, monkeypatch, captured):
    """`1..3` expands to [1,2,3] via problem_service.parse_problem_ids."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1..3"])
    assert result.exit_code == 0
    assert captured["calls"][0]["ids"] == [1, 2, 3]


def test_fetch_python_flag_sets_language(repo, monkeypatch, captured):
    """--python flag value 'python3' goes through to the service as CodeLanguage.PYTHON."""
    from bytedojo.core.models.code_language import CodeLanguage
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1", "--python"])
    assert result.exit_code == 0
    assert captured["calls"][0]["lang"] is CodeLanguage.PYTHON


def test_fetch_java_flag(repo, monkeypatch, captured):
    from bytedojo.core.models.code_language import CodeLanguage
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1", "--java"])
    assert result.exit_code == 0
    assert captured["calls"][0]["lang"] is CodeLanguage.JAVA


def test_fetch_cpp_flag(repo, monkeypatch, captured):
    from bytedojo.core.models.code_language import CodeLanguage
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1", "--cpp"])
    assert result.exit_code == 0
    assert captured["calls"][0]["lang"] is CodeLanguage.CPP


def test_fetch_force_propagates(repo, monkeypatch, captured):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(fetch, ["1", "--force"])
    assert captured["calls"][0]["force"] is True


def test_fetch_version_mode_propagates(repo, monkeypatch, captured):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(fetch, ["1", "--version", "2"])
    assert captured["calls"][0]["version"] == 2


def test_fetch_path_mode_propagates(repo, monkeypatch, captured, tmp_path):
    scratch = tmp_path / "scratch"
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(fetch, ["1", "--path", str(scratch)])
    assert captured["calls"][0]["custom_path"] == scratch


# --------------------------------------------------------------------------- #
# Mode banner + summary                                                       #
# --------------------------------------------------------------------------- #

def test_fetch_default_mode_banner(repo, monkeypatch, captured):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1"])
    assert "Fetching 1 problem(s)" in result.output


def test_fetch_version_mode_banner(repo, monkeypatch, captured):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1", "--version", "3"])
    assert "Refetching" in result.output
    assert "v3" in result.output


def test_fetch_path_mode_banner(repo, monkeypatch, captured, tmp_path):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1", "--path", str(tmp_path)])
    assert "untracked" in result.output


def test_fetch_summary_line(repo, monkeypatch, captured):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(fetch, ["1,2"])
    assert "Done:" in result.output
    assert "2 placed" in result.output


# --------------------------------------------------------------------------- #
# Skip + failure result rendering                                             #
# --------------------------------------------------------------------------- #

def test_fetch_renders_already_registered_skip(repo, monkeypatch):
    """Skip path with reason 'already registered' surfaces actionable hint."""
    def fake_batch(self, repo, ids, lang, **kw):
        return FetchBatchResult(results=[
            FetchResult(
                problem_id=1, skipped=True,
                problem=make_problem(pid=1),
                skip_reason="already registered",
            ),
        ])

    monkeypatch.setattr(
        "bytedojo.services.fetch_service.FetchService.fetch_and_place_batch",
        fake_batch,
    )
    monkeypatch.chdir(repo.root_dir)

    result = CliRunner().invoke(fetch, ["1"])
    assert result.exit_code == 0
    assert "already registered" in result.output
    assert "--force" in result.output


def test_fetch_renders_failed_result_to_stderr(repo, monkeypatch):
    def fake_batch(self, repo, ids, lang, **kw):
        return FetchBatchResult(results=[
            FetchResult(problem_id=999, error="not found"),
        ])

    monkeypatch.setattr(
        "bytedojo.services.fetch_service.FetchService.fetch_and_place_batch",
        fake_batch,
    )
    monkeypatch.chdir(repo.root_dir)

    result = CliRunner().invoke(fetch, ["999"])
    assert "not found" in result.output
