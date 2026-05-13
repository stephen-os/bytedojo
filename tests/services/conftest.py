"""
Service-test fixtures.

Builds on the top-level `repo` fixture (fresh Repository at tmp_path) by
adding service-specific helpers — most notably, populating the DB with a
real RegisteredProblem so service-level orchestration can be tested
end-to-end without mocking the Database API.
"""

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository


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
