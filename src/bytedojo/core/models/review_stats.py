"""
ReviewStats - Summary statistics for review scheduling.
"""

from dataclasses import dataclass


@dataclass
class ReviewStats:
    """Summary statistics for review scheduling."""
    due_today: int
    due_this_week: int
    total_in_review: int

    @classmethod
    def empty(cls) -> "ReviewStats":
        """Return empty stats."""
        return cls(due_today=0, due_this_week=0, total_in_review=0)
