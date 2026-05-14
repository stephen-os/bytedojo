"""Tests for `dojo pick`."""

import pytest
from click.testing import CliRunner

from bytedojo.commands.subcommands.pick import pick
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.services.pick_service import PickResult, PickScope


# --------------------------------------------------------------------------- #
# Pre-flight                                                                  #
# --------------------------------------------------------------------------- #

def test_pick_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(pick, [])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


def test_pick_unknown_difficulty_string_via_click_choice(repo, monkeypatch):
    """click.Choice rejects values outside the whitelist."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(pick, ["-d", "extreme"])
    assert result.exit_code != 0


def test_pick_unknown_tag_string_filtered_out(repo, monkeypatch):
    """An unknown tag is dropped with a logger warning; if it's the only tag,
    the command errors with 'No valid tags'."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(pick, ["-t", "made-up-tag-xyz"])
    assert result.exit_code != 0
    assert "No valid tags" in result.output


# --------------------------------------------------------------------------- #
# Service wiring                                                              #
# --------------------------------------------------------------------------- #

def _detail(pid: int = 1, *, difficulty=ProblemDifficulty.EASY,
            tags=None) -> ProblemDetail:
    return ProblemDetail(
        id=pid, title=f"P{pid}", slug=f"p{pid}",
        difficulty=difficulty, description="x",
        tags=tags or [],
    )


@pytest.fixture
def stub_pick(monkeypatch):
    """Replace PickService.pick; capture args + return a controllable result."""
    state = {"calls": [], "result": None}

    def fake_pick(self, repo, *, difficulty=ProblemDifficulty.NONE, tags=None,
                  scope=PickScope.UNSOLVED):
        state["calls"].append({
            "difficulty": difficulty, "tags": tags, "scope": scope,
        })
        if state["result"] is not None:
            return state["result"]
        picked = _detail(1)
        return PickResult(picked=picked, candidates=[picked],
                          total_count=1, registered_count=0, scope=scope)

    monkeypatch.setattr(
        "bytedojo.services.pick_service.PickService.pick", fake_pick,
    )
    return state


def test_pick_default_scope_is_unsolved(repo, monkeypatch, stub_pick):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(pick, [])
    assert result.exit_code == 0
    assert stub_pick["calls"][0]["scope"] is PickScope.UNSOLVED


def test_pick_all_scope(repo, monkeypatch, stub_pick):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(pick, ["--all"])
    assert stub_pick["calls"][0]["scope"] is PickScope.ALL


def test_pick_solved_scope(repo, monkeypatch, stub_pick):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(pick, ["--solved"])
    assert stub_pick["calls"][0]["scope"] is PickScope.SOLVED


def test_pick_difficulty_string_propagates(repo, monkeypatch, stub_pick):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(pick, ["-d", "medium"])
    assert stub_pick["calls"][0]["difficulty"] is ProblemDifficulty.MEDIUM


def test_pick_tag_propagates(repo, monkeypatch, stub_pick):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(pick, ["-t", "array"])
    assert stub_pick["calls"][0]["tags"] == [ProblemTag.ARRAY]


def test_pick_multiple_tags(repo, monkeypatch, stub_pick):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(pick, ["-t", "array", "-t", "hash-table"])
    assert stub_pick["calls"][0]["tags"] == [ProblemTag.ARRAY, ProblemTag.HASH_TABLE]


def test_pick_drops_unknown_tag_but_keeps_known(repo, monkeypatch, stub_pick):
    """Unknown tags are dropped (with warning), but a co-passed valid tag remains."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(pick, ["-t", "array", "-t", "made-up-tag"])
    assert result.exit_code == 0
    assert stub_pick["calls"][0]["tags"] == [ProblemTag.ARRAY]


# --------------------------------------------------------------------------- #
# Output rendering                                                            #
# --------------------------------------------------------------------------- #

def test_pick_renders_picked_problem(repo, monkeypatch, stub_pick):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(pick, [])
    assert result.exit_code == 0
    assert "P1" in result.output
    assert "Easy" in result.output
    assert "dojo fetch 1" in result.output


def test_pick_renders_tag_list(repo, monkeypatch, stub_pick):
    """Tags appear with the comma-separated tag list."""
    picked = _detail(1, tags=[ProblemTag.ARRAY, ProblemTag.HASH_TABLE])
    stub_pick["result"] = PickResult(
        picked=picked, candidates=[picked],
        total_count=1, registered_count=0, scope=PickScope.UNSOLVED,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(pick, [])
    assert "array" in result.output
    assert "hash-table" in result.output


def test_pick_no_candidates_unsolved(repo, monkeypatch, stub_pick):
    """UNSOLVED with everything registered -> 'all already registered' message."""
    stub_pick["result"] = PickResult(
        picked=None, candidates=[],
        total_count=5, registered_count=5, scope=PickScope.UNSOLVED,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(pick, [])
    assert "already registered" in result.output


def test_pick_no_candidates_solved(repo, monkeypatch, stub_pick):
    stub_pick["result"] = PickResult(
        picked=None, candidates=[],
        total_count=5, registered_count=0, scope=PickScope.SOLVED,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(pick, ["--solved"])
    assert "No registered problems" in result.output


def test_pick_empty_pool(repo, monkeypatch, stub_pick):
    """No matches at all -> 'No problems found' (different from 'all registered')."""
    stub_pick["result"] = PickResult(
        picked=None, candidates=[],
        total_count=0, registered_count=0, scope=PickScope.UNSOLVED,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(pick, [])
    assert "No problems found" in result.output
