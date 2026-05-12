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
import subprocess
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
from bytedojo.core.test_codegen import generate_runner_for_source, supports_codegen
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
    total_cases: int                # total in the problem's test suite
    passed_count: int
    failed_count: int
    error_count: int
    skipped_count: int = 0          # cases filtered before running (e.g. int32 overflow)
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

    `version` and `file_path` reflect what was actually tested — useful for
    the CLI/TUI header so it shows the v1 path when `--version 1` was used
    even though the `problem` argument carries the latest path.
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

        # Resolve the solution file (latest, or a specific version).
        # `resolved.version` is the version that will actually be tested —
        # populated whether or not the caller passed --version.
        resolved = resolve_solution_path(repo, problem, version=version)
        if not resolved.found:
            return self._error(
                problem,
                _format_path_error(resolved, version),
                version=resolved.version,
            )
        file_path = resolved.path
        tested_version = resolved.version

        # Carry version/path through to every early-return so the CLI/TUI
        # header can show what was actually tested.
        ctx = {"version": tested_version, "file_path": file_path}

        # Resolve the toolchain
        toolchain = get_toolchain(problem.language)
        if toolchain is None:
            return self._error(
                problem,
                f"{problem.language.value} toolchain is not registered.",
                **ctx,
            )

        # Python uses the runtime harness; Java/C++ use per-problem codegen.
        # Any other language without a registered codegen path errors here.
        if problem.language != CodeLanguage.PYTHON and not supports_codegen(problem.language):
            return self._error(
                problem,
                f"The test harness for {problem.language.value} is not yet "
                f"implemented. `dojo run` works; use Python for `dojo test`.",
                **ctx,
            )

        # Confirm the toolchain is actually present on this machine
        status = toolchain.detect()
        if not status.found:
            lines = [f"{problem.language.value} toolchain not found."]
            if status.missing:
                lines.append(f"  Missing: {', '.join(status.missing)}")
            if status.install_hint:
                lines.append(f"  Install: {status.install_hint}")
            return self._error(problem, "\n".join(lines), **ctx)

        # Load the full Problem (for test cases + starter snippet)
        full_problem = problem_service.get_problem(problem.problem_id)
        if full_problem is None:
            return self._error(
                problem, f"Problem #{problem.problem_id} data not found", **ctx,
            )

        test_cases = full_problem.test_cases
        if not test_cases:
            return self._skip(
                problem, "No test cases available for this problem", **ctx,
            )

        # Need the starter snippet to parse the method name
        code_snippet = full_problem.get_snippet(problem.language)
        if not code_snippet:
            return self._error(
                problem,
                f"No starter snippet for {problem.language.value} in problem data",
                **ctx,
            )

        method_name = parse_method_name(code_snippet, problem.language.value)
        if not method_name:
            return self._error(
                problem,
                "Could not parse method name from starter snippet",
                **ctx,
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
            return self._error(problem, f"Test execution failed: {e}", **ctx)

        # Persist the resulting status (per-version + the legacy summary on
        # `problems.test_status` so grade.py's display stays accurate).
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
        Generate the test runner, run it, and parse the results.

        Python uses the runtime harness (dynamic dispatch via getattr,
        sentinel-marked output). Java/C++ use per-problem codegen — the
        runner is a complete .java/.cpp file with the user's Solution
        embedded and all test cases baked in as literals.
        """
        language = problem.language
        build_dir = repo.build_dir / f"{problem.problem_id}_{language.value}"
        build_dir.mkdir(parents=True, exist_ok=True)

        if language == CodeLanguage.PYTHON:
            return self._run_python_tests(
                problem=problem,
                solution_path=solution_path,
                method_name=method_name,
                test_cases=test_cases,
                timeout=timeout,
                toolchain=toolchain,
                build_dir=build_dir,
            )

        return self._run_codegen_tests(
            problem=problem,
            solution_path=solution_path,
            method_name=method_name,
            test_cases=test_cases,
            timeout=timeout,
            build_dir=build_dir,
        )

    def _run_python_tests(
        self,
        *,
        problem: RegisteredProblem,
        solution_path: Path,
        method_name: str,
        test_cases: List[TestCase],
        timeout: int,
        toolchain,
        build_dir: Path,
    ) -> TestRunResult:
        """The original Python harness path — dynamic dispatch + sentinels."""
        language = problem.language

        solution_code = solution_path.read_text(encoding="utf-8")
        test_input = prepare_test_input(method_name, test_cases, language.value)
        full_code = generate_test_code(
            solution_code,
            language.value,
            test_data=test_input,
        )

        suffix = _harness_filename(language)
        harness_path = build_dir / suffix
        harness_path.write_text(full_code, encoding="utf-8")

        execution = toolchain.execute(
            harness_path, build_dir=build_dir, timeout=timeout,
        )

        if execution.timed_out:
            return _all_timed_out(problem, test_cases, timeout)
        if execution.compile_error:
            return _compile_error_result(problem, test_cases, execution.compile_error)
        if execution.exit_code != 0 and PYTHON_RESULTS_BEGIN not in execution.stdout:
            return _runtime_error_result(problem, test_cases, execution.stderr)

        return _parse_python_output(
            execution.stdout, test_cases, problem.problem_id, language.value
        )

    def _run_codegen_tests(
        self,
        *,
        problem: RegisteredProblem,
        solution_path: Path,
        method_name: str,
        test_cases: List[TestCase],
        timeout: int,
        build_dir: Path,
    ) -> TestRunResult:
        """
        Generate a per-problem test runner that embeds the user's solution,
        compile + run it, parse the JSON output.

        Used for Java + C++ where the language can't dynamically dispatch a
        method by name with arbitrary arg types.
        """
        language = problem.language

        # Load full problem for canonical types + test data.
        full_problem = problem_service.get_problem(problem.problem_id)
        if full_problem is None or full_problem.types is None:
            return _runtime_error_result(
                problem,
                test_cases,
                f"Problem #{problem.problem_id} missing canonical types — "
                f"run scripts/migrate_problem_types.py.",
            )

        # Read the user's actual solution file and generate the runner.
        user_source = solution_path.read_text(encoding="utf-8")
        try:
            runner_source = generate_runner_for_source(
                full_problem, language, method_name, user_source,
            )
        except Exception as e:  # CodegenError, parsing failures, etc.
            return _runtime_error_result(problem, test_cases, f"Codegen failed: {e}")

        if runner_source is None:
            return _runtime_error_result(
                problem, test_cases,
                f"No codegen registered for {language.value}",
            )

        # Write the runner alongside the user's solution under .dojo/build/.
        runner_path = build_dir / _runner_filename(language)
        runner_path.write_text(runner_source, encoding="utf-8")

        # Compile + run. Custom per-language because the existing
        # Toolchain.execute() is set up for "run the file as the user's code,"
        # not "compile a separately-named test runner and invoke its entry."
        try:
            stdout = self._compile_and_run_runner(
                language=language,
                runner_path=runner_path,
                build_dir=build_dir,
                timeout=timeout,
            )
        except _CompileError as e:
            return _compile_error_result(problem, test_cases, str(e))
        except _RunError as e:
            return _runtime_error_result(problem, test_cases, str(e))
        except subprocess.TimeoutExpired:
            return _all_timed_out(problem, test_cases, timeout)

        return _parse_codegen_output(
            stdout, test_cases, problem.problem_id, language.value
        )

    def _compile_and_run_runner(
        self,
        *,
        language: CodeLanguage,
        runner_path: Path,
        build_dir: Path,
        timeout: int,
    ) -> str:
        """Compile the generated runner and return its stdout."""
        if language == CodeLanguage.JAVA:
            compile_proc = subprocess.run(
                ["javac", "-d", str(build_dir), str(runner_path)],
                capture_output=True, text=True,
            )
            if compile_proc.returncode != 0:
                raise _CompileError(compile_proc.stderr.strip())
            run_proc = subprocess.run(
                ["java", "-cp", str(build_dir), "BytedojoTestRunner"],
                capture_output=True, text=True, timeout=timeout,
            )
            if run_proc.returncode != 0 and not run_proc.stdout.strip():
                raise _RunError(run_proc.stderr.strip() or "non-zero exit")
            return run_proc.stdout

        if language == CodeLanguage.CPP:
            import os
            from bytedojo.core.toolchains.cpp import compile_cpp_source

            output_name = "test_runner.exe" if os.name == "nt" else "test_runner"
            output_path = build_dir / output_name
            try:
                compile_proc = compile_cpp_source(
                    runner_path, output_path, build_dir=build_dir,
                )
            except FileNotFoundError as e:
                raise _CompileError(str(e))
            if compile_proc.returncode != 0:
                # Both stderr and stdout can carry diagnostics depending on
                # the compiler (cl writes errors to stdout by default).
                msg = (compile_proc.stderr or compile_proc.stdout or "").strip()
                raise _CompileError(msg or f"compiler exited with code {compile_proc.returncode}")
            run_proc = subprocess.run(
                [str(output_path)],
                cwd=build_dir,
                capture_output=True, text=True, timeout=timeout,
            )
            if run_proc.returncode != 0 and not run_proc.stdout.strip():
                raise _RunError(run_proc.stderr.strip() or "non-zero exit")
            return run_proc.stdout

        raise _RunError(f"Unsupported codegen language: {language.value}")

    def _skip(
        self,
        problem: RegisteredProblem,
        reason: str,
        *,
        version: Optional[int] = None,
        file_path: Optional[Path] = None,
    ) -> TestServiceResult:
        self.logger.info(
            f"test_service: skipped #{problem.problem_id} — {reason}"
        )
        return TestServiceResult(
            problem=problem,
            version=version,
            file_path=file_path,
            skipped=True,
            skip_reason=reason,
        )

    def _error(
        self,
        problem: RegisteredProblem,
        message: str,
        *,
        version: Optional[int] = None,
        file_path: Optional[Path] = None,
    ) -> TestServiceResult:
        self.logger.warning(
            f"test_service: failed #{problem.problem_id} — {message}"
        )
        return TestServiceResult(
            problem=problem,
            version=version,
            file_path=file_path,
            error=message,
        )

    def _record_status(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        run_result: TestRunResult,
        *,
        version: Optional[int] = None,
    ) -> None:
        """
        Persist test results both:
          - on `versioned_attempts` for the specific version that ran (so
            v1 / v2 keep their distinct outcomes), and
          - on `problems.test_status` for the latest-summary display that
            grade.py and friends still read.
        """
        output = f"Passed: {run_result.passed_count}/{run_result.total_cases}"
        with repo.open_db() as db:
            db.update_problem_status(
                problem_db_id=problem.id,
                status=run_result.status,
                output=output,
            )
            if version is not None:
                db.update_attempt_test_status(
                    source=problem.source,
                    problem_id=problem.problem_id,
                    language=problem.language.value,
                    version=version,
                    status=run_result.status,
                    output=output,
                )


# ----------------------------------------------------------------------------
# Output parsing (Python harness with sentinel markers).
# ----------------------------------------------------------------------------

class _CompileError(Exception):
    """Raised internally when a generated runner fails to compile."""


class _RunError(Exception):
    """Raised internally when a generated runner exits with no output."""


def _runner_filename(language: CodeLanguage) -> str:
    """Filename for the generated test runner, by language."""
    return {
        CodeLanguage.JAVA: "BytedojoTestRunner.java",
        CodeLanguage.CPP:  "bytedojo_test_runner.cpp",
    }.get(language, f"test_runner{language.extension}")


def _all_timed_out(
    problem: RegisteredProblem,
    test_cases: List[TestCase],
    timeout: int,
) -> TestRunResult:
    """Build a TestRunResult for "execution timed out before any cases finished"."""
    return TestRunResult(
        problem_id=problem.problem_id,
        language=problem.language.value,
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


def _compile_error_result(
    problem: RegisteredProblem,
    test_cases: List[TestCase],
    message: str,
) -> TestRunResult:
    return TestRunResult(
        problem_id=problem.problem_id,
        language=problem.language.value,
        total_cases=len(test_cases),
        passed_count=0,
        failed_count=0,
        error_count=len(test_cases),
        compile_error=message,
    )


def _runtime_error_result(
    problem: RegisteredProblem,
    test_cases: List[TestCase],
    message: str,
) -> TestRunResult:
    return TestRunResult(
        problem_id=problem.problem_id,
        language=problem.language.value,
        total_cases=len(test_cases),
        passed_count=0,
        failed_count=0,
        error_count=len(test_cases),
        runtime_error=(message or "Unknown runtime error").strip(),
    )


def _parse_codegen_output(
    stdout: str,
    test_cases: List[TestCase],
    problem_id: int,
    language: str,
) -> TestRunResult:
    """
    Parse a generated runner's stdout — expected to be a JSON array of
    case-result objects {case, passed, expected, actual, error}.
    """
    s = stdout.strip()
    # The runner may print other things first (debug prints from user code).
    # Find the last JSON array in the output.
    begin = s.find("[")
    end = s.rfind("]") + 1
    if begin < 0 or end <= begin:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=(
                f"No JSON results in runner output. First 200 chars: {s[:200]}"
            ),
        )

    try:
        results_data = json.loads(s[begin:end])
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
            case_number=res.get("case", i + 1),
            passed=res.get("passed", False),
            input_str=test_case.input if test_case else "",
            expected=res.get("expected", ""),
            actual=res.get("actual", ""),
            error=res.get("error"),
        )
        case_results.append(case_result)
        if res.get("error"):
            error_count += 1
        elif res.get("passed"):
            passed_count += 1
        else:
            failed_count += 1

    skipped_count = max(0, len(test_cases) - len(results_data))

    return TestRunResult(
        problem_id=problem_id,
        language=language,
        total_cases=len(test_cases),
        passed_count=passed_count,
        failed_count=failed_count,
        error_count=error_count,
        skipped_count=skipped_count,
        case_results=case_results,
    )


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
