"""Tests for BaseFormatter."""

import pytest

from bytedojo.core.formatters.base import BaseFormatter
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty


def _problem() -> Problem:
    return Problem(problem_detail=ProblemDetail(
        id=1, title="t", slug="s",
        difficulty=ProblemDifficulty.EASY, description="",
    ))


def test_base_formatter_cannot_be_instantiated_directly():
    """BaseFormatter is abstract; `format` is marked @abstractmethod."""
    with pytest.raises(TypeError):
        BaseFormatter()


def test_subclass_must_implement_format():
    """A subclass that doesn't override format() inherits the abstract marker."""
    class Incomplete(BaseFormatter):
        pass

    with pytest.raises(TypeError):
        Incomplete()


def test_extra_files_default_is_empty():
    """Default extra_files() returns an empty dict so non-node problems place cleanly."""
    class Minimal(BaseFormatter):
        def format(self, problem):
            return ""

    assert Minimal().extra_files(_problem()) == {}


def test_subclass_can_override_extra_files():
    class WithExtras(BaseFormatter):
        def format(self, problem):
            return ""
        def extra_files(self, problem):
            return {"helper.py": "x = 1"}

    assert WithExtras().extra_files(_problem()) == {"helper.py": "x = 1"}
