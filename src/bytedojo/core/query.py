"""
Query service - Search and filter problems from local data.

This module provides problem querying functionality for both CLI and TUI.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict

from bytedojo.core.repository import Repository
from bytedojo.core.attempt_service import AttemptService
from bytedojo.core import problem_service
from bytedojo.core.models import ProblemSummary, Difficulty, Status, Language, AttemptStats


@dataclass
class QueryResult:
    """Result of a problem query."""
    problems: List[ProblemSummary]
    total: int
    status_map: Dict[int, Dict[Language, AttemptStats]]  # problem_id -> language -> stats


class QueryService:
    """Service for querying problems from local data with status."""

    def __init__(self, repo: Optional[Repository] = None):
        """
        Initialize query service.

        Args:
            repo: Optional Repository. If None, creates one.
        """
        self.repo = repo or Repository(Path.cwd())
        self.attempts = AttemptService(self.repo)

    def query(
        self,
        difficulty: Difficulty = Difficulty.NONE,
        tags: Optional[List[str]] = None,
        include_status: bool = True
    ) -> QueryResult:
        """
        Query problems from local data with optional status.

        Args:
            difficulty: Filter by difficulty
            tags: Filter by algorithm tags
            include_status: Whether to include local status from database

        Returns:
            QueryResult with problems and status map
        """
        problems = problem_service.query_problems(
            difficulty=difficulty,
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
        return problem_service.get_all_tags()

    def _get_status_map(
        self,
        problems: List[ProblemSummary]
    ) -> Dict[int, Dict[Language, AttemptStats]]:
        """
        Get status map for a list of problems from versioned attempts.

        Args:
            problems: List of ProblemSummary objects

        Returns:
            Dict mapping problem_id to language -> AttemptStats
        """
        if not self.repo.is_initialized:
            return {}

        # Get all stats at once for efficiency
        all_stats = self.attempts.get_all_stats()

        # Filter to only requested problems
        problem_ids = {p.id for p in problems}
        return {pid: stats for pid, stats in all_stats.items() if pid in problem_ids}

    def get_problem_status(self, problem_id: int) -> Status:
        """
        Get best status for a single problem across all languages.

        Priority: passed > failed > skipped > ungraded > none

        Args:
            problem_id: The problem ID

        Returns:
            Status enum value (best status across languages)
        """
        stats = self.get_problem_stats(problem_id)
        if not stats:
            return Status.NONE

        # Collect latest statuses from all languages
        statuses = [s.latest_status for s in stats.values()]

        if Status.PASSED in statuses:
            return Status.PASSED
        elif Status.FAILED in statuses:
            return Status.FAILED
        elif Status.SKIPPED in statuses:
            return Status.SKIPPED
        elif Status.UNGRADED in statuses:
            return Status.UNGRADED
        else:
            return Status.NONE

    def get_problem_stats(
        self,
        problem_id: int,
        language: Optional[Language] = None
    ) -> Dict[Language, AttemptStats]:
        """
        Get detailed attempt stats for a problem.

        Args:
            problem_id: The problem ID
            language: Filter by language (None for all)

        Returns:
            Dict mapping Language to AttemptStats
        """
        return self.attempts.get_stats(problem_id, language)
