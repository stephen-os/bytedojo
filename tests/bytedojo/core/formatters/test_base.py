"""
Comprehensive test suite for BaseFormatter abstract base class.
Tests cover abstract class behavior, inheritance requirements, and interface compliance.
"""

import pytest
from abc import ABC
from unittest.mock import Mock, MagicMock, patch
from bytedojo.core.models import Problem, Case, CodeSnippet, Language, Difficulty
from bytedojo.core.formatters.base import BaseFormatter


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_problem():
    """Create a mock problem for testing."""
    problem = Mock(spec=Problem)
    problem.id = 1
    problem.title = "Two Sum"
    problem.title_slug = "two-sum"
    problem.difficulty = Difficulty.EASY
    problem.description = "<p>Given an array of integers.</p>"
    problem.test_cases = [
        Case(input="nums = [2,7,11,15], target = 9", output="[0,1]")
    ]
    problem.code_snippets = [
        CodeSnippet(lang=Language.PYTHON3, code="class Solution:\n    pass")
    ]
    problem.get_snippet.return_value = "class Solution:\n    pass"
    return problem


@pytest.fixture
def real_problem():
    """Create a real Problem instance for testing."""
    return Problem(
        id=1,
        title="Two Sum",
        title_slug="two-sum",
        difficulty=Difficulty.EASY,
        description="<p>Given an array of integers.</p>",
        code_snippets=[
            CodeSnippet(lang=Language.PYTHON3, code="class Solution:\n    pass")
        ],
        test_cases=[
            Case(input="nums = [2,7,11,15], target = 9", output="[0,1]")
        ]
    )


# ============================================================================
# ABSTRACT CLASS TESTS
# ============================================================================

