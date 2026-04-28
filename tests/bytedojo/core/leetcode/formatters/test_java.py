"""
Test suite for JavaFormatter.
"""

import pytest
from unittest.mock import Mock
from bytedojo.core.leetcode.models import Problem
from bytedojo.core.leetcode.formatters.java import JavaFormatContext, JavaFormatter


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def formatter():
    """Create a fresh formatter instance for each test."""
    return JavaFormatter()


@pytest.fixture
def basic_problem():
    """Create a basic, well-formed problem."""
    problem = Mock(spec=Problem)
    problem.id = 1
    problem.title = "Two Sum"
    problem.difficulty = "Easy"
    problem.description = "<p>Given an array of integers.</p>"
    problem.test_cases = ""
    problem.get_snippet.return_value = """class Solution {
    public int[] twoSum(int[] nums, int target) {

    }
}"""
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
        assert "TEST" in result
        assert "class Solution" in result

    def test_code_template_included(self, formatter, basic_problem):
        """Verify solution code is included."""
        result = formatter.format(basic_problem)
        assert "class Solution" in result
        assert "twoSum" in result

    def test_main_class_generated(self, formatter, basic_problem):
        """Verify Main class is generated."""
        result = formatter.format(basic_problem)
        assert "class Main" in result
        assert "public static void main" in result


# ============================================================================
# CONTEXT EXTRACTION TESTS
# ============================================================================

class TestJavaFormatContext:
    """Test JavaFormatContext metadata extraction."""

    def test_extract_class_name(self):
        """Extract class name from Java code."""
        code = """class Solution {
    public int[] twoSum(int[] nums, int target) {
        return new int[]{};
    }
}"""
        ctx = JavaFormatContext(code=code, description="", test_cases="")
        assert ctx.class_name == "Solution"

    def test_extract_method_name(self):
        """Extract method name from Java code."""
        code = """class Solution {
    public int[] twoSum(int[] nums, int target) {
        return new int[]{};
    }
}"""
        ctx = JavaFormatContext(code=code, description="", test_cases="")
        assert ctx.method_name == "twoSum"

    def test_extract_parameters(self):
        """Extract parameter info from Java code."""
        code = """class Solution {
    public int[] twoSum(int[] nums, int target) {
        return new int[]{};
    }
}"""
        ctx = JavaFormatContext(code=code, description="", test_cases="")
        assert len(ctx.param_info) == 2
        assert ctx.param_info[0] == ("nums", "int[]")
        assert ctx.param_info[1] == ("target", "int")

    def test_extract_return_type(self):
        """Extract return type from Java code."""
        code = """class Solution {
    public int[] twoSum(int[] nums, int target) {
        return new int[]{};
    }
}"""
        ctx = JavaFormatContext(code=code, description="", test_cases="")
        assert ctx.return_type == "int[]"

    def test_extract_list_return_type(self):
        """Extract List return type."""
        code = """class Solution {
    public List<Integer> findNumbers(int[] nums) {
        return new ArrayList<>();
    }
}"""
        ctx = JavaFormatContext(code=code, description="", test_cases="")
        assert ctx.return_type == "List<Integer>"

    def test_instance_name_property(self):
        """Test instance_name property."""
        code = """class Solution {
    public int solve() { return 0; }
}"""
        ctx = JavaFormatContext(code=code, description="", test_cases="")
        assert ctx.instance_name == "solution"


# ============================================================================
# IMPORT GENERATION TESTS
# ============================================================================

class TestImportGeneration:
    """Test Java import generation."""

    def test_arrays_import_for_array_return(self, formatter, basic_problem):
        """Arrays import added for array return type."""
        result = formatter.format(basic_problem)
        assert "import java.util.Arrays;" in result

    def test_list_imports(self, formatter, basic_problem):
        """List imports added when needed."""
        basic_problem.get_snippet.return_value = """class Solution {
    public List<Integer> solve(List<Integer> nums) {
        return new ArrayList<>();
    }
}"""
        result = formatter.format(basic_problem)
        assert "import java.util.List;" in result
        assert "import java.util.ArrayList;" in result


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_description(self, formatter, basic_problem):
        """Handle empty description."""
        basic_problem.description = ""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert "PROBLEM DESCRIPTION" in result

    def test_no_java_snippet(self, formatter, basic_problem):
        """Handle missing Java snippet."""
        basic_problem.get_snippet.return_value = None
        result = formatter.format(basic_problem)
        assert "No Java template available" in result

    def test_void_return_type(self, formatter, basic_problem):
        """Handle void return type."""
        basic_problem.get_snippet.return_value = """class Solution {
    public void solve(int[] nums) {

    }
}"""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert "class Main" in result

    def test_no_parameters(self, formatter, basic_problem):
        """Handle method with no parameters."""
        basic_problem.get_snippet.return_value = """class Solution {
    public int solve() {
        return 0;
    }
}"""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert "solution.solve()" in result


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_full_workflow(self, formatter, basic_problem):
        """Complete workflow for a problem."""
        result = formatter.format(basic_problem)

        # Verify structure
        assert "LeetCode Problem #1: Two Sum" in result
        assert "PROBLEM DESCRIPTION" in result
        assert "SOLUTION" in result
        assert "TEST" in result

        # Verify Java specifics
        assert "class Solution" in result
        assert "class Main" in result
        assert "public static void main" in result

    def test_complex_types(self, formatter, basic_problem):
        """Test with complex generic types."""
        basic_problem.get_snippet.return_value = """class Solution {
    public List<List<Integer>> threeSum(int[] nums) {
        return new ArrayList<>();
    }
}"""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert "List<List<Integer>>" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
