"""
Tests for the test_runner module.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bytedojo.core.test_runner import (
    TestCaseResult,
    TestRunResult,
    _parse_method_name,
    _parse_test_input,
    _normalize_output,
)


class TestParseMethodName:
    """Test the _parse_method_name function."""

    def test_parse_python_method_basic(self):
        """Test parsing a basic Python method."""
        code = """
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        pass
"""
        assert _parse_method_name(code) == "twoSum"

    def test_parse_python_method_no_type_hints(self):
        """Test parsing Python method without type hints."""
        code = """
class Solution:
    def reverse(self, x):
        pass
"""
        assert _parse_method_name(code) == "reverse"

    def test_parse_python_method_complex(self):
        """Test parsing Python method with complex signature."""
        code = """
class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        pass
"""
        assert _parse_method_name(code) == "maxProfit"

    def test_parse_no_method_found(self):
        """Test when no method is found."""
        code = "# No method here"
        assert _parse_method_name(code) is None


class TestParseTestInput:
    """Test the _parse_test_input function."""

    def test_parse_single_int(self):
        """Test parsing a single integer."""
        result = _parse_test_input("x = 123")
        assert result == {"x": 123}

    def test_parse_negative_int(self):
        """Test parsing a negative integer."""
        result = _parse_test_input("x = -123")
        assert result == {"x": -123}

    def test_parse_list(self):
        """Test parsing a list."""
        result = _parse_test_input("nums = [1, 2, 3]")
        assert result == {"nums": [1, 2, 3]}

    def test_parse_multiple_vars(self):
        """Test parsing multiple variables."""
        result = _parse_test_input("nums = [2, 7, 11, 15], target = 9")
        assert result == {"nums": [2, 7, 11, 15], "target": 9}

    def test_parse_string(self):
        """Test parsing a string."""
        result = _parse_test_input('s = "hello"')
        assert result == {"s": "hello"}

    def test_parse_nested_list(self):
        """Test parsing a nested list."""
        result = _parse_test_input("matrix = [[1, 2], [3, 4]]")
        assert result == {"matrix": [[1, 2], [3, 4]]}

    def test_parse_boolean(self):
        """Test parsing boolean values."""
        result = _parse_test_input("x = true, y = false")
        assert result == {"x": True, "y": False}

    def test_parse_null(self):
        """Test parsing null values."""
        result = _parse_test_input("root = null")
        assert result == {"root": None}

    def test_parse_list_with_nested_commas(self):
        """Test parsing list with commas inside."""
        result = _parse_test_input("nums = [1, 2, 3], k = 2")
        assert result == {"nums": [1, 2, 3], "k": 2}


class TestNormalizeOutput:
    """Test the _normalize_output function."""

    def test_normalize_int(self):
        """Test normalizing an integer."""
        assert _normalize_output(42) == "42"

    def test_normalize_list(self):
        """Test normalizing a list."""
        assert _normalize_output([1, 2, 3]) == "[1, 2, 3]"

    def test_normalize_string(self):
        """Test normalizing a string."""
        assert _normalize_output("hello") == "'hello'"

    def test_normalize_none(self):
        """Test normalizing None."""
        assert _normalize_output(None) == "None"

    def test_normalize_bool(self):
        """Test normalizing boolean."""
        assert _normalize_output(True) == "True"
        assert _normalize_output(False) == "False"


class TestTestCaseResult:
    """Test the TestCaseResult dataclass."""

    def test_passed_case(self):
        """Test a passed test case."""
        result = TestCaseResult(
            case_number=1,
            passed=True,
            input_str="nums = [1, 2]",
            expected="[0, 1]",
            actual="[0, 1]"
        )
        assert result.passed is True
        assert result.error is None
        assert result.timed_out is False

    def test_failed_case(self):
        """Test a failed test case."""
        result = TestCaseResult(
            case_number=2,
            passed=False,
            input_str="nums = [3, 3]",
            expected="[0, 1]",
            actual="[1, 0]"
        )
        assert result.passed is False
        assert result.expected == "[0, 1]"
        assert result.actual == "[1, 0]"

    def test_error_case(self):
        """Test a test case with error."""
        result = TestCaseResult(
            case_number=3,
            passed=False,
            input_str="nums = []",
            expected="None",
            actual="",
            error="IndexError: list index out of range"
        )
        assert result.passed is False
        assert result.error is not None

    def test_timeout_case(self):
        """Test a timed out test case."""
        result = TestCaseResult(
            case_number=4,
            passed=False,
            input_str="nums = [1] * 10000",
            expected="0",
            actual="",
            timed_out=True
        )
        assert result.timed_out is True


class TestTestRunResult:
    """Test the TestRunResult dataclass."""

    def test_all_passed(self):
        """Test when all tests pass."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=5,
            passed_count=5,
            failed_count=0,
            error_count=0
        )
        assert result.all_passed is True
        assert result.status == 'passed'

    def test_some_failed(self):
        """Test when some tests fail."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=5,
            passed_count=3,
            failed_count=2,
            error_count=0
        )
        assert result.all_passed is False
        assert result.status == 'failed'

    def test_compile_error(self):
        """Test with compile error."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=5,
            passed_count=0,
            failed_count=0,
            error_count=5,
            compile_error="SyntaxError: invalid syntax"
        )
        assert result.status == 'error'

    def test_runtime_error(self):
        """Test with runtime error."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=5,
            passed_count=0,
            failed_count=0,
            error_count=5,
            runtime_error="Module not found"
        )
        assert result.status == 'failed'

    def test_no_test_cases(self):
        """Test with no test cases."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=0,
            passed_count=0,
            failed_count=0,
            error_count=0
        )
        assert result.all_passed is False
        assert result.status == 'untested'

    def test_with_case_results(self):
        """Test with case results list."""
        cases = [
            TestCaseResult(1, True, "a", "b", "b"),
            TestCaseResult(2, False, "c", "d", "e"),
        ]
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=2,
            passed_count=1,
            failed_count=1,
            error_count=0,
            case_results=cases
        )
        assert len(result.case_results) == 2
        assert result.case_results[0].passed is True
        assert result.case_results[1].passed is False
