"""Tests for ReviewService."""

from datetime import date, timedelta

import pytest

from bytedojo.services.review_service import (
    ReviewActionResult,
    ReviewCompletionResult,
    ReviewQuality,
    ReviewService,
    _apply_quality,
)


# --------------------------------------------------------------------------- #
# ReviewQuality                                                               #
# --------------------------------------------------------------------------- #

def test_review_quality_values():
    assert ReviewQuality.HARD.value == "hard"
    assert ReviewQuality.GOOD.value == "good"
    assert ReviewQuality.EASY.value == "easy"


# --------------------------------------------------------------------------- #
# Result dataclasses                                                          #
# --------------------------------------------------------------------------- #

def test_completion_result_success_when_no_error():
    r = ReviewCompletionResult(problem_db_id=1, quality=ReviewQuality.GOOD)
    assert r.success and not r.failed


def test_completion_result_failed_when_error_set():
    r = ReviewCompletionResult(problem_db_id=1, error="x")
    assert r.failed and not r.success


def test_action_result_success_failed():
    assert ReviewActionResult(problem_db_id=1, action="add").success
    assert ReviewActionResult(problem_db_id=1, action="add", error="x").failed


# --------------------------------------------------------------------------- #
# _apply_quality — pure SM-2 step                                             #
# --------------------------------------------------------------------------- #

def test_apply_quality_hard_resets_interval_decreases_ease():
    """HARD always reverts to 1 day and pushes ease down (clamped at MIN)."""
    interval, ease, reps = _apply_quality(
        ReviewQuality.HARD, current_interval=12, current_ease=2.5, repetitions=3,
    )
    assert interval == 1
    assert ease == pytest.approx(2.3, abs=1e-6)   # 2.5 + (-0.2)
    assert reps == 0


def test_apply_quality_hard_clamps_ease_at_min():
    """Ease floor is 1.3 — HARD can't drive it below."""
    _, ease, _ = _apply_quality(
        ReviewQuality.HARD, current_interval=4, current_ease=1.4, repetitions=2,
    )
    assert ease == pytest.approx(1.3, abs=1e-6)


def test_apply_quality_good_first_review_keeps_interval():
    """With repetitions=0, first GOOD keeps current_interval (no ease multiply)."""
    interval, ease, reps = _apply_quality(
        ReviewQuality.GOOD, current_interval=7, current_ease=2.5, repetitions=0,
    )
    assert interval == 7
    assert ease == 2.5     # GOOD doesn't change ease
    assert reps == 1


def test_apply_quality_good_mid_track_multiplies_by_ease():
    """With repetitions >= 1, interval = round(current * ease)."""
    interval, _, reps = _apply_quality(
        ReviewQuality.GOOD, current_interval=10, current_ease=2.5, repetitions=1,
    )
    assert interval == 25   # round(10 * 2.5)
    assert reps == 2


def test_apply_quality_easy_bumps_ease_and_extends_interval():
    """EASY: extra 1.3× bonus on top of the GOOD interval; ease += 0.15."""
    interval, ease, reps = _apply_quality(
        ReviewQuality.EASY, current_interval=10, current_ease=2.0, repetitions=1,
    )
    # GOOD baseline: round(10 * 2.0) = 20.  EASY bonus: round(20 * 1.3) = 26.
    assert interval == 26
    assert ease == pytest.approx(2.15, abs=1e-6)
    assert reps == 2


def test_apply_quality_easy_clamps_ease_at_max():
    """Ease ceiling is 3.0."""
    _, ease, _ = _apply_quality(
        ReviewQuality.EASY, current_interval=10, current_ease=2.95, repetitions=1,
    )
    assert ease == pytest.approx(3.0, abs=1e-6)


def test_apply_quality_good_clamps_interval_at_one():
    """A degenerate current_interval=0 still yields at least 1 day."""
    interval, _, _ = _apply_quality(
        ReviewQuality.GOOD, current_interval=0, current_ease=2.5, repetitions=2,
    )
    assert interval >= 1


# --------------------------------------------------------------------------- #
# initial_schedule                                                            #
# --------------------------------------------------------------------------- #

def test_initial_schedule_uses_config_default(repo, registered_problem):
    interval = ReviewService().initial_schedule(repo, registered_problem.id)
    assert interval == 7    # default review_frequency_days


def test_initial_schedule_with_explicit_days(repo, registered_problem):
    interval = ReviewService().initial_schedule(
        repo, registered_problem.id, days=14,
    )
    assert interval == 14


def test_initial_schedule_writes_review_row(repo, registered_problem):
    ReviewService().initial_schedule(repo, registered_problem.id, days=5)
    with repo.open_db() as db:
        row = db.get_review(registered_problem.id)
    assert row is not None
    assert row.interval_days == 5


# --------------------------------------------------------------------------- #
# add_review                                                                  #
# --------------------------------------------------------------------------- #

