"""Tests for the formatters registry (core/formatters/__init__.py)."""

from bytedojo.core.formatters import (
    CppFormatter,
    JavaFormatter,
    PythonFormatter,
    extra_files_for,
    format_problem,
    get_formatter,
)
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty


def _problem(snippets=None) -> Problem:
    return Problem(
        problem_detail=ProblemDetail(
            id=1, title="Two Sum", slug="two-sum",
            difficulty=ProblemDifficulty.EASY, description="",
        ),
        code_snippets=snippets or [],
    )


# --------------------------------------------------------------------------- #
# get_formatter                                                               #
# --------------------------------------------------------------------------- #

def test_get_formatter_returns_python_formatter():
    assert isinstance(get_formatter(CodeLanguage.PYTHON), PythonFormatter)


def test_get_formatter_returns_java_formatter():
    assert isinstance(get_formatter(CodeLanguage.JAVA), JavaFormatter)


def test_get_formatter_returns_cpp_formatter():
    assert isinstance(get_formatter(CodeLanguage.CPP), CppFormatter)


def test_get_formatter_unsupported_language_returns_none():
    """Rust / Go / JS / TS have no registered formatter; lookup returns None."""
    assert get_formatter(CodeLanguage.RUST) is None
    assert get_formatter(CodeLanguage.GO) is None
    assert get_formatter(CodeLanguage.JAVASCRIPT) is None
    assert get_formatter(CodeLanguage.UNKNOWN) is None


# --------------------------------------------------------------------------- #
# format_problem                                                              #
# --------------------------------------------------------------------------- #

def test_format_problem_dispatches_to_registered_formatter():
    """A registered language produces full file content (header + sections)."""
    snippets = [CodeSnippet(lang=CodeLanguage.PYTHON,
                            code="class Solution:\n    def solve(self):\n        pass")]
    out = format_problem(_problem(snippets), CodeLanguage.PYTHON)
    assert "LeetCode Problem #1: Two Sum" in out
    assert "class Solution" in out


def test_format_problem_unsupported_language_falls_back_to_raw_snippet():
    """No-formatter language falls back to whatever snippet text is on the Problem."""
    raw = "fn solve() -> i32 { 0 }"
    snippets = [CodeSnippet(lang=CodeLanguage.RUST, code=raw)]
    assert format_problem(_problem(snippets), CodeLanguage.RUST) == raw


def test_format_problem_unsupported_language_no_snippet_returns_empty():
    """No formatter AND no snippet -> empty string, never None / never raises."""
    assert format_problem(_problem(), CodeLanguage.RUST) == ""


# --------------------------------------------------------------------------- #
# extra_files_for                                                             #
# --------------------------------------------------------------------------- #

def test_extra_files_for_unsupported_language_is_empty():
    assert extra_files_for(_problem(), CodeLanguage.RUST) == {}


def test_extra_files_for_supported_language_no_node_classes_is_empty():
    """Plain problem with no embedded node class -> no sibling files."""
    snippets = [CodeSnippet(lang=CodeLanguage.PYTHON,
                            code="class Solution:\n    def solve(self):\n        pass")]
    assert extra_files_for(_problem(snippets), CodeLanguage.PYTHON) == {}
