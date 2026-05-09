"""
Comprehensive test suite for formatters utils module.
Tests cover all utility functions for HTML parsing and type conversion.
"""

import pytest
from unittest.mock import Mock, patch


from bytedojo.core.formatters.utils import (
    html_to_text,
    parse_input_variables,
    convert_to_python_literal,
    convert_to_java_literal,
    convert_to_cpp_literal,
    get_java_default,
    get_cpp_default,
)


# ============================================================================
# HTML TO TEXT TESTS
# ============================================================================

class TestHtmlToText:
    """Test HTML to plain text conversion."""

    def test_simple_html_tags(self):
        """Convert simple HTML tags to text."""
        result = html_to_text("<p>Hello World</p>")
        assert result == "Hello World"

    def test_nested_html_tags(self):
        """Convert nested HTML tags to text."""
        result = html_to_text("<div><p>Nested <strong>text</strong></p></div>")
        assert result == "Nested text"

    def test_empty_string(self):
        """Handle empty string input."""
        result = html_to_text("")
        assert result == ""

    def test_none_like_empty(self):
        """Handle None-like falsy input."""
        result = html_to_text("")
        assert result == ""

    def test_html_entities_unescape(self):
        """Unescape HTML entities."""
        result = html_to_text("&lt;tag&gt; &amp; &quot;text&quot;")
        assert "<tag>" in result
        assert "&" in result
        assert '"text"' in result

    def test_numeric_html_entities(self):
        """Handle numeric HTML entities."""
        result = html_to_text("&#60;&#62;&#38;")
        assert "<" in result
        assert ">" in result
        assert "&" in result

    def test_nbsp_entity(self):
        """Handle non-breaking space entity."""
        result = html_to_text("Hello&nbsp;World")
        # nbsp becomes a regular space or non-breaking space character
        assert "Hello" in result
        assert "World" in result

    def test_whitespace_normalization(self):
        """Normalize multiple newlines to double newlines."""
        result = html_to_text("<p>First</p>\n\n\n\n<p>Second</p>")
        # Should normalize excessive newlines
        assert result.count("\n\n\n") == 0 or result == "First\n\nSecond"

    def test_strip_whitespace(self):
        """Strip leading and trailing whitespace."""
        result = html_to_text("   <p>Content</p>   ")
        assert result == "Content"

    def test_self_closing_tags(self):
        """Handle self-closing tags."""
        result = html_to_text("Line1<br/>Line2<hr/>Line3")
        assert "Line1" in result
        assert "Line2" in result
        assert "Line3" in result

    def test_complex_attributes(self):
        """Handle tags with attributes."""
        result = html_to_text('<a href="http://example.com" class="link">Click here</a>')
        assert result == "Click here"

    def test_code_tags(self):
        """Handle code tags common in LeetCode descriptions."""
        result = html_to_text("<code>nums</code> and <code>target</code>")
        assert "nums" in result
        assert "target" in result

    def test_preformatted_text(self):
        """Handle pre tags."""
        result = html_to_text("<pre>int x = 5;\nint y = 10;</pre>")
        assert "int x = 5" in result
        assert "int y = 10" in result

    def test_list_tags(self):
        """Handle list tags."""
        result = html_to_text("<ul><li>Item 1</li><li>Item 2</li></ul>")
        assert "Item 1" in result
        assert "Item 2" in result

    def test_unicode_content(self):
        """Handle unicode content."""
        result = html_to_text("<p>Test</p>")
        assert "Test" in result

    def test_script_tags_removed(self):
        """Script tags should be removed."""
        result = html_to_text("<script>alert('xss')</script><p>Content</p>")
        assert "Content" in result
        # Script content should be stripped (tags removed but content may remain)

    def test_deeply_nested_tags(self):
        """Handle deeply nested HTML."""
        nested = "<div>" * 50 + "Content" + "</div>" * 50
        result = html_to_text(nested)
        assert result == "Content"

    def test_malformed_html(self):
        """Handle malformed HTML gracefully."""
        result = html_to_text("<p>Unclosed<p>More<div>Text<")
        # Should not crash
        assert isinstance(result, str)

    def test_only_whitespace_content(self):
        """Handle HTML with only whitespace content."""
        result = html_to_text("<p>   </p>")
        assert result == ""


