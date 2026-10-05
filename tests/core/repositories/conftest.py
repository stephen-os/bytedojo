"""Shared fixtures for repository tests: a schema'd connection per test."""

import pytest

from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.repositories import _db


@pytest.fixture
def conn(tmp_path):
    """An open connection to a fresh, schema-initialised tmp database."""
    path = tmp_path / "db.sqlite"
    _db.create_schema(path)
    connection = _db.connect(path)
    yield connection
    connection.close()


def make_problem(
    pid: int = 1, slug: str = "two-sum", title: str = "Two Sum"
) -> Problem:
    return Problem(
        problem_detail=ProblemDetail(
            id=pid,
            title=title,
            slug=slug,
            difficulty=ProblemDifficulty.EASY,
            description="d",
        ),
    )
