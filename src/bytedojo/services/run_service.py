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

from bytedojo.core.errors import SolutionNotFoundError, ToolchainMissingError
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
    Outcome of running a registered problem. Pre-flight failures raise
    DojoError subclasses (§10) instead of returning a result.

    `version` and `file_path` reflect what was actually run — useful for
    the CLI header so it shows the v1 path when `--version 1` was used
    even though the `problem` argument carries the latest path.
    """

    problem: RegisteredProblem
    execution: ExecutionResult
    version: Optional[int] = None
    file_path: Optional[Path] = None


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

        # Resolve the solution file (latest, or a specific version). The
        # resolved attempt's language drives the toolchain choice.
        resolved = resolve_solution_path(repo, problem, version=version)
        if not resolved.found:
            raise SolutionNotFoundError(_format_path_error(resolved, version))
        file_path = resolved.path
        run_version = resolved.version
        language = resolved.language or problem.language

        # Resolve the toolchain
        toolchain = get_toolchain(language)
        if toolchain is None:
            raise ToolchainMissingError(
                f"{language.value} has no registered toolchain."
            )

        # Pre-flight: confirm the local toolchain is available
        status = toolchain.detect()
        if not status.found:
            raise ToolchainMissingError(_format_missing_toolchain(status))

        # Build dir for compiled artifacts; interpreted toolchains
        # (Python) ignore this argument.
        build_dir = repo.build_dir / f"{problem.problem_id}_{language.value}"

        # Execute. Defensive OSError catch in case a Toolchain implementation
        # forgets to handle a binary that vanishes between detect() and run.
        try:
            execution = toolchain.execute(
                file_path,
                build_dir=build_dir,
                timeout=timeout,
            )
        except OSError as e:
            raise ToolchainMissingError(f"Execution failed: {e}") from e

        # The run happened — count it on the attempt that was executed.
        if run_version is not None:
            with repo.session() as s:
                s.attempts.increment_run_count(
                    problem.source, problem.problem_id, run_version
                )

        self.logger.debug(
            f"run_service: #{problem.problem_id} v{run_version} "
            f"exit_code={execution.exit_code} timed_out={execution.timed_out}"
        )

        return RunServiceResult(
            problem=problem,
            version=run_version,
            file_path=file_path,
            execution=execution,
        )


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
