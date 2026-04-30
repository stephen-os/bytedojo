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

from bytedojo.core.database import DatabaseManager


@dataclass
class ReviewStats:
    """Statistics about reviews."""
    due_today: int
    due_this_week: int
    total_in_review: int
    most_reviewed: List[dict]
    review_frequency_days: int


@dataclass
class ReviewProblem:
    """A problem scheduled for review with computed fields."""
    id: int
    problem_id: str
    source: str
    title: str
    difficulty: str
    language: str
    file_path: str
    next_review_date: str
    repetitions: int
    days_until_due: int
    is_overdue: bool
    is_due_today: bool
    url: Optional[str] = None


class ReviewService:
    """Service for managing problem reviews."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize review service.

        Args:
            db: DatabaseManager instance
        """
        self.db = db

    def get_due_reviews(self, include_future: bool = False) -> List[ReviewProblem]:
        """
        Get problems due for review.

        Args:
            include_future: If True, include problems not yet due

        Returns:
            List of ReviewProblem objects sorted by due date
        """
        reviews = self.db.get_due_reviews(include_future=include_future)
        today = date.today()

        result = []
        for r in reviews:
            review_date = datetime.fromisoformat(r['next_review_date']).date()
            days_until = (review_date - today).days

            result.append(ReviewProblem(
                id=r['id'],
                problem_id=r['problem_id'],
                source=r['source'],
                title=r['title'],
                difficulty=r.get('difficulty') or 'Unknown',
                language=r.get('language', 'python'),
                file_path=r.get('file_path', ''),
                next_review_date=r['next_review_date'],
                repetitions=r['repetitions'],
                days_until_due=days_until,
                is_overdue=days_until < 0,
                is_due_today=days_until == 0,
                url=self._generate_url(r['source'], r['problem_id'], r['title'])
            ))

        return result

    def get_due_count(self) -> int:
        """
        Get count of problems due for review today or overdue.

        Returns:
            Number of problems due
        """
        reviews = self.get_due_reviews(include_future=False)
        return len(reviews)

    def pick_random_due(self) -> Optional[ReviewProblem]:
        """
        Pick a random problem from those due for review.

        Returns:
            A ReviewProblem or None if no problems are due
        """
        due_reviews = self.get_due_reviews(include_future=False)
        if not due_reviews:
            return None
        return random.choice(due_reviews)

    def get_stats(self) -> ReviewStats:
        """
        Get review statistics.

        Returns:
            ReviewStats with counts and most reviewed problems
        """
        stats = self.db.get_review_stats()
        review_freq = int(self.db.get_config('review_frequency_days', '7'))

        return ReviewStats(
            due_today=stats['due_today'],
            due_this_week=stats['due_this_week'],
            total_in_review=stats['total_in_review'],
            most_reviewed=stats['most_reviewed'],
            review_frequency_days=review_freq
        )

    def get_review_frequency(self) -> int:
        """
        Get the configured review frequency in days.

        Returns:
            Review frequency in days
        """
        return int(self.db.get_config('review_frequency_days', '7'))

    def _generate_url(self, source: str, problem_id: str, title: str) -> Optional[str]:
        """
        Generate URL for a problem based on its source.

        Args:
            source: Problem source (leetcode, codeforces, etc.)
            problem_id: Problem ID
            title: Problem title

        Returns:
            URL string or None if source not supported
        """
        if source == 'leetcode':
            # Derive slug from title (lowercase, replace spaces with hyphens)
            title_slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            return f"https://leetcode.com/problems/{title_slug}/"
        elif source == 'codeforces':
            # Parse contest_id and index from problem_id
            match = re.match(r'^(\d+)([A-Za-z]\d?)$', problem_id)
            if match:
                contest_id, index = match.groups()
                return f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
        return None

    @staticmethod
    def format_due_date(date_str: str) -> str:
        """
        Format a date string for display.

        Args:
            date_str: ISO format date string

        Returns:
            Human-readable date description
        """
        if not date_str:
            return "N/A"
        try:
            d = datetime.fromisoformat(date_str).date()
            today = date.today()
            delta = (d - today).days

            if delta < 0:
                return f"{abs(delta)} days overdue"
            elif delta == 0:
                return "Today"
            elif delta == 1:
                return "Tomorrow"
            elif delta < 7:
                return f"In {delta} days"
            else:
                return d.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return date_str
