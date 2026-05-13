"""
Test service - run tests against a registered problem and persist the result.

Loads the typed TestBundle for a problem, copies the universal runner +
converter library into a per-problem build directory alongside the user's
solution, invokes the language runtime, parses the JSON results envelope,
and updates the database with the pass/fail status.

Phase 1 supports Python only. Java and C++ return a clean "not yet
supported" error until their universal runners land.
"""

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from bytedojo.core.logger import get_logger
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.models.test_bundle import TestBundle
from bytedojo.core.paths import get_test_file
from bytedojo.core.repository import Repository
from bytedojo.core.toolchains import get_toolchain
from bytedojo.runtime.python3 import RUNTIME_DIR as PYTHON_RUNTIME_DIR
from bytedojo.services.problem_service import resolve_solution_path


#: Sentinels the universal Python runner wraps around its JSON output.
#: Anything outside this range is treated as user-program stdout noise.
_RESULTS_BEGIN = "<<<BYTEDOJO_RESULTS_BEGIN>>>"
_RESULTS_END = "<<<BYTEDOJO_RESULTS_END>>>"


# ----------------------------------------------------------------------------
# Test result structs
# ----------------------------------------------------------------------------

@dataclass
class TestCaseResult:
    """Result of running a single test case."""
    case_number: int
    passed: bool
    input_str: str
    expected: str
    actual: str
    error: Optional[str] = None
    timed_out: bool = False


@dataclass
class TestRunResult:
    """Result of running all test cases for a problem."""
    problem_id: int
    language: str
    total_cases: int
    passed_count: int
    failed_count: int
    error_count: int
    skipped_count: int = 0
    case_results: List[TestCaseResult] = field(default_factory=list)
    compile_error: Optional[str] = None
    runtime_error: Optional[str] = None

    @property
    def runnable_count(self) -> int:
        """Cases that actually ran (excludes filtered/skipped)."""
        return self.total_cases - self.skipped_count

    @property
    def all_passed(self) -> bool:
        return self.runnable_count > 0 and self.passed_count == self.runnable_count

    @property
    def status(self) -> str:
        if self.compile_error:
            return "error"
        if self.all_passed:
            return "passed"
        if self.failed_count > 0 or self.error_count > 0:
            return "failed"
        return "untested"


@dataclass
class TestServiceResult:
    """
    Outcome of testing a registered problem.

    Mutually-exclusive states:
      - success: tests ran; `run_result` populated
      - skipped: no test bundle / no cases (soft outcome, no DB update)
      - failed:  pre-flight check failed (missing file, missing toolchain,
                 unsupported language); `error` set
    """
    problem: RegisteredProblem
    version: Optional[int] = None
    file_path: Optional[Path] = None
    run_result: Optional[TestRunResult] = None
    skipped: bool = False
    skip_reason: Optional[str] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.run_result is not None

    @property
    def failed(self) -> bool:
        return not self.success and not self.skipped


# ----------------------------------------------------------------------------
# TestService
# ----------------------------------------------------------------------------

