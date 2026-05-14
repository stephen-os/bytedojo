"""Tests for `dojo test` (the CLI command, not pytest tests of code-named-test)."""

import pytest
from click.testing import CliRunner

from bytedojo.commands.subcommands.test import test as test_cmd
from bytedojo.services.test_service import (
    TestCaseResult,
    TestRunResult,
    TestServiceResult,
)


# --------------------------------------------------------------------------- #
# Pre-flight                                                                  #
# --------------------------------------------------------------------------- #

def test_test_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(test_cmd, ["1"])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


def test_test_no_selector_errors(repo, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(test_cmd, [])
    assert result.exit_code != 0
    assert "Please specify a problem" in result.output


# --------------------------------------------------------------------------- #
# Service wiring + happy path                                                 #
# --------------------------------------------------------------------------- #

def _passed_run_result(problem) -> TestRunResult:
    return TestRunResult(
        problem_id=problem.problem_id, language=problem.language.value,
        total_cases=3, passed_count=3, failed_count=0, error_count=0,
        case_results=[
            TestCaseResult(case_number=i, passed=True,
                           input_str=f"x={i}", expected="y", actual="y")
            for i in range(1, 4)
        ],
    )


def _failed_run_result(problem) -> TestRunResult:
    return TestRunResult(
        problem_id=problem.problem_id, language=problem.language.value,
        total_cases=3, passed_count=1, failed_count=2, error_count=0,
        case_results=[
            TestCaseResult(case_number=1, passed=True,
                           input_str="ok", expected="y", actual="y"),
            TestCaseResult(case_number=2, passed=False,
                           input_str="bad-1", expected="y", actual="z"),
            TestCaseResult(case_number=3, passed=False,
                           input_str="bad-2", expected="y", actual=""),
        ],
    )


@pytest.fixture
def stub_test_service(monkeypatch):
    """Replace TestService.test_problem; capture args + return controllable results."""
    state = {"calls": [], "result": None}

    def fake_test(self, repo, problem, *, version=None, timeout=60, progress_callback=None):
        state["calls"].append({
            "problem_id": problem.problem_id,
            "version": version,
            "timeout": timeout,
        })
        if state["result"] is not None:
            return state["result"]
        return TestServiceResult(
            problem=problem, version=1,
            file_path=repo.root_dir / problem.file_path,
            run_result=_passed_run_result(problem),
        )

    monkeypatch.setattr(
        "bytedojo.services.test_service.TestService.test_problem", fake_test,
    )
    return state


def test_test_dispatches_to_service(repo, registered_problem, monkeypatch, stub_test_service):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(test_cmd, ["1"])
    assert result.exit_code == 0, result.output
    assert stub_test_service["calls"][0]["problem_id"] == 1
    assert stub_test_service["calls"][0]["timeout"] == 60  # default


def test_test_passes_version_flag(repo, registered_problem, monkeypatch, stub_test_service):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(test_cmd, ["1", "--version", "3"])
    assert stub_test_service["calls"][0]["version"] == 3


def test_test_passes_timeout_flag(repo, registered_problem, monkeypatch, stub_test_service):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(test_cmd, ["1", "--timeout", "120"])
    assert stub_test_service["calls"][0]["timeout"] == 120


# --------------------------------------------------------------------------- #
# Status display                                                              #
# --------------------------------------------------------------------------- #

def test_test_passed_prints_passed_marker(repo, registered_problem, monkeypatch, stub_test_service):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(test_cmd, ["1"])
    assert "PASSED" in result.output


def test_test_failed_prints_failed_marker(repo, registered_problem, monkeypatch, stub_test_service):
    stub_test_service["result"] = TestServiceResult(
        problem=registered_problem, version=1,
        file_path=repo.root_dir / registered_problem.file_path,
        run_result=_failed_run_result(registered_problem),
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(test_cmd, ["1"])
    assert "FAILED" in result.output


def test_test_failed_shows_failing_case_details_by_default(
    repo, registered_problem, monkeypatch, stub_test_service,
):
    """Without --verbose, failed cases are shown (and at least one input snippet)."""
    stub_test_service["result"] = TestServiceResult(
        problem=registered_problem, version=1,
        file_path=repo.root_dir / registered_problem.file_path,
        run_result=_failed_run_result(registered_problem),
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(test_cmd, ["1"])
    assert "bad-1" in result.output


def test_test_verbose_shows_passing_cases_too(
    repo, registered_problem, monkeypatch, stub_test_service,
):
    """--verbose -> passing cases section appears."""
    stub_test_service["result"] = TestServiceResult(
        problem=registered_problem, version=1,
        file_path=repo.root_dir / registered_problem.file_path,
        run_result=_failed_run_result(registered_problem),
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(test_cmd, ["1", "--verbose"])
    assert "Passed Test Cases" in result.output


# --------------------------------------------------------------------------- #
# Skip + failure paths                                                        #
# --------------------------------------------------------------------------- #

def test_test_skipped_renders_skip_reason(repo, registered_problem, monkeypatch, stub_test_service):
    stub_test_service["result"] = TestServiceResult(
        problem=registered_problem, version=1,
        file_path=repo.root_dir / registered_problem.file_path,
        skipped=True, skip_reason="Bundle has zero test cases",
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(test_cmd, ["1"])
    assert result.exit_code == 0
    assert "zero test cases" in result.output


def test_test_pre_flight_failure_raises_click(repo, registered_problem, monkeypatch, stub_test_service):
    """TestServiceResult with error set -> ClickException with non-zero exit."""
    stub_test_service["result"] = TestServiceResult(
        problem=registered_problem, error="No test bundle for problem #1.",
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(test_cmd, ["1"])
    assert result.exit_code != 0
    assert "test bundle" in result.output
