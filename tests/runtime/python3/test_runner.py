"""Subprocess integration tests for the universal Python runner.

The runner is a standalone script (no bytedojo imports) that TestService
stages into a per-problem build dir. These tests recreate that build-dir
layout under tmp_path and invoke `python runner.py` exactly the way
TestService does — the most honest possible coverage.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path


from bytedojo.runtime.python3 import RUNTIME_DIR

# --------------------------------------------------------------------------- #
# Sentinels match runner.py + test_service.py.                                #
# --------------------------------------------------------------------------- #

_BEGIN = "<<<BYTEDOJO_RESULTS_BEGIN>>>"
_END = "<<<BYTEDOJO_RESULTS_END>>>"


def _stage(
    tmp_path: Path,
    *,
    solution: str,
    cases: dict,
    extras: dict = None,
) -> Path:
    """Build a build-dir mirror: runner.py + converters.py + cases.json + solution.py."""
    shutil.copyfile(RUNTIME_DIR / "runner.py", tmp_path / "runner.py")
    shutil.copyfile(RUNTIME_DIR / "converters.py", tmp_path / "converters.py")
    (tmp_path / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
    (tmp_path / "solution.py").write_text(solution, encoding="utf-8")
    for name, content in (extras or {}).items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    return tmp_path


def _invoke(build_dir: Path, *, timeout: int = 30) -> tuple[int, str, str]:
    """Run `python runner.py` in build_dir; return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(build_dir / "runner.py")],
        cwd=build_dir,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _parse_envelope(stdout: str) -> list:
    """Extract the JSON array between the sentinels."""
    begin = stdout.find(_BEGIN)
    end = stdout.find(_END)
    assert begin >= 0 and end > begin, f"no envelope in: {stdout!r}"
    payload = stdout[begin + len(_BEGIN) : end].strip()
    return json.loads(payload)


# --------------------------------------------------------------------------- #
# Happy path: a primitive-only solution                                       #
# --------------------------------------------------------------------------- #


def test_runner_emits_sentinel_envelope(tmp_path):
    _stage(
        tmp_path,
        solution=(
            "class Solution:\n" "    def add(self, a, b):\n" "        return a + b\n"
        ),
        cases={
            "schema_version": 1,
            "problem_id": 1,
            "title": "Add",
            "method": "add",
            "signature": {
                "params": [
                    {"name": "a", "type": "INT32"},
                    {"name": "b", "type": "INT32"},
                ],
                "returns": "INT32",
            },
            "cases": [
                {"case_id": 1, "input": {"a": 1, "b": 2}, "expected": 3},
                {"case_id": 2, "input": {"a": 10, "b": -5}, "expected": 5},
            ],
        },
    )
    code, stdout, stderr = _invoke(tmp_path)
    assert code == 0, stderr
    envelope = _parse_envelope(stdout)
    assert len(envelope) == 2
    assert all(r["passed"] for r in envelope)
    assert envelope[0]["case"] == 1
    assert envelope[0]["actual"] == "3"


def test_runner_reports_failing_cases(tmp_path):
    """Method returns wrong answer; runner marks passed=False but still emits envelope."""
    _stage(
        tmp_path,
        solution=(
            "class Solution:\n"
            "    def add(self, a, b):\n"
            "        return a - b\n"  # buggy
        ),
        cases={
            "schema_version": 1,
            "problem_id": 1,
            "title": "Add",
            "method": "add",
            "signature": {
                "params": [
                    {"name": "a", "type": "INT32"},
                    {"name": "b", "type": "INT32"},
                ],
                "returns": "INT32",
            },
            "cases": [{"case_id": 1, "input": {"a": 1, "b": 2}, "expected": 3}],
        },
    )
    code, stdout, _ = _invoke(tmp_path)
    assert code == 0
    envelope = _parse_envelope(stdout)
    assert envelope[0]["passed"] is False
    assert envelope[0]["actual"] == "-1"
    assert envelope[0]["expected"] == "3"


def test_runner_captures_exception_per_case(tmp_path):
    """A case that throws is reported with passed=False + error field; suite continues."""
    _stage(
        tmp_path,
        solution=(
            "class Solution:\n"
            "    def divide(self, a, b):\n"
            "        return a // b\n"
        ),
        cases={
            "schema_version": 1,
            "problem_id": 1,
            "title": "Divide",
            "method": "divide",
            "signature": {
                "params": [
                    {"name": "a", "type": "INT32"},
                    {"name": "b", "type": "INT32"},
                ],
                "returns": "INT32",
            },
            "cases": [
                {"case_id": 1, "input": {"a": 10, "b": 0}, "expected": 0},  # zero-div
                {"case_id": 2, "input": {"a": 6, "b": 2}, "expected": 3},  # passes
            ],
        },
    )
    code, stdout, _ = _invoke(tmp_path)
    assert code == 0
    envelope = _parse_envelope(stdout)
    assert envelope[0]["passed"] is False
    assert "ZeroDivisionError" in envelope[0]["error"]
    assert envelope[1]["passed"] is True


