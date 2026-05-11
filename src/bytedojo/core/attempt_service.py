"""
Attempt service - manages versioned solution attempts.

Handles creating, tracking, and querying attempts at solving problems
across multiple languages with version history.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from bytedojo.core.repository import Repository
from bytedojo.core.database import Database
from bytedojo.core import problem_service
from bytedojo.core.models.attempt import Attempt
from bytedojo.core.models.attempt_stats import AttemptStats
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus


class AttemptService:
    """Service for managing versioned solution attempts."""

    def __init__(self, repo: Optional[Repository] = None):
        """
        Initialize attempt service.

        Args:
            repo: Optional Repository. If None, creates one from cwd.
        """
        self.repo = repo or Repository(Path.cwd())

    def create_attempt(
        self,
        problem_id: int,
        language: CodeLanguage,
        source: str = "leetcode"
    ) -> Optional[Attempt]:
        """
        Create a new versioned attempt for a problem.

        Creates the folder structure and database entry:
        - problems/0001-two-sum/python/v001/solution.py

        Args:
            problem_id: Problem ID number
            language: Programming language
            source: Problem source (default: 'leetcode')

        Returns:
            The created Attempt or None if repo not initialized
        """
        if not self.repo.is_initialized:
            return None

        # Get problem data for folder name and starter code
        problem = problem_service.get_problem(problem_id)
        if not problem:
            return None

        with Database(self.repo.db_path) as db:
            # Create database entry (returns Attempt object)
            attempt = db.create_attempt(source, problem_id, language.value)

            # Create folder structure
            attempt_path = self._get_attempt_path(problem_id, language, attempt.version)
            attempt_path.mkdir(parents=True, exist_ok=True)

            # Write starter code
            starter_code = problem.get_snippet(language)
            if starter_code:
                solution_file = attempt_path / problem.get_solution_filename(language)
                solution_file.write_text(starter_code, encoding='utf-8')

            return attempt

    def get_attempt(
        self,
        problem_id: int,
        language: CodeLanguage,
        version: Optional[int] = None,
        source: str = "leetcode"
    ) -> Optional[Attempt]:
        """
        Get a specific attempt or the latest attempt.

        Args:
            problem_id: Problem ID number
            language: Programming language
            version: Specific version (None for latest)
            source: Problem source (default: 'leetcode')

        Returns:
            Attempt object or None
        """
        if not self.repo.is_initialized:
            return None

        with Database(self.repo.db_path) as db:
            return db.get_attempt(source, problem_id, language.value, version)

    def list_attempts(
        self,
        problem_id: int,
        language: Optional[CodeLanguage] = None,
        source: str = "leetcode"
    ) -> List[Attempt]:
        """
        List all attempts for a problem.

        Args:
            problem_id: Problem ID number
            language: Filter by language (None for all)
            source: Problem source (default: 'leetcode')

        Returns:
            List of Attempt objects
        """
        if not self.repo.is_initialized:
            return []

        with Database(self.repo.db_path) as db:
            lang_str = language.value if language else None
            return db.list_attempts(source, problem_id, lang_str)

    def update_status(
        self,
        problem_id: int,
        language: CodeLanguage,
        version: int,
        status: ProblemStatus,
        source: str = "leetcode"
    ) -> bool:
        """
        Update the status of an attempt.

        Args:
            problem_id: Problem ID number
            language: Programming language
            version: Attempt version
            status: New status
            source: Problem source (default: 'leetcode')

        Returns:
            True if updated successfully
        """
        if not self.repo.is_initialized:
            return False

        with Database(self.repo.db_path) as db:
            return db.update_attempt_status(
                source, problem_id, language.value, version, status.value
            )

    def increment_run_count(
        self,
        problem_id: int,
        language: CodeLanguage,
        version: int,
        source: str = "leetcode"
    ) -> bool:
        """
        Increment run count for an attempt.

        Args:
            problem_id: Problem ID number
            language: Programming language
            version: Attempt version
            source: Problem source (default: 'leetcode')

        Returns:
            True if updated successfully
        """
        if not self.repo.is_initialized:
            return False

        with Database(self.repo.db_path) as db:
            return db.increment_run_count(source, problem_id, language.value, version)

    def get_stats(
        self,
        problem_id: int,
        language: Optional[CodeLanguage] = None,
        source: str = "leetcode"
    ) -> Dict[CodeLanguage, AttemptStats]:
        """
        Get aggregated stats for a problem.

        Args:
            problem_id: Problem ID number
            language: Filter by language (None for all)
            source: Problem source (default: 'leetcode')

        Returns:
            Dictionary mapping Language to AttemptStats
        """
        if not self.repo.is_initialized:
            return {}

        with Database(self.repo.db_path) as db:
            lang_str = language.value if language else None
            raw_stats = db.get_attempt_stats(source, problem_id, lang_str)

            # Convert string keys to CodeLanguage
            result = {}
            for lang_key, stats in raw_stats.items():
                lang = CodeLanguage.from_string(lang_key)
                if lang != CodeLanguage.UNKNOWN:
                    result[lang] = stats

            return result

    def get_all_stats(
        self,
        source: str = "leetcode"
    ) -> Dict[int, Dict[CodeLanguage, AttemptStats]]:
        """
        Get stats for all problems with attempts.

        Args:
            source: Problem source (default: 'leetcode')

        Returns:
            Dictionary mapping problem_id to language stats
        """
        if not self.repo.is_initialized:
            return {}

        with Database(self.repo.db_path) as db:
            raw_stats = db.get_all_attempt_stats(source)

            # Convert string keys to CodeLanguage
            result = {}
            for pid, lang_stats in raw_stats.items():
                result[pid] = {}
                for lang_key, stats in lang_stats.items():
                    lang = CodeLanguage.from_string(lang_key)
                    if lang != CodeLanguage.UNKNOWN:
                        result[pid][lang] = stats

            return result

    def get_attempt_path(
        self,
        problem_id: int,
        language: CodeLanguage,
        version: Optional[int] = None
    ) -> Optional[Path]:
        """
        Get the file system path for an attempt.

        Args:
            problem_id: Problem ID number
            language: Programming language
            version: Specific version (None for latest)

        Returns:
            Path to attempt folder or None
        """
        if version is None:
            attempt = self.get_attempt(problem_id, language)
            if not attempt:
                return None
            version = attempt.version

        return self._get_attempt_path(problem_id, language, version)

    def _get_attempt_path(
        self,
        problem_id: int,
        language: CodeLanguage,
        version: int
    ) -> Path:
        """
        Build the file system path for an attempt.

        Structure: problems/0001-two-sum/python/v001/

        Args:
            problem_id: Problem ID number
            language: Programming language
            version: Attempt version

        Returns:
            Path to attempt folder
        """
        problem = problem_service.get_problem(problem_id)
        folder_name = problem.get_folder_name() if problem else f"{problem_id:04d}-unknown"
        version_str = f"v{version:03d}"

        return self.repo.problems_dir / folder_name / language.value / version_str
