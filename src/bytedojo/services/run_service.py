"""
Run service - execute a registered problem's solution and capture output.

Wraps the existing core.execution.ProblemExecutor so the CLI and (upcoming)
TUI can drive runs through the same result-struct API.

The caller is responsible for problem lookup / disambiguation
(see services.problem_service.find_registered_problems).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from bytedojo.core.execution import (
    DEFAULT_TIMEOUT_SECONDS,
    ExecutionResult,
    ProblemExecutor,
)
from bytedojo.core.logger import get_logger
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository


@dataclass
class RunServiceResult:
    """
    Outcome of running a registered problem.

    Mutually-exclusive states:
      - success: execution finished (regardless of exit code); `execution` set
      - failed:  pre-flight check failed (e.g. missing file); `error` set
    """
    problem: RegisteredProblem
    execution: Optional[ExecutionResult] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.execution is not None

    @property
    def failed(self) -> bool:
        return not self.success


class RunService:
    """Execute a registered problem's solution and capture its output."""

    def __init__(self):
        self.logger = get_logger()

    def run_problem(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        *,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> RunServiceResult:
        """
        Execute `problem`'s solution and capture the output.

        Args:
            repo: Repository (used by the executor for build paths).
            problem: The registered problem to execute.
            timeout: Execution timeout in seconds.

        Returns:
            RunServiceResult with the execution outcome or a pre-flight error.
        """
        self.logger.debug(
            f"run_service: running #{problem.problem_id} "
            f"({problem.language.value}) timeout={timeout}s"
        )

        # Resolve the solution file
        if not problem.file_path:
            return self._error(problem, "Problem has no associated file path")

        file_path = Path(problem.file_path)
        if not file_path.is_absolute():
            file_path = repo.root_dir / file_path

        if not file_path.exists():
            return self._error(problem, f"Solution file not found: {file_path}")

        # ProblemExecutor still expects a dict (legacy from before the
        # RegisteredProblem dataclass refactor). Build the minimum shape it
        # needs and pass the already-resolved absolute path so the executor's
        # own cwd-based fallback never kicks in.
        executor_input = {
            "language": problem.language.value,
            "file_path": str(file_path),
            "problem_id": str(problem.problem_id),
        }

        try:
            execution = ProblemExecutor(repo).execute(executor_input, timeout=timeout)
        except ValueError as e:
            return self._error(problem, str(e))

        self.logger.info(
            f"run_service: #{problem.problem_id} "
            f"exit_code={execution.exit_code} timed_out={execution.timed_out}"
        )

        return RunServiceResult(problem=problem, execution=execution)

    def _error(self, problem: RegisteredProblem, message: str) -> RunServiceResult:
        self.logger.warning(
            f"run_service: failed #{problem.problem_id} — {message}"
        )
        return RunServiceResult(problem=problem, error=message)
