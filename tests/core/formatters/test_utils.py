"""Tests for shared formatter utilities (utils.py)."""

import pytest

from bytedojo.core.formatters.utils import (
    convert_to_python_literal,
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
