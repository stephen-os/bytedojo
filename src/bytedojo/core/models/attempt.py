from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus


@dataclass
class Attempt:
    """A single versioned attempt at solving a problem in a language."""
    problem_id: int
    language: CodeLanguage
    version: int
    status: ProblemStatus               # grade status (passed/failed/skipped/ungraded)
    created_at: datetime
    run_count: int = 0
    notes: str = ""
    test_status: ProblemStatus = ProblemStatus.UNGRADED  # per-version `dojo test` outcome
    last_test_run: Optional[datetime] = None
    test_output: Optional[str] = None   # e.g. "Passed: 72/80"

    def get_version_string(self) -> str:
        """Get version as v001, v002, etc."""
        return f"v{self.version:03d}"