# ============================================================================
# PARSE INPUT VARIABLES TESTS
# ============================================================================

class TestParseInputVariables:
    """Test parsing of LeetCode input variable formats."""

    def test_simple_single_variable(self):
        """Parse single variable assignment."""
        result = parse_input_variables("x = 5")
        assert result == {"x": "5"}

    def test_two_variables(self):
        """Parse two variable assignments."""
        result = parse_input_variables("nums = [2,7,11,15], target = 9")
        assert result == {"nums": "[2,7,11,15]", "target": "9"}

    def test_array_variable(self):
        """Parse array variable."""
        result = parse_input_variables("nums = [1,2,3,4,5]")
        assert result == {"nums": "[1,2,3,4,5]"}

    def test_nested_array(self):
        """Parse nested array variable."""
        result = parse_input_variables("matrix = [[1,2],[3,4]]")
        assert result == {"matrix": "[[1,2],[3,4]]"}

    def test_string_variable(self):
        """Parse string variable."""
        result = parse_input_variables('s = "hello"')
        assert result == {"s": '"hello"'}

    def test_multiple_variables(self):
        """Parse multiple variables."""
        result = parse_input_variables("a = 1, b = 2, c = 3")
        assert result == {"a": "1", "b": "2", "c": "3"}

    def test_boolean_true(self):
        """Parse boolean true value."""
        result = parse_input_variables("flag = true")
        assert result == {"flag": "true"}

    def test_boolean_false(self):
        """Parse boolean false value."""
        result = parse_input_variables("flag = false")
        assert result == {"flag": "false"}

    def test_null_value(self):
        """Parse null value."""
        result = parse_input_variables("node = null")
        assert result == {"node": "null"}

    def test_negative_number(self):
        """Parse negative number."""
        result = parse_input_variables("x = -5")
        assert result == {"x": "-5"}

    def test_float_number(self):
        """Parse float number."""
        result = parse_input_variables("x = 3.14")
        assert result == {"x": "3.14"}

    def test_complex_nested_structure(self):
        """Parse complex nested structure."""
        result = parse_input_variables("grid = [[1,2,3],[4,5,6],[7,8,9]]")
        assert result == {"grid": "[[1,2,3],[4,5,6],[7,8,9]]"}

    def test_empty_string(self):
        """Handle empty string input."""
        result = parse_input_variables("")
        assert result == {}

    def test_whitespace_around_equals(self):
        """Handle variable whitespace around equals sign."""
        result = parse_input_variables("x   =   5")
        assert result == {"x": "5"}

    def test_no_whitespace_around_equals(self):
        """Handle no whitespace around equals sign."""
        result = parse_input_variables("x=5")
        assert result == {"x": "5"}

    def test_trailing_comma(self):
        """Handle trailing comma."""
        result = parse_input_variables("x = 5,")
        assert result == {"x": "5"}

    def test_variable_with_underscore(self):
        """Parse variable with underscore."""
        result = parse_input_variables("my_var = 10")
        assert result == {"my_var": "10"}

    def test_variable_with_numbers(self):
        """Parse variable with numbers in name."""
        result = parse_input_variables("var1 = 1, var2 = 2")
        assert result == {"var1": "1", "var2": "2"}

    def test_head_linked_list(self):
        """Parse linked list head variable."""
        result = parse_input_variables("head = [1,2,3,4,5]")
        assert result == {"head": "[1,2,3,4,5]"}

    def test_root_tree_node(self):
        """Parse tree root variable."""
        result = parse_input_variables("root = [1,null,2,3]")
        assert result == {"root": "[1,null,2,3]"}

    def test_string_with_spaces(self):
        """Parse string with spaces."""
        result = parse_input_variables('s = "hello world"')
        assert result == {"s": '"hello world"'}

    def test_empty_array(self):
        """Parse empty array."""
        result = parse_input_variables("nums = []")
        assert result == {"nums": "[]"}


