"""
Fetch service - orchestrates problem fetching and placement.

Fetching is restricted to the bundled catalog (§7): every id is
validated up front so a batch either runs against fully supported
problems or fails cleanly before touching the filesystem. Solution
stubs are synthesised from the test bundle's signature (§11).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from bytedojo.core import corpus
from bytedojo.core.errors import UnsupportedProblemError
from bytedojo.core.formatters import extra_files_for, format_problem
from bytedojo.core.logger import get_logger
from bytedojo.core.models.attempt import Attempt
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.test_bundle import TestBundle
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

    Reads problem definitions + test bundles through the corpus gateway
    and places formatter output via the Repository, returning rich
    result objects for commands to render.
    """

    def __init__(self):
        self.logger = get_logger()

    def fetch_and_place_batch(
        self,
        repo: Repository,
        problem_ids: List[int],
        language: CodeLanguage,
        *,
        new_attempt: bool = False,
        version: Optional[int] = None,
        custom_path: Optional[Path] = None,
    ) -> FetchBatchResult:
        """
        Fetch and place multiple problems.

        Every id is validated against the catalog first; any unsupported
        id aborts the whole batch with UnsupportedProblemError before
        anything is placed.
        """
        unsupported = [pid for pid in problem_ids if not corpus.has_problem(pid)]
        if unsupported:
            raise UnsupportedProblemError(unsupported)

        results = [
            self.fetch_and_place(
                repo,
                pid,
                language,
                new_attempt=new_attempt,
                version=version,
                custom_path=custom_path,
            )
            for pid in problem_ids
        ]

        batch_result = FetchBatchResult(results=results)
        self.logger.debug(
            f"fetch_service: batch complete — "
            f"placed={batch_result.placed_count} "
            f"skipped={batch_result.skipped_count} "
            f"failed={batch_result.failed_count}"
        )
        return batch_result

    def fetch_and_place(
        self,
        repo: Repository,
        problem_id: int,
        language: CodeLanguage,
        *,
        new_attempt: bool = False,
        version: Optional[int] = None,
        custom_path: Optional[Path] = None,
    ) -> FetchResult:
        """
        Fetch a supported problem and place it into the repository.

        Modes (mutually exclusive, validated by the command):
            - default: register v1; refuse if the problem is already
              registered (hint at --new-attempt / --version)
            - new_attempt: register the next version v{N+1}
            - version: rewrite tracked version N in place
            - custom_path: place into a scratch directory (no DB entry)

        Raises UnsupportedProblemError for ids outside the catalog.
        """
        self.logger.debug(
            f"fetch_service: fetch_and_place #{problem_id} "
            f"lang={language} new_attempt={new_attempt} "
            f"version={version} path={custom_path}"
        )

        problem = corpus.problem(problem_id)
        bundle = corpus.bundle(problem_id)

        if custom_path is not None:
            return self._place_scratch(repo, problem, bundle, language, custom_path)

        if version is not None:
            return self._place_version(repo, problem, bundle, language, version)

        return self._place_default(repo, problem, bundle, language, new_attempt)

    # ------------------------------------------------------------------
    # Private helpers for each mode
    # ------------------------------------------------------------------

    def _place_with_extras(
        self,
        repo: Repository,
        problem: Problem,
        bundle: TestBundle,
        language: CodeLanguage,
        target_path: Path,
    ) -> None:
        """
        Write the formatted solution file + any sibling files the formatter
        asks for (e.g. `tree_node.py`, `list_node.py`).

        Sibling files land next to the solution and follow the same
        overwrite semantics — fresh version dirs / `--version N`
        rewrites take care of "don't clobber my work" via the upstream
        version flow rather than per-file existence checks.
        """
        repo.place_problem(target_path, format_problem(problem, bundle, language))
        sibling_dir = target_path.parent
        for filename, content in extra_files_for(bundle, language).items():
            repo.place_problem(sibling_dir / filename, content)

    def _place_scratch(
        self,
        repo: Repository,
        problem: Problem,
        bundle: TestBundle,
        language: CodeLanguage,
        custom_path: Path,
    ) -> FetchResult:
        """Place into custom directory without DB registration."""
        target = custom_path / problem.get_folder_name()
        solution_path = target / problem.get_solution_filename(language)

        self._place_with_extras(repo, problem, bundle, language, solution_path)

        self.logger.debug(
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
        bundle: TestBundle,
        language: CodeLanguage,
        version: int,
    ) -> FetchResult:
        """Rewrite tracked version N in place (restores a deleted file too)."""
        problem_id = problem.problem_detail.id

        with repo.session() as s:
            attempt = s.attempts.get("leetcode", problem_id, version)
            available = [a.version for a in s.attempts.list("leetcode", problem_id)]

        if attempt is None:
            versions = ", ".join(f"v{v}" for v in available) or "none"
            return FetchResult(
                problem_id=problem_id,
                skipped=True,
                problem=problem,
                version=version,
                skip_reason=f"v{version} not registered (available: {versions})",
            )

        target = repo.attempt_path(problem, attempt.language, version)
        self._place_with_extras(repo, problem, bundle, attempt.language, target)

        self.logger.debug(
            f"fetch_service: refetched #{problem_id} "
            f"({attempt.language.value}) v{version} at {target}"
        )

        return FetchResult(
            problem_id=problem_id,
            success=True,
            problem=problem,
            target_path=target,
            version=version,
        )

    def _place_default(
        self,
        repo: Repository,
        problem: Problem,
        bundle: TestBundle,
        language: CodeLanguage,
        new_attempt: bool,
    ) -> FetchResult:
        """Register an attempt and place under problems/."""
        problem_id = problem.problem_detail.id

        if not new_attempt and repo.is_problem_registered("leetcode", problem_id):
            self.logger.debug(
                f"fetch_service: skipped #{problem_id}, already registered"
            )
            return FetchResult(
                problem_id=problem_id,
                skipped=True,
                problem=problem,
                skip_reason="already registered",
            )

        attempt: Attempt = repo.register_attempt(problem, language)
        target = repo.attempt_path(problem, language, attempt.version)
        self._place_with_extras(repo, problem, bundle, language, target)

        self.logger.debug(
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
