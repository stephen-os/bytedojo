"""Tests for the Attempt dataclass."""

from datetime import datetime

import pytest

from bytedojo.core.models.attempt import Attempt
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus


# --------------------------------------------------------------------------- #
# Construction defaults                                                       #
# --------------------------------------------------------------------------- #

def test_construct_with_defaults():
    a = Attempt(
        problem_id=1,
        language=CodeLanguage.PYTHON,
        version=1,
        status=ProblemStatus.UNGRADED,
        created_at=datetime(2025, 1, 1, 12, 0, 0),
    )
    assert a.run_count == 0
    assert a.notes == ""
    assert a.test_status is ProblemStatus.UNGRADED
    assert a.last_test_run is None
    assert a.test_output is None


# --------------------------------------------------------------------------- #
# get_version_string                                                          #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("version, expected", [
    (1, "v001"),
    (7, "v007"),
    (12, "v012"),
    (999, "v999"),
])
def test_get_version_string_zero_pads_to_three(version, expected):
    a = Attempt(
        problem_id=1, language=CodeLanguage.PYTHON, version=version,
        status=ProblemStatus.UNGRADED, created_at=datetime(2025, 1, 1),
    )
    assert a.get_version_string() == expected


# --------------------------------------------------------------------------- #
# from_row                                                                    #
# --------------------------------------------------------------------------- #

def _row(**overrides) -> dict:
    """Build a versioned_attempts row with sensible defaults."""
    base = {
        "problem_id": 1,
        "language": "python3",
        "version": 2,
        "status": "passed",
        "created_at": "2025-01-15T10:30:00",
        "run_count": 4,
        "notes": "first clean pass",
        "test_status": "passed",
        "last_test_run": "2025-01-15T10:35:00",
        "test_output": "Passed: 50/50",
    }
    base.update(overrides)
    return base


def test_from_row_roundtrip():
    row = _row()
    a = Attempt.from_row(row)
    assert a.problem_id == 1
    assert a.language is CodeLanguage.PYTHON
    assert a.version == 2
    assert a.status is ProblemStatus.PASSED
    assert a.created_at == datetime(2025, 1, 15, 10, 30, 0)
    assert a.run_count == 4
    assert a.notes == "first clean pass"
    assert a.test_status is ProblemStatus.PASSED
    assert a.last_test_run == datetime(2025, 1, 15, 10, 35, 0)
    assert a.test_output == "Passed: 50/50"


def test_from_row_handles_missing_optional_fields():
    """Optional fields drop to defaults; unknown language string -> UNKNOWN."""
    a = Attempt.from_row({
        "problem_id": 5,
        "language": "java",
        "version": 1,
        "status": "ungraded",
        "created_at": "2025-02-01T00:00:00",
    })
    assert a.run_count == 0
    assert a.notes == ""
    assert a.test_status is ProblemStatus.UNGRADED  # row.get(...) or "ungraded"
    assert a.last_test_run is None
    assert a.test_output is None


def test_from_row_accepts_datetime_for_last_test_run():
    """Sqlite drivers may already hand back a datetime object."""
    now = datetime(2025, 3, 1, 9, 0, 0)
    a = Attempt.from_row(_row(last_test_run=now))
    assert a.last_test_run == now


def test_from_row_treats_none_notes_as_empty_string():
    a = Attempt.from_row(_row(notes=None))
    assert a.notes == ""
