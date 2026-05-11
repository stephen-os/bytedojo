"""
Review service - Manage spaced repetition reviews.

This module handles review scheduling, getting due reviews,
and selecting random problems for review.
"""

import re
import random
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from bytedojo.core.database import Database
from bytedojo.core.models.review_schedule import ReviewSchedule
from bytedojo.core.models.review_stats import ReviewStats


@dataclass
class ReviewProblem:
    """A problem scheduled for review with computed fields."""
    id: int
    problem_id: int
    source: str
    title: str
    difficulty: str
    language: str
    file_path: str
    next_review_date: date
    repetitions: int
    days_until_due: int
    is_overdue: bool
    is_due_today: bool


class ReviewService:
    """Service for managing problem reviews."""

    def __init__(self, db: Database):
        """
        Initialize review service.

        Args:
            db: Database instance
        """
        self.db = db

    def get_due_reviews(self, include_future: bool = False) -> List[ReviewSchedule]:
        """
        Get problems due for review.

        Args:
            include_future: If True, include problems not yet due

        Returns:
            List of ReviewSchedule objects sorted by due date
        """
        return self.db.get_due_reviews(include_future=include_future)

    def get_due_count(self) -> int:
        """
        Get count of problems due for review today or overdue.

        Returns:
            Number of problems due
        """
        reviews = self.db.get_due_reviews(include_future=False)
        return len(reviews)

    def pick_random_due(self) -> Optional[ReviewSchedule]:
        """
        Pick a random problem from those due for review.

        Returns:
            A ReviewSchedule or None if no problems are due
        """
        due_reviews = self.db.get_due_reviews(include_future=False)
        if not due_reviews:
            return None
        return random.choice(due_reviews)

    def get_stats(self) -> ReviewStats:
        """
        Get review statistics.

        Returns:
            ReviewStats with counts
        """
        return self.db.get_review_stats()

    def get_review_frequency(self) -> int:
        """
        Get the configured review frequency in days.

        Returns:
            Review frequency in days
        """
        return int(self.db.get_config('review_frequency_days', '7'))

    @staticmethod
    def format_due_date(review_date: date) -> str:
        """
        Format a date for display.

        Args:
            review_date: Date to format

        Returns:
            Human-readable date description
        """
        today = date.today()
        delta = (review_date - today).days

        if delta < 0:
            return f"{abs(delta)} days overdue"
        elif delta == 0:
            return "Today"
        elif delta == 1:
            return "Tomorrow"
        elif delta < 7:
            return f"In {delta} days"
        else:
            return review_date.strftime("%Y-%m-%d")
