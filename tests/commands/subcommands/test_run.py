"""Tests for `dojo run`."""

import pytest
from click.testing import CliRunner

from bytedojo.commands.subcommands.run import run
from bytedojo.core.toolchains.base import ExecutionResult
from bytedojo.services.run_service import RunServiceResult

from tests.conftest import insert_registered_problem


# --------------------------------------------------------------------------- #
# Pre-flight                                                                  #
# --------------------------------------------------------------------------- #

def test_run_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(run, ["1"])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


def test_run_no_selector_errors(repo, monkeypatch):
    """No identifier / --name / --desc / --last -> actionable error from _resolve."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(run, [])
    assert result.exit_code != 0
    assert "Please specify a problem" in result.output


# --------------------------------------------------------------------------- #
# Happy path with mocked RunService                                           #
# --------------------------------------------------------------------------- #

@pytest.fixture
def stub_run_service(monkeypatch):
    """Replace RunService.run_problem; capture args + return a controllable result."""
    state = {"calls": [], "result": None}

    def fake_run(self, repo, problem, *, version=None, timeout=None):
        state["calls"].append({
            "problem_id": problem.problem_id, "version": version,
        })
        return state["result"] or RunServiceResult(
            problem=problem, version=1,
            file_path=repo.root_dir / problem.file_path,
            execution=ExecutionResult(
                exit_code=0, stdout="hello\n", stderr="",
                timed_out=False, language="python3",
                file_path=str(repo.root_dir / problem.file_path),
                compiled=False,
            ),
        )

    monkeypatch.setattr(
        "bytedojo.services.run_service.RunService.run_problem", fake_run,
    )
    return state


def test_run_dispatches_to_service(repo, registered_problem, monkeypatch, stub_run_service):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(run, ["1"])
    assert result.exit_code == 0, result.output
    assert stub_run_service["calls"] == [{"problem_id": 1, "version": None}]


def test_run_passes_version_flag(repo, registered_problem, monkeypatch, stub_run_service):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(run, ["1", "--version", "2"])
    assert result.exit_code == 0
    assert stub_run_service["calls"][0]["version"] == 2


def test_run_renders_header_with_problem_details(repo, registered_problem, monkeypatch, stub_run_service):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(run, ["1"])
    assert result.exit_code == 0
    assert "Running" in result.output
    assert "Two Sum" in result.output
    assert "[python3]" in result.output
    assert "v1" in result.output


def test_run_displays_stdout(repo, registered_problem, monkeypatch, stub_run_service):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(run, ["1"])
    assert "hello" in result.output
    assert "Execution completed successfully" in result.output


# --------------------------------------------------------------------------- #
# Service failures                                                            #
# --------------------------------------------------------------------------- #

def test_run_service_failure_raises_click_error(repo, registered_problem, monkeypatch, stub_run_service):
    """RunServiceResult with error set -> ClickException."""
    stub_run_service["result"] = RunServiceResult(
        problem=registered_problem, error="missing toolchain",
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(run, ["1"])
    assert result.exit_code != 0
    assert "missing toolchain" in result.output


def test_run_displays_compile_error(repo, registered_problem, monkeypatch, stub_run_service):
    stub_run_service["result"] = RunServiceResult(
        problem=registered_problem, version=1,
        file_path=repo.root_dir / registered_problem.file_path,
        execution=ExecutionResult(
            exit_code=1, stdout="", stderr="",
            timed_out=False, language="python3", file_path="x",
            compiled=False, compile_error="syntax error at line 5",
        ),
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(run, ["1"])
    assert "Compilation failed" in result.output
    assert "syntax error at line 5" in result.output


def test_run_displays_timeout(repo, registered_problem, monkeypatch, stub_run_service):
    stub_run_service["result"] = RunServiceResult(
        problem=registered_problem, version=1,
        file_path=repo.root_dir / registered_problem.file_path,
        execution=ExecutionResult(
            exit_code=1, stdout="", stderr="Execution timed out after 60 seconds",
            timed_out=True, language="python3", file_path="x", compiled=False,
        ),
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(run, ["1"])
    assert "timed out" in result.output.lower()


def test_run_displays_non_zero_exit_code(repo, registered_problem, monkeypatch, stub_run_service):
    stub_run_service["result"] = RunServiceResult(
        problem=registered_problem, version=1,
        file_path=repo.root_dir / registered_problem.file_path,
        execution=ExecutionResult(
            exit_code=42, stdout="", stderr="",
            timed_out=False, language="python3", file_path="x", compiled=False,
        ),
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(run, ["1"])
    assert "Execution failed" in result.output
    assert "42" in result.output
