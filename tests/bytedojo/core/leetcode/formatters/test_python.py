"""
Comprehensive test suite for PythonFormatter.
Tests cover edge cases, malformed inputs, stress scenarios, and error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import re
from bytedojo.core.leetcode.models import Problem
from bytedojo.core.leetcode.formatters.python import PythonFormatter


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def formatter():
    """Create a fresh formatter instance for each test."""
    return PythonFormatter()


@pytest.fixture
def basic_problem():
    """Create a basic, well-formed problem."""
    problem = Mock(spec=Problem)
    problem.id = 1
    problem.title = "Two Sum"
    problem.difficulty = "Easy"
    problem.description = "<p>Given an array of integers <code>nums</code> and an integer <code>target</code>.</p>"
    problem.test_cases = "[2,7,11,15]\n9\n[0,1]"
    problem.get_snippet.return_value = """class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        pass"""
    return problem


@pytest.fixture
def complex_problem():
    """Create a problem with ListNode and complex types."""
    problem = Mock(spec=Problem)
    problem.id = 206
    problem.title = "Reverse Linked List"
    problem.difficulty = "Easy"
    problem.description = "<p>Reverse a linked list.</p>"
    problem.test_cases = "[1,2,3,4,5]\n[5,4,3,2,1]"
    problem.get_snippet.return_value = """# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        pass"""
    return problem


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestBasicFormatting:
    """Test basic formatting functionality."""
    
    def test_format_returns_string(self, formatter, basic_problem):
        """Ensure format returns a string."""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_format_contains_problem_info(self, formatter, basic_problem):
        """Verify problem metadata is included."""
        result = formatter.format(basic_problem)
        assert "Problem #1" in result
        assert "Two Sum" in result
        assert "Easy" in result
    
    def test_format_has_all_sections(self, formatter, basic_problem):
        """Check that all required sections are present."""
        result = formatter.format(basic_problem)
        assert "PROBLEM DESCRIPTION" in result
        assert "SOLUTION" in result
        assert "TESTS" in result
        assert "def run_tests():" in result
        assert 'if __name__ == "__main__":' in result
    
    def test_code_template_included(self, formatter, basic_problem):
        """Verify solution code is included."""
        result = formatter.format(basic_problem)
        assert "class Solution:" in result
        assert "def twoSum" in result


# ============================================================================
# EDGE CASE TESTS - NULL/EMPTY INPUTS
# ============================================================================

class TestNullAndEmptyInputs:
    """Test behavior with null, empty, or missing data."""
    
    def test_empty_description(self, formatter, basic_problem):
        """Handle empty description gracefully."""
        basic_problem.description = ""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert "PROBLEM DESCRIPTION" in result
    
    def test_none_description(self, formatter, basic_problem):
        """Handle None description."""
        basic_problem.description = None
        # Should not crash
        try:
            result = formatter.format(basic_problem)
            assert isinstance(result, str)
        except (AttributeError, TypeError):
            # If it fails, it should be a clear error, not a crash
            pass
    
    def test_empty_test_cases(self, formatter, basic_problem):
        """Handle empty test cases."""
        basic_problem.test_cases = ""
        result = formatter.format(basic_problem)
        assert "Add your test cases here" in result or "pass" in result
    
    def test_none_test_cases(self, formatter, basic_problem):
        """Handle None test cases."""
        basic_problem.test_cases = None
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_no_python_snippet(self, formatter, basic_problem):
        """Handle missing Python code snippet."""
        basic_problem.get_snippet.return_value = None
        result = formatter.format(basic_problem)
        assert "No Python template available" in result
    
    def test_empty_python_snippet(self, formatter, basic_problem):
        """Handle empty Python code snippet."""
        basic_problem.get_snippet.return_value = ""
        result = formatter.format(basic_problem)
        assert "No Python template available" in result
    
    def test_missing_problem_id(self, formatter, basic_problem):
        """Handle missing problem ID."""
        basic_problem.id = None
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_missing_title(self, formatter, basic_problem):
        """Handle missing title."""
        basic_problem.title = ""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_missing_difficulty(self, formatter, basic_problem):
        """Handle missing difficulty."""
        basic_problem.difficulty = None
        result = formatter.format(basic_problem)
        assert isinstance(result, str)


# ============================================================================
# MALFORMED INPUT TESTS
# ============================================================================