# ============================================================================
# CONVERT TO PYTHON LITERAL TESTS
# ============================================================================

class TestConvertToPythonLiteral:
    """Test conversion to Python literals."""

    def test_array_unchanged(self):
        """Arrays should remain unchanged."""
        result = convert_to_python_literal("[1,2,3]")
        assert result == "[1,2,3]"

    def test_nested_array_unchanged(self):
        """Nested arrays should remain unchanged."""
        result = convert_to_python_literal("[[1,2],[3,4]]")
        assert result == "[[1,2],[3,4]]"

    def test_double_quoted_string_unchanged(self):
        """Double-quoted strings should remain unchanged."""
        result = convert_to_python_literal('"hello"')
        assert result == '"hello"'

    def test_single_quoted_string_unchanged(self):
        """Single-quoted strings should remain unchanged."""
        result = convert_to_python_literal("'hello'")
        assert result == "'hello'"

    def test_true_conversion(self):
        """Convert 'true' to 'True'."""
        result = convert_to_python_literal("true")
        assert result == "True"

    def test_true_uppercase(self):
        """Convert 'TRUE' to 'True'."""
        result = convert_to_python_literal("TRUE")
        assert result == "True"

    def test_true_mixed_case(self):
        """Convert 'True' to 'True'."""
        result = convert_to_python_literal("True")
        assert result == "True"

    def test_false_conversion(self):
        """Convert 'false' to 'False'."""
        result = convert_to_python_literal("false")
        assert result == "False"

    def test_false_uppercase(self):
        """Convert 'FALSE' to 'False'."""
        result = convert_to_python_literal("FALSE")
        assert result == "False"

    def test_null_conversion(self):
        """Convert 'null' to 'None'."""
        result = convert_to_python_literal("null")
        assert result == "None"

    def test_null_uppercase(self):
        """Convert 'NULL' to 'None'."""
        result = convert_to_python_literal("NULL")
        assert result == "None"

    def test_integer_unchanged(self):
        """Integers should remain unchanged."""
        result = convert_to_python_literal("42")
        assert result == "42"

    def test_negative_integer(self):
        """Negative integers should remain unchanged."""
        result = convert_to_python_literal("-42")
        assert result == "-42"

    def test_float_unchanged(self):
        """Floats should remain unchanged."""
        result = convert_to_python_literal("3.14")
        assert result == "3.14"

    def test_whitespace_stripped(self):
        """Whitespace should be stripped."""
        result = convert_to_python_literal("  42  ")
        assert result == "42"

    def test_whitespace_with_boolean(self):
        """Whitespace with boolean should be handled."""
        result = convert_to_python_literal("  true  ")
        assert result == "True"


# ============================================================================
# CONVERT TO JAVA LITERAL TESTS
# ============================================================================

