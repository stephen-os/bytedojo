"""Tests for the AttemptService versioned-attempts API."""

import pytest

from bytedojo.core.attempt_service import AttemptService
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_status import ProblemStatus


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _problem(pid: int = 1) -> Problem:
    return Problem(
        problem_detail=ProblemDetail(
            id=pid, title="Two Sum", slug="two-sum",
            difficulty=ProblemDifficulty.EASY, description="",
        ),
        code_snippets=[CodeSnippet(
            lang=CodeLanguage.PYTHON,
            code="class Solution:\n    def twoSum(self, nums, target):\n        pass",
        )],
    )


@pytest.fixture
def stub_get_problem(monkeypatch):
    """Replace problem_service.get_problem so tests don't read data/problems/."""
    state = {"problem": _problem()}
    monkeypatch.setattr(
        "bytedojo.core.attempt_service.problem_service.get_problem",
        lambda pid: state["problem"] if state["problem"] and state["problem"].problem_detail.id == pid else None,
    )
    return state


# --------------------------------------------------------------------------- #
# Uninitialised-repo guards                                                   #
# --------------------------------------------------------------------------- #

def test_create_attempt_returns_none_for_uninitialised_repo(tmp_path, stub_get_problem):
    """A path with no .dojo -> create_attempt declines and returns None."""
    from bytedojo.core.repository import Repository
    bare = Repository(root_dir=tmp_path)
    svc = AttemptService(repo=bare)
    assert svc.create_attempt(1, CodeLanguage.PYTHON) is None


def test_get_attempt_returns_none_for_uninitialised(tmp_path):
    from bytedojo.core.repository import Repository
    bare = Repository(root_dir=tmp_path)
    assert AttemptService(repo=bare).get_attempt(1, CodeLanguage.PYTHON) is None


def test_list_attempts_returns_empty_for_uninitialised(tmp_path):
    from bytedojo.core.repository import Repository
    bare = Repository(root_dir=tmp_path)
    assert AttemptService(repo=bare).list_attempts(1) == []


def test_update_status_returns_false_for_uninitialised(tmp_path):
    from bytedojo.core.repository import Repository
    bare = Repository(root_dir=tmp_path)
    ok = AttemptService(repo=bare).update_status(
        1, CodeLanguage.PYTHON, 1, ProblemStatus.PASSED,
    )
    assert ok is False


def test_increment_run_count_returns_false_for_uninitialised(tmp_path):
    from bytedojo.core.repository import Repository
    bare = Repository(root_dir=tmp_path)
    assert AttemptService(repo=bare).increment_run_count(1, CodeLanguage.PYTHON, 1) is False


def test_get_stats_returns_empty_for_uninitialised(tmp_path):
    from bytedojo.core.repository import Repository
    bare = Repository(root_dir=tmp_path)
    assert AttemptService(repo=bare).get_stats(1) == {}


def test_get_all_stats_returns_empty_for_uninitialised(tmp_path):
    from bytedojo.core.repository import Repository
    bare = Repository(root_dir=tmp_path)
    assert AttemptService(repo=bare).get_all_stats() == {}


# --------------------------------------------------------------------------- #
# create_attempt — happy path                                                 #
# --------------------------------------------------------------------------- #

def test_create_attempt_returns_none_when_problem_data_missing(repo, stub_get_problem):
    """Repo is initialised but get_problem returns None -> service returns None."""
    stub_get_problem["problem"] = None
    assert AttemptService(repo=repo).create_attempt(1, CodeLanguage.PYTHON) is None


def test_create_attempt_creates_folder_and_writes_starter(repo, stub_get_problem):
    attempt = AttemptService(repo=repo).create_attempt(1, CodeLanguage.PYTHON)
    assert attempt is not None
    assert attempt.version == 1

    solution = (
        repo.problems_dir / "0001-two-sum" / "python3" / "v001" / "solution.py"
    )
    assert solution.exists()
    assert "class Solution" in solution.read_text(encoding="utf-8")


def test_create_attempt_increments_versions(repo, stub_get_problem):
    svc = AttemptService(repo=repo)
    a1 = svc.create_attempt(1, CodeLanguage.PYTHON)
    a2 = svc.create_attempt(1, CodeLanguage.PYTHON)
    assert a1.version == 1
    assert a2.version == 2

    # Each version has its own folder/file.
    v1 = repo.problems_dir / "0001-two-sum" / "python3" / "v001" / "solution.py"
    v2 = repo.problems_dir / "0001-two-sum" / "python3" / "v002" / "solution.py"
    assert v1.exists() and v2.exists()


def test_create_attempt_without_snippet_does_not_write_file(repo, stub_get_problem):
    """Problem with no per-language snippet -> attempt row is created, no file."""
    stub_get_problem["problem"] = Problem(
        problem_detail=ProblemDetail(
            id=1, title="X", slug="x",
            difficulty=ProblemDifficulty.EASY, description="",
        ),
        code_snippets=[],  # no snippets at all
    )
    attempt = AttemptService(repo=repo).create_attempt(1, CodeLanguage.PYTHON)
    assert attempt is not None
    solution = repo.problems_dir / "0001-x" / "python3" / "v001" / "solution.py"
    assert not solution.exists()


