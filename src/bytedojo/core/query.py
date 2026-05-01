"""
Query service - Search and filter LeetCode problems.

This module provides problem querying functionality for both CLI and TUI.
"""

from dataclasses import dataclass
from typing import List, Optional

from bytedojo.core.repository import DojoRepository
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
class ProblemStatus:
    """Status information for a problem."""
    problem_id: int
    status: Optional[str]  # passed, failed, skipped, ungraded, None


@dataclass
class QueryResult:
    """Result of a problem query."""
    problems: List[ProblemSummary]
    total: int
    status_map: dict  # problem_id -> status string


class QueryService:
    """Service for querying LeetCode problems with local status."""

    def __init__(self, repo: Optional[DojoRepository] = None):
        """
        Initialize query service.

        Args:
            repo: Optional DojoRepository. If None, creates one.
        """
        self.repo = repo or DojoRepository()
        self.client = LeetCodeClient()

    def query(
        self,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_status: bool = True
    ) -> QueryResult:
        """
        Query problems from LeetCode with optional local status.

        Args:
            difficulty: Filter by difficulty (easy/medium/hard or 1/2/3)
            tags: Filter by algorithm tags
            include_status: Whether to include local status from database

        Returns:
            QueryResult with problems and status map
        """
        # Convert difficulty to int
        difficulty_int = None
        if difficulty:
            difficulty_int = DIFFICULTY_MAP.get(difficulty.lower())

        # Query from LeetCode
        problems = self.client.query_problems(
            difficulty=difficulty_int,
            tags=tags
        )

        # Get status map if requested and repo is initialized
        status_map = {}
        if include_status and problems:
            status_map = self._get_status_map(problems)

        return QueryResult(
            problems=problems,
            total=len(problems),
            status_map=status_map
        )

    def get_available_tags(self) -> List[str]:
        """Get list of available algorithm tags."""
        return self.client.get_available_tags()

    def _get_status_map(self, problems: List[ProblemSummary]) -> dict:
        """
        Get status map for a list of problems from the database.

        Returns the best status across all languages for each problem.
        Priority: passed > failed > skipped > ungraded

        Args:
            problems: List of ProblemSummary objects

        Returns:
            Dict mapping problem_id to status string
        """
        status_map = {}

        if not self.repo.is_initialized():
            return status_map

        with DatabaseManager(self.repo.get_db_path()) as db:
            for problem in problems:
                # Check all languages for this problem
                statuses = []
                for lang in ['python', 'java', 'cpp']:
                    db_problem = db.get_problem('leetcode', problem.id, lang)
                    if db_problem:
                        statuses.append(db_problem.get('test_status'))

                if statuses:
                    # Return best status (passed > failed > skipped > ungraded)
                    if 'passed' in statuses:
                        status_map[problem.id] = 'passed'
                    elif 'failed' in statuses:
                        status_map[problem.id] = 'failed'
                    elif 'skipped' in statuses:
                        status_map[problem.id] = 'skipped'
                    else:
                        status_map[problem.id] = statuses[0]  # ungraded/untested

        return status_map

    def get_problem_status(self, problem_id: int) -> Optional[str]:
        """
        Get status for a single problem.

        Args:
            problem_id: The problem ID

        Returns:
            Status string or None if not in database
        """
        if not self.repo.is_initialized():
            return None

        with DatabaseManager(self.repo.get_db_path()) as db:
            statuses = []
            for lang in ['python', 'java', 'cpp']:
                db_problem = db.get_problem('leetcode', problem_id, lang)
                if db_problem:
                    statuses.append(db_problem.get('test_status'))

            if not statuses:
                return None

            if 'passed' in statuses:
                return 'passed'
            elif 'failed' in statuses:
                return 'failed'
            elif 'skipped' in statuses:
                return 'skipped'
            else:
                return statuses[0]
