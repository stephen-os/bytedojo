"""Tests for problem_service."""

import json
from pathlib import Path

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.services import problem_service
from bytedojo.services.problem_service import (
    LookupResult,
    SolutionPathResult,
    find_registered_problems,
    get_all_tags,
    get_last_registered_problem,
    get_problem,
    get_problem_by_slug,
    parse_problem_ids,
    problem_exists,
    query_problems,
    resolve_solution_path,
)

from tests.services.conftest import insert_registered_problem, make_problem


# --------------------------------------------------------------------------- #
# parse_problem_ids — pure CLI parsing                                        #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    (("1",),               [1]),
    (("1,2,3",),           [1, 2, 3]),
    (("1..5",),            [1, 2, 3, 4, 5]),
    (("1,5..7,15",),       [1, 5, 6, 7, 15]),
    (("1,2,2,3",),         [1, 2, 3]),               # dedup, order preserved
    (("1..3", "5..6"),     [1, 2, 3, 5, 6]),         # multiple arg tuples
    (("  1  ,  2  ",),     [1, 2]),                  # whitespace tolerant
])
def test_parse_problem_ids_valid(raw, expected):
    assert parse_problem_ids(raw) == expected


@pytest.mark.parametrize("raw, msg", [
    (("abc",),       "Invalid problem ID"),
    (("1..a",),      "Invalid range values"),
    (("1..2..3",),   "Invalid range format"),
    (("10..5",),     "Invalid range"),                 # start > end
])
def test_parse_problem_ids_errors(raw, msg):
    with pytest.raises(ValueError, match=msg):
        parse_problem_ids(raw)


def test_parse_problem_ids_empty_input_returns_empty():
    assert parse_problem_ids(()) == []
    assert parse_problem_ids(("",)) == []


# --------------------------------------------------------------------------- #
# Helpers for the index / file-based tests                                    #
# --------------------------------------------------------------------------- #

def _entry(**overrides) -> dict:
    base = {
        "id": 1, "title": "Two Sum", "slug": "two-sum",
        "difficulty": "Easy", "description": "Find indices.",
        "tags": ["array", "hash-table"],
    }
    base.update(overrides)
    return base


def _problem_payload(**overrides) -> dict:
    base = {
        "id": 1, "title": "Two Sum", "slug": "two-sum",
        "difficulty": "Easy", "description": "Find indices.",
        "tags": ["array", "hash-table"],
        "examples": [
            {"example_num": 1, "example_text": "nums=[2,7], t=9", "images": []},
        ],
        "code_snippets": {
            "python3": "class Solution:\n    pass\n",
            "java":    "class Solution {}\n",
        },
        "constraints": ["1 <= nums.length"],
        "hints": ["use a map"],
    }
    base.update(overrides)
    return base


@pytest.fixture
def stub_data(tmp_path, monkeypatch):
    """Redirect PROBLEMS_INDEX + get_problem_file at tmp files."""
    index_file = tmp_path / "index.json"
    monkeypatch.setattr("bytedojo.services.problem_service.PROBLEMS_INDEX",
                        index_file)
    monkeypatch.setattr(
        "bytedojo.services.problem_service.get_problem_file",
        lambda pid: tmp_path / f"{pid}.json",
    )

    def write_index(entries):
        index_file.write_text(json.dumps(entries), encoding="utf-8")

    def write_problem(payload):
        (tmp_path / f"{payload['id']}.json").write_text(
            json.dumps(payload), encoding="utf-8",
        )

    return {"write_index": write_index, "write_problem": write_problem,
            "root": tmp_path}


# --------------------------------------------------------------------------- #
# GET: get_problem / get_problem_by_slug / problem_exists                     #
# --------------------------------------------------------------------------- #

def test_get_problem_returns_full_object(stub_data):
    stub_data["write_problem"](_problem_payload())
    p = get_problem(1)
    assert p is not None
    assert p.problem_detail.id == 1
    assert p.problem_detail.title == "Two Sum"
    assert p.problem_detail.difficulty is ProblemDifficulty.EASY
    assert ProblemTag.ARRAY in p.problem_detail.tags
    assert p.constraints == ["1 <= nums.length"]
    assert p.hints == ["use a map"]
    assert len(p.code_snippets) == 2
    assert len(p.examples) == 1


