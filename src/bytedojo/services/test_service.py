"""
Test service - run tests against a registered problem and persist the result.

Wraps the existing test_runner / test_fetcher / DB-status-update chain so
the CLI and (upcoming) TUI can drive testing through the same API.

The caller is responsible for problem lookup / disambiguation
(see services.problem_service.find_registered_problems).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from bytedojo.core.logger import get_logger
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.core.test_fetcher import fetch_test_cases
from bytedojo.core.test_runner import TestRunResult, run_tests


@dataclass
class TestServiceResult:
    """
    Outcome of testing a registered problem.

    Mutually-exclusive states:
      - success: tests ran; `run_result` populated
      - skipped: no test cases available (soft outcome, no DB update)
      - failed:  pre-flight check failed (e.g. missing file); `error` set
    """
    problem: RegisteredProblem
    run_result: Optional[TestRunResult] = None
    skipped: bool = False
    skip_reason: Optional[str] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.run_result is not None

    @property
    def failed(self) -> bool:
        return not self.success and not self.skipped


class TestService:
    """Run tests against a registered problem and record the resulting status."""

    def __init__(self):
        self.logger = get_logger()

    def test_problem(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        *,
        timeout: int = 60,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> TestServiceResult:
        """
        Test `problem` and persist the result to the repo's database.

        Args:
            repo: Repository (used to persist test status).
            problem: The registered problem to test.
            timeout: Per-run timeout in seconds.
            progress_callback: Optional callback for progress updates,
                forwarded to the underlying test runner.

        Returns:
            TestServiceResult with the run outcome, skip reason, or error.
        """
        self.logger.debug(
            f"test_service: testing #{problem.problem_id} "
            f"({problem.language.value}) timeout={timeout}s"
        )

        # Resolve the solution file (hard failure if missing — data is broken)
        if not problem.file_path:
            return self._error(problem, "Problem has no associated file path")

        file_path = Path(problem.file_path)
        if not file_path.is_absolute():
            file_path = repo.root_dir / file_path

        if not file_path.exists():
            return self._error(problem, f"Solution file not found: {file_path}")

        # Make sure we have test cases before invoking the runner.
        # Missing test cases is a soft outcome — the user can still solve it.
        test_cases = fetch_test_cases(problem.problem_id)
        if not test_cases:
            return self._skip(problem, "No test cases available for this problem")

        # Run tests
        run_result = run_tests(
            solution_path=file_path,
            problem_id=problem.problem_id,
            language=problem.language.value,
            timeout=timeout,
            progress_callback=progress_callback,
        )

        # Persist the resulting status to the DB
        self._record_status(repo, problem, run_result)

        self.logger.info(
            f"test_service: #{problem.problem_id} "
            f"status={run_result.status} "
            f"({run_result.passed_count}/{run_result.total_cases})"
        )

        return TestServiceResult(problem=problem, run_result=run_result)

    def _skip(self, problem: RegisteredProblem, reason: str) -> TestServiceResult:
        self.logger.info(
            f"test_service: skipped #{problem.problem_id} — {reason}"
        )
        return TestServiceResult(problem=problem, skipped=True, skip_reason=reason)

    def _error(self, problem: RegisteredProblem, message: str) -> TestServiceResult:
        self.logger.warning(
            f"test_service: failed #{problem.problem_id} — {message}"
        )
        return TestServiceResult(problem=problem, error=message)

    def _record_status(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        run_result: TestRunResult,
    ) -> None:
        with repo.open_db() as db:
            db.update_problem_status(
                problem_db_id=problem.id,
                status=run_result.status,
                output=f"Passed: {run_result.passed_count}/{run_result.total_cases}",
            )
