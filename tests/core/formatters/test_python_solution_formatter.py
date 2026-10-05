"""Tests for the Python stub synthesis (§11)."""

import pytest

from bytedojo.core.formatters.solutions.python_solution_formatter import (
    PythonSolutionFormatter,
    annotation,
)
from bytedojo.core.models.example import Example
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.signature import Signature
from bytedojo.core.models.test_bundle import TestBundle


def _bundle(method="twoSum", params=None, returns=None) -> TestBundle:
    return TestBundle(
        schema_version=1,
        problem_id=1,
        title="Two Sum",
        method=method,
        signature={
            "params": params
            or [
                {"name": "nums", "type": {"base": "ARRAY", "element": "INT32"}},
                {"name": "target", "type": {"base": "INT32"}},
            ],
            "returns": returns or {"base": "ARRAY", "element": "INT32"},
        },
        cases=[],
    )


def _problem() -> Problem:
    return Problem(
        problem_detail=ProblemDetail(
            id=1,
            title="Two Sum",
            slug="two-sum",
            difficulty=ProblemDifficulty.EASY,
            description="Find two numbers that add up to target.",
        ),
        examples=[Example(example_num=1, example_text="nums=[2,7], target=9")],
        constraints=["2 <= nums.length"],
    )


# --------------------------------------------------------------------------- #
# annotation — type vocabulary → PEP-484                                      #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "spec, expected",
    [
        ({"base": "INT32"}, "int"),
        ({"base": "INT64"}, "int"),
        ({"base": "FLOAT64"}, "float"),
        ({"base": "BOOL"}, "bool"),
        ({"base": "CHAR"}, "str"),
        ({"base": "STRING"}, "str"),
        ({"base": "VOID"}, "None"),
        ({"base": "ARRAY", "element": "INT32"}, "List[int]"),
        ({"base": "ARRAY", "element": "STRING"}, "List[str]"),
        ({"base": "MATRIX", "element": "CHAR"}, "List[List[str]]"),
        ({"base": "BINARY_TREE"}, "Optional[TreeNode]"),
        ({"base": "LINKED_LIST"}, "Optional[ListNode]"),
        ({"base": "ARRAY", "element": "LINKED_LIST"}, "List[Optional[ListNode]]"),
    ],
)
def test_annotation_maps_the_type_vocabulary(spec, expected):
    assert annotation(Signature.from_dict(spec)) == expected


# --------------------------------------------------------------------------- #
# format — the assembled solution file                                        #
# --------------------------------------------------------------------------- #


def test_format_solution_synthesises_typed_stub():
    body = PythonSolutionFormatter().format_solution(_bundle())
    assert "class Solution:" in body
    assert "def twoSum(self, nums: List[int], target: int) -> List[int]:" in body
    assert "pass" in body


def test_format_assembles_prose_and_sections():
    content = PythonSolutionFormatter().format(_problem(), _bundle())
    assert "LeetCode Problem #1: Two Sum" in content
    assert "Find two numbers that add up to target." in content
    assert "Example #1" in content
    assert "2 <= nums.length" in content
    assert "from typing import Dict, List, Optional, Set, Tuple" in content
    assert 'if __name__ == "__main__":' in content


def test_node_signature_adds_companion_import_and_file():
    bundle = _bundle(
        method="maxDepth",
        params=[{"name": "root", "type": {"base": "BINARY_TREE"}}],
        returns={"base": "INT32"},
    )
    formatter = PythonSolutionFormatter()
    assert "from tree_node import TreeNode" in formatter.format_imports(bundle)
    files = formatter.extra_files(bundle)
    assert "tree_node.py" in files
    assert "class TreeNode" in files["tree_node.py"]


def test_primitive_signature_needs_no_extra_files():
    assert PythonSolutionFormatter().extra_files(_bundle()) == {}