class TestService:
    """Orchestrate test runs against the typed TestBundle pipeline."""

    def __init__(self):
        self.logger = get_logger()

    def test_problem(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        *,
        version: Optional[int] = None,
        timeout: int = 60,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> TestServiceResult:
        """
        Test `problem` and persist the result to the repo's database.

        Args:
            repo: Repository (used to resolve paths and persist test status).
            problem: The registered problem to test.
            version: Specific version to test, or None for the latest.
            timeout: Per-run timeout in seconds.
            progress_callback: Reserved for future per-case progress reporting.
        """
        self.logger.debug(
            f"test_service: testing #{problem.problem_id} "
            f"({problem.language.value}) version={version or 'latest'} "
            f"timeout={timeout}s"
        )

        # Phase 1 supports Python only.
        if problem.language != CodeLanguage.PYTHON:
            return self._error(
                problem,
                f"The {problem.language.value} runner has not been ported to the "
                f"typed test schema yet. Python is the only supported language "
                f"in this phase.",
            )

        # Resolve the solution file (latest, or a specific version).
        resolved = resolve_solution_path(repo, problem, version=version)
        if not resolved.found:
            return self._error(
                problem,
                _format_path_error(resolved, version),
                version=resolved.version,
            )
        file_path = resolved.path
        tested_version = resolved.version
        ctx = {"version": tested_version, "file_path": file_path}

        # Confirm the Python toolchain is available
        toolchain = get_toolchain(problem.language)
        if toolchain is None:
            return self._error(problem, "python3 toolchain is not registered.", **ctx)
        status = toolchain.detect()
        if not status.found:
            return self._error(
                problem,
                "python3 toolchain not found.\n"
                + (f"  Missing: {', '.join(status.missing)}\n" if status.missing else "")
                + (f"  Install: {status.install_hint}" if status.install_hint else ""),
                **ctx,
            )

        # Load the typed test bundle
        bundle = TestBundle.load(problem.problem_id)
        if bundle is None:
            return self._error(
                problem,
                f"No test bundle for problem #{problem.problem_id}. "
                f"Run the migration to regenerate data/tests/{problem.problem_id}.json.",
                **ctx,
            )
        if not bundle.cases:
            return self._skip(
                problem, "Bundle has zero test cases", **ctx,
            )

        # Prepare the per-problem build directory + drop the runner files in.
        build_dir = self._prepare_build_dir(repo, problem)
        try:
            self._stage_runtime(
                build_dir=build_dir,
                solution_src=file_path,
                problem_id=problem.problem_id,
            )
        except OSError as e:
            return self._error(problem, f"Failed to prepare build dir: {e}", **ctx)

        # Run the universal Python runner
        try:
            stdout, stderr = self._invoke_runner(build_dir, timeout)
        except subprocess.TimeoutExpired:
            run_result = _all_timed_out(problem, bundle, timeout)
            self._record_status(repo, problem, run_result, version=tested_version)
            return TestServiceResult(
                problem=problem, version=tested_version,
                file_path=file_path, run_result=run_result,
            )

        # Parse the JSON envelope between sentinels
        results_data, parse_error = _parse_envelope(stdout)
        if parse_error is not None:
            run_result = _runtime_error(problem, bundle, parse_error, stderr)
            self._record_status(repo, problem, run_result, version=tested_version)
            return TestServiceResult(
                problem=problem, version=tested_version,
                file_path=file_path, run_result=run_result,
            )

        run_result = _build_run_result(problem, bundle, results_data)
        self._record_status(repo, problem, run_result, version=tested_version)

        self.logger.info(
            f"test_service: #{problem.problem_id} v{tested_version} "
            f"status={run_result.status} "
            f"({run_result.passed_count}/{run_result.total_cases})"
        )

        return TestServiceResult(
            problem=problem,
            version=tested_version,
            file_path=file_path,
            run_result=run_result,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _prepare_build_dir(self, repo: Repository, problem: RegisteredProblem) -> Path:
        """Per-problem build directory under .dojo/build/."""
        build_dir = repo.build_dir / f"{problem.problem_id}_{problem.language.value}"
        build_dir.mkdir(parents=True, exist_ok=True)
        return build_dir

    def _stage_runtime(
        self, *,
        build_dir: Path,
        solution_src: Path,
        problem_id: int,
    ) -> None:
        """Copy user solution + universal runner + cases.json into build_dir."""
        # User solution -> solution.py (imported by runner.py)
        shutil.copyfile(solution_src, build_dir / "solution.py")
        # Universal runner files
        shutil.copyfile(PYTHON_RUNTIME_DIR / "runner.py", build_dir / "runner.py")
        shutil.copyfile(PYTHON_RUNTIME_DIR / "converters.py", build_dir / "converters.py")
        # The bundle itself becomes cases.json
        shutil.copyfile(get_test_file(problem_id), build_dir / "cases.json")

    def _invoke_runner(self, build_dir: Path, timeout: int):
        """Run `python runner.py` inside build_dir; return (stdout, stderr)."""
        proc = subprocess.run(
            [sys.executable, str(build_dir / "runner.py")],
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.stdout, proc.stderr

    def _record_status(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        run_result: TestRunResult,
        *,
        version: Optional[int],
    ) -> None:
        """Persist test outcome to per-version + legacy summary."""
        status = ProblemStatus.PASSED if run_result.all_passed else ProblemStatus.FAILED
        output = f"Passed: {run_result.passed_count}/{run_result.total_cases}"
        if run_result.compile_error:
            status = ProblemStatus.FAILED
            output = "Compile error"

        with repo.open_db() as db:
            if version is not None:
                db.update_attempt_test_status(
                    problem.source, problem.problem_id, problem.language.value,
                    version, status.value, output,
                )
            db.update_problem_status(problem.id, status.value, output)

    def _error(
        self,
        problem: RegisteredProblem,
        reason: str,
        *,
        version: Optional[int] = None,
        file_path: Optional[Path] = None,
    ) -> TestServiceResult:
        self.logger.warning(
            f"test_service: pre-flight failed for #{problem.problem_id} — {reason}"
        )
        return TestServiceResult(
            problem=problem, version=version,
            file_path=file_path, error=reason,
        )

    def _skip(
        self,
        problem: RegisteredProblem,
        reason: str,
        *,
        version: Optional[int] = None,
        file_path: Optional[Path] = None,
    ) -> TestServiceResult:
        self.logger.info(f"test_service: skipped #{problem.problem_id} — {reason}")
        return TestServiceResult(
            problem=problem, version=version,
            file_path=file_path, skipped=True, skip_reason=reason,
        )


# ----------------------------------------------------------------------------
# Module-level helpers (no logger dependency, easier to unit-test)
# ----------------------------------------------------------------------------

def _parse_envelope(stdout: str):
    """Find the sentinel-wrapped JSON array; returns (data, error_message)."""
    begin_idx = stdout.find(_RESULTS_BEGIN)
    end_idx = stdout.find(_RESULTS_END)
    if begin_idx < 0 or end_idx <= begin_idx:
        return None, (
            f"No results envelope in runner stdout. "
            f"First 200 chars: {stdout[:200]!r}"
        )
    payload = stdout[begin_idx + len(_RESULTS_BEGIN):end_idx].strip()
    try:
        return json.loads(payload), None
    except json.JSONDecodeError as e:
        return None, f"Failed to parse results JSON: {e}"


def _build_run_result(problem, bundle: TestBundle, results_data: List[dict]) -> TestRunResult:
    """Convert the runner's case envelopes into a TestRunResult struct."""
    case_results: List[TestCaseResult] = []
    passed = failed = errored = 0
    for entry in results_data:
        cr = TestCaseResult(
            case_number=entry.get("case", 0),
            passed=entry.get("passed", False),
            input_str=entry.get("input", ""),
            expected=entry.get("expected", ""),
            actual=entry.get("actual", ""),
            error=entry.get("error"),
        )
        case_results.append(cr)
        if entry.get("error"):
            errored += 1
        elif entry.get("passed"):
            passed += 1
        else:
            failed += 1

    return TestRunResult(
        problem_id=problem.problem_id,
        language=problem.language.value,
        total_cases=len(bundle.cases),
        passed_count=passed,
        failed_count=failed,
        error_count=errored,
        case_results=case_results,
    )


def _all_timed_out(problem, bundle: TestBundle, timeout: int) -> TestRunResult:
    """Build a TestRunResult for "the whole run timed out before any case finished"."""
    return TestRunResult(
        problem_id=problem.problem_id,
        language=problem.language.value,
        total_cases=len(bundle.cases),
        passed_count=0,
        failed_count=0,
        error_count=len(bundle.cases),
        case_results=[
            TestCaseResult(
                case_number=c.case_id,
                passed=False,
                input_str="",
                expected="",
                actual="",
                timed_out=True,
            )
            for c in bundle.cases
        ],
        runtime_error=f"Execution timed out after {timeout} seconds",
    )


def _runtime_error(problem, bundle: TestBundle, message: str, stderr: str) -> TestRunResult:
    """Build a TestRunResult for a runner crash before any case ran."""
    detail = message.strip()
    if stderr.strip():
        detail = f"{detail}\nstderr: {stderr.strip()[:500]}"
    return TestRunResult(
        problem_id=problem.problem_id,
        language=problem.language.value,
        total_cases=len(bundle.cases),
        passed_count=0,
        failed_count=0,
        error_count=len(bundle.cases),
        runtime_error=detail,
    )


def _format_path_error(resolved, requested_version: Optional[int]) -> str:
    """Render a SolutionPathResult error, listing available versions if relevant."""
    msg = resolved.error or "Solution path could not be resolved"
    if requested_version is not None and resolved.available_versions:
        avail = ", ".join(f"v{v}" for v in resolved.available_versions)
        msg = f"{msg}. Available: {avail}"
    return msg
