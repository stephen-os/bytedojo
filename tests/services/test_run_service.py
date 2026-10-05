"""Tests for RunService."""

from pathlib import Path

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.base import ExecutionResult, ToolchainStatus
from bytedojo.services.run_service import RunService, RunServiceResult

from tests.services.conftest import insert_registered_problem


# --------------------------------------------------------------------------- #
# RunServiceResult                                                            #
# --------------------------------------------------------------------------- #

def test_result_success_when_execution_set(registered_problem):
    execution = ExecutionResult(
        exit_code=0, stdout="hi", stderr="", timed_out=False,
        language="python3", file_path="/p",
    )
    r = RunServiceResult(problem=registered_problem, execution=execution)
    assert r.success is True
    assert r.failed is False


def test_result_failed_when_no_execution(registered_problem):
    r = RunServiceResult(problem=registered_problem, error="boom")
    assert r.success is False
    assert r.failed is True


# --------------------------------------------------------------------------- #
# run_problem — pre-flight error paths                                        #
# --------------------------------------------------------------------------- #

def test_run_problem_missing_file_returns_error(repo, registered_problem):
    """Registered file_path doesn't exist on disk -> failure with a message."""
    result = RunService().run_problem(repo, registered_problem)
    assert result.failed
    assert "not found" in result.error.lower()


def test_run_problem_no_file_path_returns_error(repo):
    """A row with file_path=None bubbles up the resolver's error."""
    problem = insert_registered_problem(repo, pid=99, file_path=None)
    result = RunService().run_problem(repo, problem)
    assert result.failed
    assert "no associated file path" in result.error.lower()


def test_run_problem_unsupported_language_returns_error(repo):
    """A language with no registered toolchain returns a clean error."""
    problem = insert_registered_problem(repo, pid=42, language=CodeLanguage.RUST,
                                        file_path="problems/x/rust/v001/solution.rs")
    # Place the file so resolve_solution_path doesn't trip first.
    (repo.root_dir / "problems" / "x" / "rust" / "v001").mkdir(parents=True)
    (repo.root_dir / "problems" / "x" / "rust" / "v001" / "solution.rs").write_text("")

    result = RunService().run_problem(repo, problem)
    assert result.failed
    assert "rust" in result.error.lower()
    assert "no registered toolchain" in result.error.lower()


def test_run_problem_missing_toolchain_binary_returns_install_hint(
    repo, registered_problem, monkeypatch,
):
    """Toolchain present in registry but binaries missing -> install hint surfaced."""
    # Place the solution file so the resolver finds it.
    file_path = repo.root_dir / registered_problem.file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("print('x')\n", encoding="utf-8")

    # Patch the *python* toolchain's detect() to claim it's missing.
    from bytedojo.core.toolchains.python import PythonToolchain
    monkeypatch.setattr(
        PythonToolchain, "detect",
        lambda self: ToolchainStatus(
            language=CodeLanguage.PYTHON,
            found=False,
            missing=["python"],
            install_hint="install python from python.org",
        ),
    )

    result = RunService().run_problem(repo, registered_problem)
    assert result.failed
    assert "not found" in result.error.lower()
    assert "install python" in result.error.lower()


# --------------------------------------------------------------------------- #
# run_problem — happy path                                                    #
# --------------------------------------------------------------------------- #

def test_run_problem_python_hello_world(repo, registered_problem):
    """End-to-end: a Python file on disk runs through the real toolchain."""
    file_path = repo.root_dir / registered_problem.file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text('print("ran")\n', encoding="utf-8")

    result = RunService().run_problem(repo, registered_problem, timeout=10)
    assert result.success
    assert result.execution.exit_code == 0
    assert result.execution.stdout.strip() == "ran"
    assert result.file_path == file_path


def test_run_problem_records_run_version(repo, registered_problem):
    """An attempt registered for this problem populates the version on the result."""
    file_path = repo.root_dir / registered_problem.file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("pass\n", encoding="utf-8")

    # Seed a versioned attempt so resolve_solution_path can find a "latest" version.
    with repo.open_db() as db:
        db.create_attempt(
            source="leetcode",
            problem_id=1,
            language=CodeLanguage.PYTHON.value,
        )

    result = RunService().run_problem(repo, registered_problem, timeout=10)
    assert result.success
    assert result.version == 1


# --------------------------------------------------------------------------- #
# run_problem — version flag                                                  #
# --------------------------------------------------------------------------- #

def test_run_problem_unknown_version_lists_available(repo, registered_problem):
    """Requested version not registered -> error mentions what is available."""
    # No attempts registered yet, so v1 is not available.
    result = RunService().run_problem(repo, registered_problem, version=99)
    assert result.failed
    assert "99" in result.error