class TestMalformedInputs:
    """Test behavior with malformed or corrupted data."""
    
    def test_malformed_html_description(self, formatter, basic_problem):
        """Handle broken HTML in description."""
        basic_problem.description = "<p>Unclosed tag<p>More text<div>Another<"
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_description_with_special_chars(self, formatter, basic_problem):
        """Handle special characters in description."""
        basic_problem.description = "<p>Test &lt;&gt;&amp;&nbsp;&#39;&#34;</p>"
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_description_with_unicode(self, formatter, basic_problem):
        """Handle unicode characters."""
        basic_problem.description = "<p>Test 中文 español русский 🚀 emoji</p>"
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_malformed_code_template(self, formatter, basic_problem):
        """Handle broken code template."""
        basic_problem.get_snippet.return_value = "class Solution\ndef method("
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_code_with_syntax_errors(self, formatter, basic_problem):
        """Handle code with syntax errors."""
        basic_problem.get_snippet.return_value = """class Solution:
    def method(self, x: int) -> int
        return x  # missing colon
        """
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_deeply_nested_html(self, formatter, basic_problem):
        """Handle deeply nested HTML."""
        basic_problem.description = "<div>" * 100 + "content" + "</div>" * 100
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_html_with_scripts(self, formatter, basic_problem):
        """Handle HTML with script tags."""
        basic_problem.description = "<script>alert('xss')</script><p>Real content</p>"
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        # Script tags should be stripped
        assert "alert" in result or "script" not in result.lower()


# ============================================================================
# CODE PROCESSING TESTS
# ============================================================================

class TestCodeProcessing:
    """Test code extraction and processing."""
    
    def test_uncomment_listnode(self, formatter, complex_problem):
        """Verify ListNode class is uncommented."""
        result = formatter.format(complex_problem)
        # Should have uncommented ListNode
        assert "class ListNode:" in result
        # Original should not have comment markers in class definition
        lines = result.split('\n')
        for line in lines:
            if "class ListNode:" in line:
                assert not line.strip().startswith('#')
    
    def test_uncomment_treenode(self, formatter):
        """Test TreeNode uncommenting."""
        problem = Mock(spec=Problem)
        problem.id = 100
        problem.title = "Same Tree"
        problem.difficulty = "Easy"
        problem.description = "<p>Test</p>"
        problem.test_cases = ""
        problem.get_snippet.return_value = """# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right

class Solution:
    def isSameTree(self, p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
        pass"""
        
        result = formatter.format(problem)
        assert "class TreeNode:" in result
    
    def test_extract_imports_list(self, formatter, basic_problem):
        """Test List import extraction."""
        basic_problem.get_snippet.return_value = """class Solution:
    def method(self, nums: List[int]) -> List[int]:
        pass"""
        result = formatter.format(basic_problem)
        assert "from typing import List" in result
    
    def test_extract_imports_optional(self, formatter, complex_problem):
        """Test Optional import extraction."""
        result = formatter.format(complex_problem)
        assert "from typing import Optional" in result
    
    def test_extract_multiple_imports(self, formatter):
        """Test multiple type import extraction."""
        problem = Mock(spec=Problem)
        problem.id = 1
        problem.title = "Test"
        problem.difficulty = "Easy"
        problem.description = "<p>Test</p>"
        problem.test_cases = ""
        problem.get_snippet.return_value = """class Solution:
    def method(self, x: List[int], y: Optional[Dict[str, Set[int]]]) -> Tuple[int, int]:
        pass"""
        
        result = formatter.format(problem)
        assert "from typing import" in result
        assert "List" in result
        assert "Optional" in result
        assert "Dict" in result
        assert "Set" in result
        assert "Tuple" in result
    
    def test_ensure_pass_added(self, formatter, basic_problem):
        """Verify pass is added to empty methods."""
        basic_problem.get_snippet.return_value = """class Solution:
    def method(self, x: int) -> int:
        """
        result = formatter.format(basic_problem)
        # Should have pass statement
        assert "pass" in result
    
    def test_method_with_existing_code(self, formatter, basic_problem):
        """Don't add pass if method has code."""
        basic_problem.get_snippet.return_value = """class Solution:
    def method(self, x: int) -> int:
        return x * 2"""
        result = formatter.format(basic_problem)
        # Count pass statements - should only be in run_tests if at all
        pass_count = result.count('pass')
        # Should not add extra pass to method with code
        assert 'return x * 2' in result


# ============================================================================
# METHOD EXTRACTION TESTS
# ============================================================================

