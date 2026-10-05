"""
Test service - run tests against a registered problem and persist the result.

Loads the typed TestBundle for a problem, stages the language's universal
runner into a per-problem build directory alongside the user's solution,
invokes the language runtime, parses the JSON results envelope, and
updates the database with the pass/fail status.

Currently supports Python. Other languages return a clean
"not yet supported" error.
"""

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from bytedojo.core import corpus
from bytedojo.core.errors import SolutionNotFoundError, ToolchainMissingError
from bytedojo.core.logger import get_logger
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.models.test_bundle import TestBundle
from bytedojo.core.repository import Repository
from bytedojo.core.toolchains import get_toolchain
from bytedojo.runtime.python3 import RUNTIME_DIR as PYTHON_RUNTIME_DIR
from bytedojo.services.problem_service import resolve_solution_path
from bytedojo.services.review_service import ReviewService, ScheduleEffect

#: Languages whose universal runner is wired into TestService.
_SUPPORTED_LANGUAGES = frozenset({CodeLanguage.PYTHON})


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

    __test__ = False  # don't let pytest mistake this for a test class

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

    __test__ = False  # don't let pytest mistake this for a test class

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
        # ERROR = the solution never got evaluated (compile failure or a
        # runner crash before any case ran); FAILED = cases ran and lost.
        if self.compile_error or (self.runtime_error and not self.case_results):
            return "error"
        if self.all_passed:
            return "passed"
        if self.failed_count > 0 or self.error_count > 0:
            return "failed"
        return "ungraded"


@dataclass
class TestServiceResult:
    """
    Outcome of testing a registered problem.

    Mutually-exclusive states:
      - success: tests ran; `run_result` populated
      - skipped: bundle has zero cases (soft outcome, no DB update)

    Pre-flight failures (missing file, missing toolchain, missing
    bundle) raise DojoError subclasses (§10) instead.
    """

    __test__ = False  # don't let pytest mistake this for a test class

    problem: RegisteredProblem
    version: Optional[int] = None
    file_path: Optional[Path] = None
    run_result: Optional[TestRunResult] = None
    schedule_effect: Optional[ScheduleEffect] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.run_result is not None


# ----------------------------------------------------------------------------
# TestService
# ----------------------------------------------------------------------------