class TestBaseFormatterAbstractClass:
    """Test that BaseFormatter is properly defined as an abstract base class."""

    def test_is_abstract_class(self):
        """Verify BaseFormatter is an ABC."""
        assert issubclass(BaseFormatter, ABC)

    def test_cannot_instantiate_directly(self):
        """Ensure BaseFormatter cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseFormatter()

        # The error message should indicate abstract methods
        assert "abstract" in str(exc_info.value).lower() or "instantiate" in str(exc_info.value).lower()

    def test_has_format_abstract_method(self):
        """Verify format method is defined as abstract."""
        assert hasattr(BaseFormatter, 'format')
        assert 'format' in BaseFormatter.__abstractmethods__

    def test_format_method_signature(self):
        """Verify format method has correct signature."""
        import inspect
        sig = inspect.signature(BaseFormatter.format)
        params = list(sig.parameters.keys())

        # Should have self and problem parameters
        assert 'self' in params
        assert 'problem' in params
        assert len(params) == 2


# ============================================================================
# INHERITANCE TESTS
# ============================================================================

class TestBaseFormatterInheritance:
    """Test inheritance behavior and requirements."""

    def test_subclass_without_format_raises(self):
        """Subclass without format implementation cannot be instantiated."""
        class IncompleteFormatter(BaseFormatter):
            pass

        with pytest.raises(TypeError) as exc_info:
            IncompleteFormatter()

        assert "abstract" in str(exc_info.value).lower()

    def test_subclass_with_format_can_instantiate(self):
        """Subclass with format implementation can be instantiated."""
        class ConcreteFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return "formatted"

        formatter = ConcreteFormatter()
        assert formatter is not None
        assert isinstance(formatter, BaseFormatter)

    def test_subclass_format_is_called(self, mock_problem):
        """Verify subclass format method is actually called."""
        class TestFormatter(BaseFormatter):
            def __init__(self):
                self.format_called = False

            def format(self, problem: Problem) -> str:
                self.format_called = True
                return f"Problem: {problem.title}"

        formatter = TestFormatter()
        result = formatter.format(mock_problem)

        assert formatter.format_called
        assert result == "Problem: Two Sum"

    def test_multiple_inheritance_levels(self):
        """Test that inheritance works through multiple levels."""
        class IntermediateFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return "intermediate"

        class FinalFormatter(IntermediateFormatter):
            def format(self, problem: Problem) -> str:
                return "final"

        formatter = FinalFormatter()
        assert isinstance(formatter, BaseFormatter)
        assert isinstance(formatter, IntermediateFormatter)

    def test_intermediate_abstract_subclass(self):
        """Test intermediate abstract subclass can add more abstract methods."""
        class ExtendedFormatter(BaseFormatter):
            pass  # Still abstract - doesn't implement format

        with pytest.raises(TypeError):
            ExtendedFormatter()


# ============================================================================
# CONCRETE IMPLEMENTATION TESTS
# ============================================================================

class TestConcreteFormatterBehavior:
    """Test concrete formatter implementations through a test subclass."""

    @pytest.fixture
    def simple_formatter(self):
        """Create a simple concrete formatter for testing."""
        class SimpleFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"# {problem.title}\n{problem.description}"

        return SimpleFormatter()

    def test_format_returns_string(self, simple_formatter, mock_problem):
        """Ensure format returns a string."""
        result = simple_formatter.format(mock_problem)
        assert isinstance(result, str)

    def test_format_with_real_problem(self, simple_formatter, real_problem):
        """Test format with a real Problem object."""
        result = simple_formatter.format(real_problem)
        assert isinstance(result, str)
        assert "Two Sum" in result

    def test_format_uses_problem_data(self, simple_formatter, mock_problem):
        """Verify format uses problem data correctly."""
        result = simple_formatter.format(mock_problem)
        assert mock_problem.title in result
        assert mock_problem.description in result

    def test_format_can_return_empty_string(self, mock_problem):
        """Test that format can return empty string."""
        class EmptyFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return ""

        formatter = EmptyFormatter()
        result = formatter.format(mock_problem)
        assert result == ""

    def test_format_can_return_multiline(self, mock_problem):
        """Test that format can return multiline strings."""
        class MultilineFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"Line 1: {problem.title}\nLine 2: {problem.difficulty}\nLine 3: Done"

        formatter = MultilineFormatter()
        result = formatter.format(mock_problem)
        assert result.count('\n') == 2


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling scenarios."""

    def test_format_with_none_problem(self):
        """Test behavior when problem is None."""
        class SafeFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                if problem is None:
                    raise ValueError("Problem cannot be None")
                return str(problem.id)

        formatter = SafeFormatter()
        with pytest.raises(ValueError) as exc_info:
            formatter.format(None)

        assert "None" in str(exc_info.value)

    def test_format_exception_propagates(self, mock_problem):
        """Test that exceptions in format propagate correctly."""
        class FailingFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                raise RuntimeError("Format failed")

        formatter = FailingFormatter()
        with pytest.raises(RuntimeError) as exc_info:
            formatter.format(mock_problem)

        assert "Format failed" in str(exc_info.value)

    def test_format_with_incomplete_problem(self):
        """Test format with problem missing some attributes."""
        class RobustFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                title = getattr(problem, 'title', 'Unknown')
                return f"Problem: {title}"

        incomplete_problem = Mock()
        incomplete_problem.title = "Test"
        # Missing other attributes

        formatter = RobustFormatter()
        result = formatter.format(incomplete_problem)
        assert "Test" in result

    def test_format_attribute_error(self):
        """Test behavior when accessing missing attribute."""
        class StrictFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return problem.nonexistent_attr

        formatter = StrictFormatter()
        mock = Mock(spec=Problem)

        with pytest.raises(AttributeError):
            formatter.format(mock)


# ============================================================================
# TYPE HINT AND INTERFACE TESTS
# ============================================================================

class TestTypeHintsAndInterface:
    """Test type hints and interface compliance."""

    def test_format_return_type_annotation(self):
        """Verify format has correct return type annotation."""
        import typing
        hints = typing.get_type_hints(BaseFormatter.format)
        assert hints.get('return') == str

    def test_format_parameter_type_annotation(self):
        """Verify format has correct parameter type annotation."""
        import typing
        hints = typing.get_type_hints(BaseFormatter.format)
        assert hints.get('problem') == Problem

    def test_subclass_can_override_types(self):
        """Test that subclass can work with type hints."""
        class TypedFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                # Type checker should accept this
                problem_id: int = problem.id
                return str(problem_id)

        formatter = TypedFormatter()
        mock = Mock(spec=Problem)
        mock.id = 42

        result = formatter.format(mock)
        assert result == "42"


# ============================================================================
# DOCSTRING AND DOCUMENTATION TESTS
# ============================================================================

