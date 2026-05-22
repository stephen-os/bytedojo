"""
Review service - manage spaced repetition reviews.

Migrated from core/review_service.py and extended with a simplified SM-2
algorithm. The service now distinguishes two operations:

  - initial_schedule(): called once when a problem first enters the review
    track (e.g. on `dojo grade --pass`). Uses the configured fixed
    `review_frequency_days` as the starting interval.

  - complete_review(): called when the user reports back on a review,
    applies the SM-2 update (interval × ease for GOOD; ×1.3 bonus for
    EASY; reset to 1 for HARD), and persists the new state.

Reviews live on the `problems` table FK — one row per
(source, problem_id, language). Per-version review tracking is out of
scope for now (you're reviewing the problem, not a specific attempt).
"""

import random
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Optional

from bytedojo.core.logger import get_logger
from bytedojo.core.models.review_schedule import ReviewSchedule
from bytedojo.core.models.review_stats import ReviewStats
from bytedojo.core.repository import Repository


# SM-2 tunables — clamps prevent runaway ease factors.
_MIN_EASE = 1.3
_MAX_EASE = 3.0
_HARD_EASE_DELTA = -0.2
_EASY_EASE_DELTA = +0.15
_EASY_INTERVAL_BONUS = 1.3
_DEFAULT_INITIAL_EASE = 2.5


class ReviewQuality(str, Enum):
    """How well the user remembered a problem during review."""
    HARD = "hard"   # struggled — reset to 1 day, ease decreases
    GOOD = "good"   # recalled with effort — interval × ease
    EASY = "easy"   # recalled effortlessly — interval × ease × 1.3, ease grows


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
        with repo.open_db() as db:
            return db.get_due_reviews(include_future=include_future)

    def get_due_count(self, repo: Repository) -> int:
        with repo.open_db() as db:
            return len(db.get_due_reviews(include_future=False))

    def pick_random_due(self, repo: Repository) -> Optional[ReviewSchedule]:
        """Random selection from the due-today set, or None if caught up."""
        with repo.open_db() as db:
            due = db.get_due_reviews(include_future=False)
        return random.choice(due) if due else None

    def get_stats(self, repo: Repository) -> ReviewStats:
        with repo.open_db() as db:
            return db.get_review_stats()

    def get_review_frequency(self, repo: Repository) -> int:
        """The configured initial-interval setting (days)."""
        with repo.open_db() as db:
            return int(db.get_config('review_frequency_days', '7'))

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
        Start (or reset) a review track.

        Used on `dojo grade --pass` (days=None → configured base) and on
        `dojo review add` (days=N → caller-chosen initial interval).
        Subsequent SRS progression happens via complete_review().

        Returns the interval (days) that was scheduled.
        """
        with repo.open_db() as db:
            interval = days if days is not None else int(
                db.get_config('review_frequency_days', '7')
            )
            db.schedule_review(problem_db_id, interval)
        self.logger.debug(
            f"review_service: initial schedule for problem_db_id={problem_db_id} "
            f"at {interval} days"
        )
        return interval

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
        with repo.open_db() as db:
            if db.get_review(problem_db_id) is not None:
                return ReviewActionResult(
                    problem_db_id=problem_db_id,
                    action="add",
                    error=(
                        "Already in review queue. Use `dojo review snooze` "
                        "to delay, or `dojo review remove` to reset."
                    ),
                )

        interval = self.initial_schedule(repo, problem_db_id, days=days)
        with repo.open_db() as db:
            row = db.get_review(problem_db_id)
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
        with repo.open_db() as db:
            if db.get_review(problem_db_id) is None:
                return ReviewActionResult(
                    problem_db_id=problem_db_id,
                    action="snooze",
                    error="No review scheduled for this problem.",
                )
            db.snooze_review(problem_db_id, days)
            row = db.get_review(problem_db_id)

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
        with repo.open_db() as db:
            if db.get_review(problem_db_id) is None:
                return ReviewActionResult(
                    problem_db_id=problem_db_id,
                    action="remove",
                    error="No review scheduled for this problem.",
                )
            db.delete_review(problem_db_id)

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
        with repo.open_db() as db:
            existing = db.get_review(problem_db_id)
            if existing is None:
                return ReviewCompletionResult(
                    problem_db_id=problem_db_id,
                    quality=quality,
                    error=(
                        "No review scheduled for this problem yet. "
                        "Use `dojo grade <id> --pass` to start a review track."
                    ),
                )

            new_interval, new_ease, new_reps = _apply_quality(
                quality,
                current_interval=existing.interval_days,
                current_ease=existing.ease_factor,
                repetitions=existing.repetitions,
            )

            db.upsert_review(
                problem_db_id,
                interval_days=new_interval,
                ease_factor=new_ease,
                repetitions=new_reps,
            )
            updated = db.get_review(problem_db_id)

        self.logger.debug(
            f"review_service: completed problem_db_id={problem_db_id} "
            f"quality={quality.value} "
            f"interval {existing.interval_days}->{new_interval} "
            f"ease {existing.ease_factor:.2f}->{new_ease:.2f} "
            f"reps {existing.repetitions}->{new_reps}"
        )

        return ReviewCompletionResult(
            problem_db_id=problem_db_id,
            quality=quality,
            previous_interval=existing.interval_days,
            next_interval=new_interval,
            previous_ease=existing.ease_factor,
            next_ease=new_ease,
            previous_repetitions=existing.repetitions,
            next_repetitions=new_reps,
            next_review_date=updated.next_review_date if updated else None,
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


# ----------------------------------------------------------------------------
# SM-2 (simplified to 3 quality levels) — pure function so it's easy to test.
# ----------------------------------------------------------------------------

def _apply_quality(
    quality: ReviewQuality,
    *,
    current_interval: int,
    current_ease: float,
    repetitions: int,
) -> tuple[int, float, int]:
    """
    Return (next_interval, next_ease, next_repetitions) after applying a
    review of the given quality to the current state.

    HARD resets the track to a 1-day interval and decreases ease (the
    problem clearly isn't sticking).

    GOOD multiplies the current interval by ease — the canonical SM-2 step
    once we're past the initial learning phase.

    EASY adds an extra 1.3× bonus to the GOOD interval and bumps ease up,
    so well-known problems space out faster.
    """
    if quality == ReviewQuality.HARD:
        return 1, max(_MIN_EASE, current_ease + _HARD_EASE_DELTA), 0

    if repetitions <= 0:
        new_interval = max(1, current_interval)
    else:
        new_interval = max(1, round(current_interval * current_ease))

    if quality == ReviewQuality.EASY:
        new_interval = max(new_interval, round(new_interval * _EASY_INTERVAL_BONUS))
        new_ease = min(_MAX_EASE, current_ease + _EASY_EASE_DELTA)
    else:  # GOOD
        new_ease = current_ease

    return new_interval, new_ease, repetitions + 1
