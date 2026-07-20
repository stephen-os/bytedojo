"""Tests for the Primitive enum."""

import pytest

from bytedojo.core.models.primitive import Primitive


# --------------------------------------------------------------------------- #
# from_string                                                                 #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("INT32",   Primitive.INT32),
    ("int32",   Primitive.INT32),        # .upper() normalises case
    ("Int64",   Primitive.INT64),
    ("FLOAT64", Primitive.FLOAT64),
    ("BOOL",    Primitive.BOOL),
    ("CHAR",    Primitive.CHAR),
    ("STRING",  Primitive.STRING),
    ("VOID",    Primitive.VOID),
])
def test_from_string_known(raw, expected):
    assert Primitive.from_string(raw) is expected


@pytest.mark.parametrize("raw", ["", None])
def test_from_string_empty_returns_unknown(raw):
    assert Primitive.from_string(raw) is Primitive.UNKNOWN


@pytest.mark.parametrize("raw", ["INT32_ARRAY", "ARRAY", "nonsense", "int"])
def test_from_string_unrecognized_returns_unknown(raw):
    """
    `_missing_` collapses anything unrecognized to UNKNOWN rather than raising.

    This is why a stale or misspelled type in data/problems/*.json produces a
    wrong stub instead of an error — INT32_ARRAY is the pre-Signature spelling
    and silently degrades.
    """
    assert Primitive.from_string(raw) is Primitive.UNKNOWN


# --------------------------------------------------------------------------- #
# Direct construction                                                         #
# --------------------------------------------------------------------------- #

def test_calling_the_enum_with_a_bad_value_returns_unknown():
    """Unlike DataStructure, Primitive(...) never raises — `_missing_` absorbs it."""
    assert Primitive("NOPE") is Primitive.UNKNOWN


def test_members_compare_equal_to_their_string_value():
    """Primitive subclasses str, so it interoperates with raw JSON values."""
    assert Primitive.INT32 == "INT32"


# --------------------------------------------------------------------------- #
# __str__ / __repr__                                                          #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("member, label", [
    (Primitive.INT32,   "INT32"),
    (Primitive.STRING,  "STRING"),
    (Primitive.VOID,    "VOID"),
    (Primitive.UNKNOWN, "UNKNOWN"),
])
def test_str_is_the_canonical_name(member, label):
    assert str(member) == label


def test_repr_uses_enum_name():
    assert repr(Primitive.INT32) == "Primitive.INT32"
