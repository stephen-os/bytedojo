"""
Test runner - Execute solutions against test cases and compare results.

This module handles:
- Parsing test case inputs/outputs
- Generating test harness code
- Running solutions against test cases
- Comparing actual vs expected results
"""

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Any

from bytedojo.core.models import Case
from bytedojo.core.test_fetcher import fetch_test_cases
from bytedojo.core.problem_service import get_problem


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


def _parse_method_name(code_snippet: str) -> Optional[str]:
    """
    Parse the method name from a code snippet.

    For Python: looks for 'def methodName(self, ...'
    """
    # Python: def methodName(self, ...
    match = re.search(r'def\s+(\w+)\s*\(\s*self', code_snippet)
    if match:
        return match.group(1)
    return None


def _parse_test_input(input_str: str) -> dict:
    """
    Parse test input string into a dictionary of variable assignments.

    Example: "nums = [3,3], target = 6" -> {"nums": [3, 3], "target": 6}
    """
    result = {}

    # Split by comma, but handle nested structures
    # We need to be careful about commas inside lists/strings
    parts = []
    current = ""
    depth = 0
    in_string = False
    string_char = None

    for char in input_str:
        if char in '"\'':
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
        elif char in '[{(':
            if not in_string:
                depth += 1
        elif char in ']})':
            if not in_string:
                depth -= 1
        elif char == ',' and depth == 0 and not in_string:
            parts.append(current.strip())
            current = ""
            continue
        current += char

    if current.strip():
        parts.append(current.strip())

    # Parse each part as var = value
    for part in parts:
        if '=' in part:
            var_name, value_str = part.split('=', 1)
            var_name = var_name.strip()
            value_str = value_str.strip()

            # Try to evaluate the value
            try:
                # Handle special Python values
                value_str = value_str.replace('null', 'None')
                value_str = value_str.replace('true', 'True')
                value_str = value_str.replace('false', 'False')
                value = eval(value_str)
                result[var_name] = value
            except Exception:
                result[var_name] = value_str

    return result


def _normalize_output(output: Any) -> str:
    """Normalize output for comparison."""
    if output is None:
        return "None"
    return repr(output)


def _generate_python_harness(
    solution_path: Path,
    method_name: str,
    test_cases: List[Case],
    problem_id: int
) -> str:
    """
    Generate Python test harness code.

    The harness:
    1. Imports the solution
    2. Runs each test case
    3. Outputs JSON results
    """
    test_inputs = []
    expected_outputs = []

    for case in test_cases:
        parsed_input = _parse_test_input(case.input)
        test_inputs.append(parsed_input)
        expected_outputs.append(case.output)

    harness = f'''
import sys
import json
from typing import List, Optional

# Add solution directory to path
sys.path.insert(0, r"{solution_path.parent}")

# Import the solution
from solution import Solution

def normalize_for_display(val):
    """Normalize output for display."""
    if val is None:
        return "None"
    return repr(val)

def normalize_for_comparison(val):
    """Normalize output for comparison - convert to canonical form."""
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, (list, tuple)):
        return [normalize_for_comparison(v) for v in val]
    if isinstance(val, dict):
        return {{k: normalize_for_comparison(v) for k, v in val.items()}}
    return val

def parse_expected(expected_str, actual_type=None):
    """Parse expected output string to a Python value."""
    try:
        # Try to evaluate as Python literal
        normalized = expected_str.replace('null', 'None').replace('true', 'True').replace('false', 'False')
        result = eval(normalized)
        # If actual is a string and result is a number, the expected was likely a string too
        if actual_type == str and isinstance(result, (int, float)):
            return expected_str
        return result
    except:
        # If it fails, treat as a raw string value
        return expected_str

def main():
    solution = Solution()
    results = []

    test_inputs = {json.dumps(test_inputs)}
    expected_outputs = {json.dumps(expected_outputs)}

    for i, (inputs, expected_str) in enumerate(zip(test_inputs, expected_outputs)):
        try:
            actual = solution.{method_name}(**inputs)
            actual_normalized = normalize_for_comparison(actual)

            # Parse expected value, considering the actual result type
            expected_val = parse_expected(expected_str, type(actual))
            expected_normalized = normalize_for_comparison(expected_val)

            # Compare normalized values
            passed = actual_normalized == expected_normalized

            results.append({{
                "case": i + 1,
                "passed": passed,
                "expected": expected_str,
                "actual": normalize_for_display(actual),
                "error": None
            }})
        except Exception as e:
            results.append({{
                "case": i + 1,
                "passed": False,
                "expected": expected_str,
                "actual": "",
                "error": str(e)
            }})

    print(json.dumps(results))

if __name__ == "__main__":
    main()
'''
    return harness


def run_tests(
    solution_path: Path,
    problem_id: int,
    language: str = 'python3',
    timeout: int = 60
) -> TestRunResult:
    """
    Run test cases against a solution file.

    Args:
        solution_path: Path to the solution file
        problem_id: Problem ID (to fetch test cases)
        language: Programming language
        timeout: Execution timeout in seconds

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
    from bytedojo.core.models import Language
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

    method_name = _parse_method_name(code_snippet)
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

    # Currently only support Python
    if language not in ('python', 'python3'):
        return TestRunResult(
            problem_id=problem_id,
            language=language,
            total_cases=len(test_cases),
            passed_count=0,
            failed_count=0,
            error_count=len(test_cases),
            runtime_error=f"Test runner not yet implemented for: {language}"
        )

    # Generate and run test harness
    harness_code = _generate_python_harness(solution_path, method_name, test_cases, problem_id)

    # Write harness to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(harness_code)
        harness_path = Path(f.name)

    try:
        # Run the harness
        result = subprocess.run(
            ['python', str(harness_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=solution_path.parent
        )

        if result.returncode != 0:
            # Check if it's a compile error vs runtime error
            error_output = result.stderr.strip()
            if 'SyntaxError' in error_output or 'IndentationError' in error_output:
                return TestRunResult(
                    problem_id=problem_id,
                    language=language,
                    total_cases=len(test_cases),
                    passed_count=0,
                    failed_count=0,
                    error_count=len(test_cases),
                    compile_error=error_output
                )
            return TestRunResult(
                problem_id=problem_id,
                language=language,
                total_cases=len(test_cases),
                passed_count=0,
                failed_count=0,
                error_count=len(test_cases),
                runtime_error=error_output
            )

        # Parse results
        try:
            results_data = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return TestRunResult(
                problem_id=problem_id,
                language=language,
                total_cases=len(test_cases),
                passed_count=0,
                failed_count=0,
                error_count=len(test_cases),
                runtime_error=f"Failed to parse test output: {result.stdout[:200]}"
            )

        # Build case results
        case_results = []
        passed_count = 0
        failed_count = 0
        error_count = 0

        for i, (res, test_case) in enumerate(zip(results_data, test_cases)):
            case_result = TestCaseResult(
                case_number=res['case'],
                passed=res['passed'],
                input_str=test_case.input,
                expected=res['expected'],
                actual=res['actual'],
                error=res.get('error')
            )
            case_results.append(case_result)

            if res.get('error'):
                error_count += 1
            elif res['passed']:
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

    except subprocess.TimeoutExpired:
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
    finally:
        # Clean up temp file
        try:
            harness_path.unlink()
        except Exception:
            pass
