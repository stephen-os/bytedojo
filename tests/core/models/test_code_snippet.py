"""Tests for the CodeSnippet dataclass."""

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet


# --------------------------------------------------------------------------- #
# __post_init__ coercion                                                      #
# --------------------------------------------------------------------------- #

def test_string_lang_is_coerced_to_enum():
    """Construction from raw JSON: lang arrives as a string and gets typed."""
    snippet = CodeSnippet(lang="java", code="class Solution {}")
    assert snippet.lang is CodeLanguage.JAVA


def test_enum_lang_passes_through():
    snippet = CodeSnippet(lang=CodeLanguage.CPP, code="class Solution {};")
    assert snippet.lang is CodeLanguage.CPP


def test_unknown_lang_string_becomes_unknown_enum():
    snippet = CodeSnippet(lang="brainfuck", code="++++.")
    assert snippet.lang is CodeLanguage.UNKNOWN


# --------------------------------------------------------------------------- #
# __str__                                                                     #
# --------------------------------------------------------------------------- #

def test_str_returns_code_verbatim():
    body = "def solve(): pass"
    snippet = CodeSnippet(lang=CodeLanguage.PYTHON, code=body)
    assert str(snippet) == body
