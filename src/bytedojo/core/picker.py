"""
Picker service - Randomly select problems.

This module provides problem picking functionality for both CLI and TUI.
"""

import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager
from bytedojo.core.leetcode import LeetCodeClient
from bytedojo.core.leetcode.models import ProblemSummary


DIFFICULTY_MAP = {
    'easy': 1,
    'medium': 2,
    'hard': 3,
    '1': 1,
    '2': 2,
    '3': 3,
}


@dataclass
class PickResult:
    """Result of picking a problem."""
    problem: Optional[ProblemSummary]
    unsolved_count: int
    solved_count: int
    total_count: int


class ProblemPicker:
    """Service for picking random unsolved problems."""

    def __init__(self, repo: Optional[Repository] = None):
        """
        Initialize picker service.

        Args:
            repo: Optional Repository. If None, creates one.
        """
        self.repo = repo or Repository(Path.cwd())
        self.client = LeetCodeClient()

    def pick(
        self,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_premium: bool = False
    ) -> PickResult:
        """
        Pick a random unsolved problem.

        Args:
            difficulty: Filter by difficulty (easy/medium/hard or 1/2/3)
            tags: Filter by algorithm tags
            include_premium: Whether to include premium (paid) problems

        Returns:
            PickResult with the picked problem and stats
        """
        # Convert difficulty to int
        difficulty_int = None
        if difficulty:
            difficulty_int = DIFFICULTY_MAP.get(difficulty.lower())

        # Query all matching problems from LeetCode
        all_problems = self.client.query_problems(
            difficulty=difficulty_int,
            tags=tags
        )

        if not all_problems:
            return PickResult(
                problem=None,
                unsolved_count=0,
                solved_count=0,
                total_count=0
            )

        # Filter out premium problems unless requested
        if not include_premium:
            all_problems = [p for p in all_problems if not p.paid_only]

        if not all_problems:
            return PickResult(
                problem=None,
                unsolved_count=0,
                solved_count=0,
                total_count=0
            )

        # Get problems already in database
        fetched_ids = self._get_fetched_problem_ids()

        # Filter to unsolved problems only
        unsolved = [p for p in all_problems if p.id not in fetched_ids]

        if not unsolved:
            return PickResult(
                problem=None,
                unsolved_count=0,
                solved_count=len(fetched_ids),
                total_count=len(all_problems)
            )

        # Pick a random problem
        picked = random.choice(unsolved)

        return PickResult(
            problem=picked,
            unsolved_count=len(unsolved),
            solved_count=len(fetched_ids),
            total_count=len(all_problems)
        )

    def _get_fetched_problem_ids(self) -> Set[int]:
        """Get set of problem IDs already in the database."""
        fetched_ids: Set[int] = set()

        if self.repo.is_initialized:
            with DatabaseManager(self.repo.db_path) as db:
                problems = db.list_problems(source='leetcode')
                fetched_ids = {int(p['problem_id']) for p in problems}

        return fetched_ids

    def get_unsolved_problems(
        self,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_premium: bool = False
    ) -> List[ProblemSummary]:
        """
        Get all unsolved problems matching criteria.

        Args:
            difficulty: Filter by difficulty
            tags: Filter by algorithm tags
            include_premium: Whether to include premium problems

        Returns:
            List of unsolved ProblemSummary objects
        """
        # Convert difficulty to int
        difficulty_int = None
        if difficulty:
            difficulty_int = DIFFICULTY_MAP.get(difficulty.lower())

        # Query all matching problems
        all_problems = self.client.query_problems(
            difficulty=difficulty_int,
            tags=tags
        )

        if not all_problems:
            return []

        # Filter out premium
        if not include_premium:
            all_problems = [p for p in all_problems if not p.paid_only]

        # Filter to unsolved
        fetched_ids = self._get_fetched_problem_ids()
        return [p for p in all_problems if p.id not in fetched_ids]