# --------------------------------------------------------------------------- #
# get_attempt / list_attempts                                                 #
# --------------------------------------------------------------------------- #

def test_get_attempt_latest(repo, stub_get_problem):
    svc = AttemptService(repo=repo)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    latest = svc.get_attempt(1, CodeLanguage.PYTHON)
    assert latest is not None
    assert latest.version == 2


def test_get_attempt_specific_version(repo, stub_get_problem):
    svc = AttemptService(repo=repo)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    v1 = svc.get_attempt(1, CodeLanguage.PYTHON, version=1)
    assert v1.version == 1


def test_get_attempt_missing(repo, stub_get_problem):
    assert AttemptService(repo=repo).get_attempt(99, CodeLanguage.PYTHON) is None


def test_list_attempts_with_and_without_language_filter(repo, stub_get_problem):
    svc = AttemptService(repo=repo)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    svc.create_attempt(1, CodeLanguage.JAVA)

    py = svc.list_attempts(1, CodeLanguage.PYTHON)
    all_ = svc.list_attempts(1)

    assert len(py) == 2
    assert len(all_) == 3


# --------------------------------------------------------------------------- #
# update_status / increment_run_count                                         #
# --------------------------------------------------------------------------- #

def test_update_status_persists(repo, stub_get_problem):
    svc = AttemptService(repo=repo)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    ok = svc.update_status(1, CodeLanguage.PYTHON, 1, ProblemStatus.PASSED)
    assert ok is True

    attempt = svc.get_attempt(1, CodeLanguage.PYTHON, version=1)
    assert attempt.status is ProblemStatus.PASSED


def test_update_status_returns_false_when_attempt_missing(repo):
    """No attempt with that version -> service returns False, no exception."""
    ok = AttemptService(repo=repo).update_status(
        1, CodeLanguage.PYTHON, 99, ProblemStatus.PASSED,
    )
    assert ok is False


def test_increment_run_count(repo, stub_get_problem):
    svc = AttemptService(repo=repo)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    svc.increment_run_count(1, CodeLanguage.PYTHON, 1)
    svc.increment_run_count(1, CodeLanguage.PYTHON, 1)
    attempt = svc.get_attempt(1, CodeLanguage.PYTHON, version=1)
    assert attempt.run_count == 2


# --------------------------------------------------------------------------- #
# get_stats / get_all_stats                                                   #
# --------------------------------------------------------------------------- #

def test_get_stats_groups_by_language(repo, stub_get_problem):
    svc = AttemptService(repo=repo)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    svc.update_status(1, CodeLanguage.PYTHON, 2, ProblemStatus.PASSED)
    svc.create_attempt(1, CodeLanguage.JAVA)

    stats = svc.get_stats(1)
    assert CodeLanguage.PYTHON in stats
    assert CodeLanguage.JAVA in stats
    py = stats[CodeLanguage.PYTHON]
    assert py.total_attempts == 2
    assert py.pass_count == 1


def test_get_stats_filtered_by_language(repo, stub_get_problem):
    svc = AttemptService(repo=repo)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    svc.create_attempt(1, CodeLanguage.JAVA)
    py_only = svc.get_stats(1, CodeLanguage.PYTHON)
    assert set(py_only.keys()) == {CodeLanguage.PYTHON}


def test_get_all_stats_groups_by_problem(repo, stub_get_problem):
    """Each registered problem appears once in the all-stats map."""
    svc = AttemptService(repo=repo)
    stub_get_problem["problem"] = _problem(pid=1)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    stub_get_problem["problem"] = _problem(pid=2)
    svc.create_attempt(2, CodeLanguage.PYTHON)

    all_stats = svc.get_all_stats()
    assert set(all_stats.keys()) == {1, 2}


# --------------------------------------------------------------------------- #
# get_attempt_path                                                            #
# --------------------------------------------------------------------------- #

def test_get_attempt_path_explicit_version(repo, stub_get_problem):
    """With an explicit version, no DB lookup needed."""
    svc = AttemptService(repo=repo)
    path = svc.get_attempt_path(1, CodeLanguage.PYTHON, version=7)
    # Returns the attempt folder: problems/<slug>/<lang>/v<NNN>/
    assert path.parts[-3:] == ("0001-two-sum", "python3", "v007")


def test_get_attempt_path_latest_uses_latest_version(repo, stub_get_problem):
    svc = AttemptService(repo=repo)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    svc.create_attempt(1, CodeLanguage.PYTHON)
    path = svc.get_attempt_path(1, CodeLanguage.PYTHON)
    assert "v002" in path.parts


def test_get_attempt_path_latest_when_no_attempt_returns_none(repo, stub_get_problem):
    """No attempt for the (problem, language) pair -> None."""
    path = AttemptService(repo=repo).get_attempt_path(99, CodeLanguage.PYTHON)
    assert path is None