def test_add_review_happy_path(repo, registered_problem):
    result = ReviewService().add_review(repo, registered_problem.id, days=3)
    assert result.success
    assert result.action == "add"
    assert result.interval_days == 3
    assert result.next_review_date is not None


def test_add_review_errors_when_already_scheduled(repo, registered_problem):
    """Add cannot stomp an existing track."""
    svc = ReviewService()
    svc.add_review(repo, registered_problem.id)
    result = svc.add_review(repo, registered_problem.id)

    assert result.failed
    assert "already in review queue" in result.error.lower()


# --------------------------------------------------------------------------- #
# snooze_review                                                               #
# --------------------------------------------------------------------------- #

def test_snooze_review_pushes_date_out(repo, registered_problem):
    svc = ReviewService()
    svc.add_review(repo, registered_problem.id, days=1)

    result = svc.snooze_review(repo, registered_problem.id, days=5)
    assert result.success
    assert result.next_review_date == date.today() + timedelta(days=5)


def test_snooze_review_errors_when_no_track(repo, registered_problem):
    result = ReviewService().snooze_review(repo, registered_problem.id)
    assert result.failed
    assert "no review" in result.error.lower()


# --------------------------------------------------------------------------- #
# remove_review                                                               #
# --------------------------------------------------------------------------- #

def test_remove_review_drops_the_track(repo, registered_problem):
    svc = ReviewService()
    svc.add_review(repo, registered_problem.id)

    result = svc.remove_review(repo, registered_problem.id)
    assert result.success
    with repo.open_db() as db:
        assert db.get_review(registered_problem.id) is None


def test_remove_review_errors_when_no_track(repo, registered_problem):
    result = ReviewService().remove_review(repo, registered_problem.id)
    assert result.failed
    assert "no review" in result.error.lower()


# --------------------------------------------------------------------------- #
# complete_review                                                             #
# --------------------------------------------------------------------------- #

def test_complete_review_applies_sm2_and_records(repo, registered_problem):
    """End-to-end persistence path; SM-2 math is exercised by _apply_quality tests."""
    svc = ReviewService()
    svc.initial_schedule(repo, registered_problem.id, days=2)

    result = svc.complete_review(repo, registered_problem.id, ReviewQuality.GOOD)
    assert result.success
    assert result.previous_interval == 2
    # schedule_review starts a fresh track at repetitions=1, so the first
    # complete_review bumps to 2. The exact bookkeeping is documented in
    # core/database.schedule_review; here we only confirm the result struct
    # carries before/after values, persists, and computes a next date.
    assert result.next_repetitions == result.previous_repetitions + 1
    assert result.next_review_date is not None


def test_complete_review_errors_with_no_track(repo, registered_problem):
    result = ReviewService().complete_review(
        repo, registered_problem.id, ReviewQuality.GOOD,
    )
    assert result.failed
    assert "no review scheduled" in result.error.lower()


# --------------------------------------------------------------------------- #
# Reads (get_due_reviews / pick_random_due / stats / frequency)               #
# --------------------------------------------------------------------------- #

def test_get_due_reviews_returns_due_today(repo, registered_problem):
    ReviewService().initial_schedule(repo, registered_problem.id, days=0)
    due = ReviewService().get_due_reviews(repo)
    assert len(due) == 1
    assert due[0].problem_id == registered_problem.id


def test_get_due_count(repo, registered_problem):
    ReviewService().initial_schedule(repo, registered_problem.id, days=0)
    assert ReviewService().get_due_count(repo) == 1


def test_pick_random_due_returns_none_when_caught_up(repo):
    assert ReviewService().pick_random_due(repo) is None


def test_pick_random_due_returns_a_due_problem(repo, registered_problem):
    ReviewService().initial_schedule(repo, registered_problem.id, days=0)
    picked = ReviewService().pick_random_due(repo)
    assert picked is not None
    assert picked.problem_id == registered_problem.id


def test_get_stats_empty_repo(repo):
    stats = ReviewService().get_stats(repo)
    assert stats.due_today == 0
    assert stats.total_in_review == 0


def test_get_review_frequency_default(repo):
    """Fresh repo: configured default is 7."""
    assert ReviewService().get_review_frequency(repo) == 7


# --------------------------------------------------------------------------- #
# format_due_date — pure presentation logic                                   #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("delta_days, expected", [
    (0,   "Today"),
    (1,   "Tomorrow"),
    (3,   "In 3 days"),
    (6,   "In 6 days"),
])
def test_format_due_date_near_term(delta_days, expected):
    when = date.today() + timedelta(days=delta_days)
    assert ReviewService.format_due_date(when) == expected


def test_format_due_date_past_shows_overdue():
    when = date.today() - timedelta(days=3)
    assert "3 days overdue" in ReviewService.format_due_date(when)


def test_format_due_date_far_future_shows_iso_date():
    when = date.today() + timedelta(days=30)
    label = ReviewService.format_due_date(when)
    assert label == when.strftime("%Y-%m-%d")
