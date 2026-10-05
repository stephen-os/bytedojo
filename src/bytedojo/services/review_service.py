"""
Review service - manage spaced repetition reviews.

Owns the §9 status/schedule state machine on the schedule side: the
apply_pass / apply_fail / apply_skip transitions are what `test` and
`grade` call after recording an outcome, while complete_review handles
an explicit `dojo review complete --easy/--good/--hard`.

All interval arithmetic lives in core/scheduler.py (pure SM-2, §8);
this service only loads state, applies a transition, and persists.

Reviews live on the `problems` table FK — one row per problem
(you're reviewing the problem, not a specific attempt).
"""

import random
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Optional

from bytedojo.core import scheduler
from bytedojo.core.logger import get_logger
from bytedojo.core.models.review_schedule import ReviewSchedule
from bytedojo.core.models.review_stats import ReviewStats
from bytedojo.core.repository import Repository
from bytedojo.core.scheduler import Quality, ScheduleState
from bytedojo.core.settings import SettingsManager


class ReviewQuality(str, Enum):
    """How well the user remembered a problem during review."""

    HARD = "hard"  # struggled — lapse: interval resets, ease drops
    GOOD = "good"  # recalled with effort — standard SM-2 step
    EASY = "easy"  # recalled effortlessly — ease grows

    @property
    def sm2(self) -> Quality:
        """The scheduler quality this CLI grade maps to."""
        return {
            ReviewQuality.HARD: Quality.HARD,
            ReviewQuality.GOOD: Quality.GOOD,
            ReviewQuality.EASY: Quality.EASY,
        }[self]


@dataclass
class ScheduleEffect:
    """What a §9 transition did to a problem's schedule (for display)."""

    action: str  # created|advanced|lapsed|removed|none
    interval_days: Optional[int] = None
    next_review_date: Optional[date] = None


@dataclass
class ReviewCompletionResult:
    """Outcome of completing a review."""

    problem_db_id: int
    quality: Optional[ReviewQuality] = None
    previous_interval: Optional[int] = None
    next_interval: Optional[int] = None
    previous_ease: Optional[float] = None
    next_ease: Optional[float] = None
    previous_repetitions: Optional[int] = None
    next_repetitions: Optional[int] = None
    next_review_date: Optional[date] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def failed(self) -> bool:
        return self.error is not None


@dataclass
class ReviewActionResult:
    """
    Outcome of a non-completion review action (add / snooze / remove).

    `action` is one of "add", "snooze", "remove". `interval_days` and
    `next_review_date` are populated when relevant for display.
    """

    problem_db_id: int
    action: str
    interval_days: Optional[int] = None
    next_review_date: Optional[date] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def failed(self) -> bool:
        return self.error is not None


