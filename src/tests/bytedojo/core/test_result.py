"""
Tests for Result dataclass.
"""

import pytest
from bytedojo.core.result import Result


class TestResultInit:
    """Test Result dataclass initialization."""

    def test_create_success_result(self):
        """Test creating a successful Result."""
        result = Result(success=True, message="Operation completed successfully")

        assert result.success is True
        assert result.message == "Operation completed successfully"

    def test_create_failure_result(self):
        """Test creating a failed Result."""
        result = Result(success=False, message="Operation failed")

        assert result.success is False
        assert result.message == "Operation failed"

    def test_create_result_with_empty_message(self):
        """Test creating a Result with an empty message."""
        result = Result(success=True, message="")

        assert result.success is True
        assert result.message == ""

    def test_create_result_with_multiline_message(self):
        """Test creating a Result with a multiline message."""
        message = "Error occurred:\n  - First issue\n  - Second issue"
        result = Result(success=False, message=message)

        assert result.success is False
        assert result.message == message
        assert "\n" in result.message


class TestResultSuccessCases:
    """Test Result success scenarios."""

    def test_success_with_descriptive_message(self):
        """Test successful result with descriptive message."""
        result = Result(success=True, message="File saved to disk")

        assert result.success is True
        assert "saved" in result.message

    def test_success_with_detailed_info(self):
        """Test successful result with detailed information."""
        result = Result(
            success=True,
            message="Created 5 files in directory /path/to/output"
        )

        assert result.success is True
        assert "5 files" in result.message


class TestResultErrorCases:
    """Test Result error scenarios."""

    def test_error_with_error_message(self):
        """Test failed result with error message."""
        result = Result(success=False, message="File not found: config.json")

        assert result.success is False
        assert "not found" in result.message

    def test_error_with_exception_info(self):
        """Test failed result containing exception information."""
        result = Result(
            success=False,
            message="ValueError: Invalid input parameter"
        )

        assert result.success is False
        assert "ValueError" in result.message

    def test_error_with_stack_trace_info(self):
        """Test failed result with stack trace information."""
        message = "Error at line 42: IndexError - list index out of range"
        result = Result(success=False, message=message)

        assert result.success is False
        assert "IndexError" in result.message


class TestResultEquality:
    """Test Result equality comparisons."""

    def test_identical_results_are_equal(self):
        """Test that identical Results are equal."""
        result1 = Result(success=True, message="Test message")
        result2 = Result(success=True, message="Test message")

        assert result1 == result2

    def test_different_success_values_are_not_equal(self):
        """Test that Results with different success values are not equal."""
        result1 = Result(success=True, message="Same message")
        result2 = Result(success=False, message="Same message")

        assert result1 != result2

    def test_different_messages_are_not_equal(self):
        """Test that Results with different messages are not equal."""
        result1 = Result(success=True, message="Message 1")
        result2 = Result(success=True, message="Message 2")

        assert result1 != result2

    def test_both_fields_different_are_not_equal(self):
        """Test that Results with both fields different are not equal."""
        result1 = Result(success=True, message="Success")
        result2 = Result(success=False, message="Failure")

        assert result1 != result2


class TestResultAttributes:
    """Test Result attribute access."""

    def test_success_attribute_type(self):
        """Test that success attribute is boolean."""
        result = Result(success=True, message="test")

        assert isinstance(result.success, bool)

    def test_message_attribute_type(self):
        """Test that message attribute is string."""
        result = Result(success=True, message="test")

        assert isinstance(result.message, str)

    def test_result_is_dataclass(self):
        """Test that Result behaves as a dataclass."""
        result = Result(success=True, message="test")

        # Dataclasses have __dataclass_fields__
        assert hasattr(result, '__dataclass_fields__')
        assert 'success' in result.__dataclass_fields__
        assert 'message' in result.__dataclass_fields__


class TestResultRepr:
    """Test Result string representation."""

    def test_repr_contains_class_name(self):
        """Test that repr contains the class name."""
        result = Result(success=True, message="test")

        repr_str = repr(result)
        assert "Result" in repr_str

    def test_repr_contains_success_value(self):
        """Test that repr contains the success value."""
        result = Result(success=True, message="test")

        repr_str = repr(result)
        assert "success=True" in repr_str

    def test_repr_contains_message_value(self):
        """Test that repr contains the message value."""
        result = Result(success=False, message="error message")

        repr_str = repr(result)
        assert "message=" in repr_str
        assert "error message" in repr_str


class TestResultUsagePatterns:
    """Test common Result usage patterns."""

    def test_result_in_conditional(self):
        """Test using Result.success in conditional statements."""
        result = Result(success=True, message="OK")

        if result.success:
            status = "passed"
        else:
            status = "failed"

        assert status == "passed"

    def test_result_failure_in_conditional(self):
        """Test using failed Result in conditional statements."""
        result = Result(success=False, message="Error")

        if not result.success:
            status = "failed"
        else:
            status = "passed"

        assert status == "failed"

    def test_result_message_formatting(self):
        """Test formatting Result message in output."""
        result = Result(success=False, message="Connection timeout")

        formatted = f"Status: {'OK' if result.success else 'ERROR'} - {result.message}"

        assert formatted == "Status: ERROR - Connection timeout"
