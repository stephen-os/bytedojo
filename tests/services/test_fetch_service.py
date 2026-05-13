"""Tests for FetchService."""

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.services.fetch_service import (
    FetchBatchResult,
    FetchResult,
    FetchService,
)

from tests.services.conftest import make_problem


# --------------------------------------------------------------------------- #
# FetchResult                                                                 #
# --------------------------------------------------------------------------- #

def test_fetch_result_failed_when_neither_success_nor_skipped():
    r = FetchResult(problem_id=1, error="x")
    assert r.failed is True


def test_fetch_result_success_not_failed():
    r = FetchResult(problem_id=1, success=True)
    assert r.failed is False


def test_fetch_result_skipped_not_failed():
    r = FetchResult(problem_id=1, skipped=True)
    assert r.failed is False


def test_fetch_result_title_falls_back_to_empty_when_no_problem():
    assert FetchResult(problem_id=1).title == ""


def test_fetch_result_title_from_problem_detail():
    p = make_problem(title="Two Sum")
    assert FetchResult(problem_id=1, problem=p).title == "Two Sum"


# --------------------------------------------------------------------------- #
# FetchBatchResult                                                            #
# --------------------------------------------------------------------------- #

def test_batch_result_counts():
    results = [
        FetchResult(problem_id=1, success=True),
        FetchResult(problem_id=2, skipped=True),
        FetchResult(problem_id=3, error="x"),
        FetchResult(problem_id=4, success=True),
    ]
    batch = FetchBatchResult(results=results)
    assert batch.placed_count == 2
    assert batch.skipped_count == 1
    assert batch.failed_count == 1


# --------------------------------------------------------------------------- #
# FetchService.fetch_problem — just routes to problem_service.get_problem     #
# --------------------------------------------------------------------------- #

@pytest.fixture
def stub_get_problem(monkeypatch):
    """Replace problem_service.get_problem with a controllable fake."""
    state = {"problem": None}

    def fake_get(pid):
        return state["problem"]

    monkeypatch.setattr(
        "bytedojo.services.fetch_service.problem_service.get_problem", fake_get,
    )
    return state


def test_fetch_problem_returns_problem_when_found(stub_get_problem):
    p = make_problem(pid=1)
    stub_get_problem["problem"] = p
    assert FetchService().fetch_problem(1) is p


def test_fetch_problem_returns_none_when_missing(stub_get_problem):
    stub_get_problem["problem"] = None
    assert FetchService().fetch_problem(99) is None


# --------------------------------------------------------------------------- #
# fetch_and_place — default mode (register + place)                           #
# --------------------------------------------------------------------------- #

def test_fetch_and_place_problem_not_found(repo, stub_get_problem):
    stub_get_problem["problem"] = None
    result = FetchService().fetch_and_place(repo, 99, CodeLanguage.PYTHON)
    assert result.failed
    assert result.error == "not found"


def test_fetch_and_place_default_mode_places_solution_file(repo, stub_get_problem):
    """Successful fetch writes solution.py at problems/<slug>/python3/v001/."""
    stub_get_problem["problem"] = make_problem(pid=1, slug="two-sum")
    result = FetchService().fetch_and_place(repo, 1, CodeLanguage.PYTHON)

    assert result.success
    assert result.target_path.exists()
    assert result.target_path.name == "solution.py"
    assert "0001-two-sum" in str(result.target_path)
    assert result.version == 1


def test_fetch_and_place_default_skips_already_registered(repo, stub_get_problem):
    """Without --force, re-running the default mode is a skip."""
    stub_get_problem["problem"] = make_problem(pid=1)
    svc = FetchService()
    first = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON)
    second = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON)

    assert first.success
    assert second.skipped
    assert second.skip_reason == "already registered"


def test_fetch_and_place_force_creates_new_attempt(repo, stub_get_problem):
    """--force registers a new attempt even if one already exists."""
    stub_get_problem["problem"] = make_problem(pid=1)
    svc = FetchService()
    svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON)
    forced = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON, force=True)

    assert forced.success
    assert forced.version == 2


# --------------------------------------------------------------------------- #
# fetch_and_place — --version mode (rewrite existing version)                 #
# --------------------------------------------------------------------------- #

def test_fetch_and_place_version_rewrites_existing(repo, stub_get_problem):
    """--version N rewrites v{N} in place."""
    stub_get_problem["problem"] = make_problem(pid=1, slug="two-sum")
    svc = FetchService()
    placed = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON)
    original_mtime = placed.target_path.stat().st_mtime_ns

    refetched = svc.fetch_and_place(repo, 1, CodeLanguage.PYTHON, version=1)
    assert refetched.success
    assert refetched.target_path == placed.target_path
    assert refetched.target_path.stat().st_mtime_ns >= original_mtime


def test_fetch_and_place_version_not_found_is_skipped(repo, stub_get_problem):
    """Requesting --version N when N doesn't exist returns a skip with reason."""
    stub_get_problem["problem"] = make_problem(pid=1, slug="two-sum")
    result = FetchService().fetch_and_place(
        repo, 1, CodeLanguage.PYTHON, version=99,
    )
    assert result.skipped
    assert "v99" in result.skip_reason


# --------------------------------------------------------------------------- #
# fetch_and_place — --path mode (scratch, untracked)                          #
# --------------------------------------------------------------------------- #

def test_fetch_and_place_custom_path_writes_to_scratch_dir(repo, stub_get_problem, tmp_path):
    """--path writes into a custom dir, doesn't register in the DB."""
    scratch = tmp_path / "scratch"
    stub_get_problem["problem"] = make_problem(pid=1, slug="two-sum")
    result = FetchService().fetch_and_place(
        repo, 1, CodeLanguage.PYTHON, custom_path=scratch,
    )

    assert result.success
    assert scratch in result.target_path.parents
    assert result.version is None    # untracked

    # No DB row was created.
    with repo.open_db() as db:
        assert db.get_problem("leetcode", 1, "python3") is None


# --------------------------------------------------------------------------- #
# fetch_and_place_batch                                                       #
# --------------------------------------------------------------------------- #

def test_fetch_and_place_batch_aggregates(repo, monkeypatch):
    """Batch calls fetch_and_place per id and aggregates outcomes."""
    problems = {
        1: make_problem(pid=1, slug="a"),
        2: make_problem(pid=2, slug="b"),
        3: None,   # signals "not found" -> failed
    }
    monkeypatch.setattr(
        "bytedojo.services.fetch_service.problem_service.get_problem",
        lambda pid: problems.get(pid),
    )

    batch = FetchService().fetch_and_place_batch(
        repo, [1, 2, 3], CodeLanguage.PYTHON,
    )
    assert len(batch.results) == 3
    assert batch.placed_count == 2
    assert batch.failed_count == 1
    assert batch.skipped_count == 0


def test_fetch_and_place_batch_skip_then_force(repo, monkeypatch):
    """Batch with the same id twice -> second is skipped without --force."""
    problems = {1: make_problem(pid=1, slug="a")}
    monkeypatch.setattr(
        "bytedojo.services.fetch_service.problem_service.get_problem",
        lambda pid: problems.get(pid),
    )

    batch = FetchService().fetch_and_place_batch(
        repo, [1, 1], CodeLanguage.PYTHON,
    )
    assert batch.placed_count == 1
    assert batch.skipped_count == 1
