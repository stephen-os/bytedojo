"""
Fetch service - orchestrates problem fetching and placement.

Provides a unified API for fetching problems from local data and placing
them into a repository. Returns rich result objects for logging/display.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from bytedojo.core import problem_service
from bytedojo.core.logger import get_logger
from bytedojo.core.models.attempt import Attempt
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.repository import Repository


@dataclass
class FetchResult:
    """Result of a single fetch operation."""
    problem_id: int
    success: bool = False
    skipped: bool = False
    problem: Optional[Problem] = None
    target_path: Optional[Path] = None
    version: Optional[int] = None
    skip_reason: Optional[str] = None
    error: Optional[str] = None

    @property
    def failed(self) -> bool:
        return not self.success and not self.skipped

    @property
    def title(self) -> str:
        """Problem title if available."""
        if self.problem:
            return self.problem.problem_detail.title
        return ""


@dataclass
class FetchBatchResult:
    """Aggregated results from a batch fetch operation."""
    results: List[FetchResult]

    @property
    def placed_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.failed)


class FetchService:
    """
    Orchestrates problem fetching and placement.

    Wraps problem_service (read) and repository (write) operations,
    returning rich result objects for commands to log/display as needed.
    """

    def __init__(self):
        self.logger = get_logger()

    def fetch_problem(self, problem_id: int) -> Optional[Problem]:
        """
        Fetch problem data by ID.

        Returns:
            Problem if found, None otherwise.
        """
        self.logger.debug(f"fetch_service: loading problem #{problem_id}")
        return problem_service.get_problem(problem_id)

    def fetch_and_place(
        self,
        repo: Repository,
        problem_id: int,
        language: CodeLanguage,
        *,
        force: bool = False,
        version: Optional[int] = None,
        custom_path: Optional[Path] = None,
    ) -> FetchResult:
        """
        Fetch a problem and place it into the repository.

        Modes:
            - default: Register new attempt, place under problems/.../v{N}/
            - version: Rewrite existing tracked version in place
            - custom_path: Place into custom directory (untracked)

        Args:
            repo: The repository to place into.
            problem_id: Problem ID to fetch.
            language: Language for starter code.
            force: Create new attempt even if already registered.
            version: Rewrite specific version in place.
            custom_path: Custom directory for untracked placement.

        Returns:
            FetchResult with outcome, problem data, and target path.
        """
        self.logger.debug(
            f"fetch_service: fetch_and_place #{problem_id} "
            f"lang={language} force={force} version={version} path={custom_path}"
        )

        # Load problem
        problem = problem_service.get_problem(problem_id)
        if problem is None:
            self.logger.warning(f"fetch_service: problem #{problem_id} not found")
            return FetchResult(
                problem_id=problem_id,
                error="not found",
            )

        # Mode 1: Scratch (custom path, no DB)
        if custom_path is not None:
            return self._place_scratch(repo, problem, language, custom_path)

        # Mode 2: Refetch existing version
        if version is not None:
            return self._place_version(repo, problem, language, version)

        # Mode 3: Default (new attempt)
        return self._place_default(repo, problem, language, force)

    def fetch_and_place_batch(
        self,
        repo: Repository,
        problem_ids: List[int],
        language: CodeLanguage,
        *,
        force: bool = False,
        version: Optional[int] = None,
        custom_path: Optional[Path] = None,
    ) -> FetchBatchResult:
        """
        Fetch and place multiple problems.

        Args:
            repo: The repository to place into.
            problem_ids: List of problem IDs to fetch.
            language: Language for starter code.
            force: Create new attempts even if already registered.
            version: Rewrite specific version in place (applies to all).
            custom_path: Custom directory for untracked placement.

        Returns:
            FetchBatchResult with all individual results.
        """
        self.logger.debug(
            f"fetch_service: batch fetch {len(problem_ids)} problems"
        )

        results = []
        for pid in problem_ids:
            result = self.fetch_and_place(
                repo,
                pid,
                language,
                force=force,
                version=version,
                custom_path=custom_path,
            )
            results.append(result)

        batch_result = FetchBatchResult(results=results)
        self.logger.info(
            f"fetch_service: batch complete — "
            f"placed={batch_result.placed_count} "
            f"skipped={batch_result.skipped_count} "
            f"failed={batch_result.failed_count}"
        )

        return batch_result

    # ------------------------------------------------------------------
    # Private helpers for each mode
    # ------------------------------------------------------------------

    def _place_scratch(
        self,
        repo: Repository,
        problem: Problem,
        language: CodeLanguage,
        custom_path: Path,
    ) -> FetchResult:
        """Place into custom directory without DB registration."""
        target = custom_path / problem.get_folder_name()
        solution_path = target / problem.get_solution_filename(language)

        repo.place_problem(problem, language, solution_path)

        self.logger.info(
            f"fetch_service: placed #{problem.problem_detail.id} "
            f"({language.value}) at {solution_path}, untracked"
        )

        return FetchResult(
            problem_id=problem.problem_detail.id,
            success=True,
            problem=problem,
            target_path=solution_path,
        )

    def _place_version(
        self,
        repo: Repository,
        problem: Problem,
        language: CodeLanguage,
        version: int,
    ) -> FetchResult:
        """Rewrite existing tracked version in place."""
        target = repo.attempt_path(problem, language, version)

        if not target.exists():
            self.logger.warning(
                f"fetch_service: #{problem.problem_detail.id} "
                f"v{version} not found at {target}"
            )
            return FetchResult(
                problem_id=problem.problem_detail.id,
                skipped=True,
                problem=problem,
                version=version,
                skip_reason=f"v{version} not found at {target}",
            )

        repo.place_problem(problem, language, target)

        self.logger.info(
            f"fetch_service: refetched #{problem.problem_detail.id} "
            f"({language.value}) v{version} at {target}"
        )

        return FetchResult(
            problem_id=problem.problem_detail.id,
            success=True,
            problem=problem,
            target_path=target,
            version=version,
        )

    def _place_default(
        self,
        repo: Repository,
        problem: Problem,
        language: CodeLanguage,
        force: bool,
    ) -> FetchResult:
        """Register new attempt and place under problems/."""
        problem_id = problem.problem_detail.id

        # Check if already registered
        if not force and repo.is_problem_registered("leetcode", problem_id, language):
            self.logger.info(
                f"fetch_service: skipped #{problem_id} ({language.value}), "
                f"already registered"
            )
            return FetchResult(
                problem_id=problem_id,
                skipped=True,
                problem=problem,
                skip_reason="already registered",
            )

        # Register and place
        attempt: Attempt = repo.register_attempt(problem, language)
        target = repo.attempt_path(problem, language, attempt.version)
        repo.place_problem(problem, language, target)

        self.logger.info(
            f"fetch_service: placed #{problem_id} ({language.value}) "
            f"v{attempt.version} at {target}"
        )

        return FetchResult(
            problem_id=problem_id,
            success=True,
            problem=problem,
            target_path=target,
            version=attempt.version,
        )
