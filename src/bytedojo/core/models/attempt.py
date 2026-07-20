"""
Attempt - a single versioned attempt at solving a problem in a language.

Each `dojo fetch` of a problem registers a new attempt with version
`v001`, `v002`, ... Re-fetching with `--version N` rewrites that version
in place rather than incrementing. Attempts are stored in the
`versioned_attempts` table and round-trip through `from_row` /
`_row_to_attempt`.
"""

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
    status: ProblemStatus               # grade status (passed/failed/skipped/ungraded)
    created_at: datetime
    run_count: int = 0
    notes: str = ""

    @classmethod
    def from_row(cls, row: dict) -> "Attempt":
        """Build an Attempt from a versioned_attempts row dict."""
        return cls(
            problem_id=row["problem_id"],
            language=CodeLanguage.from_string(row["language"]),
            version=row["version"],
            status=ProblemStatus.from_string(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            run_count=row.get("run_count", 0),
            notes=row.get("notes", "") or "",
        )

    def get_version_string(self) -> str:
        """Return version as `v001`, `v002`, etc."""
        return f"v{self.version:03d}"
