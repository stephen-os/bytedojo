"""Tests for the CppFormatter."""

import pytest

from bytedojo.core.formatters.cpp import CppFormatContext, CppFormatter
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
public:
    vector<int> twoSum(vector<int>& nums, int target) {

    }
};
"""

TREE_NODE_SNIPPET = """\
/**
 * Definition for a binary tree node.
 * struct TreeNode {
 *     int val;
 *     TreeNode *left;
 *     TreeNode *right;
 *     TreeNode() : val(0), left(nullptr), right(nullptr) {}
 *     TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
 * };
 */
class Solution {
public:
    int maxDepth(TreeNode* root) {

    }
};
"""

SNIPPET_WITH_INCLUDES = """\
#include <vector>
using namespace std;
class Solution {
public:
    int run() {

    }
};
"""


def _problem(*, pid: int = 1, title: str = "Two Sum", slug: str = "two-sum",
             description: str = "<p>Find indices.</p>",
             snippet_code: str = TWO_SUM_SNIPPET) -> Problem:
    return Problem(
        problem_detail=ProblemDetail(
            id=pid, title=title, slug=slug,
            difficulty=ProblemDifficulty.EASY, description=description,
        ),
        code_snippets=[CodeSnippet(lang=CodeLanguage.CPP, code=snippet_code)],
    )


# --------------------------------------------------------------------------- #
# CppFormatContext                                                            #
# --------------------------------------------------------------------------- #

def test_context_extracts_class_method_params_return_type():
    ctx = CppFormatContext(code=TWO_SUM_SNIPPET, description="")
    assert ctx.class_name == "Solution"
    assert ctx.method_name == "twoSum"
    assert ctx.param_info == [("nums", "vector<int>&"), ("target", "int")]
    assert ctx.return_type == "vector<int>"


def test_context_void_return_type():
    snippet = "class Solution {\npublic:\n    void run() {}\n};"
    ctx = CppFormatContext(code=snippet, description="")
    assert ctx.return_type == "void"


def test_context_no_class_falls_back_to_solution():
    ctx = CppFormatContext(code="// nothing here", description="")
    assert ctx.class_name == "Solution"


# --------------------------------------------------------------------------- #
# CppFormatter.format — file structure                                        #
# --------------------------------------------------------------------------- #

@pytest.fixture
def formatter() -> CppFormatter:
    return CppFormatter()


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


def test_format_includes_baseline_includes(formatter):
    out = formatter.format(_problem())
    assert "#include <vector>" in out
    assert "#include <unordered_map>" in out
    assert "#include <algorithm>" in out


def test_format_includes_using_namespace_std(formatter):
    """LeetCode-style `using namespace std;` matches user habits."""
    assert "using namespace std;" in formatter.format(_problem())


def test_format_includes_solution_class_and_main(formatter):
    out = formatter.format(_problem())
    assert "class Solution" in out
    assert "int main()" in out
    assert "TODO: edit me, or run `dojo test`" in out


def test_format_description_is_commented(formatter):
    out = formatter.format(_problem(description="<p>Find indices.</p>"))
    assert "// Find indices." in out


def test_format_injects_default_return_for_non_void(formatter):
    """An empty `vector<int> twoSum(...)` body gets a `return {};` injected."""
    out = formatter.format(_problem())
    assert "return {}" in out


def test_format_strips_snippet_level_includes_and_using(formatter):
    """`#include` and `using ...;` in the snippet move out into the includes section."""
    out = formatter.format(_problem(snippet_code=SNIPPET_WITH_INCLUDES))
    # Should only see one copy of <vector> (from the baseline), not duplicated.
    assert out.count("#include <vector>") == 1
    assert out.count("using namespace std;") == 1


# --------------------------------------------------------------------------- #
# Node-class extraction + extra_files                                         #
# --------------------------------------------------------------------------- #

def test_extra_files_for_tree_node_problem(formatter):
    extras = formatter.extra_files(_problem(snippet_code=TREE_NODE_SNIPPET))
    assert "tree_node.hpp" in extras
    body = extras["tree_node.hpp"]
    assert "#ifndef TREE_NODE_HPP_" in body
    assert "#define TREE_NODE_HPP_" in body
    assert "#endif" in body
    assert "struct TreeNode" in body
    # The "Definition for ..." leader comment is stripped.
    assert "Definition for" not in body


def test_extra_files_empty_for_plain_problem(formatter):
    assert formatter.extra_files(_problem()) == {}


def test_format_includes_node_header_when_extracted(formatter):
    """Solution.cpp gets `#include "tree_node.hpp"` when a node struct is extracted."""
    out = formatter.format(_problem(snippet_code=TREE_NODE_SNIPPET))
    assert '#include "tree_node.hpp"' in out


def test_format_strips_node_struct_doxygen_from_solution_file(formatter):
    """The Doxygen-wrapped TreeNode body is in tree_node.hpp, not solution.cpp."""
    out = formatter.format(_problem(snippet_code=TREE_NODE_SNIPPET))
    # solution.cpp should not contain the struct fields
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
    assert "No C++ template available" in out