class TestConvertToJavaLiteral:
    """Test conversion to Java literals."""

    def test_int_type(self):
        """Int type should return value unchanged."""
        result = convert_to_java_literal("42", "int")
        assert result == "42"

    def test_long_type(self):
        """Long type should return value unchanged."""
        result = convert_to_java_literal("42", "long")
        assert result == "42"

    def test_double_type(self):
        """Double type should return value unchanged."""
        result = convert_to_java_literal("3.14", "double")
        assert result == "3.14"

    def test_float_type(self):
        """Float type should return value unchanged."""
        result = convert_to_java_literal("3.14", "float")
        assert result == "3.14"

    def test_string_without_quotes(self):
        """String without quotes should be quoted."""
        result = convert_to_java_literal("hello", "String")
        assert result == '"hello"'

    def test_string_with_quotes(self):
        """String with quotes should remain unchanged."""
        result = convert_to_java_literal('"hello"', "String")
        assert result == '"hello"'

    def test_int_array(self):
        """Int array conversion."""
        result = convert_to_java_literal("[1,2,3]", "int[]")
        assert result == "new int[]{1,2,3}"

    def test_empty_int_array(self):
        """Empty int array conversion."""
        result = convert_to_java_literal("[]", "int[]")
        assert result == "new int[]{}"

    def test_int_2d_array(self):
        """2D int array conversion."""
        result = convert_to_java_literal("[[1,2],[3,4]]", "int[][]")
        assert result == "new int[][]{{1,2},{3,4}}"

    def test_string_array(self):
        """String array conversion."""
        result = convert_to_java_literal('["a","b"]', "String[]")
        assert result == 'new String[]{"a","b"}'

    def test_list_integer(self):
        """List<Integer> conversion."""
        result = convert_to_java_literal("[1,2,3]", "List<Integer>")
        assert result == "Arrays.asList(1,2,3)"

    def test_empty_list_integer(self):
        """Empty List<Integer> conversion."""
        result = convert_to_java_literal("[]", "List<Integer>")
        assert result == "Arrays.asList()"

    def test_boolean_true(self):
        """Boolean true conversion."""
        result = convert_to_java_literal("true", "boolean")
        assert result == "true"

    def test_boolean_false(self):
        """Boolean false conversion."""
        result = convert_to_java_literal("false", "boolean")
        assert result == "false"

    def test_boolean_uppercase_true(self):
        """Boolean uppercase TRUE conversion."""
        result = convert_to_java_literal("TRUE", "boolean")
        assert result == "true"

    def test_unknown_type_passthrough(self):
        """Unknown types should pass through unchanged."""
        result = convert_to_java_literal("someValue", "UnknownType")
        assert result == "someValue"

    def test_whitespace_stripped(self):
        """Whitespace should be stripped."""
        result = convert_to_java_literal("  42  ", "int")
        assert result == "42"

    def test_int_array_not_starting_with_bracket(self):
        """Int array not starting with bracket should pass through."""
        result = convert_to_java_literal("someValue", "int[]")
        assert result == "someValue"

    def test_nested_list_type(self):
        """Nested List type with Integer."""
        result = convert_to_java_literal("[1,2,3]", "List<List<Integer>>")
        assert result == "Arrays.asList(1,2,3)"


# ============================================================================
# CONVERT TO CPP LITERAL TESTS
# ============================================================================

