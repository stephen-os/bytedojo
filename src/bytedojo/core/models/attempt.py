from dataclasses import dataclass
from datetime import datetime

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus


@dataclass
class Attempt:
    """A single versioned attempt at solving a problem in a language."""
    problem_id: int
    language: CodeLanguage
    version: int
    status: ProblemStatus
    created_at: datetime
    run_count: int = 0
    notes: str = ""

    def get_version_string(self) -> str:
        """Get version as v001, v002, etc."""
        return f"v{self.version:03d}"
