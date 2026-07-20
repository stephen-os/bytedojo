"""Tests for `dojo review` (group + every subcommand)."""

from datetime import date, timedelta

import pytest
from click.testing import CliRunner

from bytedojo.commands.subcommands.review import review
from bytedojo.core.models.review_schedule import ReviewSchedule
from bytedojo.core.models.review_stats import ReviewStats
from bytedojo.services.review_service import (
    ReviewActionResult,
    ReviewCompletionResult,
    ReviewQuality,
)


# --------------------------------------------------------------------------- #
# Default subcommand: show due reviews                                        #
# --------------------------------------------------------------------------- #

def test_review_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(review, [])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


def test_review_default_no_dues_caught_up_message(repo, monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.get_due_reviews",
        lambda self, repo, *, include_future=False: [],
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, [])
    assert result.exit_code == 0
    assert "No problems due for review" in result.output


def test_review_default_all_flag_no_scheduled_message(repo, monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.get_due_reviews",
        lambda self, repo, *, include_future=False: [],
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["--all"])
    assert result.exit_code == 0
    assert "No problems scheduled for review yet" in result.output


def test_review_default_renders_due_reviews(repo, monkeypatch):
    """A due review row appears with its problem title + due-date label."""
    review_row = ReviewSchedule(
        problem_id=1,
        next_review_date=date.today(),
        interval_days=7, ease_factor=2.5, repetitions=1,
        problem_num=42, title="Two Sum", source="leetcode", language="python3",
    )
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.get_due_reviews",
        lambda self, repo, *, include_future=False: [review_row],
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, [])
    assert result.exit_code == 0
    assert "Problems Due for Review" in result.output
    assert "Two Sum" in result.output
    assert "42" in result.output      # display_id from problem_num


# --------------------------------------------------------------------------- #
# pick subcommand                                                             #
# --------------------------------------------------------------------------- #

def test_review_pick_caught_up(repo, monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.pick_random_due",
        lambda self, repo: None,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["pick"])
    assert result.exit_code == 0
    assert "No problems due for review" in result.output


def test_review_pick_renders_chosen_problem(repo, monkeypatch):
    chosen = ReviewSchedule(
        problem_id=1,
        next_review_date=date.today() + timedelta(days=0),
        interval_days=14, ease_factor=2.6, repetitions=3,
        problem_num=42, title="Two Sum", source="leetcode",
        language="python3", file_path="problems/0042-x/python3/v001/solution.py",
    )
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.pick_random_due",
        lambda self, repo: chosen,
    )
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.get_due_count",
        lambda self, repo: 5,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["pick"])
    assert result.exit_code == 0
    assert "Review This Problem" in result.output
    assert "Two Sum" in result.output
    assert "14 days" in result.output
    assert "ease 2.60" in result.output
    assert "dojo review complete 42 --python --good" in result.output


# --------------------------------------------------------------------------- #
# complete subcommand                                                         #
# --------------------------------------------------------------------------- #

def test_review_complete_requires_quality_flag(repo, registered_problem, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["complete", "1"])
    assert result.exit_code != 0
    assert "--easy" in result.output and "--good" in result.output and "--hard" in result.output


@pytest.fixture
def stub_complete(monkeypatch):
    state = {"calls": []}

    def fake_complete(self, repo, problem_db_id, quality):
        state["calls"].append({"problem_db_id": problem_db_id, "quality": quality})
        return ReviewCompletionResult(
            problem_db_id=problem_db_id, quality=quality,
            previous_interval=7, next_interval=18,
            previous_ease=2.5, next_ease=2.5,
            previous_repetitions=1, next_repetitions=2,
            next_review_date=date.today() + timedelta(days=18),
        )

    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.complete_review",
        fake_complete,
    )
    return state


@pytest.mark.parametrize("flag, expected", [
    ("--easy", ReviewQuality.EASY),
    ("--good", ReviewQuality.GOOD),
    ("--hard", ReviewQuality.HARD),
])
def test_review_complete_quality_flags(
    repo, registered_problem, monkeypatch, stub_complete, flag, expected,
):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["complete", "1", flag])
    assert result.exit_code == 0, result.output
    assert stub_complete["calls"][0]["quality"] is expected


def test_review_complete_renders_before_after(repo, registered_problem, monkeypatch, stub_complete):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["complete", "1", "--good"])
    assert "Review Complete — GOOD" in result.output
    assert "7 days" in result.output
    assert "18 days" in result.output


def test_review_complete_service_error_raises(repo, registered_problem, monkeypatch):
    """ReviewCompletionResult.error set -> ClickException."""
    def fake_complete(self, repo, problem_db_id, quality):
        return ReviewCompletionResult(
            problem_db_id=problem_db_id, quality=quality,
            error="No review scheduled for this problem yet.",
        )

    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.complete_review",
        fake_complete,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["complete", "1", "--good"])
    assert result.exit_code != 0
    assert "No review scheduled" in result.output


