"""Tests for CanonicalType enum."""

import pytest

from bytedojo.core.models.canonical_type import CanonicalType


# --------------------------------------------------------------------------- #
# from_string                                                                 #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    # Primitives
    ("INT32",       CanonicalType.INT32),
    ("int32",       CanonicalType.INT32),         # .upper() normalises case
    ("INT64",       CanonicalType.INT64),
    ("FLOAT64",     CanonicalType.FLOAT64),
    ("BOOL",        CanonicalType.BOOL),
    ("CHAR",        CanonicalType.CHAR),
    ("STRING",      CanonicalType.STRING),
    ("VOID",        CanonicalType.VOID),
    # 1-D arrays
    ("INT32_ARRAY", CanonicalType.INT32_ARRAY),
    ("CHAR_ARRAY",  CanonicalType.CHAR_ARRAY),
    ("STRING_ARRAY", CanonicalType.STRING_ARRAY),
    # 2-D arrays
    ("INT32_MATRIX", CanonicalType.INT32_MATRIX),
    ("CHAR_MATRIX",  CanonicalType.CHAR_MATRIX),
    ("STRING_MATRIX", CanonicalType.STRING_MATRIX),
    # Reference types
    ("TREE_NODE",        CanonicalType.TREE_NODE),
    ("LIST_NODE",        CanonicalType.LIST_NODE),
    ("LIST_NODE_ARRAY",  CanonicalType.LIST_NODE_ARRAY),
])
def test_from_string_known(raw, expected):
    assert CanonicalType.from_string(raw) is expected


@pytest.mark.parametrize("raw", ["", None])
def test_from_string_empty_returns_unknown(raw):
    assert CanonicalType.from_string(raw) is CanonicalType.UNKNOWN


@pytest.mark.parametrize("raw", ["int", "long", "INT16", "DOUBLE", "STRING_3D"])
def test_from_string_unknown_falls_back(raw):
    """`_missing_` collapses unrecognized types to UNKNOWN."""
    assert CanonicalType.from_string(raw) is CanonicalType.UNKNOWN


# --------------------------------------------------------------------------- #
# __str__ / __repr__                                                          #
# --------------------------------------------------------------------------- #

def test_str_returns_value():
    assert str(CanonicalType.INT32) == "INT32"
    assert str(CanonicalType.CHAR_MATRIX) == "CHAR_MATRIX"


def test_repr_uses_enum_name():
    assert repr(CanonicalType.INT32) == "CanonicalType.INT32"