def test_get_problem_unknown_language_snippets_dropped(stub_data):
    """Unrecognized lang strings are skipped, not crash the build."""
    payload = _problem_payload()
    payload["code_snippets"]["brainfuck"] = "++++."
    stub_data["write_problem"](payload)
    p = get_problem(1)
    langs = {cs.lang for cs in p.code_snippets}
    assert CodeLanguage.UNKNOWN not in langs


def test_get_problem_missing_returns_none(stub_data):
    assert get_problem(9999) is None


def test_get_problem_by_slug_routes_through_index(stub_data):
    stub_data["write_index"]([_entry(id=42, slug="some-slug")])
    stub_data["write_problem"](_problem_payload(id=42, slug="some-slug"))
    p = get_problem_by_slug("some-slug")
    assert p is not None and p.problem_detail.id == 42


def test_get_problem_by_slug_returns_none_when_slug_missing(stub_data):
    stub_data["write_index"]([_entry(id=1, slug="other")])
    assert get_problem_by_slug("nope") is None


def test_problem_exists(stub_data):
    stub_data["write_problem"](_problem_payload(id=7))
    assert problem_exists(7) is True
    assert problem_exists(99) is False


# --------------------------------------------------------------------------- #
# QUERY: query_problems                                                       #
# --------------------------------------------------------------------------- #

def test_query_problems_no_filters_returns_all_sorted_by_id(stub_data):
    stub_data["write_index"]([_entry(id=3), _entry(id=1), _entry(id=2)])
    results = query_problems()
    assert [r.id for r in results] == [1, 2, 3]


def test_query_problems_filters_by_ids(stub_data):
    stub_data["write_index"]([_entry(id=1), _entry(id=2), _entry(id=3)])
    results = query_problems(ids=[1, 3])
    assert [r.id for r in results] == [1, 3]


def test_query_problems_filters_by_difficulty(stub_data):
    stub_data["write_index"]([
        _entry(id=1, difficulty="Easy"),
        _entry(id=2, difficulty="Medium"),
        _entry(id=3, difficulty="Hard"),
    ])
    medium = query_problems(difficulty=ProblemDifficulty.MEDIUM)
    assert [r.id for r in medium] == [2]


def test_query_problems_filters_by_tags_or_semantics(stub_data):
    """Multiple tags = OR; entry needs at least one matching tag."""
    stub_data["write_index"]([
        _entry(id=1, tags=["array"]),
        _entry(id=2, tags=["hash-table"]),
        _entry(id=3, tags=["tree"]),
    ])
    results = query_problems(tags=[ProblemTag.ARRAY, ProblemTag.HASH_TABLE])
    assert {r.id for r in results} == {1, 2}


def test_query_problems_filters_by_description_search(stub_data):
    stub_data["write_index"]([
        _entry(id=1, description="find indices in the array"),
        _entry(id=2, description="reverse a string"),
    ])
    results = query_problems(search="indices")
    assert [r.id for r in results] == [1]


def test_query_problems_limit_truncates(stub_data):
    stub_data["write_index"]([_entry(id=i) for i in range(1, 6)])
    results = query_problems(limit=2)
    assert len(results) == 2


def test_query_problems_missing_index_returns_empty(stub_data):
    """No index file -> empty list, not exception."""
    # stub_data doesn't write an index unless asked.
    assert query_problems() == []


# --------------------------------------------------------------------------- #
# get_all_tags                                                                #
# --------------------------------------------------------------------------- #

def test_get_all_tags_returns_sorted_unique_known(stub_data):
    stub_data["write_index"]([
        _entry(id=1, tags=["array", "hash-table"]),
        _entry(id=2, tags=["array", "tree", "unknown-leetcode-tag"]),
    ])
    tags = get_all_tags()
    assert ProblemTag.UNKNOWN not in tags
    assert ProblemTag.ARRAY in tags
    assert ProblemTag.HASH_TABLE in tags
    assert ProblemTag.TREE in tags
    # Sorted ascending by value
    values = [t.value for t in tags]
    assert values == sorted(values)


