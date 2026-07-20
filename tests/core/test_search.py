"""Tests for the search / fuzzy-match utilities in core/search.py."""

from pathlib import Path

import click
import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.search import (
    _fuzzy_match,
    _normalize,
    _score_match,
    find_problems,
    resolve_problem,
    select_problem,
)
from bytedojo.core.models.registered_problem import RegisteredProblem


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _problem(pid: int = 1, title: str = "Two Sum",
             description: str = "Find indices.") -> Problem:
    return Problem(
        problem_detail=ProblemDetail(
            id=pid, title=title, slug=title.lower().replace(" ", "-"),
            difficulty=ProblemDifficulty.EASY, description=description,
        ),
        code_snippets=[CodeSnippet(lang=CodeLanguage.PYTHON, code="pass")],
    )


def _registered(pid: int, title: str, description: str = "") -> RegisteredProblem:
    """Build a RegisteredProblem without going through the DB."""
    return RegisteredProblem.from_row({
        "id": pid, "source": "leetcode", "problem_id": str(pid),
        "language": "python3", "title": title, "difficulty": "Easy",
        "description": description, "file_path": "x.py",
        "status": "ungraded",
        "fetched_at": "2025-01-01T00:00:00",
        "last_graded": None, "notes": None,
    })


# --------------------------------------------------------------------------- #
# _normalize / _fuzzy_match                                                   #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("HELLO",         "hello"),
    ("  Padded  ",    "padded"),
    ("Mixed CASE",    "mixed case"),
])
def test_normalize_lowercases_and_strips(raw, expected):
    assert _normalize(raw) == expected


def test_fuzzy_match_substring():
    assert _fuzzy_match("sum", "Two Sum") is True


def test_fuzzy_match_case_insensitive():
    assert _fuzzy_match("two sum", "TWO SUM") is True


def test_fuzzy_match_words_in_order_or_not():
    """All query words must appear in text — order doesn't matter."""
    assert _fuzzy_match("sum two", "Two Sum") is True


def test_fuzzy_match_missing_word_returns_false():
    assert _fuzzy_match("sum tree", "Two Sum") is False


def test_fuzzy_match_empty_query_matches_anything():
    """Empty query is a substring of any text."""
    assert _fuzzy_match("", "anything") is True


# --------------------------------------------------------------------------- #
# _score_match — relevance ranking                                            #
# --------------------------------------------------------------------------- #

def test_score_exact_title_match_is_top():
    assert _score_match("two sum", _registered(1, "Two Sum")) == 100


def test_score_starts_with_query_is_high():
    assert _score_match("two", _registered(1, "Two Sum")) == 80


def test_score_substring_in_title():
    assert _score_match("sum", _registered(1, "Two Sum")) == 60


def test_score_all_query_words_in_title():
    """All query words present, but not as a contiguous substring."""
    assert _score_match("sum problem", _registered(1, "Sum Of Problem Inputs")) == 40


def test_score_partial_word_match():
    """At least one query word present; not all."""
    assert _score_match("sum xyz", _registered(1, "Two Sum")) == 20


def test_score_no_match_is_zero():
    assert _score_match("graph", _registered(1, "Two Sum")) == 0


def test_score_orders_high_to_low():
    """Higher relevance must always produce a strictly larger score."""
    p = _registered(1, "Two Sum")
    assert _score_match("two sum", p) > _score_match("two", p)
    assert _score_match("two", p) > _score_match("sum", p)
    assert _score_match("sum", p) > _score_match("sum problem", p)


# --------------------------------------------------------------------------- #
# find_problems — integration with repo + db                                  #
# --------------------------------------------------------------------------- #

def _seed(repo, **kwargs) -> int:
    """Insert a problem; return its DB row id."""
    problem = _problem(**kwargs)
    with repo.open_db() as db:
        db.register_problem(problem, source="leetcode",
                            language="python3", file_path="x.py")
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM problems WHERE problem_id = ?",
                       (str(kwargs.get("pid", 1)),))
        return cursor.fetchone()[0]


