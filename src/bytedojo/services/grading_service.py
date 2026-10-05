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
from bytedojo.core.settings import SettingsManager
from bytedojo.services.review_service import ReviewService, ScheduleEffect

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
    schedule_effect: Optional[ScheduleEffect] = None
    review_frequency_days: int = 0
    error: Optional[str] = None

    @property
    def scheduled_review(self) -> bool:
        """Whether this grade created a fresh review track."""
        return (
            self.schedule_effect is not None
            and self.schedule_effect.action == "created"
        )

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

        with repo.session() as s:
            s.problems.update_status(problem.id, status, notes)
            # The attempt row is what `dojo query` reads for its status badge,
            # so the grade has to land on both or the two disagree.
            s.attempts.update_latest_status(problem.source, problem.problem_id, status)
        review_freq = SettingsManager(repo.dojo_dir).load().review_frequency_days

        # Schedule effect per the §9 state machine — manual grades trust
        # the user the same way a test outcome is trusted.
        reviews = ReviewService()
        if status == "passed":
            effect = reviews.apply_pass(repo, problem.id)
        elif status == "failed":
            effect = reviews.apply_fail(repo, problem.id)
        else:  # skipped — set the problem aside
            effect = reviews.apply_skip(repo, problem.id)

        self.logger.debug(
            f"grading_service: graded #{problem.problem_id} as {status} "
            f"(schedule={effect.action})"
        )

        return GradeResult(
            problem=problem,
            status=status,
            notes=notes,
            schedule_effect=effect,
            review_frequency_days=review_freq,
        )

    def list_by_status(
        self,
        repo: Repository,
        status: str,
    ) -> List[RegisteredProblem]:
        """List registered problems with the given status."""
        with repo.session() as s:
            return s.problems.list(status=status)

    def list_ungraded(self, repo: Repository) -> List[RegisteredProblem]:
        """List registered problems that have not been graded yet."""
        return self.list_by_status(repo, "ungraded")
