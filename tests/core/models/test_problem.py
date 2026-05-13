"""Tests for the Problem dataclass."""

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.example import Example
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty


def _detail(**overrides) -> ProblemDetail:
    base = dict(
        id=1, title="Two Sum", slug="two-sum",
        difficulty=ProblemDifficulty.EASY, description="",
    )
    base.update(overrides)
    return ProblemDetail(**base)


# --------------------------------------------------------------------------- #
# Defaults                                                                    #
# --------------------------------------------------------------------------- #

def test_construct_with_defaults():
    p = Problem(problem_detail=_detail())
    assert p.code_snippets == []
    assert p.examples == []
    assert p.constraints == []
    assert p.hints == []


# --------------------------------------------------------------------------- #
# get_code_snippet / get_snippet                                              #
# --------------------------------------------------------------------------- #

def test_get_code_snippet_returns_matching_lang():
    py = CodeSnippet(lang=CodeLanguage.PYTHON, code="def solve(): pass")
    cpp = CodeSnippet(lang=CodeLanguage.CPP, code="class Solution {};")
    p = Problem(problem_detail=_detail(), code_snippets=[py, cpp])
    assert p.get_code_snippet(CodeLanguage.PYTHON) is py
    assert p.get_code_snippet(CodeLanguage.CPP) is cpp


def test_get_code_snippet_returns_none_when_missing():
    p = Problem(problem_detail=_detail(),
                code_snippets=[CodeSnippet(lang=CodeLanguage.PYTHON, code="x")])
    assert p.get_code_snippet(CodeLanguage.JAVA) is None


def test_get_snippet_returns_text():
    p = Problem(problem_detail=_detail(),
                code_snippets=[CodeSnippet(lang=CodeLanguage.PYTHON, code="body")])
    assert p.get_snippet(CodeLanguage.PYTHON) == "body"


def test_get_snippet_returns_none_when_missing():
    p = Problem(problem_detail=_detail())
    assert p.get_snippet(CodeLanguage.PYTHON) is None


# --------------------------------------------------------------------------- #
# get_folder_name                                                             #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("pid, slug, expected", [
    (1,    "two-sum",                 "0001-two-sum"),
    (200,  "number-of-islands",       "0200-number-of-islands"),
    (9999, "very-large",              "9999-very-large"),
    (12345, "five-digit-id",          "12345-five-digit-id"),   # zero-pad floor, not truncate
])
def test_get_folder_name_zero_pads_to_four(pid, slug, expected):
    p = Problem(problem_detail=_detail(id=pid, slug=slug))
    assert p.get_folder_name() == expected


# --------------------------------------------------------------------------- #
# get_solution_filename                                                       #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("lang, expected", [
    (CodeLanguage.PYTHON, "solution.py"),
    (CodeLanguage.JAVA,   "solution.java"),
    (CodeLanguage.CPP,    "solution.cpp"),
    (CodeLanguage.GO,     "solution.go"),
])
def test_get_solution_filename(lang, expected):
    p = Problem(problem_detail=_detail())
    assert p.get_solution_filename(lang) == expected


def test_get_solution_filename_unknown_language_has_no_extension():
    p = Problem(problem_detail=_detail())
    assert p.get_solution_filename(CodeLanguage.UNKNOWN) == "solution"


# --------------------------------------------------------------------------- #
# Examples / constraints / hints are independent lists                        #
# --------------------------------------------------------------------------- #

def test_default_factory_lists_are_independent_per_instance():
    a = Problem(problem_detail=_detail())
    b = Problem(problem_detail=_detail())
    a.examples.append(Example(example_num=1, example_text="x"))
    a.constraints.append("c1")
    a.hints.append("h1")
    assert b.examples == []
    assert b.constraints == []
    assert b.hints == []
