"""Tests for the ReviewSchedule dataclass."""

from datetime import date, timedelta

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.review_schedule import ReviewSchedule


def _schedule(**overrides) -> ReviewSchedule:
    base = dict(
        problem_id=1,
        next_review_date=date.today(),
        interval_days=1,
        ease_factor=2.5,
        repetitions=0,
    )
    base.update(overrides)
    return ReviewSchedule(**base)


# --------------------------------------------------------------------------- #
# __post_init__ enum coercion                                                 #
# --------------------------------------------------------------------------- #

def test_string_difficulty_is_coerced_to_enum():
    s = _schedule(difficulty="Medium")
    assert s.difficulty is ProblemDifficulty.MEDIUM


def test_string_language_is_coerced_to_enum():
    s = _schedule(language="java")
    assert s.language is CodeLanguage.JAVA


def test_enum_difficulty_passes_through():
    s = _schedule(difficulty=ProblemDifficulty.HARD)
    assert s.difficulty is ProblemDifficulty.HARD


def test_default_difficulty_is_none_sentinel():
    s = _schedule()
    assert s.difficulty is ProblemDifficulty.NONE


def test_default_language_is_unknown_sentinel():
    """Joined fields default to sentinel so callers can detect a no-JOIN query."""
    s = _schedule()
    assert s.language is CodeLanguage.UNKNOWN


# --------------------------------------------------------------------------- #
# days_until_due / is_overdue / is_due_today / is_due                         #
# --------------------------------------------------------------------------- #

def test_days_until_due_today_is_zero():
    s = _schedule(next_review_date=date.today())
    assert s.days_until_due == 0


def test_days_until_due_future_is_positive():
    s = _schedule(next_review_date=date.today() + timedelta(days=5))
    assert s.days_until_due == 5


def test_days_until_due_past_is_negative():
    s = _schedule(next_review_date=date.today() - timedelta(days=3))
    assert s.days_until_due == -3


def test_is_overdue_only_true_when_past():
    assert _schedule(next_review_date=date.today() - timedelta(days=1)).is_overdue
    assert not _schedule(next_review_date=date.today()).is_overdue
    assert not _schedule(next_review_date=date.today() + timedelta(days=1)).is_overdue


def test_is_due_today_only_true_today():
    assert _schedule(next_review_date=date.today()).is_due_today
    assert not _schedule(next_review_date=date.today() - timedelta(days=1)).is_due_today
    assert not _schedule(next_review_date=date.today() + timedelta(days=1)).is_due_today


def test_is_due_covers_today_and_overdue():
    assert _schedule(next_review_date=date.today()).is_due()
    assert _schedule(next_review_date=date.today() - timedelta(days=2)).is_due()
    assert not _schedule(next_review_date=date.today() + timedelta(days=1)).is_due()


# --------------------------------------------------------------------------- #
# from_row                                                                    #
# --------------------------------------------------------------------------- #

def _row(**overrides) -> dict:
    """Build a reviews-row dict (no JOIN columns) with sensible defaults."""
    base = {
        "problem_id": 7,
        "next_review_date": "2025-06-01",
        "interval_days": 4,
        "ease_factor": 2.6,
        "repetitions": 2,
    }
    base.update(overrides)
    return base


def test_from_row_minimal_no_join():
    s = ReviewSchedule.from_row(_row())
    assert s.problem_id == 7
    assert s.next_review_date == date(2025, 6, 1)
    assert s.interval_days == 4
    assert s.ease_factor == 2.6
    assert s.repetitions == 2
    # JOIN columns absent -> defaults
    assert s.problem_num is None
    assert s.source == "leetcode"
    assert s.title == ""
    assert s.difficulty is ProblemDifficulty.NONE
    assert s.language is CodeLanguage.UNKNOWN
    assert s.file_path is None


def test_from_row_with_joined_columns():
    s = ReviewSchedule.from_row(_row(
        problem_num="1",
        source="leetcode",
        title="Two Sum",
        difficulty="Easy",
        language="python3",
        file_path="problems/0001-two-sum/python3/v001/solution.py",
    ))
    assert s.problem_num == 1
    assert s.title == "Two Sum"
    assert s.difficulty is ProblemDifficulty.EASY
    assert s.language is CodeLanguage.PYTHON
    assert s.file_path.endswith("solution.py")


def test_from_row_accepts_date_object_for_next_review_date():
    s = ReviewSchedule.from_row(_row(next_review_date=date(2025, 7, 4)))
    assert s.next_review_date == date(2025, 7, 4)
