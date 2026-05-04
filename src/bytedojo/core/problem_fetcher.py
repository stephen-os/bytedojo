"""
Problem fetching service - Fetch problems from LeetCode.

This module handles fetching problems, formatting them, and saving to disk.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Callable

from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager
from bytedojo.core.leetcode_api import LeetCodeAPI
from bytedojo.core.formatters import PythonFormatter, JavaFormatter, CppFormatter
from bytedojo.core.file_writer import FileWriter
from bytedojo.core.settings import SettingsManager


# Language to formatter mapping
FORMATTERS = {
    'python': PythonFormatter,
    'java': JavaFormatter,
    'cpp': CppFormatter,
}


@dataclass
class FetchedProblem:
    """Information about a fetched problem."""
    problem_id: int
    title: str
    language: str
    file_path: str
    success: bool
    skipped: bool = False
    error: Optional[str] = None


@dataclass
class FetchResult:
    """Result of fetching problems."""
    success_count: int
    skip_count: int
    error_count: int
    problems: List[FetchedProblem] = field(default_factory=list)


class ProblemFetcher:
    """Fetches problems from LeetCode and saves them locally."""

    def __init__(self, repo: Repository):
        """
        Initialize fetcher with repository context.

        Args:
            repo: The Repository instance
        """
        self.repo = repo
        self.client = LeetCodeAPI()
        self.writer = FileWriter()

    def fetch(
        self,
        problem_ids: List[int],
        language: str,
        output_dir: Path,
        force: bool = False,
        on_progress: Optional[Callable[[FetchedProblem], None]] = None
    ) -> FetchResult:
        """
        Fetch problems from LeetCode.

        Args:
            problem_ids: List of problem IDs to fetch
            language: Programming language (python, java, cpp)
            output_dir: Directory to save problem files
            force: If True, overwrite existing problems
            on_progress: Optional callback called after each problem

        Returns:
            FetchResult with counts and problem details
        """
        # Load settings for organization mode
        settings_manager = SettingsManager(self.repo.dojo_dir)
        settings = settings_manager.load()
        organization = settings.leetcode.organization

        # Get formatter for language
        formatter_class = FORMATTERS.get(language, PythonFormatter)
        formatter = formatter_class()

        success_count = 0
        skip_count = 0
        error_count = 0
        problems: List[FetchedProblem] = []

        with DatabaseManager(self.repo.db_path) as db:
            for problem_id in problem_ids:
                result = self._fetch_single(
                    db=db,
                    problem_id=problem_id,
                    language=language,
                    output_dir=output_dir,
                    organization=organization,
                    formatter=formatter,
                    force=force
                )

                problems.append(result)

                if result.success and not result.skipped:
                    success_count += 1
                elif result.skipped:
                    skip_count += 1
                else:
                    error_count += 1

                # Call progress callback if provided
                if on_progress:
                    on_progress(result)

        return FetchResult(
            success_count=success_count,
            skip_count=skip_count,
            error_count=error_count,
            problems=problems
        )

    def _fetch_single(
        self,
        db: DatabaseManager,
        problem_id: int,
        language: str,
        output_dir: Path,
        organization: str,
        formatter,
        force: bool
    ) -> FetchedProblem:
        """
        Fetch a single problem.

        Args:
            db: Database manager
            problem_id: Problem ID to fetch
            language: Programming language
            output_dir: Output directory
            organization: Folder organization mode
            formatter: Language formatter
            force: Overwrite existing

        Returns:
            FetchedProblem with details
        """
        # Fetch problem from LeetCode
        problem = self.client.get_problem_by_id(problem_id)
        if not problem:
            return FetchedProblem(
                problem_id=problem_id,
                title="",
                language=language,
                file_path="",
                success=False,
                error=f"Problem {problem_id} not found"
            )

        # Check if already registered for this language (unless force)
        if not force and db.is_problem_registered('leetcode', problem.id, language):
            return FetchedProblem(
                problem_id=problem_id,
                title=problem.title,
                language=language,
                file_path="",
                success=True,
                skipped=True
            )

        # Format to string
        content = formatter.format(problem)

        # Get folder name and solution filename
        folder_name = problem.get_folder_name()
        solution_filename = problem.get_solution_filename(language)

        # Build file path based on organization setting
        if organization == "difficulty":
            filepath = output_dir / problem.difficulty.lower() / folder_name / solution_filename
        else:  # flat (default)
            filepath = output_dir / folder_name / solution_filename

        # Write to file
        self.writer.write(content, filepath)

        # Register in database with language
        db.register_problem(
            problem,
            source='leetcode',
            language=language,
            file_path=filepath,
            force=force
        )

        return FetchedProblem(
            problem_id=problem.id,
            title=problem.title,
            language=language,
            file_path=str(filepath),
            success=True
        )

    @staticmethod
    def parse_problem_ids(arguments: tuple) -> List[int]:
        """
        Parse problem ID arguments into a list of integers.

        Supports formats:
        - Single: "1"
        - Multiple: "1,2,3"
        - Range: "1..10"
        - Mixed: "1,2,5..10"

        Args:
            arguments: Tuple of string arguments

        Returns:
            Sorted list of problem IDs

        Raises:
            ValueError: If argument format is invalid
        """
        problem_ids: List[int] = []

        for token in arguments:
            parts = token.split(',')

            for part in parts:
                if '..' in part:  # Range
                    try:
                        start, end = part.split('..', 1)
                        start, end = int(start), int(end)
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid range '{part}'. Expected format: start..end")

                    step = 1 if start <= end else -1
                    problem_ids.extend(range(start, end + step, step))
                else:  # Single
                    try:
                        problem_ids.append(int(part))
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid number '{part}'. Expected an integer.")

        return sorted(problem_ids)
