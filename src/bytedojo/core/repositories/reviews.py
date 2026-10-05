"""
ReviewsRepository — persistence for the spaced-repetition schedule.

One row per problem (keyed by the problems table row id). The SM-2
arithmetic lives in core/scheduler.py; this class only stores and
retrieves schedule state.
"""

import sqlite3
from datetime import date, timedelta
from typing import List, Optional

from bytedojo.core.models.review_schedule import ReviewSchedule
from bytedojo.core.models.review_stats import ReviewStats

#: Columns selected for every schedule read — review state plus the
#: joined problem metadata ReviewSchedule displays.
_SELECT = """
    SELECT
        r.problem_id, r.next_review_date, r.interval_days, r.ease_factor, r.repetitions,
        p.problem_id as problem_num, p.source, p.title, p.difficulty, p.language, p.file_path
    FROM reviews r
    LEFT JOIN problems p ON r.problem_id = p.id
"""


class ReviewsRepository:
    """Raw-sqlite persistence for review schedules."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get(self, problem_db_id: int) -> Optional[ReviewSchedule]:
        """The schedule for a problem, or None if it has no track."""
        row = self._conn.execute(
            _SELECT + " WHERE r.problem_id = ?", (problem_db_id,)
        ).fetchone()
        return ReviewSchedule.from_row(dict(row)) if row else None

    def due(self, *, include_future: bool = False) -> List[ReviewSchedule]:
        """Schedules due today (or all, soonest first, when include_future)."""
        if include_future:
            rows = self._conn.execute(
                _SELECT + " ORDER BY r.next_review_date ASC"
            ).fetchall()
        else:
            rows = self._conn.execute(
                _SELECT
                + " WHERE r.next_review_date <= ? ORDER BY r.next_review_date ASC",
                (date.today().isoformat(),),
            ).fetchall()
        return [ReviewSchedule.from_row(dict(row)) for row in rows]

    def upsert(
        self,
        problem_db_id: int,
        *,
        interval_days: int,
        ease_factor: float,
        repetitions: int,
        due: Optional[date] = None,
    ) -> None:
        """Write the exact schedule state (due defaults to today+interval)."""
        next_review = (
            due if due is not None else date.today() + timedelta(days=interval_days)
        )
        self._conn.execute(
            """
            INSERT INTO reviews (problem_id, next_review_date, interval_days,
                                 ease_factor, repetitions)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(problem_id) DO UPDATE SET
                next_review_date = excluded.next_review_date,
                interval_days = excluded.interval_days,
                ease_factor = excluded.ease_factor,
                repetitions = excluded.repetitions
            """,
            (
                problem_db_id,
                next_review.isoformat(),
                interval_days,
                ease_factor,
                repetitions,
            ),
        )
        self._conn.commit()

    def snooze(self, problem_db_id: int, days: int) -> bool:
        """Push next_review_date to today+days, leaving SM-2 state alone."""
        cursor = self._conn.execute(
            "UPDATE reviews SET next_review_date = ? WHERE problem_id = ?",
            ((date.today() + timedelta(days=days)).isoformat(), problem_db_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def delete(self, problem_db_id: int) -> bool:
        """Drop the review track. Returns True if a row was deleted."""
        cursor = self._conn.execute(
            "DELETE FROM reviews WHERE problem_id = ?", (problem_db_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def stats(self) -> ReviewStats:
        """Due-today / due-this-week / total counts."""
        today = date.today()

        def _count_due(cutoff: date) -> int:
            return self._conn.execute(
                "SELECT COUNT(*) FROM reviews WHERE next_review_date <= ?",
                (cutoff.isoformat(),),
            ).fetchone()[0]

        total = self._conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        return ReviewStats(
            due_today=_count_due(today),
            due_this_week=_count_due(today + timedelta(days=7)),
            total_in_review=total,
        )
