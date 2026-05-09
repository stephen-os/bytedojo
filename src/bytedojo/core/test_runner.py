"""
Test runner - Execute solutions against test cases using containerized execution.

This module provides a unified interface for running code across multiple languages
using Podman containers. It handles:
- Loading test cases
- Generating test harness code
- Executing via containers
- Parsing and returning structured results
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from bytedojo.core.models import Case, Language
from bytedojo.core.test_fetcher import fetch_test_cases
from bytedojo.core.problem_service import get_problem
from bytedojo.core.container import PodmanManager, PodmanNotFoundError, ContainerError
from bytedojo.core.harness import (
    load_language_config,
    generate_test_code,
    prepare_test_input,
    parse_method_name,
    HarnessError,
)


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


def run_tests(
    solution_path: Path,
    problem_id: int,
    language: str = 'python3',
    timeout: int = 60,
    progress_callback=None
) -> TestRunResult:
    """
    Run test cases against a solution file using containerized execution.

    Args:
        solution_path: Path to the solution file
        problem_id: Problem ID (to fetch test cases)
        language: Programming language
        timeout: Execution timeout in seconds
        progress_callback: Optional callback for progress updates

    Returns:
        TestRunResult with detailed results
    """
    # Fetch test cases
    test_cases = fetch_test_cases(problem_id)

    if not test_cases:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=0,
            passed_count=0,
            failed_count=0,
            error_count=0,
            runtime_error="No test cases found for this problem"
        )

    # Get problem to extract method name
    problem = get_problem(problem_id)
    if not problem:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error="Problem data not found"
        )

    # Get code snippet and extract method name
    lang_enum = Language.from_string(language)
    code_snippet = problem.get_snippet(lang_enum)

    if not code_snippet:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=f"No code snippet for language: {language}"
        )

    # Parse method name
    method_name = parse_method_name(code_snippet, language)
    if not method_name:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error="Could not parse method name from code snippet"
        )

    # Read user's solution code
    try:
        solution_code = solution_path.read_text(encoding='utf-8')
    except Exception as e:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=f"Failed to read solution file: {e}"
        )

    # Prepare test input and generate test code with embedded data
    test_input = prepare_test_input(method_name, test_cases, language)

    try:
        config = load_language_config(language)
        full_code = generate_test_code(solution_code, language, config, test_data=test_input)
    except HarnessError as e:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=str(e)
        )

    # Execute in container
    try:
        manager = PodmanManager()

        if progress_callback:
            progress_callback("Starting container...")

        # Run code (test data is embedded in the code itself)
        result = manager.run_code(
            image=config.image,
            command=config.run_command,
            code=full_code,
            timeout=timeout
        )
    except PodmanNotFoundError as e:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=str(e)
        )
    except ContainerError as e:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=f"Container error: {e}"
        )

    # Handle runtime errors (no output)
    if result.exit_code != 0 and not result.stdout.strip():
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=result.stderr or "Unknown runtime error"
        )

    # Handle timeout
    if result.timed_out:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
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
                    timed_out=True
                )
                for i, tc in enumerate(test_cases)
            ],
            runtime_error=f"Execution timed out after {timeout} seconds"
        )

    # Parse JSON output from harness
    return _parse_harness_output(result.stdout, test_cases, problem_id, language)


def _parse_harness_output(
    stdout: str,
    test_cases: List[Case],
    problem_id: int,
    language: str
) -> TestRunResult:
    """Parse the JSON output from the test harness."""
    try:
        # Find JSON array in output (may have other output before/after)
        stdout = stdout.strip()
        json_start = stdout.find('[')
        json_end = stdout.rfind(']') + 1

        if json_start < 0 or json_end <= json_start:
            return TestRunResult(
                problem_id=problem_id,
                language=language,
                total_cases=len(test_cases),
                passed_count=0,
                failed_count=0,
                error_count=len(test_cases),
                runtime_error=f"No JSON output from harness. Output: {stdout[:200]}"
            )

        json_str = stdout[json_start:json_end]
        results_data = json.loads(json_str)

    except json.JSONDecodeError as e:
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=f"Failed to parse test output: {e}. Output: {stdout[:200]}"
        )

    # Build case results
    case_results = []
    passed_count = 0
    failed_count = 0
    error_count = 0

    for i, res in enumerate(results_data):
        # Get corresponding test case for input_str
        test_case = test_cases[i] if i < len(test_cases) else None

        case_result = TestCaseResult(
            case_number=res.get('case', i + 1),
            passed=res.get('passed', False),
            input_str=test_case.input if test_case else "",
            expected=res.get('expected', ''),
            actual=res.get('actual', ''),
            error=res.get('error')
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
        case_results=case_results
    )