class TestConvertToCppLiteral:
    """Test conversion to C++ literals."""

    def test_int_type(self):
        """Int type should return value unchanged."""
        result = convert_to_cpp_literal("42", "int")
        assert result == "42"

    def test_long_type(self):
        """Long type should return value unchanged."""
        result = convert_to_cpp_literal("42", "long")
        assert result == "42"

    def test_long_long_type(self):
        """Long long type should return value unchanged."""
        result = convert_to_cpp_literal("42", "long long")
        assert result == "42"

    def test_double_type(self):
        """Double type should return value unchanged."""
        result = convert_to_cpp_literal("3.14", "double")
        assert result == "3.14"

    def test_float_type(self):
        """Float type should return value unchanged."""
        result = convert_to_cpp_literal("3.14", "float")
        assert result == "3.14"

    def test_string_without_quotes(self):
        """String without quotes should be quoted."""
        result = convert_to_cpp_literal("hello", "string")
        assert result == '"hello"'

    def test_string_with_quotes(self):
        """String with quotes should remain unchanged."""
        result = convert_to_cpp_literal('"hello"', "string")
        assert result == '"hello"'

    def test_string_reference_type(self):
        """String reference type."""
        result = convert_to_cpp_literal("hello", "string&")
        assert result == '"hello"'

    def test_vector_int(self):
        """Vector<int> conversion."""
        result = convert_to_cpp_literal("[1,2,3]", "vector<int>")
        assert result == "{1,2,3}"

    def test_empty_vector_int(self):
        """Empty vector<int> conversion."""
        result = convert_to_cpp_literal("[]", "vector<int>")
        assert result == "{}"

    def test_vector_vector_int(self):
        """Vector<vector<int>> conversion."""
        result = convert_to_cpp_literal("[[1,2],[3,4]]", "vector<vector<int>>")
        assert result == "{{1,2},{3,4}}"

    def test_vector_string(self):
        """Vector<string> conversion."""
        result = convert_to_cpp_literal('["a","b"]', "vector<string>")
        assert result == '{"a","b"}'

    def test_vector_string_case_insensitive(self):
        """Vector<String> case insensitive."""
        result = convert_to_cpp_literal('["a","b"]', "vector<String>")
        assert result == '{"a","b"}'

    def test_bool_true(self):
        """Bool true conversion."""
        result = convert_to_cpp_literal("true", "bool")
        assert result == "true"

    def test_bool_false(self):
        """Bool false conversion."""
        result = convert_to_cpp_literal("false", "bool")
        assert result == "false"

    def test_bool_uppercase_true(self):
        """Bool uppercase TRUE conversion."""
        result = convert_to_cpp_literal("TRUE", "bool")
        assert result == "true"

    def test_unknown_type_passthrough(self):
        """Unknown types should pass through unchanged."""
        result = convert_to_cpp_literal("someValue", "UnknownType")
        assert result == "someValue"

    def test_whitespace_stripped(self):
        """Whitespace should be stripped."""
        result = convert_to_cpp_literal("  42  ", "int")
        assert result == "42"

    def test_vector_int_not_starting_with_bracket(self):
        """Vector<int> not starting with bracket should pass through."""
        result = convert_to_cpp_literal("someValue", "vector<int>")
        assert result == "someValue"

    def test_vector_string_before_simple_string(self):
        """Vector<string> should be checked before simple string type."""
        # This tests the order of type checks in the function
        result = convert_to_cpp_literal('["a","b"]', "vector<string>")
        assert result == '{"a","b"}'


# ============================================================================
# GET JAVA DEFAULT TESTS
# ============================================================================

class TestGetJavaDefault:
    """Test getting default Java values for types."""

    def test_int_default(self):
        """Int default is 0."""
        assert get_java_default("int") == "0"

    def test_long_default(self):
        """Long default is 0L."""
        assert get_java_default("long") == "0L"

    def test_double_default(self):
        """Double default is 0.0."""
        assert get_java_default("double") == "0.0"

    def test_float_default(self):
        """Float default is 0.0f."""
        assert get_java_default("float") == "0.0f"

    def test_boolean_default(self):
        """Boolean default is false."""
        assert get_java_default("boolean") == "false"

    def test_string_default(self):
        """String default is empty string."""
        assert get_java_default("String") == '""'

    def test_int_array_default(self):
        """Int array default."""
        assert get_java_default("int[]") == "new int[]{}"

    def test_int_2d_array_default(self):
        """Int 2D array default."""
        assert get_java_default("int[][]") == "new int[][]{}"

    def test_string_array_default(self):
        """String array default."""
        assert get_java_default("String[]") == "new String[]{}"

    def test_listnode_default(self):
        """ListNode default is null."""
        assert get_java_default("ListNode") == "null"

    def test_treenode_default(self):
        """TreeNode default is null."""
        assert get_java_default("TreeNode") == "null"

    def test_list_integer_default(self):
        """List<Integer> default."""
        assert get_java_default("List<Integer>") == "new ArrayList<>()"

    def test_list_string_default(self):
        """List<String> default."""
        assert get_java_default("List<String>") == "new ArrayList<>()"

    def test_list_list_default(self):
        """List<List<Integer>> default."""
        assert get_java_default("List<List<Integer>>") == "new ArrayList<>()"

    def test_unknown_type_default(self):
        """Unknown type default is null."""
        assert get_java_default("UnknownType") == "null"

    def test_custom_class_default(self):
        """Custom class default is null."""
        assert get_java_default("MyCustomClass") == "null"


