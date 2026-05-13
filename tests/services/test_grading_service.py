"""Tests for GradingService."""

import pytest

from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.services.grading_service import GradeResult, GradingService

from tests.services.conftest import insert_registered_problem


# --------------------------------------------------------------------------- #
# GradeResult                                                                 #
# --------------------------------------------------------------------------- #

def test_grade_result_success_when_no_error(registered_problem):
    r = GradeResult(problem=registered_problem, status="passed")
    assert r.success is True
    assert r.failed is False


def test_grade_result_failed_when_error_set(registered_problem):
    r = GradeResult(problem=registered_problem, error="boom")
    assert r.success is False
    assert r.failed is True


# --------------------------------------------------------------------------- #
# grade — validation                                                          #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("bad_status", [
    "nope", "ungraded", "unknown", "Pass", "PASSED", "", "complete",
])
def test_grade_rejects_invalid_status(repo, registered_problem, bad_status):
    """Anything outside passed / failed / skipped is rejected with an error."""
    result = GradingService().grade(repo, registered_problem, status=bad_status)
    assert result.failed
    assert "Invalid status" in result.error
    assert "passed" in result.error and "failed" in result.error and "skipped" in result.error


def test_grade_valid_statuses_match_problem_status_enum(repo, registered_problem):
    """The accepted vocabulary is exactly PASSED / FAILED / SKIPPED."""
    for status in ("passed", "failed", "skipped"):
        result = GradingService().grade(repo, registered_problem, status=status)
        assert result.success, f"{status} should be valid"


def test_grade_explicitly_rejects_ungraded(repo, registered_problem):
    """UNGRADED is a state, not a grade — must be rejected."""
    result = GradingService().grade(repo, registered_problem,
                                    status=ProblemStatus.UNGRADED.value)
    assert result.failed


# --------------------------------------------------------------------------- #
# grade — persistence + review scheduling                                     #
# --------------------------------------------------------------------------- #

def test_grade_passed_records_status_in_db(repo, registered_problem):
    GradingService().grade(repo, registered_problem, status="passed")
    with repo.open_db() as db:
        fresh = db.get_problem("leetcode", 1, "python3")
    assert fresh.status is ProblemStatus.PASSED


def test_grade_failed_records_status_in_db(repo, registered_problem):
    GradingService().grade(repo, registered_problem, status="failed")
    with repo.open_db() as db:
        fresh = db.get_problem("leetcode", 1, "python3")
    assert fresh.status is ProblemStatus.FAILED


def test_grade_passed_schedules_a_review(repo, registered_problem):
    result = GradingService().grade(repo, registered_problem, status="passed")
    assert result.success
    assert result.scheduled_review is True


def test_grade_failed_does_not_schedule_a_review(repo, registered_problem):
    result = GradingService().grade(repo, registered_problem, status="failed")
    assert result.success
    assert result.scheduled_review is False


def test_grade_skipped_does_not_schedule_a_review(repo, registered_problem):
    result = GradingService().grade(repo, registered_problem, status="skipped")
    assert result.success
    assert result.scheduled_review is False


def test_grade_records_notes(repo, registered_problem):
    result = GradingService().grade(
        repo, registered_problem, status="passed", notes="clean BFS",
    )
    assert result.notes == "clean BFS"


def test_grade_carries_review_frequency_from_config(repo, registered_problem):
    """The default review_frequency_days is exposed on the result."""
    result = GradingService().grade(repo, registered_problem, status="passed")
    assert result.review_frequency_days == 7    # default in fresh repo config


# --------------------------------------------------------------------------- #
# list_by_status / list_ungraded                                              #
# --------------------------------------------------------------------------- #

def test_list_by_status_returns_only_matching(repo, registered_problem):
    # Add a second problem and grade them differently.
    other = insert_registered_problem(repo, pid=2, slug="add-two-numbers",
                                      title="Add Two Numbers")
    GradingService().grade(repo, registered_problem, status="passed")
    GradingService().grade(repo, other, status="failed")

    passed = GradingService().list_by_status(repo, "passed")
    failed = GradingService().list_by_status(repo, "failed")

    assert [p.problem_id for p in passed] == [1]
    assert [p.problem_id for p in failed] == [2]


def test_list_ungraded_returns_only_ungraded(repo, registered_problem):
    # registered_problem starts ungraded by default.
    other = insert_registered_problem(repo, pid=2, slug="x", title="X")
    GradingService().grade(repo, other, status="passed")

    ungraded = GradingService().list_ungraded(repo)
    assert [p.problem_id for p in ungraded] == [1]