class TestService:
    """Orchestrate test runs against the typed TestBundle pipeline."""

    __test__ = False  # don't let pytest mistake this for a test class

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

        # Resolve the solution file (latest, or a specific version). The
        # resolved attempt's language — not the problem row's — drives the
        # runner choice, since older versions may be in another language.
        resolved = resolve_solution_path(repo, problem, version=version)
        if not resolved.found:
            raise SolutionNotFoundError(_format_path_error(resolved, version))
        file_path = resolved.path
        tested_version = resolved.version
        language = resolved.language or problem.language
        ctx = {"version": tested_version, "file_path": file_path}

        if language not in _SUPPORTED_LANGUAGES:
            raise ToolchainMissingError(
                f"The {language.value} runner has not been ported to the "
                f"typed test schema yet. Currently supported: "
                f"{', '.join(sorted(lang.value for lang in _SUPPORTED_LANGUAGES))}."
            )

        # Confirm the language toolchain is available
        toolchain = get_toolchain(language)
        if toolchain is None:
            raise ToolchainMissingError(
                f"{language.value} toolchain is not registered."
            )
        status = toolchain.detect()
        if not status.found:
            raise ToolchainMissingError(
                f"{language.value} toolchain not found.\n"
                + (
                    f"  Missing: {', '.join(status.missing)}\n"
                    if status.missing
                    else ""
                )
                + (f"  Install: {status.install_hint}" if status.install_hint else "")
            )

        # Load the typed test bundle. Fetch guarantees every registered
        # problem has one, so a BundleNotFoundError here is defensive
        # and propagates as-is (§10).
        bundle = corpus.bundle(problem.problem_id)
        if not bundle.cases:
            return self._skip(
                problem,
                "Bundle has zero test cases",
                **ctx,
            )

        # Prepare the per-problem build directory + drop the runner files in.
        build_dir = self._prepare_build_dir(repo, problem, language)
        try:
            self._stage_runtime(
                language=language,
                build_dir=build_dir,
                solution_src=file_path,
                problem_id=problem.problem_id,
            )
        except OSError as e:
            raise ToolchainMissingError(f"Failed to prepare build dir: {e}") from e

        # Compile (if needed) and invoke the language runtime
        try:
            stdout, stderr, compile_error = self._invoke_runner(
                language=language,
                build_dir=build_dir,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            run_result = _all_timed_out(problem, bundle, timeout)
            effect = self._record_status(
                repo, problem, run_result, version=tested_version
            )
            return TestServiceResult(
                problem=problem,
                version=tested_version,
                file_path=file_path,
                run_result=run_result,
                schedule_effect=effect,
            )

        # Compile-stage failure — short-circuit before we try to parse a
        # results envelope that doesn't exist. (Python never compiles; kept
        # for languages added later.)
        if compile_error is not None:
            run_result = _compile_error_result(problem, bundle, compile_error)
            effect = self._record_status(
                repo, problem, run_result, version=tested_version
            )
            return TestServiceResult(
                problem=problem,
                version=tested_version,
                file_path=file_path,
                run_result=run_result,
                schedule_effect=effect,
            )

        # Parse the JSON envelope between sentinels
        results_data, parse_error = _parse_envelope(stdout)
        if parse_error is not None:
            run_result = _runtime_error(problem, bundle, parse_error, stderr)
            effect = self._record_status(
                repo, problem, run_result, version=tested_version
            )
            return TestServiceResult(
                problem=problem,
                version=tested_version,
                file_path=file_path,
                run_result=run_result,
                schedule_effect=effect,
            )

        run_result = _build_run_result(problem, bundle, results_data)
        effect = self._record_status(repo, problem, run_result, version=tested_version)

        self.logger.debug(
            f"test_service: #{problem.problem_id} v{tested_version} "
            f"status={run_result.status} "
            f"({run_result.passed_count}/{run_result.total_cases})"
        )

        return TestServiceResult(
            problem=problem,
            version=tested_version,
            file_path=file_path,
            run_result=run_result,
            schedule_effect=effect,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _prepare_build_dir(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        language: CodeLanguage,
    ) -> Path:
        """Per-problem build directory under .dojo/build/."""
        build_dir = repo.build_dir / f"{problem.problem_id}_{language.value}"
        build_dir.mkdir(parents=True, exist_ok=True)
        return build_dir

    def _stage_runtime(
        self,
        *,
        language: CodeLanguage,
        build_dir: Path,
        solution_src: Path,
        problem_id: int,
    ) -> None:
        """Stage solution + universal runner + cases.json into build_dir.

        Python: copy solution.py + runner.py + converters.py + cases.json.
        """
        (build_dir / "cases.json").write_text(
            corpus.bundle_text(problem_id), encoding="utf-8"
        )

        if language == CodeLanguage.PYTHON:
            shutil.copyfile(solution_src, build_dir / "solution.py")
            # Carry sibling node-class modules (tree_node.py / list_node.py)
            # from the solution dir into the build dir so the runner's
            # converters can `from tree_node import TreeNode` etc.
            for name in ("tree_node.py", "list_node.py", "node.py"):
                sibling = solution_src.parent / name
                if sibling.exists():
                    shutil.copyfile(sibling, build_dir / name)
            shutil.copyfile(PYTHON_RUNTIME_DIR / "runner.py", build_dir / "runner.py")
            shutil.copyfile(
                PYTHON_RUNTIME_DIR / "converters.py", build_dir / "converters.py"
            )
            return

        raise RuntimeError(
            f"_stage_runtime called for unsupported language: {language}"
        )

    def _invoke_runner(
        self,
        *,
        language: CodeLanguage,
        build_dir: Path,
        timeout: int,
    ) -> Tuple[str, str, Optional[str]]:
        """Run the language's universal runner; return (stdout, stderr, compile_error)."""
        if language == CodeLanguage.PYTHON:
            proc = subprocess.run(
                [sys.executable, str(build_dir / "runner.py")],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return proc.stdout, proc.stderr, None

        raise RuntimeError(
            f"_invoke_runner called for unsupported language: {language}"
        )

    def _record_status(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        run_result: TestRunResult,
        *,
        version: Optional[int],
    ) -> ScheduleEffect:
        """Persist test outcome and drive the §9 schedule state machine.

        The grade lands on both the versioned attempt (what `dojo query`
        reads) and the problem row (which also carries the pass/fail notes),
        mirroring GradingService so the two never disagree. Testing IS the
        primary loop: a pass creates/advances the review track, a
        fail/error lapses it.
        """
        status = ProblemStatus.from_string(run_result.status)
        output = f"Passed: {run_result.passed_count}/{run_result.total_cases}"
        if run_result.compile_error:
            output = "Compile error"
        elif run_result.runtime_error and not run_result.case_results:
            output = "Runtime error"

        with repo.session() as s:
            if version is not None:
                s.attempts.update_status(
                    problem.source,
                    problem.problem_id,
                    version,
                    status.value,
                )
            s.problems.update_status(problem.id, status.value, output)

        reviews = ReviewService()
        if status is ProblemStatus.PASSED:
            return reviews.apply_pass(repo, problem.id)
        if status in (ProblemStatus.FAILED, ProblemStatus.ERROR):
            return reviews.apply_fail(repo, problem.id)
        return ScheduleEffect(action="none")

    def _skip(
        self,
        problem: RegisteredProblem,
        reason: str,
        *,
        version: Optional[int] = None,
        file_path: Optional[Path] = None,
    ) -> TestServiceResult:
        self.logger.debug(f"test_service: skipped #{problem.problem_id} — {reason}")
        return TestServiceResult(
            problem=problem,
            version=version,
            file_path=file_path,
            skipped=True,
            skip_reason=reason,
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
    payload = stdout[begin_idx + len(_RESULTS_BEGIN) : end_idx].strip()
    try:
        return json.loads(payload), None
    except json.JSONDecodeError as e:
        return None, f"Failed to parse results JSON: {e}"


def _build_run_result(
    problem, bundle: TestBundle, results_data: List[dict]
) -> TestRunResult:
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


def _runtime_error(
    problem, bundle: TestBundle, message: str, stderr: str
) -> TestRunResult:
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


def _compile_error_result(problem, bundle: TestBundle, message: str) -> TestRunResult:
    """Build a TestRunResult for a compile-stage failure."""
    return TestRunResult(
        problem_id=problem.problem_id,
        language=problem.language.value,
        total_cases=len(bundle.cases),
        passed_count=0,
        failed_count=0,
        error_count=len(bundle.cases),
        compile_error=message.strip(),
    )


def _format_path_error(resolved, requested_version: Optional[int]) -> str:
    """Render a SolutionPathResult error, listing available versions if relevant."""
    msg = resolved.error or "Solution path could not be resolved"
    if requested_version is not None and resolved.available_versions:
        avail = ", ".join(f"v{v}" for v in resolved.available_versions)
        msg = f"{msg}. Available: {avail}"
    return msg
