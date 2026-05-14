"""Tests for `dojo query`."""

import pytest
from click.testing import CliRunner

from bytedojo.commands.subcommands.query import query
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag


# --------------------------------------------------------------------------- #
# Pre-flight                                                                  #
# --------------------------------------------------------------------------- #

def test_query_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(query, [])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


def test_query_unknown_difficulty_via_click_choice(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(query, ["-d", "extreme"])
    assert result.exit_code != 0


# --------------------------------------------------------------------------- #
# --list-tags shortcut (no interactive prompt)                                #
# --------------------------------------------------------------------------- #

def test_list_tags_outputs_known_tags(repo, monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.problem_service.get_all_tags",
        lambda: [ProblemTag.ARRAY, ProblemTag.HASH_TABLE, ProblemTag.TREE],
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(query, ["--list-tags"])
    assert result.exit_code == 0
    assert "Available tags" in result.output
    assert "array" in result.output
    assert "hash-table" in result.output
    assert "tree" in result.output


def test_list_tags_empty_message(repo, monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.problem_service.get_all_tags", lambda: [],
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(query, ["--list-tags"])
    assert result.exit_code == 0
    assert "No tags found" in result.output


# --------------------------------------------------------------------------- #
# Interactive listing (provide 'q' to exit immediately)                       #
# --------------------------------------------------------------------------- #

def _detail(pid: int = 1, *, title: str = "P", difficulty=ProblemDifficulty.EASY,
            tags=None) -> ProblemDetail:
    return ProblemDetail(
        id=pid, title=title, slug=f"p{pid}",
        difficulty=difficulty, description=f"desc {pid}",
        tags=tags or [],
    )


@pytest.fixture
def stub_query(monkeypatch):
    """Replace problem_service.query_problems + AttemptService.get_all_stats."""
    state = {"problems": [], "calls": []}

    def fake_query(**kwargs):
        state["calls"].append(kwargs)
        return list(state["problems"])

    monkeypatch.setattr(
        "bytedojo.services.problem_service.query_problems", fake_query,
    )
    monkeypatch.setattr(
        "bytedojo.core.attempt_service.AttemptService.get_all_stats",
        lambda self: {},
    )
    return state


def test_query_no_results_message(repo, monkeypatch, stub_query):
    stub_query["problems"] = []
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(query, [])
    assert result.exit_code == 0
    assert "No problems found" in result.output


def test_query_renders_pagination_header(repo, monkeypatch, stub_query):
    stub_query["problems"] = [_detail(i) for i in range(1, 6)]
    monkeypatch.chdir(repo.root_dir)
    # 'q' to exit the prompt loop immediately after the first render.
    result = CliRunner().invoke(query, [], input="q\n")
    assert result.exit_code == 0
    assert "Problems (Page 1/1, 5 total)" in result.output


def test_query_passes_difficulty_filter(repo, monkeypatch, stub_query):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(query, ["-d", "medium"], input="q\n")
    assert stub_query["calls"][0]["difficulty"] is ProblemDifficulty.MEDIUM


def test_query_passes_tag_filter(repo, monkeypatch, stub_query):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(query, ["-t", "array"], input="q\n")
    assert stub_query["calls"][0]["tags"] == [ProblemTag.ARRAY]


def test_query_passes_comma_separated_tags(repo, monkeypatch, stub_query):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(query, ["-t", "array,hash-table"], input="q\n")
    assert stub_query["calls"][0]["tags"] == [ProblemTag.ARRAY, ProblemTag.HASH_TABLE]


def test_query_passes_search(repo, monkeypatch, stub_query):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(query, ["-s", "binary"], input="q\n")
    assert stub_query["calls"][0]["search"] == "binary"


def test_query_passes_id_range(repo, monkeypatch, stub_query):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(query, ["1..3"], input="q\n")
    assert stub_query["calls"][0]["ids"] == [1, 2, 3]


def test_query_invalid_id_format(repo, monkeypatch, stub_query):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(query, ["abc"], input="q\n")
    assert result.exit_code != 0
    assert "Invalid problem ID" in result.output


# --------------------------------------------------------------------------- #
# Pagination loop navigation                                                  #
# --------------------------------------------------------------------------- #

def test_query_navigates_to_next_page(repo, monkeypatch, stub_query):
    """`n` advances; second page header appears in the output."""
    stub_query["problems"] = [_detail(i) for i in range(1, 51)]
    monkeypatch.chdir(repo.root_dir)
    # n then q.
    result = CliRunner().invoke(
        query, ["--per-page", "20"], input="n\nq\n",
    )
    assert "Page 2/3" in result.output


def test_query_jump_to_invalid_page_reports_error(repo, monkeypatch, stub_query):
    stub_query["problems"] = [_detail(i) for i in range(1, 11)]
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(
        query, ["--per-page", "5"], input="9\nq\n",
    )
    assert "Invalid page" in result.output


def test_query_jump_to_negative_page_reports_error(repo, monkeypatch, stub_query):
    stub_query["problems"] = [_detail(i) for i in range(1, 11)]
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(
        query, ["--per-page", "5"], input="garbage\nq\n",
    )
    assert "Invalid input" in result.output