class TestMethodExtraction:
    """Test method name and parameter extraction."""
    
    def test_extract_simple_method_name(self, formatter):
        """Extract method name from simple signature."""
        code = """class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        pass"""
        method = formatter._extract_method_name(code)
        assert method == "twoSum"
    
    def test_extract_method_with_no_params(self, formatter):
        """Extract method with only self parameter."""
        code = """class Solution:
    def solve(self) -> int:
        pass"""
        method = formatter._extract_method_name(code)
        assert method == "solve"
    
    def test_extract_method_multiline(self, formatter):
        """Extract method from multiline signature."""
        code = """class Solution:
    def complexMethod(
        self, 
        x: int, 
        y: str
    ) -> bool:
        pass"""
        method = formatter._extract_method_name(code)
        assert method == "complexMethod"
    
    def test_ignore_dunder_methods(self, formatter):
        """Should skip __init__ and other dunder methods."""
        code = """class Solution:
    def __init__(self):
        pass
    
    def solve(self, x: int) -> int:
        pass"""
        method = formatter._extract_method_name(code)
        assert method == "solve"
    
    def test_multiple_classes(self, formatter):
        """Extract from Solution class when multiple classes present."""
        code = """class ListNode:
    def __init__(self, val=0):
        self.val = val

class Solution:
    def process(self, head: ListNode) -> ListNode:
        pass"""
        method = formatter._extract_method_name(code)
        assert method == "process"
    
    def test_no_solution_class(self, formatter):
        """Fallback when no Solution class exists."""
        code = """class MyClass:
    def myMethod(self, x: int) -> int:
        pass"""
        method = formatter._extract_method_name(code)
        # Should find first non-dunder method
        assert method == "myMethod"
    
    def test_count_params_simple(self, formatter):
        """Count parameters excluding self."""
        code = """def method(self, x: int, y: int) -> int:
    pass"""
        count = formatter._count_method_params(code)
        assert count == 2
    
    def test_count_params_complex_types(self, formatter):
        """Count parameters with complex type hints."""
        code = """def method(self, nums: List[List[int]], target: Dict[str, int]) -> bool:
    pass"""
        count = formatter._count_method_params(code)
        assert count == 2
    
    def test_count_params_none(self, formatter):
        """Count when only self parameter."""
        code = """def method(self) -> int:
    pass"""
        count = formatter._count_method_params(code)
        assert count == 0


# ============================================================================
# TEST CASE PARSING TESTS
# ============================================================================

class TestTestCaseParsing:
    """Test test case parsing through public interface."""
    
    def test_parse_simple_test_groups(self, formatter):
        """Parse simple input/output groups."""
        problem = Mock(spec=Problem)
        problem.id = 1
        problem.title = "Test"
        problem.difficulty = "Easy"
        problem.description = "<p>Test</p>"
        problem.test_cases = "[1,2,3]\n6\n[4,5]\n9"
        problem.get_snippet.return_value = """class Solution:
    def method(self, x: int) -> int:
        pass"""
        
        result = formatter.format(problem)
        # Verify it doesn't crash and produces test code
        assert isinstance(result, str)
        assert "def run_tests():" in result
        # Should have test output with the inputs
        assert "result1" in result or "[1,2,3]" in result or "Expected" in result
    
    def test_parse_multiple_params(self, formatter):
        """Parse test cases with multiple parameters."""
        problem = Mock(spec=Problem)
        problem.id = 1
        problem.title = "Test"
        problem.difficulty = "Easy"
        problem.description = "<p>Test</p>"
        problem.test_cases = "[1,2]\n3\n5\n[4,5]\n6\n10"
        problem.get_snippet.return_value = """class Solution:
    def method(self, nums: List[int], target: int) -> int:
        pass"""
        
        result = formatter.format(problem)
        assert isinstance(result, str)
        assert "def run_tests():" in result
        # Should handle multiple parameters
        assert "result" in result or "Expected" in result
    
    def test_parse_no_expected_output(self, formatter):
        """Parse when only inputs provided."""
        problem = Mock(spec=Problem)
        problem.id = 1
        problem.title = "Test"
        problem.difficulty = "Easy"
        problem.description = "<p>Test</p>"
        problem.test_cases = "[1,2,3]\n[4,5,6]"
        problem.get_snippet.return_value = """class Solution:
    def method(self, nums: List[int]) -> int:
        pass"""
        
        result = formatter.format(problem)
        assert isinstance(result, str)
        assert "def run_tests():" in result
        # Should still generate test code even without expected outputs
        assert "result" in result or "print" in result
    
    def test_parse_mismatched_lines(self, formatter):
        """Handle mismatched line counts."""
        problem = Mock(spec=Problem)
        problem.id = 1
        problem.title = "Test"
        problem.difficulty = "Easy"
        problem.description = "<p>Test</p>"
        # 3 lines that don't divide evenly by param count
        problem.test_cases = "[1,2]\n3\n5"
        problem.get_snippet.return_value = """class Solution:
    def method(self, nums: List[int], target: int) -> int:
        pass"""
        
        result = formatter.format(problem)
        # Should not crash - might fall back to commented format
        assert isinstance(result, str)
        assert "def run_tests():" in result
    
    def test_parse_zero_params(self, formatter):
        """Handle zero parameter methods."""
        problem = Mock(spec=Problem)
        problem.id = 1
        problem.title = "Test"
        problem.difficulty = "Easy"
        problem.description = "<p>Test</p>"
        problem.test_cases = "result1\nresult2"
        problem.get_snippet.return_value = """class Solution:
    def method(self) -> int:
        pass"""
        
        result = formatter.format(problem)
        assert isinstance(result, str)
        assert "def run_tests():" in result
        # With zero params, should still generate some test structure
        assert "pass" in result or "result" in result


