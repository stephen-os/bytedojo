"""Tests for the DataStructure enum."""

import pytest

from bytedojo.core.models.data_structure import DataStructure


# --------------------------------------------------------------------------- #
# from_string                                                                 #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("ARRAY",              DataStructure.ARRAY),
    ("array",              DataStructure.ARRAY),      # .upper() normalises case
    ("Matrix",             DataStructure.MATRIX),
    ("LINKED_LIST",        DataStructure.LINKED_LIST),
    ("DOUBLY_LINKED_LIST", DataStructure.DOUBLY_LINKED_LIST),
    ("BINARY_TREE",        DataStructure.BINARY_TREE),
    ("GRAPH",              DataStructure.GRAPH),
    ("HASH_MAP",           DataStructure.HASH_MAP),
    ("HEAP",               DataStructure.HEAP),
])
def test_from_string_known(raw, expected):
    assert DataStructure.from_string(raw) is expected


@pytest.mark.parametrize("raw", ["", None])
def test_from_string_empty_returns_none(raw):
    assert DataStructure.from_string(raw) is None


@pytest.mark.parametrize("raw", ["INT32", "nonsense", "LIST", "TREE"])
def test_from_string_unrecognized_returns_none(raw):
    """
    None is the "not a data structure" signal that lets Signature fall through
    to Primitive. Note INT32 lands here — it is a Primitive, not a structure.
    """
    assert DataStructure.from_string(raw) is None


# --------------------------------------------------------------------------- #
# Direct construction                                                         #
# --------------------------------------------------------------------------- #

def test_calling_the_enum_with_a_bad_value_raises():
    """
    `_missing_` returns None here, which Enum turns into ValueError.

    This is the opposite of Primitive, which absorbs bad values into UNKNOWN.
    Call from_string when a miss should be recoverable.
    """
    with pytest.raises(ValueError):
        DataStructure("NOPE")


def test_members_compare_equal_to_their_string_value():
    """DataStructure subclasses str, so it interoperates with raw JSON values."""
    assert DataStructure.LINKED_LIST == "LINKED_LIST"


# --------------------------------------------------------------------------- #
# __str__ / __repr__                                                          #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("member, label", [
    (DataStructure.ARRAY,       "ARRAY"),
    (DataStructure.LINKED_LIST, "LINKED_LIST"),
    (DataStructure.BINARY_TREE, "BINARY_TREE"),
])
def test_str_is_the_canonical_name(member, label):
    assert str(member) == label


def test_repr_uses_enum_name():
    assert repr(DataStructure.ARRAY) == "DataStructure.ARRAY"
