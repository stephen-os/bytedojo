"""
ProblemsRepository — persistence for the problems aggregate.

One row per (source, problem_id). `language` and `file_path` describe
the problem's latest attempt; `status` is the per-problem grade driven
by the state machine in §9.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

from bytedojo.core.models.problem import Problem
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.models.repository_stats import RepositoryStats


class ProblemsRepository:
    """Raw-sqlite persistence for registered problems."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def is_registered(self, source: str, problem_id: int) -> bool:
        """Whether a problem row exists for (source, problem_id)."""
        row = self._conn.execute(
            "SELECT 1 FROM problems WHERE source = ? AND problem_id = ?",
            (source, problem_id),
        ).fetchone()
        return row is not None

    def register(
        self,
        problem: Problem,
        *,
        source: str,
        language: str,
        file_path: Optional[str] = None,
    ) -> None:
        """Insert or refresh a problem row.

        On re-register (a new attempt) the row id and recorded grade are
        preserved — only the metadata, latest-attempt language/path and
        fetched_at move.
        """
        detail = problem.problem_detail
        self._conn.execute(
            """
            INSERT INTO problems (
                source, problem_id, language, title, difficulty,
                description, file_path, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, problem_id) DO UPDATE SET
                language = excluded.language,
                title = excluded.title,
                difficulty = excluded.difficulty,
                description = excluded.description,
                file_path = excluded.file_path,
                fetched_at = excluded.fetched_at
            """,
            (
                source,
                detail.id,
                language,
                detail.title,
                detail.difficulty.value,
                detail.description,
                file_path,
                datetime.now().isoformat(),
            ),
        )
        self._conn.commit()

    def get(self, source: str, problem_id: int) -> Optional[RegisteredProblem]:
        """The registered problem for (source, problem_id), or None."""
        row = self._conn.execute(
            "SELECT * FROM problems WHERE source = ? AND problem_id = ?",
            (source, problem_id),
        ).fetchone()
        return RegisteredProblem.from_row(dict(row)) if row else None

    def list(
        self,
        *,
        source: Optional[str] = None,
        difficulty: Optional[str] = None,
        language: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[RegisteredProblem]:
        """Registered problems matching the filters, ordered by problem id."""
        query = "SELECT * FROM problems WHERE 1=1"
        params: list = []
        for clause, value in (
            (" AND source = ?", source),
            (" AND difficulty = ?", difficulty),
            (" AND language = ?", language),
            (" AND status = ?", status),
        ):
            if value:
                query += clause
                params.append(value)
        query += " ORDER BY problem_id ASC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        rows = self._conn.execute(query, params).fetchall()
        return [RegisteredProblem.from_row(dict(row)) for row in rows]

    def latest(self, *, source: Optional[str] = None) -> Optional[RegisteredProblem]:
        """The most recently fetched problem, or None if none registered."""
        query = "SELECT * FROM problems"
        params: list = []
        if source:
            query += " WHERE source = ?"
            params.append(source)
        query += " ORDER BY fetched_at DESC, id DESC LIMIT 1"
        row = self._conn.execute(query, params).fetchone()
        return RegisteredProblem.from_row(dict(row)) if row else None

    def update_status(
        self,
        problem_db_id: int,
        status: str,
        notes: Optional[str] = None,
    ) -> None:
        """Record a grade on the problem row, stamping when it was graded."""
        self._conn.execute(
            "UPDATE problems SET status = ?, last_graded = ?, notes = ? WHERE id = ?",
            (status, datetime.now().isoformat(), notes, problem_db_id),
        )
        self._conn.commit()

    def summary_stats(self) -> RepositoryStats:
        """Registered-problem counts grouped by difficulty / source / language."""
        total = self._conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]

        def _group(column: str) -> dict:
            rows = self._conn.execute(
                f"SELECT {column}, COUNT(*) FROM problems GROUP BY {column}"
            ).fetchall()
            return {row[0]: row[1] for row in rows if row[0]}

        return RepositoryStats(
            total_problems=total,
            by_difficulty=_group("difficulty"),
            by_source=_group("source"),
            by_language=_group("language"),
        )
