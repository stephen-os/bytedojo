"""Tests for TestService."""

import json

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.models.test_bundle import TestBundle, TestCase, TestSignature
from bytedojo.services.test_service import (
    TestCaseResult,
    TestRunResult,
    TestService,
    TestServiceResult,
    _all_timed_out,
    _build_run_result,
    _compile_error_result,
    _format_path_error,
    _parse_envelope,
    _runtime_error,
)

from tests.services.conftest import insert_registered_problem


# --------------------------------------------------------------------------- #
# Result dataclasses                                                          #
# --------------------------------------------------------------------------- #

def test_test_case_result_defaults():
    r = TestCaseResult(case_number=1, passed=True,
                       input_str="x", expected="y", actual="y")
    assert r.error is None
    assert r.timed_out is False


def test_test_run_result_runnable_count():
    r = TestRunResult(
        problem_id=1, language="python3", total_cases=10,
        passed_count=7, failed_count=2, error_count=0, skipped_count=1,
    )
    assert r.runnable_count == 9


def test_test_run_result_all_passed_true_when_runnable_passed():
    r = TestRunResult(
        problem_id=1, language="python3", total_cases=3,
        passed_count=3, failed_count=0, error_count=0,
    )
    assert r.all_passed is True
    assert r.status == "passed"


def test_test_run_result_all_passed_false_when_zero_runnable():
    """A bundle with zero cases is not 'all passed' — it's degenerate."""
    r = TestRunResult(
        problem_id=1, language="python3", total_cases=0,
        passed_count=0, failed_count=0, error_count=0,
    )
    assert r.all_passed is False


def test_test_run_result_status_compile_error_wins():
    r = TestRunResult(
        problem_id=1, language="python3", total_cases=3,
        passed_count=3, failed_count=0, error_count=0,
        compile_error="oops",
    )
    assert r.status == "error"


def test_test_run_result_status_failed_when_any_failure():
    r = TestRunResult(
        problem_id=1, language="python3", total_cases=3,
        passed_count=1, failed_count=2, error_count=0,
    )
    assert r.status == "failed"


def test_test_run_result_status_ungraded_for_partial_passed_only():
    """All-skipped: nothing failed, but `all_passed` is False -> 'ungraded'."""
    r = TestRunResult(
        problem_id=1, language="python3", total_cases=3,
        passed_count=2, failed_count=0, error_count=0, skipped_count=1,
    )
    # runnable=2, passed=2 -> all_passed True actually. Let me build a real
    # "no passes, no failures" case.
    r2 = TestRunResult(
        problem_id=1, language="python3", total_cases=3,
        passed_count=0, failed_count=0, error_count=0, skipped_count=3,
    )
    assert r2.status == "ungraded"


def test_test_service_result_states_are_mutually_exclusive():
    fake_run = TestRunResult(
        problem_id=1, language="python3", total_cases=1,
        passed_count=1, failed_count=0, error_count=0,
    )

    success = TestServiceResult(problem=None, run_result=fake_run)
    skipped = TestServiceResult(problem=None, skipped=True)
    failed = TestServiceResult(problem=None, error="x")

    assert success.success and not success.failed
    assert not skipped.success and not skipped.failed     # skipped is its own thing
    assert not failed.success and failed.failed


# --------------------------------------------------------------------------- #
# _parse_envelope — pure JSON envelope parsing                                #
# --------------------------------------------------------------------------- #

_BEGIN = "<<<BYTEDOJO_RESULTS_BEGIN>>>"
_END = "<<<BYTEDOJO_RESULTS_END>>>"


def test_parse_envelope_happy_path():
    payload = json.dumps([{"case": 1, "passed": True}])
    out = f"noise before\n{_BEGIN}{payload}{_END}\nnoise after"
    data, err = _parse_envelope(out)
    assert err is None
    assert data == [{"case": 1, "passed": True}]


def test_parse_envelope_handles_whitespace_around_payload():
    payload = json.dumps([{"case": 1}])
    out = f"{_BEGIN}\n   {payload}   \n{_END}"
    data, err = _parse_envelope(out)
    assert err is None
    assert data == [{"case": 1}]


def test_parse_envelope_missing_sentinels_returns_error():
    data, err = _parse_envelope("user program output without sentinels")
    assert data is None
    assert err is not None
    assert "No results envelope" in err


def test_parse_envelope_end_before_begin_returns_error():
    """Malformed: end sentinel appears before begin -> error."""
    out = f"{_END}some junk{_BEGIN}[]{_END}"
    # The first _BEGIN find is well after the first _END find -> begin > end
    # Actually find returns first occurrence in each case, so begin > end.
    data, err = _parse_envelope(out)
    assert data is None
    assert err is not None