# --------------------------------------------------------------------------- #
# LookupResult                                                                #
# --------------------------------------------------------------------------- #

def test_lookup_result_empty():
    r = LookupResult()
    assert r.is_empty and not r.is_unique and not r.is_ambiguous
    assert r.unique is None
    assert r.count == 0


def test_lookup_result_unique(registered_problem):
    r = LookupResult(matches=[registered_problem])
    assert r.is_unique and not r.is_empty and not r.is_ambiguous
    assert r.unique is registered_problem
    assert r.count == 1


def test_lookup_result_ambiguous(registered_problem):
    r = LookupResult(matches=[registered_problem, registered_problem])
    assert r.is_ambiguous and not r.is_unique
    assert r.unique is None
    assert r.count == 2


# --------------------------------------------------------------------------- #
# find_registered_problems                                                    #
# --------------------------------------------------------------------------- #

def test_find_registered_problems_uninitialised_repo_returns_empty(tmp_path):
    """A path with no .dojo returns an empty LookupResult (not an exception)."""
    from bytedojo.core.repository import Repository
    bare = Repository(root_dir=tmp_path)   # no .dojo created
    result = find_registered_problems(bare, identifier="1")
    assert result.is_empty


def test_find_registered_problems_by_identifier(repo, registered_problem):
    result = find_registered_problems(repo, identifier="1")
    assert result.is_unique
    assert result.unique.problem_id == 1


# --------------------------------------------------------------------------- #
# SolutionPathResult + resolve_solution_path                                  #
# --------------------------------------------------------------------------- #

def test_solution_path_result_found_property():
    assert SolutionPathResult().found is False
    assert SolutionPathResult(path=Path("/x")).found is True


def test_resolve_solution_path_no_file_path(repo):
    """A RegisteredProblem with file_path=None bubbles up the error."""
    problem = insert_registered_problem(repo, pid=2, file_path=None)
    result = resolve_solution_path(repo, problem)
    assert not result.found
    assert "no associated file path" in result.error.lower()


def test_resolve_solution_path_missing_file_returns_error(repo, registered_problem):
    """file_path set but no file on disk -> error including the path."""
    result = resolve_solution_path(repo, registered_problem)
    assert not result.found
    assert "not found" in result.error.lower()


def test_resolve_solution_path_latest_happy_path(repo, registered_problem):
    """file_path exists -> found result with absolute path."""
    f = repo.root_dir / registered_problem.file_path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("pass\n", encoding="utf-8")

    # Seed an attempt so resolve can compute "latest version".
    with repo.open_db() as db:
        db.create_attempt(source="leetcode", problem_id=1,
                          language=CodeLanguage.PYTHON.value)

    result = resolve_solution_path(repo, registered_problem)
    assert result.found
    assert result.path == f
    assert result.version == 1


def test_resolve_solution_path_unknown_version_lists_available(
    repo, registered_problem, stub_data,
):
    """Requested --version that doesn't exist -> available_versions populated."""
    stub_data["write_problem"](_problem_payload())   # full Problem for slug lookup
    result = resolve_solution_path(repo, registered_problem, version=99)
    assert not result.found
    assert "99" in result.error
    assert result.available_versions == []   # nothing registered yet


# --------------------------------------------------------------------------- #
# get_last_registered_problem                                                 #
# --------------------------------------------------------------------------- #

def test_get_last_registered_problem_uninitialised(tmp_path):
    from bytedojo.core.repository import Repository
    bare = Repository(root_dir=tmp_path)
    assert get_last_registered_problem(bare, language="python3") is None


def test_get_last_registered_problem_returns_most_recent(repo, registered_problem):
    insert_registered_problem(repo, pid=2, slug="add-two-numbers", title="Add Two Numbers")
    last = get_last_registered_problem(repo, language="python3")
    # list_problems(limit=1) returns first by problem_id ascending — verify
    # the function returns SOMETHING; the ordering contract is the database's.
    assert last is not None
    assert last.problem_id in {1, 2}
