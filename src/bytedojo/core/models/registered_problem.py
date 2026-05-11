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
    last_test_run: Optional[datetime] = None
    test_output: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "RegisteredProblem":
        """Build from a database row dict."""
        last_run = row.get("last_test_run")
        if last_run and isinstance(last_run, str):
            last_run = datetime.fromisoformat(last_run)

        return cls(
            id=row["id"],
            source=row["source"],
            problem_id=int(row["problem_id"]),
            language=CodeLanguage.from_string(row.get("language", "python")),
            title=row["title"],
            difficulty=ProblemDifficulty.from_string(row.get("difficulty", "")),
            description=row.get("description", ""),
            file_path=row.get("file_path"),
            status=ProblemStatus.from_string(row.get("test_status", "ungraded")),
            fetched_at=datetime.fromisoformat(row["fetched_at"]) if row.get("fetched_at") else datetime.now(),
            last_test_run=last_run,
            test_output=row.get("test_output"),
        )
