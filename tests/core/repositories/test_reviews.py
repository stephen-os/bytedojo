"""Tests for ReviewsRepository."""

from datetime import date, timedelta

import pytest

from bytedojo.core.repositories import ProblemsRepository, ReviewsRepository

from tests.core.repositories.conftest import make_problem


@pytest.fixture
def problem_db_id(conn) -> int:
    problems = ProblemsRepository(conn)
    problems.register(make_problem(), source="leetcode", language="python3")
    return problems.get("leetcode", 1).id


def _repo(conn) -> ReviewsRepository:
    return ReviewsRepository(conn)


def test_upsert_inserts_then_get(conn, problem_db_id):
    repo = _repo(conn)
    repo.upsert(problem_db_id, interval_days=5, ease_factor=2.5, repetitions=1)
    review = repo.get(problem_db_id)
    assert review is not None
    assert review.interval_days == 5
    assert review.repetitions == 1
    assert review.next_review_date == date.today() + timedelta(days=5)
    # Joined problem metadata comes through
    assert review.title == "Two Sum"
    assert review.problem_num == 1


def test_upsert_overwrites_state(conn, problem_db_id):
    repo = _repo(conn)
    repo.upsert(problem_db_id, interval_days=3, ease_factor=2.5, repetitions=1)
    repo.upsert(problem_db_id, interval_days=14, ease_factor=2.65, repetitions=4)
    review = repo.get(problem_db_id)
    assert review.interval_days == 14
    assert review.ease_factor == pytest.approx(2.65)
    assert review.repetitions == 4


def test_upsert_with_explicit_due_date(conn, problem_db_id):
    repo = _repo(conn)
    due = date.today() + timedelta(days=42)
    repo.upsert(problem_db_id, interval_days=7, ease_factor=2.5, repetitions=1, due=due)
    assert repo.get(problem_db_id).next_review_date == due


def test_get_returns_none_when_no_track(conn, problem_db_id):
    assert _repo(conn).get(problem_db_id) is None


def test_snooze_pushes_date_only(conn, problem_db_id):
    repo = _repo(conn)
    repo.upsert(problem_db_id, interval_days=1, ease_factor=2.5, repetitions=1)
    assert repo.snooze(problem_db_id, days=5) is True
    review = repo.get(problem_db_id)
    assert review.next_review_date == date.today() + timedelta(days=5)
    assert review.interval_days == 1  # SM-2 state untouched


def test_snooze_returns_false_when_no_row(conn, problem_db_id):
    assert _repo(conn).snooze(problem_db_id, days=5) is False


def test_delete(conn, problem_db_id):
    repo = _repo(conn)
    repo.upsert(problem_db_id, interval_days=1, ease_factor=2.5, repetitions=1)
    assert repo.delete(problem_db_id) is True
    assert repo.get(problem_db_id) is None


def test_delete_returns_false_when_no_row(conn, problem_db_id):
    assert _repo(conn).delete(problem_db_id) is False


def test_due_today_only_vs_include_future(conn, problem_db_id):
    repo = _repo(conn)
    repo.upsert(problem_db_id, interval_days=10, ease_factor=2.5, repetitions=1)
    assert repo.due() == []
    assert len(repo.due(include_future=True)) == 1


def test_due_includes_today_and_overdue(conn, problem_db_id):
    repo = _repo(conn)
    repo.upsert(problem_db_id, interval_days=0, ease_factor=2.5, repetitions=1)
    assert len(repo.due()) == 1


def test_stats_counts(conn, problem_db_id):
    repo = _repo(conn)
    repo.upsert(problem_db_id, interval_days=0, ease_factor=2.5, repetitions=1)
    stats = repo.stats()
    assert stats.due_today == 1
    assert stats.due_this_week == 1
    assert stats.total_in_review == 1
