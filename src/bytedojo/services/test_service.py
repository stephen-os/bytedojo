"""
Test service - run tests against a registered problem and persist the result.

Generates a self-contained test harness (solution + harness template + test
data) for the language, runs it through the language's Toolchain, parses the
results between sentinel markers, and updates the DB with the pass/fail
status. Today only Python is supported; other languages return a clean
"not yet supported" error via the toolchain registry.

The caller is responsible for problem lookup / disambiguation
(see services.problem_service.find_registered_problems).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from bytedojo.core.harness import (
    PYTHON_RESULTS_BEGIN,
    PYTHON_RESULTS_END,
    generate_test_code,
    parse_method_name,
    prepare_test_input,
)
from bytedojo.core.logger import get_logger
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.models.test_case import TestCase
from bytedojo.core.repository import Repository
from bytedojo.core.toolchains import get_toolchain
from bytedojo.services import problem_service
from bytedojo.services.problem_service import resolve_solution_path


# ----------------------------------------------------------------------------
# Test result structs (moved here from the old core/test_runner.py).
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
    case_results: List[TestCaseResult] = field(default_factory=list)
    compile_error: Optional[str] = None
    runtime_error: Optional[str] = None

    @property
    def all_passed(self) -> bool:
        return self.passed_count == self.total_cases and self.total_cases > 0

    @property
    def status(self) -> str:
        if self.compile_error:
            return 'error'
        if self.all_passed:
            return 'passed'
        if self.failed_count > 0 or self.error_count > 0:
            return 'failed'
        return 'untested'


# ----------------------------------------------------------------------------
# TestService — the public entry point.
# ----------------------------------------------------------------------------

@dataclass
class TestServiceResult:
    """
    Outcome of testing a registered problem.

    Mutually-exclusive states:
      - success: tests ran; `run_result` populated
      - skipped: no test cases available (soft outcome, no DB update)
      - failed:  pre-flight check failed (missing file, missing toolchain,
                 unsupported language, no starter snippet); `error` set
    """
    problem: RegisteredProblem
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


class TestService:
    """Generate a test harness, run it through the toolchain, persist results."""

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
            progress_callback: Optional callback for progress updates (not
                currently invoked by Python; reserved for compiled-language
                toolchains).

        Returns:
            TestServiceResult with the run outcome, skip reason, or error.
        """
        self.logger.debug(
            f"test_service: testing #{problem.problem_id} "
            f"({problem.language.value}) version={version or 'latest'} "
            f"timeout={timeout}s"
        )

        # Resolve the solution file (latest, or a specific version)
        resolved = resolve_solution_path(repo, problem, version=version)
        if not resolved.found:
            return self._error(problem, _format_path_error(resolved, version))
        file_path = resolved.path

        # Resolve the toolchain (Java/C++ return None today — clean error path)
        toolchain = get_toolchain(problem.language)
        if toolchain is None:
            return self._error(
                problem,
                f"{problem.language.value} is not yet supported. "
                f"Only Python is implemented at this time.",
            )

        # Confirm the toolchain is actually present on this machine
        status = toolchain.detect()
        if not status.found:
            lines = [f"{problem.language.value} toolchain not found."]
            if status.missing:
                lines.append(f"  Missing: {', '.join(status.missing)}")
            if status.install_hint:
                lines.append(f"  Install: {status.install_hint}")
            return self._error(problem, "\n".join(lines))

        # Load the full Problem (for test cases + starter snippet)
        full_problem = problem_service.get_problem(problem.problem_id)
        if full_problem is None:
            return self._error(
                problem, f"Problem #{problem.problem_id} data not found"
            )

        test_cases = full_problem.test_cases
        if not test_cases:
            return self._skip(problem, "No test cases available for this problem")

        # Need the starter snippet to parse the method name
        code_snippet = full_problem.get_snippet(problem.language)
        if not code_snippet:
            return self._error(
                problem,
                f"No starter snippet for {problem.language.value} in problem data",
            )

        method_name = parse_method_name(code_snippet, problem.language.value)
        if not method_name:
            return self._error(
                problem,
                "Could not parse method name from starter snippet",
            )

        # Generate and run the test harness
        try:
            run_result = self._run_tests(
                repo=repo,
                problem=problem,
                solution_path=file_path,
                method_name=method_name,
                test_cases=test_cases,
                timeout=timeout,
                toolchain=toolchain,
            )
        except OSError as e:
            return self._error(problem, f"Test execution failed: {e}")

        # Persist the resulting status
        self._record_status(repo, problem, run_result)

        self.logger.info(
            f"test_service: #{problem.problem_id} "
            f"status={run_result.status} "
            f"({run_result.passed_count}/{run_result.total_cases})"
        )

        return TestServiceResult(problem=problem, run_result=run_result)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_tests(
        self,
        *,
        repo: Repository,
        problem: RegisteredProblem,
        solution_path: Path,
        method_name: str,
        test_cases: List[TestCase],
        timeout: int,
        toolchain,
    ) -> TestRunResult:
        """
        Generate the test harness, write it to repo.build_dir, run it via
        the toolchain, and parse the results.

        Currently only the Python harness (sentinel-marked JSON output) is
        wired up — other languages will need their own parsing once their
        toolchains land.
        """
        language = problem.language

        solution_code = solution_path.read_text(encoding="utf-8")
        test_input = prepare_test_input(method_name, test_cases, language.value)
        full_code = generate_test_code(
            solution_code,
            language.value,
            test_data=test_input,
        )

        # Write the generated harness to the build dir so it can be inspected
        # after the run (helpful for debugging mismatched outputs).
        build_dir = repo.build_dir / f"{problem.problem_id}_{language.value}"
        build_dir.mkdir(parents=True, exist_ok=True)
        suffix = _harness_filename(language)
        harness_path = build_dir / suffix
        harness_path.write_text(full_code, encoding="utf-8")

        # Execute via the toolchain
        execution = toolchain.execute(harness_path, timeout=timeout)

        # If the run timed out before producing any output, emit per-case
        # timed-out results so the CLI can show which cases didn't finish.
        if execution.timed_out:
            return TestRunResult(
                problem_id=problem.problem_id,
                language=language.value,
                total_cases=len(test_cases),
                passed_count=0,
                failed_count=0,
                error_count=len(test_cases),
                case_results=[
                    TestCaseResult(
                        case_number=i + 1,
                        passed=False,
                        input_str=tc.input,
                        expected=tc.output,
                        actual="",
                        timed_out=True,
                    )
                    for i, tc in enumerate(test_cases)
                ],
                runtime_error=f"Execution timed out after {timeout} seconds",
            )

        # Compile errors (none for Python; populated when Java/C++ land)
        if execution.compile_error:
            return TestRunResult(
                problem_id=problem.problem_id,
                language=language.value,
                total_cases=len(test_cases),
                passed_count=0,
                failed_count=0,
                error_count=len(test_cases),
                compile_error=execution.compile_error,
            )

        # Runtime error before any results were emitted
        if execution.exit_code != 0 and PYTHON_RESULTS_BEGIN not in execution.stdout:
            return TestRunResult(
                problem_id=problem.problem_id,
                language=language.value,
                total_cases=len(test_cases),
                passed_count=0,
                failed_count=0,
                error_count=len(test_cases),
                runtime_error=execution.stderr.strip() or "Unknown runtime error",
            )

        # Happy path: parse the JSON between the sentinel markers
        return _parse_python_output(
            execution.stdout, test_cases, problem.problem_id, language.value
        )

    def _skip(self, problem: RegisteredProblem, reason: str) -> TestServiceResult:
        self.logger.info(
            f"test_service: skipped #{problem.problem_id} — {reason}"
        )
        return TestServiceResult(problem=problem, skipped=True, skip_reason=reason)

    def _error(self, problem: RegisteredProblem, message: str) -> TestServiceResult:
        self.logger.warning(
            f"test_service: failed #{problem.problem_id} — {message}"
        )
        return TestServiceResult(problem=problem, error=message)

    def _record_status(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        run_result: TestRunResult,
    ) -> None:
        with repo.open_db() as db:
            db.update_problem_status(
                problem_db_id=problem.id,
                status=run_result.status,
                output=f"Passed: {run_result.passed_count}/{run_result.total_cases}",
            )


