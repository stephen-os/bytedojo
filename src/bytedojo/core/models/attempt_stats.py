from dataclasses import dataclass

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus


@dataclass
class AttemptStats:
    """Aggregated stats for a problem/language combination."""
    problem_id: int
    language: CodeLanguage
    total_attempts: int
    latest_version: int
    latest_status: ProblemStatus
    pass_count: int
    fail_count: int
    skip_count: int
    total_runs: int
