"""Tests for ProblemDifficulty enum."""

import pytest

from bytedojo.core.models.problem_difficulty import ProblemDifficulty


# --------------------------------------------------------------------------- #
# from_string                                                                 #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("Easy",   ProblemDifficulty.EASY),
    ("easy",   ProblemDifficulty.EASY),
    ("EASY",   ProblemDifficulty.EASY),       # .capitalize() handles upper
    ("Medium", ProblemDifficulty.MEDIUM),
    ("medium", ProblemDifficulty.MEDIUM),
    ("Hard",   ProblemDifficulty.HARD),
    ("hard",   ProblemDifficulty.HARD),
])
def test_from_string_known(raw, expected):
    assert ProblemDifficulty.from_string(raw) is expected


@pytest.mark.parametrize("raw", ["", None])
def test_from_string_empty_returns_none(raw):
    assert ProblemDifficulty.from_string(raw) is ProblemDifficulty.NONE


@pytest.mark.parametrize("raw", ["impossible", "trivial", "1", "10/10"])
def test_from_string_unknown_falls_back(raw):
    """`_missing_` collapses unrecognized values to NONE."""
    assert ProblemDifficulty.from_string(raw) is ProblemDifficulty.NONE


# --------------------------------------------------------------------------- #
# all                                                                         #
# --------------------------------------------------------------------------- #

def test_all_excludes_none_sentinel():
    diffs = ProblemDifficulty.all()
    assert ProblemDifficulty.NONE not in diffs
    assert set(diffs) == {
        ProblemDifficulty.EASY,
        ProblemDifficulty.MEDIUM,
        ProblemDifficulty.HARD,
    }


# --------------------------------------------------------------------------- #
# __str__ / __repr__                                                          #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("diff, label", [
    (ProblemDifficulty.NONE,   "None"),
    (ProblemDifficulty.EASY,   "Easy"),
    (ProblemDifficulty.MEDIUM, "Medium"),
    (ProblemDifficulty.HARD,   "Hard"),
])
def test_str_returns_value(diff, label):
    assert str(diff) == label


def test_repr_uses_enum_name():
    assert repr(ProblemDifficulty.EASY) == "ProblemDifficulty.EASY"
