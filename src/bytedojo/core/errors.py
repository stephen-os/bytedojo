"""
Error taxonomy for the ByteDojo CLI.

Every user-facing failure raises a DojoError subclass carrying an exit
code and an actionable message. main() catches DojoError at the top
level, renders the message, and exits with the carried code — commands
and services never call sys.exit themselves.

Click usage errors keep Click's own exit code 2; SIGINT keeps 130.
"""


class DojoError(Exception):
    """Base for all user-facing ByteDojo failures."""

    exit_code = 1

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class RepoNotFoundError(DojoError):
    """No .dojo repository in the current directory or any ancestor."""

    def __init__(self, message: str = ""):
        super().__init__(
            message or "Not inside a .dojo repository. Run 'dojo init' first."
        )


class ProblemNotFoundError(DojoError):
    """A problem selector (id / --name / --desc / --last) matched nothing."""


class UnsupportedProblemError(DojoError):
    """Fetch of one or more problem ids outside the bundled catalog."""

    def __init__(self, problem_ids):
        ids = [problem_ids] if isinstance(problem_ids, int) else list(problem_ids)
        label = ", ".join(f"#{pid}" for pid in ids)
        noun = "Problems" if len(ids) > 1 else "Problem"
        verb = "are" if len(ids) > 1 else "is"
        super().__init__(
            f"{noun} {label} {verb} not in the bundled catalog. "
            f"Browse supported problems with 'dojo query'."
        )
        self.problem_ids = ids


class SolutionNotFoundError(DojoError):
    """No solution file / version on disk for the resolved attempt."""


class BundleNotFoundError(DojoError):
    """Defensive: a registered problem has no test bundle (should not happen)."""

    def __init__(self, problem_id: int):
        super().__init__(
            f"No test bundle for problem #{problem_id}. "
            f"The bundled corpus may be corrupted — reinstall bytedojo."
        )
        self.problem_id = problem_id


class ToolchainMissingError(DojoError):
    """A required language interpreter/compiler is absent."""


class DataError(DojoError):
    """Bundled corpus or repository database is malformed."""
