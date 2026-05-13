"""
Test service - run tests against a registered problem and persist the result.

Stub: the previous codegen-at-runtime pipeline was removed by the data
migration (see data/MIGRATION.md). The universal-runner-per-language
replacement reads data/tests/{id}.json via TestBundle and dispatches the
user's Solution against the bundled cases. Until that lands, every
test_problem() call returns a TestServiceResult flagged with `error`.

The public dataclasses (TestCaseResult, TestRunResult, TestServiceResult)
stay in place so the CLI display code and the services/__init__.py
re-exports keep working.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from bytedojo.core.logger import get_logger
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository


# ----------------------------------------------------------------------------
# Test result structs (kept so CLI display code can compile)
# ----------------------------------------------------------------------------

@dataclass
class TestCaseResult:
    """Result of running a single test case."""
    case_number: int
    passed: bool
    input_str: str
    expected: str
    actual: str
    error: Optional[str] = None
    timed_out: bool = False


@dataclass
class TestRunResult:
    """Result of running all test cases for a problem."""
    problem_id: int
    language: str
    total_cases: int
    passed_count: int
    failed_count: int
    error_count: int
    skipped_count: int = 0
    case_results: List[TestCaseResult] = field(default_factory=list)
    compile_error: Optional[str] = None
    runtime_error: Optional[str] = None

    @property
    def runnable_count(self) -> int:
        """Cases that actually ran (excludes filtered/skipped)."""
        return self.total_cases - self.skipped_count

    @property
    def all_passed(self) -> bool:
        return self.runnable_count > 0 and self.passed_count == self.runnable_count

    @property
    def status(self) -> str:
        if self.compile_error:
            return 'error'
        if self.all_passed:
            return 'passed'
        if self.failed_count > 0 or self.error_count > 0:
            return 'failed'
        return 'untested'


@dataclass
class TestServiceResult:
    """Outcome of testing a registered problem."""
    problem: RegisteredProblem
    version: Optional[int] = None
    file_path: Optional[Path] = None
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


# ----------------------------------------------------------------------------
# TestService — stubbed until the universal runner lands
# ----------------------------------------------------------------------------

_NOT_IMPLEMENTED_MSG = (
    "Test execution is temporarily unavailable. The legacy codegen pipeline "
    "was removed during the data migration to the typed test schema "
    "(data/tests/{id}.json). The universal-runner replacement is in progress."
)


class TestService:
    """Placeholder until the universal-runner-per-language implementation lands."""

    def __init__(self):
        self.logger = get_logger()

    def test_problem(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        *,
        version: Optional[int] = None,
        timeout: int = 60,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> TestServiceResult:
        """Return a 'not yet implemented' error result for every call."""
        self.logger.warning(
            f"test_service: #{problem.problem_id} ({problem.language.value}) "
            f"not run — universal runner pending"
        )
        return TestServiceResult(problem=problem, error=_NOT_IMPLEMENTED_MSG)
