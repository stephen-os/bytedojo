"""Tests for ProblemTag enum."""

import pytest

from bytedojo.core.models.problem_tag import ProblemTag


# --------------------------------------------------------------------------- #
# from_string                                                                 #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("array",          ProblemTag.ARRAY),
    ("ARRAY",          ProblemTag.ARRAY),         # .lower() normalises case
    ("hash-table",     ProblemTag.HASH_TABLE),    # hyphenated slug preserved as value
    ("two-pointers",   ProblemTag.TWO_POINTERS),
    ("dynamic-programming", ProblemTag.DYNAMIC_PROGRAMMING),
    ("union-find",     ProblemTag.UNION_FIND),
])
def test_from_string_known(raw, expected):
    assert ProblemTag.from_string(raw) is expected


@pytest.mark.parametrize("raw", ["", None])
def test_from_string_empty_returns_unknown(raw):
    assert ProblemTag.from_string(raw) is ProblemTag.UNKNOWN


@pytest.mark.parametrize("raw", ["nonsense", "new-tag-leetcode-just-added"])
def test_from_string_unknown_falls_back(raw):
    """`_missing_` collapses unrecognized slugs to UNKNOWN."""
    assert ProblemTag.from_string(raw) is ProblemTag.UNKNOWN


# --------------------------------------------------------------------------- #
# all                                                                         #
# --------------------------------------------------------------------------- #

def test_all_excludes_unknown_sentinel():
    tags = ProblemTag.all()
    assert ProblemTag.UNKNOWN not in tags
    # Sanity: there should be many real tags.
    assert len(tags) > 30
    assert ProblemTag.ARRAY in tags
    assert ProblemTag.HASH_TABLE in tags


# --------------------------------------------------------------------------- #
# __str__ / __repr__                                                          #
# --------------------------------------------------------------------------- #

def test_str_returns_slug_verbatim():
    """`__str__` returns the LeetCode slug, hyphens included."""
    assert str(ProblemTag.HASH_TABLE) == "hash-table"
    assert str(ProblemTag.UNION_FIND) == "union-find"


def test_repr_uses_enum_name():
    assert repr(ProblemTag.ARRAY) == "ProblemTag.ARRAY"