# ----------------------------------------------------------------------------
# Output parsing (Python harness with sentinel markers).
# ----------------------------------------------------------------------------

def _format_path_error(resolved, requested_version: Optional[int]) -> str:
    """Render a SolutionPathResult error, listing available versions if relevant."""
    msg = resolved.error or "Solution path could not be resolved"
    if requested_version is not None and resolved.available_versions:
        avail = ", ".join(f"v{v}" for v in resolved.available_versions)
        msg = f"{msg}. Available: {avail}"
    return msg


def _harness_filename(language: CodeLanguage) -> str:
    """Filename for the generated harness, by language."""
    return {
        CodeLanguage.PYTHON: "test_main.py",
    }.get(language, f"test_main{_extension_for(language)}")


def _extension_for(language: CodeLanguage) -> str:
    """File extension for a language."""
    return language.extension or ".txt"


def _parse_python_output(
    stdout: str,
    test_cases: List[TestCase],
    problem_id: int,
    language: str,
) -> TestRunResult:
    """Parse the sentinel-wrapped JSON results from the Python harness."""
    begin = stdout.find(PYTHON_RESULTS_BEGIN)
    end = stdout.find(PYTHON_RESULTS_END)

    if begin < 0 or end < 0 or end <= begin:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=(
                "No result markers found in harness output. "
                f"Output: {stdout[:200]}"
            ),
        )

    json_str = stdout[begin + len(PYTHON_RESULTS_BEGIN):end].strip()

    try:
        results_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=f"Failed to parse test output: {e}",
        )

    case_results = []
    passed_count = 0
    failed_count = 0
    error_count = 0

    for i, res in enumerate(results_data):
        test_case = test_cases[i] if i < len(test_cases) else None
        case_result = TestCaseResult(
            case_number=res.get('case', i + 1),
            passed=res.get('passed', False),
            input_str=test_case.input if test_case else "",
            expected=res.get('expected', ''),
            actual=res.get('actual', ''),
            error=res.get('error'),
        )
        case_results.append(case_result)

        if res.get('error'):
            error_count += 1
        elif res.get('passed'):
            passed_count += 1
        else:
            failed_count += 1

    return TestRunResult(
        problem_id=problem_id,
        language=language,
        total_cases=len(test_cases),
        passed_count=passed_count,
        failed_count=failed_count,
        error_count=error_count,
        case_results=case_results,
    )