def test_parse_envelope_invalid_json_returns_error():
    out = f"{_BEGIN}{{ not valid json {_END}"
    data, err = _parse_envelope(out)
    assert data is None
    assert "Failed to parse" in err


# --------------------------------------------------------------------------- #
# _build_run_result / _all_timed_out / _runtime_error / _compile_error_result #
# --------------------------------------------------------------------------- #

def _bundle(cases_count: int = 2) -> TestBundle:
    return TestBundle(
        schema_version=1, problem_id=1, title="t", method="solve",
        signature=TestSignature(),
        cases=[TestCase(case_id=i, input={}, expected=None) for i in range(1, cases_count + 1)],
    )


def _problem_stub(pid: int = 1, lang: CodeLanguage = CodeLanguage.PYTHON):
    """Minimal duck-typed object for _build_run_result / friends."""
    class P:
        pass
    P.problem_id = pid
    P.language = lang
    return P()


def test_build_run_result_counts_pass_fail_error():
    bundle = _bundle(3)
    entries = [
        {"case": 1, "passed": True,  "input": "", "expected": "", "actual": ""},
        {"case": 2, "passed": False, "input": "", "expected": "", "actual": ""},
        {"case": 3, "passed": False, "input": "", "expected": "", "actual": "",
         "error": "boom"},
    ]
    r = _build_run_result(_problem_stub(), bundle, entries)
    assert r.passed_count == 1
    assert r.failed_count == 1
    assert r.error_count == 1
    assert len(r.case_results) == 3
    assert r.case_results[2].error == "boom"


def test_all_timed_out_marks_every_case():
    bundle = _bundle(3)
    r = _all_timed_out(_problem_stub(), bundle, timeout=10)
    assert r.total_cases == 3
    assert r.error_count == 3
    assert all(cr.timed_out for cr in r.case_results)
    assert "timed out" in r.runtime_error.lower()


def test_runtime_error_populates_count_and_detail():
    bundle = _bundle(2)
    r = _runtime_error(_problem_stub(), bundle, "crash", "Traceback (...)")
    assert r.passed_count == 0
    assert r.error_count == 2
    assert "crash" in r.runtime_error
    assert "Traceback" in r.runtime_error


def test_compile_error_result():
    bundle = _bundle(2)
    r = _compile_error_result(_problem_stub(), bundle, "syntax error")
    assert r.compile_error == "syntax error"
    assert r.error_count == 2
    assert r.status == "error"


# --------------------------------------------------------------------------- #
# _format_path_error                                                          #
# --------------------------------------------------------------------------- #

def test_format_path_error_with_no_version_uses_error_string():
    from bytedojo.services.problem_service import SolutionPathResult
    resolved = SolutionPathResult(error="solution file not found at /x")
    msg = _format_path_error(resolved, requested_version=None)
    assert msg == "solution file not found at /x"


def test_format_path_error_with_version_lists_available():
    from bytedojo.services.problem_service import SolutionPathResult
    resolved = SolutionPathResult(
        error="Version 5 not found", available_versions=[1, 2, 3],
    )
    msg = _format_path_error(resolved, requested_version=5)
    assert "Version 5 not found" in msg
    assert "Available: v1, v2, v3" in msg


def test_format_path_error_with_version_but_no_available_keeps_message():
    from bytedojo.services.problem_service import SolutionPathResult
    resolved = SolutionPathResult(error="bad", available_versions=[])
    msg = _format_path_error(resolved, requested_version=5)
    assert msg == "bad"


# --------------------------------------------------------------------------- #
# TestService.test_problem — pre-flight error paths                           #
# --------------------------------------------------------------------------- #

def test_test_problem_unsupported_language(repo):
    problem = insert_registered_problem(repo, pid=1, language=CodeLanguage.RUST,
                                        file_path="x/y/solution.rs")
    result = TestService().test_problem(repo, problem)
    assert result.failed
    assert "rust" in result.error.lower()
    assert "currently supported" in result.error.lower()


def test_test_problem_missing_solution_file(repo, registered_problem):
    result = TestService().test_problem(repo, registered_problem)
    assert result.failed
    assert "not found" in result.error.lower()


def _patch_bundle_path(monkeypatch, bundle_file):
    """Redirect both copies of get_test_file at a custom bundle file.

    test_bundle.load() uses the import in core.models.test_bundle;
    test_service._stage_runtime uses the import in services.test_service.
    Both must agree or the runner reads a different bundle than the service.
    """
    fake = lambda pid: bundle_file
    monkeypatch.setattr(
        "bytedojo.core.models.test_bundle.get_test_file", fake,
    )
    monkeypatch.setattr(
        "bytedojo.services.test_service.get_test_file", fake,
    )


