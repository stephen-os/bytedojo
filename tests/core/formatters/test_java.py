"""Tests for the JavaFormatter."""

import pytest

from bytedojo.core.formatters.java import JavaFormatContext, JavaFormatter
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #

TWO_SUM_SNIPPET = """\
class Solution {
    public int[] twoSum(int[] nums, int target) {

    }
}
"""

TREE_NODE_SNIPPET = """\
/**
 * Definition for a binary tree node.
 * public class TreeNode {
 *     int val;
 *     TreeNode left;
 *     TreeNode right;
 *     TreeNode() {}
 *     TreeNode(int val) { this.val = val; }
 *     TreeNode(int val, TreeNode left, TreeNode right) {
 *         this.val = val;
 *         this.left = left;
 *         this.right = right;
 *     }
 * }
 */
class Solution {
    public int maxDepth(TreeNode root) {

    }
}
"""


def _problem(*, pid: int = 1, title: str = "Two Sum", slug: str = "two-sum",
             description: str = "<p>Find indices.</p>",
             snippet_code: str = TWO_SUM_SNIPPET) -> Problem:
    return Problem(
        problem_detail=ProblemDetail(
            id=pid, title=title, slug=slug,
            difficulty=ProblemDifficulty.EASY, description=description,
        ),
        code_snippets=[CodeSnippet(lang=CodeLanguage.JAVA, code=snippet_code)],
    )


# --------------------------------------------------------------------------- #
# JavaFormatContext                                                           #
# --------------------------------------------------------------------------- #

def test_context_extracts_class_method_params_return_type():
    ctx = JavaFormatContext(code=TWO_SUM_SNIPPET, description="")
    assert ctx.class_name == "Solution"
    assert ctx.method_name == "twoSum"
    assert ctx.param_info == [("nums", "int[]"), ("target", "int")]
    assert ctx.return_type == "int[]"


def test_context_void_return_type():
    snippet = "class Solution {\n    public void run() {\n    }\n}"
    ctx = JavaFormatContext(code=snippet, description="")
    assert ctx.return_type == "void"


def test_context_handles_generic_params():
    snippet = "class Solution {\n    public List<Integer> solve(List<String> ws) { return null; }\n}"
    ctx = JavaFormatContext(code=snippet, description="")
    assert ctx.param_info == [("ws", "List<String>")]
    assert ctx.return_type == "List<Integer>"


def test_context_no_class_falls_back_to_solution():
    ctx = JavaFormatContext(code="// just a comment", description="")
    assert ctx.class_name == "Solution"


# --------------------------------------------------------------------------- #
# JavaFormatter.format — file structure                                       #
# --------------------------------------------------------------------------- #

@pytest.fixture
def formatter() -> JavaFormatter:
    return JavaFormatter()


def test_format_produces_problem_header(formatter):
    out = formatter.format(_problem(pid=1, title="Two Sum"))
    assert "LeetCode Problem #1: Two Sum" in out
    assert "Difficulty: Easy" in out


def test_format_emits_section_headers_in_order(formatter):
    out = formatter.format(_problem())
    idx_desc = out.index("PROBLEM DESCRIPTION")
    idx_sol  = out.index("SOLUTION")
    idx_test = out.index("TEST")
    assert idx_desc < idx_sol < idx_test


def test_format_includes_baseline_import(formatter):
    out = formatter.format(_problem())
    assert "import java.util.*;" in out


def test_format_includes_solution_class_and_main(formatter):
    out = formatter.format(_problem())
    assert "class Solution" in out
    assert "class Main" in out
    assert "public static void main(String[] args)" in out
    assert "TODO: edit me, or run `dojo test`" in out


def test_format_description_is_commented(formatter):
    out = formatter.format(_problem(description="<p>Find indices.</p>"))
    assert "// Find indices." in out


def test_format_injects_default_return_for_non_void(formatter):
    """An empty `int[] twoSum(...)` body gets a `return new int[]{};` injected."""
    out = formatter.format(_problem())
    assert "return new int[]{}" in out


def test_format_does_not_inject_return_for_void(formatter):
    snippet = "class Solution {\n    public void run() {\n\n    }\n}"
    out = formatter.format(_problem(snippet_code=snippet))
    # No `return ...;` injected when return type is void
    assert "return" not in out.split("class Main")[0]


# --------------------------------------------------------------------------- #
# Node-class extraction + extra_files                                         #
# --------------------------------------------------------------------------- #

def test_extra_files_for_tree_node_problem(formatter):
    extras = formatter.extra_files(_problem(snippet_code=TREE_NODE_SNIPPET))
    assert "TreeNode.java" in extras
    body = extras["TreeNode.java"]
    assert "public class TreeNode" in body
    assert "int val;" in body
    # The "Definition for ..." leader comment is stripped.
    assert "Definition for" not in body


def test_extra_files_empty_for_plain_problem(formatter):
    assert formatter.extra_files(_problem()) == {}


def test_format_strips_node_class_javadoc_from_solution_file(formatter):
    """The JavaDoc-wrapped TreeNode is in TreeNode.java, not solution.java."""
    out = formatter.format(_problem(snippet_code=TREE_NODE_SNIPPET))
    # solution.java should not contain the class fields
    assert "int val;" not in out


# --------------------------------------------------------------------------- #
# Edge cases                                                                  #
# --------------------------------------------------------------------------- #

def test_format_missing_snippet_falls_back_to_placeholder(formatter):
    problem = Problem(problem_detail=ProblemDetail(
        id=1, title="t", slug="s",
        difficulty=ProblemDifficulty.EASY, description="",
    ))
    out = formatter.format(problem)
    assert "No Java template available" in out