def test_runner_supports_unordered_all(tmp_path):
    _stage(
        tmp_path,
        solution=(
            "class Solution:\n"
            "    def threeSum(self, nums):\n"
            "        return [[-1, -1, 2], [-1, 0, 1]]\n"
        ),
        cases={
            "schema_version": 1,
            "problem_id": 15,
            "title": "3Sum",
            "method": "threeSum",
            "signature": {
                "params": [{"name": "nums", "type": "INT32_ARRAY"}],
                "returns": "INT32_MATRIX",
            },
            "cases": [
                {
                    "case_id": 1,
                    "input": {"nums": [-1, 0, 1, 2, -1, -4]},
                    # Same set of triples, different ordering.
                    "expected": [[-1, 0, 1], [2, -1, -1]],
                }
            ],
            "comparison": "unordered_all",
        },
    )
    code, stdout, _ = _invoke(tmp_path)
    assert code == 0
    envelope = _parse_envelope(stdout)
    assert envelope[0]["passed"] is True


# --------------------------------------------------------------------------- #
# Solution / method shape errors                                              #
# --------------------------------------------------------------------------- #


def test_runner_missing_method_reports_clean_error(tmp_path):
    """Solution exists but lacks the method bundle.method references."""
    _stage(
        tmp_path,
        solution="class Solution:\n    def somethingElse(self): pass\n",
        cases={
            "schema_version": 1,
            "problem_id": 1,
            "title": "X",
            "method": "missingMethod",
            "signature": {"params": [], "returns": "VOID"},
            "cases": [{"case_id": 1, "input": {}, "expected": None}],
        },
    )
    code, stdout, _ = _invoke(tmp_path)
    assert code == 0  # not a crash — envelope still emitted
    envelope = _parse_envelope(stdout)
    assert envelope[0]["passed"] is False
    assert "missingMethod" in envelope[0]["error"]


def test_runner_missing_cases_json_reports_clean_error(tmp_path):
    """No cases.json staged -> runner emits a case-0 error envelope."""
    shutil.copyfile(RUNTIME_DIR / "runner.py", tmp_path / "runner.py")
    shutil.copyfile(RUNTIME_DIR / "converters.py", tmp_path / "converters.py")
    (tmp_path / "solution.py").write_text("class Solution: pass\n", encoding="utf-8")
    code, stdout, _ = _invoke(tmp_path)
    assert code == 0
    envelope = _parse_envelope(stdout)
    assert envelope[0]["case"] == 0
    assert "cases.json" in envelope[0]["error"]


def test_runner_solution_import_error_is_surfaced(tmp_path):
    """A solution.py with a SyntaxError -> runner's top-level catch reports it."""
    _stage(
        tmp_path,
        solution="class Solution\n",  # missing colon
        cases={
            "schema_version": 1,
            "problem_id": 1,
            "title": "X",
            "method": "x",
            "signature": {"params": [], "returns": "VOID"},
            "cases": [],
        },
    )
    code, stdout, _ = _invoke(tmp_path)
    assert code == 1
    envelope = _parse_envelope(stdout)
    assert "runner crash" in envelope[0]["error"]


# --------------------------------------------------------------------------- #
# Reference-type integration (uses sibling tree_node / list_node modules)     #
# --------------------------------------------------------------------------- #

_TREE_NODE_SRC = (
    "class TreeNode:\n"
    "    def __init__(self, val=0, left=None, right=None):\n"
    "        self.val = val\n"
    "        self.left = left\n"
    "        self.right = right\n"
)

_LIST_NODE_SRC = (
    "class ListNode:\n"
    "    def __init__(self, val=0, next=None):\n"
    "        self.val = val\n"
    "        self.next = next\n"
)


def test_runner_tree_node_problem(tmp_path):
    """A tree-input problem: solution returns the input root unchanged."""
    _stage(
        tmp_path,
        solution=(
            "from tree_node import TreeNode\n"
            "class Solution:\n"
            "    def identity(self, root: TreeNode) -> TreeNode:\n"
            "        return root\n"
        ),
        cases={
            "schema_version": 1,
            "problem_id": 1,
            "title": "T",
            "method": "identity",
            "signature": {
                "params": [{"name": "root", "type": "TREE_NODE"}],
                "returns": "TREE_NODE",
            },
            "cases": [
                {
                    "case_id": 1,
                    "input": {"root": [1, 2, 3]},
                    "expected": [1, 2, 3],
                }
            ],
        },
        extras={"tree_node.py": _TREE_NODE_SRC},
    )
    code, stdout, _ = _invoke(tmp_path)
    assert code == 0
    envelope = _parse_envelope(stdout)
    assert envelope[0]["passed"] is True


