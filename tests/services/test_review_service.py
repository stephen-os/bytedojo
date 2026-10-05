"""Tests for ReviewService."""

from datetime import date, timedelta

import pytest

from bytedojo.services.review_service import (
    ReviewActionResult,
    ReviewCompletionResult,
    ReviewQuality,
    ReviewService,
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
# ReviewQuality → scheduler quality mapping                                   #
# --------------------------------------------------------------------------- #


def test_review_quality_maps_to_sm2_grades():
    from bytedojo.core.scheduler import Quality

    assert ReviewQuality.HARD.sm2 is Quality.HARD
    assert ReviewQuality.GOOD.sm2 is Quality.GOOD
    assert ReviewQuality.EASY.sm2 is Quality.EASY


# --------------------------------------------------------------------------- #
# §9 transitions: apply_pass / apply_fail / apply_skip                        #
# --------------------------------------------------------------------------- #


def test_apply_pass_creates_track_when_none(repo, registered_problem):
    effect = ReviewService().apply_pass(repo, registered_problem.id)
    assert effect.action == "created"
    assert effect.interval_days == 7  # configured base
    with repo.session() as s:
        row = s.reviews.get(registered_problem.id)
    assert row is not None
    assert row.repetitions == 1


def test_apply_pass_advances_when_due(repo, registered_problem):
    svc = ReviewService()
    svc.initial_schedule(repo, registered_problem.id, days=0)  # due today

    effect = svc.apply_pass(repo, registered_problem.id)
    assert effect.action == "advanced"
    with repo.session() as s:
        row = s.reviews.get(registered_problem.id)
    assert row.repetitions == 2


def test_apply_pass_leaves_undue_schedule_alone(repo, registered_problem):
    """Early practice must not pull the review earlier or thrash state."""
    svc = ReviewService()
    svc.initial_schedule(repo, registered_problem.id, days=10)  # not due
    with repo.session() as s:
        before = s.reviews.get(registered_problem.id)

    effect = svc.apply_pass(repo, registered_problem.id)
    assert effect.action == "none"
    with repo.session() as s:
        after = s.reviews.get(registered_problem.id)
    assert after.next_review_date == before.next_review_date
    assert after.repetitions == before.repetitions


def test_apply_fail_lapses_scheduled_problem(repo, registered_problem):
    svc = ReviewService()
    svc.initial_schedule(repo, registered_problem.id, days=10)

    effect = svc.apply_fail(repo, registered_problem.id)
    assert effect.action == "lapsed"
    assert effect.interval_days == 1
    with repo.session() as s:
        row = s.reviews.get(registered_problem.id)
    assert row.repetitions == 0
    assert row.next_review_date == date.today() + timedelta(days=1)


def test_apply_fail_without_schedule_is_a_noop(repo, registered_problem):
    effect = ReviewService().apply_fail(repo, registered_problem.id)
    assert effect.action == "none"
    with repo.session() as s:
        assert s.reviews.get(registered_problem.id) is None


def test_apply_skip_removes_the_track(repo, registered_problem):
    svc = ReviewService()
    svc.initial_schedule(repo, registered_problem.id)

    effect = svc.apply_skip(repo, registered_problem.id)
    assert effect.action == "removed"
    with repo.session() as s:
        assert s.reviews.get(registered_problem.id) is None


def test_apply_skip_without_schedule_is_a_noop(repo, registered_problem):
    assert ReviewService().apply_skip(repo, registered_problem.id).action == "none"


# --------------------------------------------------------------------------- #
# initial_schedule                                                            #
# --------------------------------------------------------------------------- #


def test_initial_schedule_uses_config_default(repo, registered_problem):
    interval = ReviewService().initial_schedule(repo, registered_problem.id)
    assert interval == 7  # default review_frequency_days


def test_initial_schedule_with_explicit_days(repo, registered_problem):
    interval = ReviewService().initial_schedule(
        repo,
        registered_problem.id,
        days=14,
    )
    assert interval == 14


def test_initial_schedule_writes_review_row(repo, registered_problem):
    ReviewService().initial_schedule(repo, registered_problem.id, days=5)
    with repo.session() as s:
        row = s.reviews.get(registered_problem.id)
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
    with repo.session() as s:
        assert s.reviews.get(registered_problem.id) is None


def test_remove_review_errors_when_no_track(repo, registered_problem):
    result = ReviewService().remove_review(repo, registered_problem.id)
    assert result.failed
    assert "no review" in result.error.lower()


# --------------------------------------------------------------------------- #
# complete_review                                                             #
# --------------------------------------------------------------------------- #


def test_complete_review_applies_sm2_and_records(repo, registered_problem):
    """End-to-end persistence path; the SM-2 math itself is covered in
    tests/core/test_scheduler.py."""
    svc = ReviewService()
    svc.initial_schedule(repo, registered_problem.id, days=2)

    result = svc.complete_review(repo, registered_problem, ReviewQuality.GOOD)
    assert result.success
    assert result.previous_interval == 2
    assert result.next_repetitions == result.previous_repetitions + 1
    assert result.next_review_date is not None


def test_complete_review_errors_with_no_track(repo, registered_problem):
    result = ReviewService().complete_review(
        repo,
        registered_problem,
        ReviewQuality.GOOD,
    )
    assert result.failed
    assert "no review scheduled" in result.error.lower()


def test_complete_review_marks_problem_passed(repo, registered_problem):
    """§9: completing a review lands PASSED on both rows, even for --hard."""
    from bytedojo.core.models.problem_status import ProblemStatus

    with repo.session() as s:
        s.attempts.create("leetcode", 1, "python3")
    svc = ReviewService()
    svc.initial_schedule(repo, registered_problem.id, days=0)
    svc.apply_fail(repo, registered_problem.id)  # simulate an earlier lapse

    result = svc.complete_review(repo, registered_problem, ReviewQuality.HARD)
    assert result.success
    with repo.session() as s:
        assert s.problems.get("leetcode", 1).status is ProblemStatus.PASSED
        assert s.attempts.get("leetcode", 1, version=1).status is ProblemStatus.PASSED


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


@pytest.mark.parametrize(
    "delta_days, expected",
    [
        (0, "Today"),
        (1, "Tomorrow"),
        (3, "In 3 days"),
        (6, "In 6 days"),
    ],
)
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