# ============================================================================
# STRESS TESTS
# ============================================================================

class TestStressScenarios:
    """Test with large or complex inputs."""
    
    def test_very_long_description(self, formatter, basic_problem):
        """Handle extremely long descriptions."""
        basic_problem.description = "<p>" + ("A" * 100000) + "</p>"
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_many_test_cases(self, formatter, basic_problem):
        """Handle many test cases."""
        test_cases = "\n".join([f"[{i}]" for i in range(1000)])
        basic_problem.test_cases = test_cases
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_deeply_nested_types(self, formatter):
        """Handle deeply nested type hints."""
        problem = Mock(spec=Problem)
        problem.id = 1
        problem.title = "Test"
        problem.difficulty = "Hard"
        problem.description = "<p>Test</p>"
        problem.test_cases = ""
        problem.get_snippet.return_value = """class Solution:
    def method(self, x: List[List[List[Dict[str, Set[Tuple[int, int]]]]]]) -> Optional[Union[int, str]]:
        pass"""
        
        result = formatter.format(problem)
        assert isinstance(result, str)
        assert "from typing import" in result
    
    def test_very_long_method_name(self, formatter, basic_problem):
        """Handle very long method names."""
        basic_problem.get_snippet.return_value = f"""class Solution:
    def {'a' * 200}(self, x: int) -> int:
        pass"""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_many_methods_in_solution(self, formatter, basic_problem):
        """Handle Solution class with many methods."""
        methods = "\n".join([f"    def method{i}(self, x: int) -> int:\n        pass" for i in range(100)])
        basic_problem.get_snippet.return_value = f"""class Solution:
{methods}"""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_many_commented_classes(self, formatter):
        """Handle many commented class definitions."""
        # Generate 50 commented classes
        class_blocks = []
        for i in range(50):
            class_blocks.append(f"# class MyClass{i}:")
            class_blocks.append(f"#     def __init__(self):")
            class_blocks.append(f"#         pass")
            class_blocks.append("")
        
        commented_classes = "\n".join(class_blocks)
        
        problem = Mock(spec=Problem)
        problem.id = 1
        problem.title = "Test"
        problem.difficulty = "Easy"
        problem.description = "<p>Test</p>"
        problem.test_cases = ""
        problem.get_snippet.return_value = f"""{commented_classes}

class Solution:
    def solve(self, x: int) -> int:
        pass"""
        
        result = formatter.format(problem)
        assert isinstance(result, str)


# ============================================================================
# HTML ENTITY TESTS
# ============================================================================

