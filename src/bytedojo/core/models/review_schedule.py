"""
ReviewSchedule - Spaced repetition review scheduling for a problem.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class ReviewSchedule:
    """A scheduled review for a problem with optional problem details."""
    problem_id: int  # database row id of the problem
    next_review_date: date
    interval_days: int
    ease_factor: float
    repetitions: int
    # Problem details (populated from JOIN query)
    problem_num: Optional[int] = None  # The actual problem number (e.g., 1 for Two Sum)
    source: str = "leetcode"
    title: str = ""
    difficulty: str = ""
    language: str = "python"
    file_path: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "ReviewSchedule":
        """Build from a database row dict (supports JOIN results)."""
        review_date = row["next_review_date"]
        if isinstance(review_date, str):
            review_date = date.fromisoformat(review_date)

        return cls(
            problem_id=row["problem_id"],
            next_review_date=review_date,
            interval_days=row.get("interval_days", 1),
            ease_factor=row.get("ease_factor", 2.5),
            repetitions=row.get("repetitions", 0),
            # Problem details from JOIN
            problem_num=int(row["problem_num"]) if row.get("problem_num") else None,
            source=row.get("source", "leetcode"),
            title=row.get("title", ""),
            difficulty=row.get("difficulty", ""),
            language=row.get("language", "python"),
            file_path=row.get("file_path"),
        )

    @property
    def days_until_due(self) -> int:
        """Days until this review is due (negative if overdue)."""
        return (self.next_review_date - date.today()).days

    @property
    def is_overdue(self) -> bool:
        """Whether this review is past its due date."""
        return self.days_until_due < 0

    @property
    def is_due_today(self) -> bool:
        """Whether this review is due today."""
        return self.days_until_due == 0

    def is_due(self) -> bool:
        """Check if this review is due today or overdue."""
        return self.next_review_date <= date.today()
