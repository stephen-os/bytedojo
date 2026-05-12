"""
Run service - execute a registered problem's solution and capture output.

Delegates execution to the per-language Toolchain registry. Adding a new
language is purely a matter of registering its Toolchain — the service
does not need to change.

The caller is responsible for problem lookup / disambiguation
(see services.problem_service.find_registered_problems).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from bytedojo.core.logger import get_logger
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.core.toolchains import (
    DEFAULT_TIMEOUT_SECONDS,
    ExecutionResult,
    get_toolchain,
)
from bytedojo.services.problem_service import resolve_solution_path


@dataclass
class RunServiceResult:
    """
    Outcome of running a registered problem.

    Mutually-exclusive states:
      - success: execution finished (regardless of exit code); `execution` set
      - failed:  pre-flight check failed (e.g. missing file, missing
                 toolchain, unsupported language); `error` set
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
        version: Optional[int] = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> RunServiceResult:
        """
        Execute `problem`'s solution and capture the output.

        Args:
            repo: Repository (used to resolve the solution path).
            problem: The registered problem to execute.
            version: Specific version to run, or None for the latest.
            timeout: Execution timeout in seconds.

        Returns:
            RunServiceResult with the execution outcome or a pre-flight error.
        """
        self.logger.debug(
            f"run_service: running #{problem.problem_id} "
            f"({problem.language.value}) version={version or 'latest'} "
            f"timeout={timeout}s"
        )

        # Resolve the solution file (latest, or a specific version)
        resolved = resolve_solution_path(repo, problem, version=version)
        if not resolved.found:
            return self._error(problem, _format_path_error(resolved, version))
        file_path = resolved.path

        # Resolve the toolchain
        toolchain = get_toolchain(problem.language)
        if toolchain is None:
            return self._error(
                problem,
                f"{problem.language.value} is not yet supported. "
                f"Only Python is implemented at this time.",
            )

        # Pre-flight: confirm the local toolchain is available
        status = toolchain.detect()
        if not status.found:
            return self._error(problem, _format_missing_toolchain(status))

        # Build dir for compiled artifacts (Java .class, C++ binary).
        # Interpreted toolchains (Python) ignore this argument.
        build_dir = repo.build_dir / f"{problem.problem_id}_{problem.language.value}"

        # Execute. Defensive OSError catch in case a Toolchain implementation
        # forgets to handle a binary that vanishes between detect() and run.
        try:
            execution = toolchain.execute(
                file_path, build_dir=build_dir, timeout=timeout,
            )
        except OSError as e:
            return self._error(problem, f"Execution failed: {e}")

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


def _format_missing_toolchain(status) -> str:
    """Render a missing-toolchain ToolchainStatus into an actionable message."""
    lines = [f"{status.language.value} toolchain not found."]
    if status.missing:
        lines.append(f"  Missing: {', '.join(status.missing)}")
    if status.install_hint:
        lines.append(f"  Install: {status.install_hint}")
    return "\n".join(lines)


def _format_path_error(resolved, requested_version: Optional[int]) -> str:
    """Render a SolutionPathResult error, listing available versions if relevant."""
    msg = resolved.error or "Solution path could not be resolved"
    if requested_version is not None and resolved.available_versions:
        avail = ", ".join(f"v{v}" for v in resolved.available_versions)
        msg = f"{msg}. Available: {avail}"
    return msg