# --------------------------------------------------------------------------- #
# add subcommand                                                              #
# --------------------------------------------------------------------------- #

def test_review_add_dispatches_with_default_days(repo, registered_problem, monkeypatch):
    state = {"calls": []}

    def fake_add(self, repo, problem_db_id, *, days=None):
        state["calls"].append({"problem_db_id": problem_db_id, "days": days})
        return ReviewActionResult(
            problem_db_id=problem_db_id, action="add",
            interval_days=7, next_review_date=date.today() + timedelta(days=7),
        )

    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.add_review", fake_add,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["add", "1"])
    assert result.exit_code == 0
    assert state["calls"][0]["days"] is None    # defer to configured default


def test_review_add_propagates_days_flag(repo, registered_problem, monkeypatch):
    state = {"calls": []}

    def fake_add(self, repo, problem_db_id, *, days=None):
        state["calls"].append({"days": days})
        return ReviewActionResult(
            problem_db_id=problem_db_id, action="add",
            interval_days=days, next_review_date=date.today() + timedelta(days=days or 0),
        )

    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.add_review", fake_add,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["add", "1", "--days", "3"])
    assert result.exit_code == 0
    assert state["calls"][0]["days"] == 3
    assert "Added to Review Queue" in result.output


def test_review_add_service_error_raises(repo, registered_problem, monkeypatch):
    def fake_add(self, repo, problem_db_id, *, days=None):
        return ReviewActionResult(
            problem_db_id=problem_db_id, action="add",
            error="Already in review queue.",
        )

    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.add_review", fake_add,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["add", "1"])
    assert result.exit_code != 0
    assert "Already in review queue" in result.output


# --------------------------------------------------------------------------- #
# snooze subcommand                                                           #
# --------------------------------------------------------------------------- #

def test_review_snooze_default_days_is_one(repo, registered_problem, monkeypatch):
    state = {"calls": []}

    def fake_snooze(self, repo, problem_db_id, *, days=1):
        state["calls"].append({"days": days})
        return ReviewActionResult(
            problem_db_id=problem_db_id, action="snooze",
            interval_days=days, next_review_date=date.today() + timedelta(days=days),
        )

    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.snooze_review", fake_snooze,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["snooze", "1"])
    assert result.exit_code == 0
    assert state["calls"][0]["days"] == 1
    assert "Review Snoozed" in result.output


def test_review_snooze_with_days(repo, registered_problem, monkeypatch):
    state = {"calls": []}

    def fake_snooze(self, repo, problem_db_id, *, days=1):
        state["calls"].append({"days": days})
        return ReviewActionResult(
            problem_db_id=problem_db_id, action="snooze",
            interval_days=days, next_review_date=date.today() + timedelta(days=days),
        )

    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.snooze_review", fake_snooze,
    )
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(review, ["snooze", "1", "--days", "7"])
    assert state["calls"][0]["days"] == 7


def test_review_snooze_service_error_raises(repo, registered_problem, monkeypatch):
    def fake_snooze(self, repo, problem_db_id, *, days=1):
        return ReviewActionResult(
            problem_db_id=problem_db_id, action="snooze",
            error="No review scheduled for this problem.",
        )

    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.snooze_review", fake_snooze,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["snooze", "1"])
    assert result.exit_code != 0
    assert "No review scheduled" in result.output


# --------------------------------------------------------------------------- #
# remove subcommand                                                           #
# --------------------------------------------------------------------------- #

def test_review_remove_happy_path(repo, registered_problem, monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.remove_review",
        lambda self, repo, problem_db_id: ReviewActionResult(
            problem_db_id=problem_db_id, action="remove",
        ),
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["remove", "1"])
    assert result.exit_code == 0
    assert "Removed from Queue" in result.output


def test_review_remove_service_error_raises(repo, registered_problem, monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.remove_review",
        lambda self, repo, problem_db_id: ReviewActionResult(
            problem_db_id=problem_db_id, action="remove",
            error="No review scheduled for this problem.",
        ),
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["remove", "1"])
    assert result.exit_code != 0
    assert "No review scheduled" in result.output


# --------------------------------------------------------------------------- #
# stats subcommand                                                            #
# --------------------------------------------------------------------------- #

def test_review_stats_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(review, ["stats"])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


def test_review_stats_renders_counts(repo, monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.get_stats",
        lambda self, repo: ReviewStats(due_today=2, due_this_week=5, total_in_review=12),
    )
    monkeypatch.setattr(
        "bytedojo.services.review_service.ReviewService.get_review_frequency",
        lambda self, repo: 10,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(review, ["stats"])
    assert result.exit_code == 0
    assert "Review Statistics" in result.output
    assert "10 days" in result.output
    assert "Due Today" in result.output
    assert "2" in result.output
    assert "5" in result.output
    assert "12" in result.output
