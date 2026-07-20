"""
Grading service - apply grades and schedule reviews for passed problems.

Migrated from core/grading.py to match the services/ result-struct pattern.
Takes a Repository per call (rather than a Database in __init__) so the CLI
and TUI can both drive grading through the same API.
"""

from dataclasses import dataclass
from typing import List, Optional

from bytedojo.core.logger import get_logger
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository


#: The statuses a user can manually apply via `dojo grade` — derived from
#: ProblemStatus so the canonical vocabulary stays single-sourced.
#: UNGRADED is a state (not yet graded), not a grade you apply, so it's
#: excluded; UNKNOWN is the unrecognized-input fallback.
_VALID_GRADE_STATUSES = (
    ProblemStatus.PASSED,
    ProblemStatus.FAILED,
    ProblemStatus.SKIPPED,
)
_VALID_GRADE_VALUES = tuple(s.value for s in _VALID_GRADE_STATUSES)


@dataclass
class GradeResult:
    """
    Outcome of grading a problem.

    Mutually-exclusive states:
      - success: grade was applied; `status` reflects what was recorded
      - failed:  pre-flight check failed (e.g. invalid status); `error` set
    """
    problem: RegisteredProblem
    status: Optional[str] = None
    notes: Optional[str] = None
    scheduled_review: bool = False
    review_frequency_days: int = 0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def failed(self) -> bool:
        return self.error is not None


class GradingService:
    """Apply pass/fail/skip grades to registered problems and schedule reviews."""

    def __init__(self):
        self.logger = get_logger()

    def grade(
        self,
        repo: Repository,
        problem: RegisteredProblem,
        *,
        status: str,
        notes: Optional[str] = None,
    ) -> GradeResult:
        """
        Apply a grade to `problem` and (if passed) schedule the next review.

        Args:
            repo: Repository (used to persist status and review schedule).
            problem: The registered problem to grade.
            status: Grade status — must be one of 'passed', 'failed', 'skipped'.
            notes: Optional notes about the grade.

        Returns:
            GradeResult with the applied status and review scheduling info,
            or an error if the status string is invalid.
        """
        if status not in _VALID_GRADE_VALUES:
            return GradeResult(
                problem=problem,
                error=(
                    f"Invalid status '{status}'. "
                    f"Must be one of: {', '.join(_VALID_GRADE_VALUES)}"
                ),
            )

        with repo.open_db() as db:
            db.update_problem_status(problem.id, status, notes)
            # The attempt row is what `dojo query` reads for its status badge,
            # so the grade has to land on both or the two disagree.
            db.update_latest_attempt_status(
                problem.source, problem.problem_id, problem.language.value, status
            )
            review_freq = int(db.get_config('review_frequency_days', '7'))

        scheduled = False
        if status == 'passed':
            # Start (or reset) the SRS track at the base interval. Future
            # SM-2 progression happens through ReviewService.complete_review.
            from bytedojo.services.review_service import ReviewService
            ReviewService().initial_schedule(repo, problem.id)
            scheduled = True

        self.logger.debug(
            f"grading_service: graded #{problem.problem_id} as {status} "
            f"(scheduled_review={scheduled})"
        )

        return GradeResult(
            problem=problem,
            status=status,
            notes=notes,
            scheduled_review=scheduled,
            review_frequency_days=review_freq,
        )

    def list_by_status(
        self,
        repo: Repository,
        status: str,
    ) -> List[RegisteredProblem]:
        """List registered problems with the given status."""
        with repo.open_db() as db:
            return db.list_problems(status=status)

    def list_ungraded(self, repo: Repository) -> List[RegisteredProblem]:
        """List registered problems that have not been graded yet."""
        return self.list_by_status(repo, 'ungraded')
