"""
RegisteredProblem - A problem that has been fetched and registered in the database.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_status import ProblemStatus


@dataclass
class RegisteredProblem:
    """A problem registered in the .dojo database."""
    id: int  # database row id
    source: str
    problem_id: int
    language: CodeLanguage
    title: str
    difficulty: ProblemDifficulty
    description: str
    file_path: Optional[str]
    status: ProblemStatus
    fetched_at: datetime
    last_graded: Optional[datetime] = None
    notes: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "RegisteredProblem":
        """Build from a database row dict."""
        last_graded = row.get("last_graded")
        if last_graded and isinstance(last_graded, str):
            last_graded = datetime.fromisoformat(last_graded)

        return cls(
            id=row["id"],
            source=row["source"],
            problem_id=int(row["problem_id"]),
            language=CodeLanguage.from_string(row.get("language", "python")),
            title=row["title"],
            difficulty=ProblemDifficulty.from_string(row.get("difficulty", "")),
            description=row.get("description", ""),
            file_path=row.get("file_path"),
            status=ProblemStatus.from_string(row["status"]),
            fetched_at=datetime.fromisoformat(row["fetched_at"]) if row.get("fetched_at") else datetime.now(),
            last_graded=last_graded,
            notes=row.get("notes"),
        )