class TestDocumentation:
    """Test that BaseFormatter has proper documentation."""

    def test_class_has_docstring(self):
        """Verify BaseFormatter has a docstring."""
        assert BaseFormatter.__doc__ is not None
        assert len(BaseFormatter.__doc__) > 0

    def test_format_method_has_docstring(self):
        """Verify format method has a docstring."""
        assert BaseFormatter.format.__doc__ is not None
        assert len(BaseFormatter.format.__doc__) > 0

    def test_docstring_describes_purpose(self):
        """Verify docstrings describe purpose."""
        assert "formatter" in BaseFormatter.__doc__.lower() or "format" in BaseFormatter.__doc__.lower()
        assert "problem" in BaseFormatter.format.__doc__.lower()

    def test_docstring_mentions_return(self):
        """Verify format docstring mentions return value."""
        doc = BaseFormatter.format.__doc__.lower()
        assert "return" in doc
        assert "string" in doc or "str" in doc


# ============================================================================
# POLYMORPHISM TESTS
# ============================================================================

class TestPolymorphism:
    """Test polymorphic behavior with different formatter implementations."""

    @pytest.fixture
    def formatters(self):
        """Create multiple formatter implementations."""
        class MarkdownFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"# {problem.title}\n\n{problem.description}"

        class HTMLFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"<h1>{problem.title}</h1><p>{problem.description}</p>"

        class PlainTextFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"{problem.title}\n{'-' * len(problem.title)}\n{problem.description}"

        return [MarkdownFormatter(), HTMLFormatter(), PlainTextFormatter()]

    def test_all_formatters_are_base_instances(self, formatters):
        """All formatters should be instances of BaseFormatter."""
        for formatter in formatters:
            assert isinstance(formatter, BaseFormatter)

    def test_polymorphic_format_calls(self, formatters, mock_problem):
        """Different formatters produce different outputs."""
        results = [f.format(mock_problem) for f in formatters]

        # All should return strings
        assert all(isinstance(r, str) for r in results)

        # All should contain the title
        assert all(mock_problem.title in r for r in results)

        # But they should be different formats
        assert len(set(results)) == len(results)  # All unique

    def test_can_iterate_over_formatters(self, formatters, mock_problem):
        """Test iterating over formatters."""
        outputs = []
        for formatter in formatters:
            outputs.append(formatter.format(mock_problem))

        assert len(outputs) == 3

    def test_formatter_list_type_checking(self, formatters):
        """Test that a list of formatters maintains type."""
        from typing import List
        formatter_list: List[BaseFormatter] = formatters

        assert all(isinstance(f, BaseFormatter) for f in formatter_list)


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_format_with_unicode_content(self, mock_problem):
        """Test formatting with unicode content."""
        mock_problem.title = "Two Sum"
        mock_problem.description = "Given an array of integers."

        class UnicodeFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"{problem.title}: {problem.description}"

        formatter = UnicodeFormatter()
        result = formatter.format(mock_problem)
        assert isinstance(result, str)

    def test_format_with_empty_strings(self):
        """Test formatting with empty problem fields."""
        problem = Mock(spec=Problem)
        problem.id = 0
        problem.title = ""
        problem.description = ""

        class EmptyFieldFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"ID: {problem.id}, Title: '{problem.title}'"

        formatter = EmptyFieldFormatter()
        result = formatter.format(problem)
        assert "ID: 0" in result
        assert "Title: ''" in result

    def test_format_with_very_long_content(self):
        """Test formatting with very long content."""
        problem = Mock(spec=Problem)
        problem.title = "A" * 10000
        problem.description = "B" * 100000

        class LongContentFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"{problem.title}\n{problem.description}"

        formatter = LongContentFormatter()
        result = formatter.format(problem)
        assert len(result) > 100000

    def test_format_with_special_characters(self):
        """Test formatting with special characters."""
        problem = Mock(spec=Problem)
        problem.title = "Test <>&\"'`~!@#$%^&*()"
        problem.description = "Content with\ttabs\nand\nnewlines"

        class SpecialCharFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"{problem.title}: {problem.description}"

        formatter = SpecialCharFormatter()
        result = formatter.format(problem)
        assert "<>&" in result
        assert "\t" in result
        assert "\n" in result


# ============================================================================
# MOCK AND SPY TESTS
# ============================================================================

