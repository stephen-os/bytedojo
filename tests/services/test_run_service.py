"""Tests for RunService."""

import pytest

from bytedojo.core.errors import SolutionNotFoundError, ToolchainMissingError
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.base import ToolchainStatus
from bytedojo.services.run_service import RunService

from tests.services.conftest import insert_registered_problem

# --------------------------------------------------------------------------- #
# run_problem — pre-flight error paths (typed, §10)                           #
# --------------------------------------------------------------------------- #


def test_run_problem_missing_file_raises(repo, registered_problem):
    """Registered file_path doesn't exist on disk -> SolutionNotFoundError."""
    with pytest.raises(SolutionNotFoundError, match="not found"):
        RunService().run_problem(repo, registered_problem)


def test_run_problem_no_file_path_raises(repo):
    """A row with file_path=None bubbles up the resolver's error."""
    problem = insert_registered_problem(repo, pid=99, file_path=None)
    with pytest.raises(SolutionNotFoundError, match="no associated file path"):
        RunService().run_problem(repo, problem)


def test_run_problem_unsupported_language_raises(repo):
    """A language with no registered toolchain raises ToolchainMissingError."""
    problem = insert_registered_problem(
        repo,
        pid=42,
        language=CodeLanguage.RUST,
        file_path="problems/x/rust/v001/solution.rs",
    )
    # Place the file so resolve_solution_path doesn't trip first.
    (repo.root_dir / "problems" / "x" / "rust" / "v001").mkdir(parents=True)
    (repo.root_dir / "problems" / "x" / "rust" / "v001" / "solution.rs").write_text("")

    with pytest.raises(ToolchainMissingError, match="rust.*no registered toolchain"):
        RunService().run_problem(repo, problem)


def test_run_problem_missing_toolchain_binary_includes_install_hint(
    repo,
    registered_problem,
    monkeypatch,
):
    """Toolchain present in registry but binaries missing -> install hint surfaced."""
    file_path = repo.root_dir / registered_problem.file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("print('x')\n", encoding="utf-8")

    from bytedojo.core.toolchains.python import PythonToolchain

    monkeypatch.setattr(
        PythonToolchain,
        "detect",
        lambda self: ToolchainStatus(
            language=CodeLanguage.PYTHON,
            found=False,
            missing=["python"],
            install_hint="install python from python.org",
        ),
    )

    with pytest.raises(ToolchainMissingError) as exc:
        RunService().run_problem(repo, registered_problem)
    assert "not found" in exc.value.message.lower()
    assert "install python" in exc.value.message.lower()


# --------------------------------------------------------------------------- #
# run_problem — happy path                                                    #
# --------------------------------------------------------------------------- #


def test_run_problem_python_hello_world(repo, registered_problem):
    """End-to-end: a Python file on disk runs through the real toolchain."""
    file_path = repo.root_dir / registered_problem.file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text('print("ran")\n', encoding="utf-8")

    result = RunService().run_problem(repo, registered_problem, timeout=10)
    assert result.execution.exit_code == 0
    assert result.execution.stdout.strip() == "ran"
    assert result.file_path == file_path


def test_run_problem_records_run_version_and_count(repo, registered_problem):
    """A run resolves the latest attempt and bumps its run counter (§7)."""
    file_path = repo.root_dir / registered_problem.file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("pass\n", encoding="utf-8")

    with repo.session() as s:
        s.attempts.create(
            source="leetcode",
            problem_id=1,
            language=CodeLanguage.PYTHON.value,
        )

    result = RunService().run_problem(repo, registered_problem, timeout=10)
    assert result.version == 1
    with repo.session() as s:
        assert s.attempts.get("leetcode", 1, version=1).run_count == 1


# --------------------------------------------------------------------------- #
# run_problem — version flag                                                  #
# --------------------------------------------------------------------------- #


def test_run_problem_unknown_version_lists_available(repo, registered_problem):
    """Requested version not registered -> error mentions what was asked."""
    with pytest.raises(SolutionNotFoundError, match="99"):
        RunService().run_problem(repo, registered_problem, version=99)
