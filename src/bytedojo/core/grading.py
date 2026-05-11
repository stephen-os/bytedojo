"""
Grading service - Grade problems and manage review scheduling.

This module handles grading problems with pass/fail/skip status
and scheduling reviews for passed problems.
"""

from dataclasses import dataclass
from typing import Optional, List

from bytedojo.core.database import Database
from bytedojo.core.models.registered_problem import RegisteredProblem


@dataclass
class GradeResult:
    """Result of grading a problem."""
    success: bool
    status: str
    notes: Optional[str]
    scheduled_review: bool
    review_frequency_days: int


class GradingService:
    """Service for grading problems and managing review scheduling."""

    def __init__(self, db: Database):
        """
        Initialize grading service.

        Args:
            db: Database instance
        """
        self.db = db

    def grade_problem(
        self,
        problem_id: int,
        status: str,
        notes: Optional[str] = None
    ) -> GradeResult:
        """
        Apply a grade to a problem.

        Args:
            problem_id: Database ID of the problem (not problem_id string)
            status: Grade status ('passed', 'failed', 'skipped')
            notes: Optional notes about the grade

        Returns:
            GradeResult with status and review scheduling info

        Raises:
            ValueError: If status is invalid
        """
        valid_statuses = ('passed', 'failed', 'skipped')
        if status not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {valid_statuses}")

        # Update the status
        self.db.update_problem_status(problem_id, status, notes)

        # Schedule review if passed
        scheduled_review = False
        review_freq = int(self.db.get_config('review_frequency_days', '7'))

        if status == 'passed':
            self.db.schedule_review(problem_id, review_freq)
            scheduled_review = True

        return GradeResult(
            success=True,
            status=status,
            notes=notes,
            scheduled_review=scheduled_review,
            review_frequency_days=review_freq
        )

    def get_ungraded_problems(self) -> List[RegisteredProblem]:
        """
        Get all ungraded problems.

        Returns:
            List of RegisteredProblem with status 'ungraded'
        """
        return self.db.list_problems(status='ungraded')

    def get_problems_by_status(self, status: str) -> List[RegisteredProblem]:
        """
        Get problems filtered by status.

        Args:
            status: Status to filter by ('passed', 'failed', 'skipped', 'ungraded')

        Returns:
            List of RegisteredProblem objects
        """
        return self.db.list_problems(status=status)
