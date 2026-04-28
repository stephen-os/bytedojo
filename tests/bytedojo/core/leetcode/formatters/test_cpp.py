"""
Test suite for CppFormatter.
"""

import pytest
from unittest.mock import Mock
from bytedojo.core.leetcode.models import Problem
from bytedojo.core.leetcode.formatters.cpp import CppFormatContext, CppFormatter


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def formatter():
    """Create a fresh formatter instance for each test."""
    return CppFormatter()


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
public:
    vector<int> twoSum(vector<int>& nums, int target) {

    }
};"""
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

    def test_main_function_generated(self, formatter, basic_problem):
        """Verify main function is generated."""
        result = formatter.format(basic_problem)
        assert "int main()" in result
        assert "return 0;" in result


# ============================================================================
# CONTEXT EXTRACTION TESTS
# ============================================================================

class TestCppFormatContext:
    """Test CppFormatContext metadata extraction."""

    def test_extract_class_name(self):
        """Extract class name from C++ code."""
        code = """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        return {};
    }
};"""
        ctx = CppFormatContext(code=code, description="", test_cases="")
        assert ctx.class_name == "Solution"

    def test_extract_method_name(self):
        """Extract method name from C++ code."""
        code = """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        return {};
    }
};"""
        ctx = CppFormatContext(code=code, description="", test_cases="")
        assert ctx.method_name == "twoSum"

    def test_extract_parameters(self):
        """Extract parameter info from C++ code."""
        code = """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        return {};
    }
};"""
        ctx = CppFormatContext(code=code, description="", test_cases="")
        assert len(ctx.param_info) == 2
        assert ctx.param_info[0] == ("nums", "vector<int>&")
        assert ctx.param_info[1] == ("target", "int")

    def test_extract_return_type(self):
        """Extract return type from C++ code."""
        code = """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        return {};
    }
};"""
        ctx = CppFormatContext(code=code, description="", test_cases="")
        assert ctx.return_type == "vector<int>"

    def test_extract_nested_vector_type(self):
        """Extract nested vector return type."""
        code = """class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {
        return {};
    }
};"""
        ctx = CppFormatContext(code=code, description="", test_cases="")
        assert ctx.return_type == "vector<vector<int>>"

    def test_instance_name_property(self):
        """Test instance_name property."""
        code = """class Solution {
public:
    int solve() { return 0; }
};"""
        ctx = CppFormatContext(code=code, description="", test_cases="")
        assert ctx.instance_name == "solution"


# ============================================================================
# INCLUDE GENERATION TESTS
# ============================================================================

class TestIncludeGeneration:
    """Test C++ include generation."""

    def test_vector_include(self, formatter, basic_problem):
        """Vector include added when vector used."""
        result = formatter.format(basic_problem)
        assert "#include <vector>" in result

    def test_iostream_include(self, formatter, basic_problem):
        """iostream include always added for main."""
        result = formatter.format(basic_problem)
        assert "#include <iostream>" in result

    def test_using_namespace(self, formatter, basic_problem):
        """using namespace std is included."""
        result = formatter.format(basic_problem)
        assert "using namespace std;" in result


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

    def test_no_cpp_snippet(self, formatter, basic_problem):
        """Handle missing C++ snippet."""
        basic_problem.get_snippet.return_value = None
        result = formatter.format(basic_problem)
        assert "No C++ template available" in result

    def test_void_return_type(self, formatter, basic_problem):
        """Handle void return type."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    void solve(vector<int>& nums) {

    }
};"""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert "int main()" in result

    def test_no_parameters(self, formatter, basic_problem):
        """Handle method with no parameters."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    int solve() {
        return 0;
    }
};"""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert "solution.solve()" in result


# ============================================================================
# PRINT CODE GENERATION TESTS
# ============================================================================

class TestPrintCodeGeneration:
    """Test print code generation for different types."""

    def test_vector_print(self, formatter, basic_problem):
        """Vector output uses loop."""
        result = formatter.format(basic_problem)
        # Should have vector printing logic
        assert "cout" in result

    def test_simple_type_print(self, formatter, basic_problem):
        """Simple types use direct cout."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    int solve(int x) {
        return x;
    }
};"""
        result = formatter.format(basic_problem)
        assert "cout <<" in result


# ============================================================================
# DEFAULT RETURN INJECTION TESTS
# ============================================================================

class TestDefaultReturnInjection:
    """Test that default return statements are injected for runnable output."""

    def test_vector_int_return_injected(self, formatter, basic_problem):
        """Empty vector<int> method gets default return."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {

    }
};"""
        result = formatter.format(basic_problem)
        assert "return {};" in result

    def test_int_return_injected(self, formatter, basic_problem):
        """Empty int method gets default return."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    int solve(int x) {

    }
};"""
        result = formatter.format(basic_problem)
        assert "return 0;" in result

    def test_bool_return_injected(self, formatter, basic_problem):
        """Empty bool method gets default return."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    bool isValid(string s) {

    }
};"""
        result = formatter.format(basic_problem)
        assert "return false;" in result

    def test_string_return_injected(self, formatter, basic_problem):
        """Empty string method gets default return."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    string convert(string s) {

    }
};"""
        result = formatter.format(basic_problem)
        assert 'return "";' in result

    def test_nested_vector_return_injected(self, formatter, basic_problem):
        """Empty vector<vector<int>> method gets default return."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {

    }
};"""
        result = formatter.format(basic_problem)
        assert "return {};" in result

    def test_void_no_return_injected(self, formatter, basic_problem):
        """Void method does not get return injected."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    void solve(vector<int>& nums) {

    }
};"""
        result = formatter.format(basic_problem)
        # Should not have a return statement in the Solution class
        solution_section = result.split("int main()")[0]
        assert "return" not in solution_section

    def test_existing_code_not_modified(self, formatter, basic_problem):
        """Method with existing code is not modified."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        return {0, 1};
    }
};"""
        result = formatter.format(basic_problem)
        assert "return {0, 1};" in result


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

        # Verify C++ specifics
        assert "class Solution" in result
        assert "int main()" in result
        assert "#include" in result
        assert "using namespace std;" in result

    def test_complex_types(self, formatter, basic_problem):
        """Test with complex nested types."""
        basic_problem.get_snippet.return_value = """class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {
        return {};
    }
};"""
        result = formatter.format(basic_problem)
        assert isinstance(result, str)
        assert "vector<vector<int>>" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
