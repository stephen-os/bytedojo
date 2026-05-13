"""
AttemptStats - aggregated counts for a problem/language combination.

Built by `database.list_attempt_stats` from a GROUP BY over the
versioned_attempts table. Used by the `dojo stats` command to render
per-problem grade summaries (how many versions, how many passed, etc.).
"""

from dataclasses import dataclass

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus


@dataclass
class AttemptStats:
    """Aggregated stats across all versions of a problem/language combination."""
    problem_id: int
    language: CodeLanguage
    total_attempts: int
    latest_version: int
    latest_status: ProblemStatus
    pass_count: int
    fail_count: int
    skip_count: int
    total_runs: int