class ReviewService:
    """Spaced repetition review management with SM-2-style scheduling."""

    def __init__(self):
        self.logger = get_logger()

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_due_reviews(
        self,
        repo: Repository,
        *,
        include_future: bool = False,
    ) -> List[ReviewSchedule]:
        """All reviews due today (or all if `include_future=True`)."""
        with repo.session() as s:
            return s.reviews.due(include_future=include_future)

    def get_due_count(self, repo: Repository) -> int:
        with repo.session() as s:
            return len(s.reviews.due())

    def pick_random_due(self, repo: Repository) -> Optional[ReviewSchedule]:
        """Random selection from the due-today set, or None if caught up."""
        with repo.session() as s:
            due = s.reviews.due()
        return random.choice(due) if due else None

    def get_stats(self, repo: Repository) -> ReviewStats:
        with repo.session() as s:
            return s.reviews.stats()

    def get_review_frequency(self, repo: Repository) -> int:
        """The configured base interval in days (settings.json)."""
        return _base_days(repo)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def initial_schedule(
        self,
        repo: Repository,
        problem_db_id: int,
        *,
        days: Optional[int] = None,
    ) -> int:
        """
        Start (or reset) a review track via scheduler.initial().

        `days` overrides the configured base interval (used by
        `dojo review add --days N`). Returns the scheduled interval.
        """
        interval = days if days is not None else _base_days(repo)
        with repo.session() as s:
            state = scheduler.initial(interval)
            self._persist(s, problem_db_id, state)
        self.logger.debug(
            f"review_service: initial schedule for problem_db_id={problem_db_id} "
            f"at {state.interval_days} days"
        )
        return state.interval_days

    # ------------------------------------------------------------------
    # §9 state-machine transitions (called by test/grade after an outcome)
    # ------------------------------------------------------------------

    def apply_pass(self, repo: Repository, problem_db_id: int) -> ScheduleEffect:
        """A pass (test pass or `grade --pass`).

        No track → create one; due → advance (quality GOOD); scheduled
        but not yet due → leave alone (early practice doesn't thrash the
        schedule).
        """
        base = _base_days(repo)
        with repo.session() as s:
            existing = s.reviews.get(problem_db_id)

            if existing is None:
                state = scheduler.initial(base)
                self._persist(s, problem_db_id, state)
                return self._effect("created", state)

            if existing.is_due():
                state = scheduler.review(_to_state(existing), Quality.GOOD, base)
                self._persist(s, problem_db_id, state)
                return self._effect("advanced", state)

        return ScheduleEffect(action="none")

    def apply_fail(self, repo: Repository, problem_db_id: int) -> ScheduleEffect:
        """A fail/error (test failure or `grade --fail`) — a lapse if scheduled."""
        base = _base_days(repo)
        with repo.session() as s:
            existing = s.reviews.get(problem_db_id)
            if existing is None:
                return ScheduleEffect(action="none")
            state = scheduler.review(_to_state(existing), Quality.FAIL, base)
            self._persist(s, problem_db_id, state)
        return self._effect("lapsed", state)

    def apply_skip(self, repo: Repository, problem_db_id: int) -> ScheduleEffect:
        """A `grade --skip` — the problem is set aside: drop its track."""
        with repo.session() as s:
            removed = s.reviews.delete(problem_db_id)
        return ScheduleEffect(action="removed" if removed else "none")

    def _persist(self, s, problem_db_id: int, state: ScheduleState) -> None:
        s.reviews.upsert(
            problem_db_id,
            interval_days=state.interval_days,
            ease_factor=state.ease,
            repetitions=state.reps,
            due=state.due,
        )

    @staticmethod
    def _effect(action: str, state: ScheduleState) -> ScheduleEffect:
        return ScheduleEffect(
            action=action,
            interval_days=state.interval_days,
            next_review_date=state.due,
        )

    def add_review(
        self,
        repo: Repository,
        problem_db_id: int,
        *,
        days: Optional[int] = None,
    ) -> ReviewActionResult:
        """
        Manually queue a problem for review.

        Errors if a review track already exists — `dojo review snooze` is
        the right tool to push out an existing review, or `remove` first
        to reset.
        """
        with repo.session() as s:
            if s.reviews.get(problem_db_id) is not None:
                return ReviewActionResult(
                    problem_db_id=problem_db_id,
                    action="add",
                    error=(
                        "Already in review queue. Use `dojo review snooze` "
                        "to delay, or `dojo review remove` to reset."
                    ),
                )

        interval = self.initial_schedule(repo, problem_db_id, days=days)
        with repo.session() as s:
            row = s.reviews.get(problem_db_id)
        return ReviewActionResult(
            problem_db_id=problem_db_id,
            action="add",
            interval_days=interval,
            next_review_date=row.next_review_date if row else None,
        )

    def snooze_review(
        self,
        repo: Repository,
        problem_db_id: int,
        *,
        days: int = 1,
    ) -> ReviewActionResult:
        """
        Push `next_review_date` out without touching SRS state.

        Errors if no track exists for this problem.
        """
        with repo.session() as s:
            if s.reviews.get(problem_db_id) is None:
                return ReviewActionResult(
                    problem_db_id=problem_db_id,
                    action="snooze",
                    error="No review scheduled for this problem.",
                )
            s.reviews.snooze(problem_db_id, days)
            row = s.reviews.get(problem_db_id)

        self.logger.debug(
            f"review_service: snoozed problem_db_id={problem_db_id} by {days} days"
        )
        return ReviewActionResult(
            problem_db_id=problem_db_id,
            action="snooze",
            interval_days=days,
            next_review_date=row.next_review_date if row else None,
        )

    def remove_review(
        self,
        repo: Repository,
        problem_db_id: int,
    ) -> ReviewActionResult:
        """Drop the review track for a problem. Errors if no track exists."""
        with repo.session() as s:
            if s.reviews.get(problem_db_id) is None:
                return ReviewActionResult(
                    problem_db_id=problem_db_id,
                    action="remove",
                    error="No review scheduled for this problem.",
                )
            s.reviews.delete(problem_db_id)

        self.logger.debug(
            f"review_service: removed problem_db_id={problem_db_id} from review queue"
        )
        return ReviewActionResult(problem_db_id=problem_db_id, action="remove")

    def complete_review(
        self,
        repo: Repository,
        problem_db_id: int,
        quality: ReviewQuality,
    ) -> ReviewCompletionResult:
        """
        Apply an SM-2 update to a problem's review state and persist.

        Errors if the problem has no review row yet — `dojo grade --pass`
        (or R3's `dojo review add`) must run first to create the track.
        """
        with repo.session() as s:
            existing = s.reviews.get(problem_db_id)
            if existing is None:
                return ReviewCompletionResult(
                    problem_db_id=problem_db_id,
                    quality=quality,
                    error=(
                        "No review scheduled for this problem yet. "
                        "Use `dojo grade <id> --pass` to start a review track."
                    ),
                )

            state = scheduler.review(_to_state(existing), quality.sm2, _base_days(repo))
            self._persist(s, problem_db_id, state)

        self.logger.debug(
            f"review_service: completed problem_db_id={problem_db_id} "
            f"quality={quality.value} "
            f"interval {existing.interval_days}->{state.interval_days} "
            f"ease {existing.ease_factor:.2f}->{state.ease:.2f} "
            f"reps {existing.repetitions}->{state.reps}"
        )

        return ReviewCompletionResult(
            problem_db_id=problem_db_id,
            quality=quality,
            previous_interval=existing.interval_days,
            next_interval=state.interval_days,
            previous_ease=existing.ease_factor,
            next_ease=state.ease,
            previous_repetitions=existing.repetitions,
            next_repetitions=state.reps,
            next_review_date=state.due,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def format_due_date(review_date: date) -> str:
        """Human-readable due-date label (Today / Tomorrow / In N days / overdue)."""
        today = date.today()
        delta = (review_date - today).days
        if delta < 0:
            return f"{abs(delta)} days overdue"
        if delta == 0:
            return "Today"
        if delta == 1:
            return "Tomorrow"
        if delta < 7:
            return f"In {delta} days"
        return review_date.strftime("%Y-%m-%d")


def _base_days(repo: Repository) -> int:
    """The configured SM-2 base interval (§8 base_days)."""
    return SettingsManager(repo.dojo_dir).load().review_frequency_days


def _to_state(row: ReviewSchedule) -> ScheduleState:
    """Lift a persisted review row into the scheduler's pure state."""
    return ScheduleState(
        reps=row.repetitions,
        ease=row.ease_factor,
        interval_days=row.interval_days,
        due=row.next_review_date,
    )