def test_find_problems_by_numeric_identifier(repo):
    _seed(repo, pid=1)
    _seed(repo, pid=2, title="Add Two Numbers")
    with repo.open_db() as db:
        matches = find_problems(db, identifier="2")
    assert [m.problem_id for m in matches] == [2]


def test_find_problems_by_identifier_returns_empty_when_unknown(repo):
    _seed(repo, pid=1)
    with repo.open_db() as db:
        matches = find_problems(db, identifier="99")
    assert matches == []


def test_find_problems_by_name_fuzzy(repo):
    _seed(repo, pid=1)
    _seed(repo, pid=2, title="Add Two Numbers")
    with repo.open_db() as db:
        matches = find_problems(db, name="two")
    # Both titles contain "two" — relevance order is the contract.
    titles = [m.title for m in matches]
    assert "Two Sum" in titles
    assert "Add Two Numbers" in titles


def test_find_problems_by_name_orders_by_score(repo):
    """Exact match outranks substring match."""
    _seed(repo, pid=1, title="Two Sum")
    _seed(repo, pid=2, title="Sum Of Two Squares")
    with repo.open_db() as db:
        matches = find_problems(db, name="two sum")
    # "Two Sum" is the exact match (score 100); "Sum Of Two Squares" is
    # a "all words present" match (score 40).
    assert matches[0].title == "Two Sum"


def test_find_problems_by_description(repo):
    _seed(repo, pid=1, description="hash table approach")
    _seed(repo, pid=2, title="Other", description="binary tree traversal")
    with repo.open_db() as db:
        matches = find_problems(db, desc="hash")
    assert [m.problem_id for m in matches] == [1]


def test_find_problems_no_criteria_returns_all_with_low_score(repo):
    """With no name/desc/identifier filters, every problem matches with score 1."""
    _seed(repo, pid=1)
    _seed(repo, pid=2, title="Other")
    with repo.open_db() as db:
        matches = find_problems(db)
    assert {m.problem_id for m in matches} == {1, 2}


def test_find_problems_name_no_match_excluded(repo):
    """A name filter that misses excludes the problem entirely."""
    _seed(repo, pid=1, title="Two Sum")
    with repo.open_db() as db:
        matches = find_problems(db, name="binary tree")
    assert matches == []


# --------------------------------------------------------------------------- #
# select_problem — non-interactive paths only                                 #
# --------------------------------------------------------------------------- #

def test_select_problem_empty_returns_none():
    assert select_problem([]) is None


def test_select_problem_single_match_returns_it_without_prompting():
    """One option -> no UI prompt needed, just return it."""
    only = _registered(1, "Two Sum")
    assert select_problem([only]) is only


# --------------------------------------------------------------------------- #
# resolve_problem — uses Repository.find (the search.py:232 fix)              #
# --------------------------------------------------------------------------- #

def test_resolve_problem_raises_when_no_repo_at_or_above_cwd(tmp_path, monkeypatch):
    """No .dojo anywhere up from cwd -> ClickException."""
    deep = tmp_path / "no" / "dojo"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    with pytest.raises(click.ClickException, match="No .dojo repository found"):
        resolve_problem(identifier="1")


def test_resolve_problem_walks_up_to_find_repo(repo, monkeypatch):
    """Run from a nested subdir of an initialised repo — find() climbs to it."""
    _seed(repo, pid=1)
    deep = repo.root_dir / "a" / "b"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    found = resolve_problem(identifier="1")
    assert found is not None
    assert found.problem_id == 1


def test_resolve_problem_raises_when_no_matches(repo, monkeypatch):
    """Repo exists, query finds nothing -> ClickException with criteria detail."""
    _seed(repo, pid=1)
    monkeypatch.chdir(repo.root_dir)
    with pytest.raises(click.ClickException, match="No problems found"):
        resolve_problem(identifier="999")


def test_resolve_problem_auto_select_skips_disambiguation(repo, monkeypatch):
    """auto_select=True returns the first match even when multiple match."""
    _seed(repo, pid=1, title="Two Sum")
    _seed(repo, pid=2, title="Add Two Numbers")
    monkeypatch.chdir(repo.root_dir)

    chosen = resolve_problem(name="two", auto_select=True)
    assert chosen is not None
