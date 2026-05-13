"""Tests for CodeLanguage enum."""

import pytest

from bytedojo.core.models.code_language import CodeLanguage


# --------------------------------------------------------------------------- #
# from_string                                                                 #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("python3", CodeLanguage.PYTHON),
    ("Python3", CodeLanguage.PYTHON),          # case-insensitive
    ("PYTHON3", CodeLanguage.PYTHON),
    ("java", CodeLanguage.JAVA),
    ("cpp", CodeLanguage.CPP),
    ("rust", CodeLanguage.RUST),
    ("golang", CodeLanguage.GO),
    ("javascript", CodeLanguage.JAVASCRIPT),
    ("typescript", CodeLanguage.TYPESCRIPT),
])
def test_from_string_known(raw, expected):
    assert CodeLanguage.from_string(raw) is expected


@pytest.mark.parametrize("raw", ["", None])
def test_from_string_empty_returns_unknown(raw):
    assert CodeLanguage.from_string(raw) is CodeLanguage.UNKNOWN


@pytest.mark.parametrize("raw", ["c#", "kotlin", "ruby", "unrecognized-language"])
def test_from_string_unknown_falls_back(raw):
    """`_missing_` collapses unrecognized values to UNKNOWN."""
    assert CodeLanguage.from_string(raw) is CodeLanguage.UNKNOWN


# --------------------------------------------------------------------------- #
# default                                                                     #
# --------------------------------------------------------------------------- #

def test_default_is_python():
    assert CodeLanguage.default() is CodeLanguage.PYTHON


# --------------------------------------------------------------------------- #
# extension                                                                   #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("lang, ext", [
    (CodeLanguage.PYTHON, ".py"),
    (CodeLanguage.JAVA, ".java"),
    (CodeLanguage.CPP, ".cpp"),
    (CodeLanguage.RUST, ".rs"),
    (CodeLanguage.GO, ".go"),
    (CodeLanguage.JAVASCRIPT, ".js"),
    (CodeLanguage.TYPESCRIPT, ".ts"),
])
def test_extension(lang, ext):
    assert lang.extension == ext


def test_extension_unknown_is_empty():
    assert CodeLanguage.UNKNOWN.extension == ""


# --------------------------------------------------------------------------- #
# __str__ / __repr__                                                          #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("lang, label", [
    (CodeLanguage.PYTHON, "Python"),
    (CodeLanguage.JAVA, "Java"),
    (CodeLanguage.CPP, "C++"),
    (CodeLanguage.GO, "Go"),
    (CodeLanguage.JAVASCRIPT, "JavaScript"),
    (CodeLanguage.TYPESCRIPT, "TypeScript"),
])
def test_str_uses_display_name(lang, label):
    assert str(lang) == label


def test_repr_uses_enum_name():
    assert repr(CodeLanguage.PYTHON) == "CodeLanguage.PYTHON"


# --------------------------------------------------------------------------- #
# Enum identity                                                               #
# --------------------------------------------------------------------------- #

def test_enum_is_str_subclass():
    """CodeLanguage(str, Enum) lets values compare to raw strings."""
    assert CodeLanguage.PYTHON == "python3"
    assert CodeLanguage.JAVA.value == "java"
