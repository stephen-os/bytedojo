"""Tests for ProblemStatus enum."""

import pytest

from bytedojo.core.models.problem_status import ProblemStatus


# --------------------------------------------------------------------------- #
# from_string                                                                 #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("passed",   ProblemStatus.PASSED),
    ("PASSED",   ProblemStatus.PASSED),       # .lower() normalises case
    ("Failed",   ProblemStatus.FAILED),
    ("skipped",  ProblemStatus.SKIPPED),
    ("ungraded", ProblemStatus.UNGRADED),
])
def test_from_string_known(raw, expected):
    assert ProblemStatus.from_string(raw) is expected


@pytest.mark.parametrize("raw", ["", None])
def test_from_string_empty_returns_unknown(raw):
    assert ProblemStatus.from_string(raw) is ProblemStatus.UNKNOWN


@pytest.mark.parametrize("raw", ["untested", "complete", "wip"])
def test_from_string_unknown_falls_back(raw):
    """`_missing_` collapses unrecognized values to UNKNOWN."""
    assert ProblemStatus.from_string(raw) is ProblemStatus.UNKNOWN


# --------------------------------------------------------------------------- #
# all                                                                         #
# --------------------------------------------------------------------------- #

def test_all_excludes_unknown_sentinel():
    statuses = ProblemStatus.all()
    assert ProblemStatus.UNKNOWN not in statuses
    assert set(statuses) == {
        ProblemStatus.PASSED,
        ProblemStatus.FAILED,
        ProblemStatus.SKIPPED,
        ProblemStatus.UNGRADED,
    }


# --------------------------------------------------------------------------- #
# __str__ / __repr__                                                          #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("status, label", [
    (ProblemStatus.PASSED,   "Passed"),
    (ProblemStatus.FAILED,   "Failed"),
    (ProblemStatus.SKIPPED,  "Skipped"),
    (ProblemStatus.UNGRADED, "Ungraded"),
    (ProblemStatus.UNKNOWN,  "Unknown"),
])
def test_str_capitalizes_value(status, label):
    assert str(status) == label


def test_repr_uses_enum_name():
    assert repr(ProblemStatus.PASSED) == "ProblemStatus.PASSED"