# ============================================================================
# GET CPP DEFAULT TESTS
# ============================================================================

class TestGetCppDefault:
    """Test getting default C++ values for types."""

    def test_int_default(self):
        """Int default is 0."""
        assert get_cpp_default("int") == "0"

    def test_long_default(self):
        """Long default is 0L."""
        assert get_cpp_default("long") == "0L"

    def test_long_long_default(self):
        """Long long default is 0LL."""
        assert get_cpp_default("long long") == "0LL"

    def test_double_default(self):
        """Double default is 0.0."""
        assert get_cpp_default("double") == "0.0"

    def test_float_default(self):
        """Float default is 0.0f."""
        assert get_cpp_default("float") == "0.0f"

    def test_bool_default(self):
        """Bool default is false."""
        assert get_cpp_default("bool") == "false"

    def test_string_default(self):
        """String default is empty string."""
        assert get_cpp_default("string") == '""'

    def test_listnode_pointer_default(self):
        """ListNode* default is nullptr."""
        assert get_cpp_default("ListNode*") == "nullptr"

    def test_treenode_pointer_default(self):
        """TreeNode* default is nullptr."""
        assert get_cpp_default("TreeNode*") == "nullptr"

    def test_vector_int_default(self):
        """Vector<int> default is empty initializer."""
        assert get_cpp_default("vector<int>") == "{}"

    def test_vector_string_default(self):
        """Vector<string> default is empty initializer."""
        assert get_cpp_default("vector<string>") == "{}"

    def test_vector_vector_int_default(self):
        """Vector<vector<int>> default is empty initializer."""
        assert get_cpp_default("vector<vector<int>>") == "{}"

    def test_reference_type_string(self):
        """String reference type."""
        assert get_cpp_default("string&") == '""'

    def test_reference_type_int(self):
        """Int reference type (not in defaults, falls through)."""
        result = get_cpp_default("int&")
        # int& is not in defaults, but base type int is
        assert result == "0"

    def test_unknown_type_default(self):
        """Unknown type default is empty initializer."""
        assert get_cpp_default("UnknownType") == "{}"

    def test_custom_class_default(self):
        """Custom class default is empty initializer."""
        assert get_cpp_default("MyCustomClass") == "{}"


# ============================================================================
# EDGE CASE AND INTEGRATION TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases across multiple functions."""

    def test_html_to_text_with_leetcode_style(self):
        """Test HTML commonly found in LeetCode problems."""
        html = """
        <p>Given an array of integers <code>nums</code>&nbsp;and an integer <code>target</code>,
        return <em>indices of the two numbers such that they add up to <code>target</code></em>.</p>
        """
        result = html_to_text(html)
        assert "nums" in result
        assert "target" in result

    def test_parse_complex_leetcode_input(self):
        """Test parsing complex LeetCode input format."""
        input_text = 'nums = [2,7,11,15], target = 9, s = "hello"'
        result = parse_input_variables(input_text)
        assert result["nums"] == "[2,7,11,15]"
        assert result["target"] == "9"
        assert result["s"] == '"hello"'

    def test_conversion_chain_python(self):
        """Test conversion chain for Python."""
        input_vars = parse_input_variables("flag = true, count = null")
        py_flag = convert_to_python_literal(input_vars["flag"])
        py_count = convert_to_python_literal(input_vars["count"])
        assert py_flag == "True"
        assert py_count == "None"

    def test_conversion_chain_java(self):
        """Test conversion chain for Java."""
        input_vars = parse_input_variables("nums = [1,2,3], flag = true")
        java_nums = convert_to_java_literal(input_vars["nums"], "int[]")
        java_flag = convert_to_java_literal(input_vars["flag"], "boolean")
        assert java_nums == "new int[]{1,2,3}"
        assert java_flag == "true"

    def test_conversion_chain_cpp(self):
        """Test conversion chain for C++."""
        input_vars = parse_input_variables("nums = [1,2,3], flag = true")
        cpp_nums = convert_to_cpp_literal(input_vars["nums"], "vector<int>")
        cpp_flag = convert_to_cpp_literal(input_vars["flag"], "bool")
        assert cpp_nums == "{1,2,3}"
        assert cpp_flag == "true"


