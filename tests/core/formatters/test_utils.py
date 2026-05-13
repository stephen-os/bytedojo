"""Tests for shared formatter utilities (utils.py)."""

import pytest

from bytedojo.core.formatters.utils import (
    convert_to_cpp_literal,
    convert_to_java_literal,
    convert_to_python_literal,
    get_cpp_default,
    get_java_default,
    html_to_text,
    parse_input_variables,
)


# --------------------------------------------------------------------------- #
# html_to_text                                                                #
# --------------------------------------------------------------------------- #

def test_html_to_text_strips_tags():
    assert html_to_text("<p>hello <em>world</em></p>") == "hello world"


def test_html_to_text_unescapes_entities():
    assert html_to_text("a &lt; b &amp;&amp; c &gt; d") == "a < b && c > d"


def test_html_to_text_collapses_blank_lines():
    """Multiple blank lines collapse to a single empty line between blocks."""
    assert html_to_text("para 1\n\n\n\npara 2") == "para 1\n\npara 2"


@pytest.mark.parametrize("raw", ["", None])
def test_html_to_text_empty_input_returns_empty(raw):
    assert html_to_text(raw) == ""


def test_html_to_text_strips_outer_whitespace():
    assert html_to_text("   <p>x</p>   ") == "x"


# --------------------------------------------------------------------------- #
# parse_input_variables                                                       #
# --------------------------------------------------------------------------- #

def test_parse_input_variables_two_vars():
    assert parse_input_variables("nums = [2,7,11,15], target = 9") == {
        "nums": "[2,7,11,15]",
        "target": "9",
    }


def test_parse_input_variables_single_var():
    assert parse_input_variables("n = 42") == {"n": "42"}


def test_parse_input_variables_string_value():
    assert parse_input_variables('s = "hello"') == {"s": '"hello"'}


def test_parse_input_variables_no_vars_returns_empty_dict():
    assert parse_input_variables("just a sentence") == {}


# --------------------------------------------------------------------------- #
# convert_to_python_literal                                                   #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("[1,2,3]",       "[1,2,3]"),       # array passes through
    ('"hello"',       '"hello"'),       # quoted string passes through
    ("'hi'",          "'hi'"),
    ("true",          "True"),
    ("True",          "True"),
    ("false",         "False"),
    ("null",          "None"),
    ("NULL",          "None"),
    ("42",            "42"),
    ("3.14",          "3.14"),
])
def test_convert_to_python_literal(raw, expected):
    assert convert_to_python_literal(raw) == expected


# --------------------------------------------------------------------------- #
# convert_to_java_literal                                                     #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, java_type, expected", [
    ("42",            "int",                 "42"),
    ("3.14",          "double",              "3.14"),
    ("hello",         "String",              '"hello"'),       # auto-quote
    ('"hello"',       "String",              '"hello"'),       # already quoted
    ("[1,2,3]",       "int[]",               "new int[]{1,2,3}"),
    ("[[1,2],[3]]",   "int[][]",             "new int[][]{{1,2},{3}}"),
    ('["a","b"]',     "String[]",            'new String[]{"a","b"}'),
    ("[1,2,3]",       "List<Integer>",       "Arrays.asList(1,2,3)"),
    ("True",          "boolean",             "true"),
    ("FALSE",         "boolean",             "false"),
])
def test_convert_to_java_literal(raw, java_type, expected):
    assert convert_to_java_literal(raw, java_type) == expected


# --------------------------------------------------------------------------- #
# convert_to_cpp_literal                                                      #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, cpp_type, expected", [
    ("42",            "int",                  "42"),
    ("3.14",          "double",               "3.14"),
    ("hello",         "string",               '"hello"'),
    ('"hello"',       "string",               '"hello"'),
    ("[1,2,3]",       "vector<int>",          "{1,2,3}"),
    ("[[1,2],[3]]",   "vector<vector<int>>",  "{{1,2},{3}}"),
    ('["a","b"]',     "vector<string>",       '{"a","b"}'),
    ("True",          "bool",                 "true"),
])
def test_convert_to_cpp_literal(raw, cpp_type, expected):
    assert convert_to_cpp_literal(raw, cpp_type) == expected


def test_convert_to_cpp_literal_distinguishes_string_from_vector_string():
    """Regression: 'string' must not match inside 'vector<string>'."""
    assert convert_to_cpp_literal("hello", "string") == '"hello"'
    assert convert_to_cpp_literal('["a"]', "vector<string>") == '{"a"}'


# --------------------------------------------------------------------------- #
# get_java_default                                                            #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("java_type, expected", [
    ("int",      "0"),
    ("long",     "0L"),
    ("double",   "0.0"),
    ("float",    "0.0f"),
    ("boolean",  "false"),
    ("String",   '""'),
    ("int[]",    "new int[]{}"),
    ("int[][]",  "new int[][]{}"),
    ("String[]", 'new String[]{}'),
    ("ListNode", "null"),
    ("TreeNode", "null"),
])
def test_get_java_default_known_types(java_type, expected):
    assert get_java_default(java_type) == expected


def test_get_java_default_list_type_returns_arraylist():
    assert get_java_default("List<Integer>") == "new ArrayList<>()"
    assert get_java_default("List<String>") == "new ArrayList<>()"


def test_get_java_default_unknown_type_falls_back_to_null():
    assert get_java_default("SomeCustomType") == "null"


# --------------------------------------------------------------------------- #
# get_cpp_default                                                             #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cpp_type, expected", [
    ("int",        "0"),
    ("long",       "0L"),
    ("long long",  "0LL"),
    ("double",     "0.0"),
    ("float",      "0.0f"),
    ("bool",       "false"),
    ("string",     '""'),
    ("ListNode*",  "nullptr"),
    ("TreeNode*",  "nullptr"),
])
def test_get_cpp_default_known_types(cpp_type, expected):
    assert get_cpp_default(cpp_type) == expected


def test_get_cpp_default_reference_strips_ampersand():
    """`int&` resolves the same as `int`."""
    assert get_cpp_default("int&") == "0"
    assert get_cpp_default("string&") == '""'


def test_get_cpp_default_vector_returns_braced_empty():
    assert get_cpp_default("vector<int>") == "{}"
    assert get_cpp_default("vector<vector<int>>") == "{}"


def test_get_cpp_default_unknown_type_falls_back_to_braced_empty():
    assert get_cpp_default("SomeCustomType") == "{}"