class TestMockingBehavior:
    """Test mocking scenarios for BaseFormatter."""

    def test_can_mock_concrete_formatter(self, mock_problem):
        """Test that concrete formatters can be mocked."""
        class RealFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return "real output"

        formatter = RealFormatter()
        with patch.object(formatter, 'format', return_value="mocked output"):
            result = formatter.format(mock_problem)
            assert result == "mocked output"

    def test_format_call_count(self, mock_problem):
        """Test tracking format call count."""
        class TrackingFormatter(BaseFormatter):
            def __init__(self):
                self.call_count = 0

            def format(self, problem: Problem) -> str:
                self.call_count += 1
                return "output"

        formatter = TrackingFormatter()

        formatter.format(mock_problem)
        formatter.format(mock_problem)
        formatter.format(mock_problem)

        assert formatter.call_count == 3

    def test_format_arguments_captured(self):
        """Test capturing arguments passed to format."""
        class CapturingFormatter(BaseFormatter):
            def __init__(self):
                self.captured_problems = []

            def format(self, problem: Problem) -> str:
                self.captured_problems.append(problem)
                return "output"

        formatter = CapturingFormatter()
        problem1 = Mock(spec=Problem)
        problem1.id = 1
        problem2 = Mock(spec=Problem)
        problem2.id = 2

        formatter.format(problem1)
        formatter.format(problem2)

        assert len(formatter.captured_problems) == 2
        assert formatter.captured_problems[0].id == 1
        assert formatter.captured_problems[1].id == 2


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests with real Problem objects."""

    def test_format_with_full_problem(self):
        """Test formatting with a fully populated Problem."""
        problem = Problem(
            id=42,
            title="Maximum Subarray",
            title_slug="maximum-subarray",
            difficulty=Difficulty.MEDIUM,
            description="<p>Find the contiguous subarray with largest sum.</p>",
            code_snippets=[
                CodeSnippet(lang=Language.PYTHON3, code="class Solution:\n    def maxSubArray(self, nums):\n        pass")
            ],
            test_cases=[
                Case(input="nums = [-2,1,-3,4,-1,2,1,-5,4]", output="6"),
                Case(input="nums = [1]", output="1")
            ]
        )

        class FullFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                lines = [
                    f"Problem #{problem.id}: {problem.title}",
                    f"Difficulty: {problem.difficulty.value}",
                    f"Description: {problem.description}",
                    f"Test Cases: {len(problem.test_cases)}",
                ]
                return "\n".join(lines)

        formatter = FullFormatter()
        result = formatter.format(problem)

        assert "Problem #42: Maximum Subarray" in result
        assert "Difficulty: Medium" in result
        assert "Test Cases: 2" in result

    def test_format_preserves_problem_data(self):
        """Ensure formatting doesn't modify the original problem."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="Original",
            code_snippets=[],
            test_cases=[]
        )

        original_title = problem.title
        original_desc = problem.description

        class ModifyingFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                # Formatting should read, not modify
                return f"{problem.title.upper()} - {problem.description.upper()}"

        formatter = ModifyingFormatter()
        formatter.format(problem)

        # Original should be unchanged
        assert problem.title == original_title
        assert problem.description == original_desc


# ============================================================================
# STATE MANAGEMENT TESTS
# ============================================================================

class TestStateManagement:
    """Test formatters with internal state."""

    def test_stateful_formatter(self, mock_problem):
        """Test formatter that maintains state."""
        class StatefulFormatter(BaseFormatter):
            def __init__(self):
                self.formatted_count = 0
                self.last_problem_id = None

            def format(self, problem: Problem) -> str:
                self.formatted_count += 1
                self.last_problem_id = problem.id
                return f"Formatted #{self.formatted_count}"

        formatter = StatefulFormatter()

        result1 = formatter.format(mock_problem)
        assert result1 == "Formatted #1"
        assert formatter.last_problem_id == mock_problem.id

        result2 = formatter.format(mock_problem)
        assert result2 == "Formatted #2"
        assert formatter.formatted_count == 2

    def test_stateless_formatter(self, mock_problem):
        """Test that stateless formatters produce consistent output."""
        class StatelessFormatter(BaseFormatter):
            def format(self, problem: Problem) -> str:
                return f"ID: {problem.id}"

        formatter = StatelessFormatter()

        result1 = formatter.format(mock_problem)
        result2 = formatter.format(mock_problem)
        result3 = formatter.format(mock_problem)

        assert result1 == result2 == result3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
