"""
ReviewSchedule - spaced-repetition state for a problem.

One row per problem in the `review_schedule` table tracks when the
next review is due and the SM-2-style ease/interval state. The trailing
optional fields (title, difficulty, language, ...) are populated by a
JOIN against the `problems` table when the schedule is fetched together
with its problem metadata — they're left unset when the schedule is
queried on its own.

`__post_init__` coerces raw strings on the typed enum fields so a row
dict can be passed straight through without the caller pre-converting.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty


@dataclass
class ReviewSchedule:
    """A scheduled review for a problem, optionally enriched with problem metadata."""
    problem_id: int                                 # database row id of the problem
    next_review_date: date
    interval_days: int
    ease_factor: float
    repetitions: int
    # Joined problem metadata (None / sentinel values when not populated by JOIN).
    problem_num: Optional[int] = None               # the LeetCode problem number, e.g. 1 for Two Sum
    source: str = "leetcode"
    title: str = ""
    difficulty: ProblemDifficulty = ProblemDifficulty.NONE
    language: CodeLanguage = CodeLanguage.UNKNOWN
    file_path: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.difficulty, str):
            self.difficulty = ProblemDifficulty.from_string(self.difficulty)
        if isinstance(self.language, str):
            self.language = CodeLanguage.from_string(self.language)

    @classmethod
    def from_row(cls, row: dict) -> "ReviewSchedule":
        """Build from a database row dict (supports JOIN results)."""
        review_date = row["next_review_date"]
        if isinstance(review_date, str):
            review_date = date.fromisoformat(review_date)
        return cls(
            problem_id=row["problem_id"],
            next_review_date=review_date,
            interval_days=row["interval_days"],
            ease_factor=row["ease_factor"],
            repetitions=row["repetitions"],
            # Joined problem metadata
            problem_num=int(row["problem_num"]) if row.get("problem_num") else None,
            source=row.get("source", "leetcode"),
            title=row.get("title", ""),
            difficulty=ProblemDifficulty.from_string(row.get("difficulty", "")),
            language=CodeLanguage.from_string(row.get("language", "")),
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
        """Whether this review falls on today's date."""
        return self.days_until_due == 0

    def is_due(self) -> bool:
        """Whether this review is due today or overdue."""
        return self.next_review_date <= date.today()
