"""
Shared pytest fixtures for the bytedojo test suite.

- `_initialise_logger` (session, autouse): sets up the global logger so
  `get_logger()` works for direct-import tests. Production callers always
  go through main()'s explicit setup_logger; this fills the gap for tests.

- `repo` (function): builds a fresh, fully-initialised Repository at
  tmp_path. Each test gets its own sqlite DB + .dojo / problems / build
  directories, so service- and command-level tests can exercise real DB
  writes and file placement without mocks.

- `registered_problem` + `insert_registered_problem` / `make_problem`:
  helpers for seeding the repo's DB with a Problem so command / service
  tests can exercise lookup, grading, review-scheduling, etc. against
  real rows.
"""

import pytest

from bytedojo.core.logger import setup_logger
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository


@pytest.fixture(scope="session", autouse=True)
def _initialise_logger():
    setup_logger(debug=False)


@pytest.fixture
def repo(tmp_path) -> Repository:
    """Fresh Repository at tmp_path — real sqlite, real filesystem layout."""
    return Repository.create(tmp_path)


# --------------------------------------------------------------------------- #
# Problem seeding helpers — shared across services + commands tests           #
# --------------------------------------------------------------------------- #

def make_problem(
    *,
    pid: int = 1,
    title: str = "Two Sum",
    slug: str = "two-sum",
    difficulty: ProblemDifficulty = ProblemDifficulty.EASY,
    description: str = "Given an array...",
    snippet_lang: CodeLanguage = CodeLanguage.PYTHON,
    snippet_code: str = "class Solution:\n    def twoSum(self, nums, target):\n        pass",
) -> Problem:
    """Minimal Problem suitable for db.register_problem and friends."""
    if isinstance(difficulty, str):
        difficulty = ProblemDifficulty.from_string(difficulty)
    return Problem(
        problem_detail=ProblemDetail(
            id=pid, title=title, slug=slug,
            difficulty=difficulty, description=description,
        ),
        code_snippets=[CodeSnippet(lang=snippet_lang, code=snippet_code)],
    )


def insert_registered_problem(
    repo: Repository,
    *,
    pid: int = 1,
    language: CodeLanguage = CodeLanguage.PYTHON,
    file_path: str = "problems/0001-two-sum/python3/v001/solution.py",
    **problem_kwargs,
) -> RegisteredProblem:
    """Insert a Problem into the repo's DB and return the resulting RegisteredProblem."""
    problem = make_problem(pid=pid, **problem_kwargs)
    with repo.open_db() as db:
        db.register_problem(problem, source="leetcode",
                            language=language.value, file_path=file_path)
        registered = db.get_problem("leetcode", pid, language.value)
    assert registered is not None, "register_problem did not insert"
    return registered


@pytest.fixture
def registered_problem(repo) -> RegisteredProblem:
    """A Repository pre-seeded with one Python-language Two Sum entry."""
    return insert_registered_problem(repo)