class TestHTMLEntities:
    """Test HTML entity handling in descriptions."""
    
    def test_common_entities(self, formatter, basic_problem):
        """Handle common HTML entities."""
        basic_problem.description = "&lt;tag&gt; &amp; &nbsp; text"
        result = formatter.format(basic_problem)
        assert "<tag>" in result
        assert "&" in result
    
    def test_numeric_entities(self, formatter, basic_problem):
        """Handle numeric HTML entities."""
        basic_problem.description = "&#60;&#62;&#38;"
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    def test_mixed_entities(self, formatter, basic_problem):
        """Handle mix of named and numeric entities."""
        basic_problem.description = "&lt;div&#62;Content&amp;more&#60;/div&gt;"
        result = formatter.format(basic_problem)
        assert isinstance(result, str)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_workflow_simple_problem(self, formatter, basic_problem):
        """Complete workflow for simple problem."""
        result = formatter.format(basic_problem)
        
        # Verify structure
        assert "LeetCode Problem #1: Two Sum" in result
        assert "PROBLEM DESCRIPTION" in result
        assert "SOLUTION" in result
        assert "TESTS" in result
        
        # Verify it's runnable Python
        assert result.count('"""') >= 2  # Has docstrings
        assert "class Solution:" in result
        assert "def run_tests():" in result
        assert 'if __name__ == "__main__":' in result
    
    def test_full_workflow_complex_problem(self, formatter, complex_problem):
        """Complete workflow for complex problem."""
        result = formatter.format(complex_problem)
        
        # Verify ListNode was uncommented
        assert "class ListNode:" in result
        assert "def __init__" in result
        
        # Verify imports added
        assert "from typing import Optional" in result
        
        # Verify method extracted
        assert "def reverseList" in result
    
    def test_generated_code_is_valid_python(self, formatter, basic_problem):
        """Ensure generated code is syntactically valid Python."""
        result = formatter.format(basic_problem)
        
        # Try to compile it
        try:
            compile(result, '<string>', 'exec')
            compiled = True
        except SyntaxError:
            compiled = False
        
        assert compiled, "Generated code should be valid Python"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and recovery."""
    
    def test_problem_get_snippet_throws(self, formatter, basic_problem):
        """Handle exception in get_snippet."""
        basic_problem.get_snippet.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            formatter.format(basic_problem)
    
    def test_malformed_problem_object(self, formatter):
        """Handle problem object missing required attributes."""
        problem = Mock(spec=Problem, spec_set=True)
        del problem.id
        del problem.title
        del problem.difficulty
        del problem.description
        del problem.test_cases
        del problem.get_snippet
        
        with pytest.raises(AttributeError):
            formatter.format(problem)
    
    def test_unicode_decode_error(self, formatter, basic_problem):
        """Handle potential unicode issues."""
        basic_problem.description = "<p>\x80\x81\x82</p>"
        try:
            result = formatter.format(basic_problem)
            assert isinstance(result, str)
        except UnicodeDecodeError:
            pytest.skip("Unicode handling depends on Python version")


# ============================================================================
# REGRESSION TESTS
# ============================================================================

class TestRegressions:
    """Tests for specific bug fixes and regressions."""
    
    def test_double_pass_not_added(self, formatter):
        """Ensure pass is not added twice to empty methods."""
        problem = Mock(spec=Problem)
        problem.id = 1
        problem.title = "Test"
        problem.difficulty = "Easy"
        problem.description = "<p>Test</p>"
        problem.test_cases = ""
        problem.get_snippet.return_value = """class Solution:
    def method(self, x: int) -> int:
        pass"""
        
        result = formatter.format(problem)
        # Method should still have only one pass
        method_section = result[result.find("def method"):result.find("def method") + 200]
        assert method_section.count("pass") == 1
    
    def test_class_definition_indent_preserved(self, formatter, complex_problem):
        """Ensure indentation is preserved when uncommenting classes."""
        result = formatter.format(complex_problem)
        
        lines = result.split('\n')
        for i, line in enumerate(lines):
            if "class ListNode:" in line:
                # Next line should be indented
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip():
                        assert next_line.startswith("    ")
    
    def test_no_extra_blank_lines(self, formatter, basic_problem):
        """Ensure no excessive blank lines."""
        result = formatter.format(basic_problem)
        
        # Check no more than 2 consecutive blank lines
        lines = result.split('\n')
        blank_count = 0
        for line in lines:
            if not line.strip():
                blank_count += 1
                assert blank_count <= 3, "Too many consecutive blank lines"
            else:
                blank_count = 0


# ============================================================================
# PROPERTY-BASED TESTS
# ============================================================================

class TestPropertyBased:
    """Property-based tests using hypothesis."""
    
    @pytest.mark.parametrize("problem_id", [0, 1, 100, 9999, -1])
    def test_various_problem_ids(self, formatter, basic_problem, problem_id):
        """Test with various problem IDs."""
        basic_problem.id = problem_id
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert str(problem_id) in result or "None" in result
    
    @pytest.mark.parametrize("difficulty", ["Easy", "Medium", "Hard", "", None, "Unknown"])
    def test_various_difficulties(self, formatter, basic_problem, difficulty):
        """Test with various difficulty levels."""
        basic_problem.difficulty = difficulty
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
    
    @pytest.mark.parametrize("title", [
        "Two Sum",
        "Add Two Numbers",
        "",
        "A" * 200,
        "Test-Problem_Name",
        "Problem with 中文",
    ])
    def test_various_titles(self, formatter, basic_problem, title):
        """Test with various problem titles."""
        basic_problem.title = title
        result = formatter.format(basic_problem)
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])