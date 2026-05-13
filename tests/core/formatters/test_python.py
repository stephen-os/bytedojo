"""Tests for the PythonFormatter."""

import pytest

from bytedojo.core.formatters.python import (
    FormatContext,
    PythonFormatter,
)
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #

TWO_SUM_SNIPPET = """\
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        \
"""

TREE_NODE_SNIPPET = """\
# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
class Solution:
    def maxDepth(self, root: Optional[TreeNode]) -> int:
        pass
"""


def _problem(*, pid: int = 1, title: str = "Two Sum", slug: str = "two-sum",
             description: str = "<p>Find indices.</p>",
             snippet_code: str = TWO_SUM_SNIPPET,
             snippet_lang: CodeLanguage = CodeLanguage.PYTHON) -> Problem:
    return Problem(
        problem_detail=ProblemDetail(
            id=pid, title=title, slug=slug,
            difficulty=ProblemDifficulty.EASY, description=description,
        ),
        code_snippets=[CodeSnippet(lang=snippet_lang, code=snippet_code)],
    )


# --------------------------------------------------------------------------- #
# FormatContext                                                               #
# --------------------------------------------------------------------------- #

def test_format_context_extracts_class_method_params_return_type():
    ctx = FormatContext(code=TWO_SUM_SNIPPET, description="")
    assert ctx.class_name == "Solution"
    assert ctx.method_name == "twoSum"
    assert ctx.param_info == [("nums", "List[int]"), ("target", "int")]
    assert ctx.return_type == "List[int]"
    assert ctx.param_count == 2


def test_format_context_instance_name_is_lowercase_class():
    ctx = FormatContext(code="class Codec:\n    def encode(self): pass", description="")
    assert ctx.instance_name == "codec"


def test_format_context_no_class_falls_back_to_solution():
    ctx = FormatContext(code="def standalone(): pass", description="")
    assert ctx.class_name == "Solution"


def test_format_context_skips_node_classes_when_picking_main_class():
    code = "class TreeNode:\n    pass\nclass MyCustom:\n    def solve(self): pass"
    ctx = FormatContext(code=code, description="")
    assert ctx.class_name == "MyCustom"


def test_format_context_detects_tree_and_list_node_helpers():
    code = "class TreeNode:\n    pass\nclass Solution: pass"
    ctx = FormatContext(code=code, description="")
    assert ctx.helpers_needed["treenode"] is True
    assert ctx.helpers_needed["listnode"] is False


# --------------------------------------------------------------------------- #
# PythonFormatter.format — file structure                                     #
# --------------------------------------------------------------------------- #

@pytest.fixture
def formatter() -> PythonFormatter:
    return PythonFormatter()


def test_format_produces_problem_header(formatter):
    out = formatter.format(_problem(pid=1, title="Two Sum"))
    assert 'LeetCode Problem #1: Two Sum' in out
    assert 'Difficulty: Easy' in out


def test_format_emits_section_headers_in_order(formatter):
    out = formatter.format(_problem())
    idx_desc = out.index("PROBLEM DESCRIPTION")
    idx_sol  = out.index("SOLUTION")
    idx_test = out.index("TEST")
    assert idx_desc < idx_sol < idx_test


def test_format_includes_baseline_imports(formatter):
    out = formatter.format(_problem())
    assert "from typing import" in out
    assert "from collections import Counter, defaultdict, deque" in out
    assert "from functools import lru_cache" in out
    assert "from heapq import heappop, heappush" in out
    assert "from math import inf" in out


def test_format_includes_solution_class(formatter):
    out = formatter.format(_problem())
    assert "class Solution:" in out
    assert "def twoSum" in out


def test_format_includes_main_block_with_todo(formatter):
    out = formatter.format(_problem())
    assert 'if __name__ == "__main__":' in out
    assert "TODO: edit me, or run `dojo test`" in out


def test_format_description_is_commented(formatter):
    out = formatter.format(_problem(description="<p>Find indices.</p>"))
    assert "# Find indices." in out


def test_format_empty_method_gets_pass(formatter):
    """An empty method body in the snippet becomes `pass` so the file parses."""
    snippet = "class Solution:\n    def solve(self, n: int) -> int:\n"
    out = formatter.format(_problem(snippet_code=snippet))
    assert "pass" in out


# --------------------------------------------------------------------------- #
# Node-class extraction + extra_files                                         #
# --------------------------------------------------------------------------- #

def test_extra_files_for_tree_node_problem(formatter):
    extras = formatter.extra_files(_problem(snippet_code=TREE_NODE_SNIPPET))
    assert "tree_node.py" in extras
    body = extras["tree_node.py"]
    assert "class TreeNode:" in body
    assert "self.val = val" in body


def test_extra_files_empty_for_plain_problem(formatter):
    assert formatter.extra_files(_problem()) == {}


def test_format_strips_node_class_from_solution_file(formatter):
    """When a node class is extracted, it must not also appear in solution.py."""
    out = formatter.format(_problem(snippet_code=TREE_NODE_SNIPPET))
    # The class body proper goes to tree_node.py, not solution.py
    assert "self.val = val" not in out
    # And solution.py imports it from the sibling module.
    assert "from tree_node import TreeNode" in out


def test_format_strips_top_level_imports_from_snippet(formatter):
    """A snippet with `import` lines doesn't duplicate them in solution.py."""
    snippet = "import math\nfrom typing import List\nclass Solution:\n    def solve(self): pass"
    out = formatter.format(_problem(snippet_code=snippet))
    # Imports section comes from the baseline; the snippet's lines are gone.
    assert out.count("import math") == 0


# --------------------------------------------------------------------------- #
# Edge cases                                                                  #
# --------------------------------------------------------------------------- #

def test_format_missing_snippet_falls_back_to_placeholder(formatter):
    """No Python3 snippet -> the file still places, with a TODO comment."""
    problem = Problem(problem_detail=ProblemDetail(
        id=1, title="t", slug="s",
        difficulty=ProblemDifficulty.EASY, description="",
    ))
    out = formatter.format(problem)
    assert "No Python template available" in out