def test_test_problem_missing_bundle(repo, registered_problem, tmp_path, monkeypatch):
    """File present but no test bundle JSON -> failure with regenerate hint."""
    f = repo.root_dir / registered_problem.file_path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("pass\n", encoding="utf-8")

    _patch_bundle_path(monkeypatch, tmp_path / "1.json")     # doesn't exist

    result = TestService().test_problem(repo, registered_problem)
    assert result.failed
    assert "no test bundle" in result.error.lower()


def test_test_problem_empty_bundle_is_skipped(repo, registered_problem, tmp_path, monkeypatch):
    """Bundle exists but has zero cases -> soft skip, no DB update."""
    f = repo.root_dir / registered_problem.file_path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("pass\n", encoding="utf-8")

    bundle_file = tmp_path / "1.json"
    bundle_file.write_text(json.dumps({
        "schema_version": 1, "problem_id": 1, "title": "t", "method": "solve",
        "signature": {"params": [], "returns": "VOID"},
        "cases": [],
    }), encoding="utf-8")
    _patch_bundle_path(monkeypatch, bundle_file)

    result = TestService().test_problem(repo, registered_problem)
    assert result.skipped
    assert "zero test cases" in result.skip_reason.lower()


def test_test_problem_missing_toolchain_binary(
    repo, registered_problem, tmp_path, monkeypatch,
):
    """A registered language whose toolchain.detect() reports not-found."""
    f = repo.root_dir / registered_problem.file_path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("pass\n", encoding="utf-8")

    # Mark python toolchain as missing.
    from bytedojo.core.toolchains.base import ToolchainStatus
    from bytedojo.core.toolchains.python import PythonToolchain
    monkeypatch.setattr(
        PythonToolchain, "detect",
        lambda self: ToolchainStatus(
            language=CodeLanguage.PYTHON, found=False,
            missing=["python"], install_hint="install py",
        ),
    )

    result = TestService().test_problem(repo, registered_problem)
    assert result.failed
    assert "not found" in result.error.lower()
    assert "install py" in result.error


# --------------------------------------------------------------------------- #
# TestService.test_problem — Python happy path                                #
# --------------------------------------------------------------------------- #

def test_test_problem_python_happy_path(repo, registered_problem, tmp_path, monkeypatch):
    """End-to-end Python: stage, run, parse, record passing status."""
    # Solution: takes nums + target, returns indices summing to target.
    solution = repo.root_dir / registered_problem.file_path
    solution.parent.mkdir(parents=True, exist_ok=True)
    solution.write_text(
        "class Solution:\n"
        "    def twoSum(self, nums, target):\n"
        "        seen = {}\n"
        "        for i, n in enumerate(nums):\n"
        "            if target - n in seen:\n"
        "                return [seen[target - n], i]\n"
        "            seen[n] = i\n"
        "        return []\n",
        encoding="utf-8",
    )

    bundle_file = tmp_path / "1.json"
    bundle_file.write_text(json.dumps({
        "schema_version": 1, "problem_id": 1, "title": "Two Sum",
        "method": "twoSum",
        "signature": {
            "params": [
                {"name": "nums",   "type": "INT32_ARRAY"},
                {"name": "target", "type": "INT32"},
            ],
            "returns": "INT32_ARRAY",
        },
        "cases": [
            {"case_id": 1, "input": {"nums": [2, 7, 11, 15], "target": 9},
             "expected": [0, 1]},
            {"case_id": 2, "input": {"nums": [3, 2, 4], "target": 6},
             "expected": [1, 2]},
        ],
        "comparison": "unordered_all",
    }), encoding="utf-8")
    _patch_bundle_path(monkeypatch, bundle_file)

    # Seed an attempt so resolve_solution_path can compute "latest".
    with repo.open_db() as db:
        db.create_attempt(source="leetcode", problem_id=1,
                          language=CodeLanguage.PYTHON.value)

    result = TestService().test_problem(repo, registered_problem, timeout=30)
    assert result.success, getattr(result, "error", None)
    assert result.run_result.all_passed
    assert result.run_result.passed_count == 2

    # Persisted to DB on both the problem row and the versioned_attempt.
    with repo.open_db() as db:
        fresh = db.get_problem("leetcode", 1, "python3")
    assert fresh.status is ProblemStatus.PASSED