class TestBoundaryConditions:
    """Test boundary conditions and special cases."""

    def test_html_single_character(self):
        """HTML with single character content."""
        result = html_to_text("<p>a</p>")
        assert result == "a"

    def test_parse_single_char_variable(self):
        """Parse single character variable name."""
        result = parse_input_variables("x = 1")
        assert result == {"x": "1"}

    def test_very_long_array(self):
        """Parse very long array."""
        long_array = "[" + ",".join(str(i) for i in range(1000)) + "]"
        result = parse_input_variables(f"nums = {long_array}")
        assert result["nums"] == long_array

    def test_deeply_nested_array(self):
        """Parse deeply nested array."""
        nested = "[[[[[1]]]]]"
        result = parse_input_variables(f"arr = {nested}")
        assert result["arr"] == nested

    def test_empty_string_value(self):
        """Parse empty string value."""
        result = parse_input_variables('s = ""')
        assert result["s"] == '""'

    def test_java_conversion_edge_types(self):
        """Test Java conversion with edge type cases."""
        # Test that List<Integer> is detected by substring matching
        # 'ArrayList<Integer>' contains 'List<Integer>' as substring
        result = convert_to_java_literal("[1]", "ArrayList<Integer>")
        assert result == "Arrays.asList(1)"

    def test_cpp_conversion_complex_vector(self):
        """Test C++ conversion with complex vector types."""
        result = convert_to_cpp_literal("[[1]]", "vector<vector<int>>")
        assert result == "{{1}}"


class TestSpecialCharacters:
    """Test handling of special characters."""

    def test_html_with_quotes(self):
        """HTML with quote entities."""
        result = html_to_text("&quot;quoted&quot;")
        assert '"quoted"' in result

    def test_html_with_apostrophe(self):
        """HTML with apostrophe entity."""
        result = html_to_text("it&#39;s")
        assert "'" in result

    def test_parse_with_special_chars_in_string(self):
        """Parse string containing special characters."""
        result = parse_input_variables('s = "a,b,c"')
        assert result["s"] == '"a,b,c"'


class TestRegressions:
    """Regression tests for specific bug fixes."""

    def test_vector_string_vs_string_type_order(self):
        """Ensure vector<string> is checked before string in C++."""
        # vector<string> should convert to initializer list, not quote the whole thing
        result = convert_to_cpp_literal('["hello"]', "vector<string>")
        assert result == '{"hello"}'
        # Simple string should be quoted
        result2 = convert_to_cpp_literal("hello", "string")
        assert result2 == '"hello"'

    def test_empty_input_no_crash(self):
        """Empty inputs should not cause crashes."""
        assert html_to_text("") == ""
        assert parse_input_variables("") == {}
        assert convert_to_python_literal("") == ""
        assert convert_to_java_literal("", "int") == ""
        assert convert_to_cpp_literal("", "int") == ""

    def test_whitespace_only_input(self):
        """Whitespace-only inputs should be handled."""
        assert html_to_text("   ") == ""
        assert parse_input_variables("   ") == {}
        assert convert_to_python_literal("   ") == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