def test_runner_list_node_problem(tmp_path):
    """A linked-list problem: solution reverses the list."""
    _stage(
        tmp_path,
        solution=(
            "from list_node import ListNode\n"
            "class Solution:\n"
            "    def reverse(self, head):\n"
            "        prev = None\n"
            "        while head:\n"
            "            nxt = head.next\n"
            "            head.next = prev\n"
            "            prev = head\n"
            "            head = nxt\n"
            "        return prev\n"
        ),
        cases={
            "schema_version": 1,
            "problem_id": 206,
            "title": "Reverse LL",
            "method": "reverse",
            "signature": {
                "params": [{"name": "head", "type": "LIST_NODE"}],
                "returns": "LIST_NODE",
            },
            "cases": [
                {
                    "case_id": 1,
                    "input": {"head": [1, 2, 3]},
                    "expected": [3, 2, 1],
                }
            ],
        },
        extras={"list_node.py": _LIST_NODE_SRC},
    )
    code, stdout, _ = _invoke(tmp_path)
    assert code == 0
    envelope = _parse_envelope(stdout)
    assert envelope[0]["passed"] is True


# --------------------------------------------------------------------------- #
# format_input / display flow through to the envelope                         #
# --------------------------------------------------------------------------- #


def test_runner_envelope_contains_input_and_expected_strings(tmp_path):
    """`input` and `expected` are stringified for display in failures."""
    _stage(
        tmp_path,
        solution=(
            "class Solution:\n" "    def add(self, a, b):\n" "        return a + b\n"
        ),
        cases={
            "schema_version": 1,
            "problem_id": 1,
            "title": "Add",
            "method": "add",
            "signature": {
                "params": [
                    {"name": "a", "type": "INT32"},
                    {"name": "b", "type": "INT32"},
                ],
                "returns": "INT32",
            },
            "cases": [{"case_id": 1, "input": {"a": 1, "b": 2}, "expected": 3}],
        },
    )
    _, stdout, _ = _invoke(tmp_path)
    envelope = _parse_envelope(stdout)
    assert envelope[0]["input"] == "a = 1, b = 2"
    assert envelope[0]["expected"] == "3"


# --------------------------------------------------------------------------- #
# Regression: a user exception on one node-typed case must not collapse the   #
# whole run (the except path once called display() on the raw expected list). #
# --------------------------------------------------------------------------- #


_TREE_NODE_MODULE = (
    "class TreeNode:\n"
    "    def __init__(self, val=0, left=None, right=None):\n"
    "        self.val = val\n"
    "        self.left = left\n"
    "        self.right = right\n"
)


def test_runner_preserves_other_cases_when_a_tree_case_raises(tmp_path):
    build = _stage(
        tmp_path,
        solution=(
            "from tree_node import TreeNode\n"
            "class Solution:\n"
            "    def maxDepth(self, root):\n"
            "        if root is not None and root.val == 99:\n"
            "            raise RuntimeError('boom')\n"
            "        if root is None:\n"
            "            return 0\n"
            "        return 1 + max(self.maxDepth(root.left),\n"
            "                       self.maxDepth(root.right))\n"
        ),
        cases={
            "schema_version": 1,
            "problem_id": 104,
            "title": "Max Depth",
            "method": "maxDepth",
            "signature": {
                "params": [{"name": "root", "type": {"base": "BINARY_TREE"}}],
                "returns": {"base": "INT32"},
            },
            "comparison": "exact",
            "cases": [
                {"case_id": 1, "input": {"root": [1, 2, 3]}, "expected": 2},
                {"case_id": 2, "input": {"root": [99]}, "expected": 1},
                {"case_id": 3, "input": {"root": []}, "expected": 0},
            ],
        },
        extras={"tree_node.py": _TREE_NODE_MODULE},
    )

    code, stdout, _ = _invoke(build)
    results = _parse_envelope(stdout)

    assert code == 0
    assert [r["case"] for r in results] == [1, 2, 3]
    assert results[0]["passed"] is True
    assert results[2]["passed"] is True
    assert results[1]["passed"] is False
    assert "RuntimeError: boom" in results[1]["error"]


def test_runner_reports_crash_on_node_return_type_without_collapsing(tmp_path):
    """Same regression on the *return* side: expected is a node structure."""
    build = _stage(
        tmp_path,
        solution=(
            "from tree_node import TreeNode\n"
            "class Solution:\n"
            "    def invertTree(self, root):\n"
            "        if root is not None and root.val == 99:\n"
            "            raise ValueError('nope')\n"
            "        return root\n"
        ),
        cases={
            "schema_version": 1,
            "problem_id": 226,
            "title": "Invert",
            "method": "invertTree",
            "signature": {
                "params": [{"name": "root", "type": {"base": "BINARY_TREE"}}],
                "returns": {"base": "BINARY_TREE"},
            },
            "comparison": "exact",
            "cases": [
                {"case_id": 1, "input": {"root": [99]}, "expected": [99]},
                {"case_id": 2, "input": {"root": [1]}, "expected": [1]},
            ],
        },
        extras={"tree_node.py": _TREE_NODE_MODULE},
    )

    _, stdout, _ = _invoke(build)
    results = _parse_envelope(stdout)

    assert [r["case"] for r in results] == [1, 2]
    assert "ValueError: nope" in results[0]["error"]
    assert results[0]["expected"] == "[99]"  # parsed + serialized, not crashed
    assert results[1]["passed"] is True
