"""Tests for the RegisteredProblem dataclass."""

from datetime import datetime

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.models.registered_problem import RegisteredProblem


def _row(**overrides) -> dict:
    """Build a problems-table row dict with sensible defaults."""
    base = {
        "id": 7,
        "source": "leetcode",
        "problem_id": "1",
        "language": "python3",
        "title": "Two Sum",
        "difficulty": "Easy",
        "description": "Given an array...",
        "file_path": "problems/0001-two-sum/python3/v001/solution.py",
        "status": "ungraded",
        "fetched_at": "2025-01-15T10:30:00",
        "last_graded": "2025-01-15T10:35:00",
        "notes": "clean pass on the second try",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# from_row roundtrip                                                          #
# --------------------------------------------------------------------------- #

def test_from_row_roundtrip():
    p = RegisteredProblem.from_row(_row())
    assert p.id == 7
    assert p.source == "leetcode"
    assert p.problem_id == 1
    assert p.language is CodeLanguage.PYTHON
    assert p.title == "Two Sum"
    assert p.difficulty is ProblemDifficulty.EASY
    assert p.description == "Given an array..."
    assert p.file_path == "problems/0001-two-sum/python3/v001/solution.py"
    assert p.status is ProblemStatus.UNGRADED
    assert p.fetched_at == datetime(2025, 1, 15, 10, 30, 0)
    assert p.last_graded == datetime(2025, 1, 15, 10, 35, 0)
    assert p.notes == "clean pass on the second try"


def test_from_row_coerces_problem_id_to_int():
    p = RegisteredProblem.from_row(_row(problem_id="42"))
    assert p.problem_id == 42
    assert isinstance(p.problem_id, int)


def test_from_row_with_no_last_graded():
    p = RegisteredProblem.from_row(_row(last_graded=None))
    assert p.last_graded is None


def test_from_row_accepts_datetime_for_last_graded():
    now = datetime(2025, 3, 1, 9, 0, 0)
    p = RegisteredProblem.from_row(_row(last_graded=now))
    assert p.last_graded == now


def test_from_row_status_routes_through_problem_status():
    """The status column maps to RegisteredProblem.status via ProblemStatus.from_string."""
    assert RegisteredProblem.from_row(_row(status="passed")).status is ProblemStatus.PASSED
    assert RegisteredProblem.from_row(_row(status="failed")).status is ProblemStatus.FAILED
    assert RegisteredProblem.from_row(_row(status="skipped")).status is ProblemStatus.SKIPPED
