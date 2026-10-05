"""
AttemptsRepository — persistence for versioned solution attempts.

Versions are flat per problem (§7.1): `version` is a monotonic ordinal
per (source, problem_id) regardless of language. Language is a column
recording what each attempt was written in; it drives the file
extension and toolchain choice, never the version key.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

from bytedojo.core.models.attempt import Attempt
from bytedojo.core.models.attempt_stats import AttemptStats
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus


class AttemptsRepository:
    """Raw-sqlite persistence for versioned attempts."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, source: str, problem_id: int, language: str) -> Attempt:
        """Create the next attempt (version = MAX+1 for the problem)."""
        version = self._conn.execute(
            """
            SELECT COALESCE(MAX(version), 0) + 1 FROM attempts
            WHERE source = ? AND problem_id = ?
            """,
            (source, problem_id),
        ).fetchone()[0]

        now = datetime.now()
        self._conn.execute(
            """
            INSERT INTO attempts (source, problem_id, language, version, status, created_at)
            VALUES (?, ?, ?, ?, 'ungraded', ?)
            """,
            (source, problem_id, language, version, now.isoformat()),
        )
        self._conn.commit()

        return Attempt(
            problem_id=problem_id,
            language=CodeLanguage.from_string(language),
            version=version,
            status=ProblemStatus.UNGRADED,
            created_at=now,
            run_count=0,
            notes="",
        )

    def get(
        self,
        source: str,
        problem_id: int,
        version: Optional[int] = None,
    ) -> Optional[Attempt]:
        """A specific attempt, or the latest when `version` is None."""
        if version is not None:
            row = self._conn.execute(
                """
                SELECT * FROM attempts
                WHERE source = ? AND problem_id = ? AND version = ?
                """,
                (source, problem_id, version),
            ).fetchone()
        else:
            row = self._conn.execute(
                """
                SELECT * FROM attempts
                WHERE source = ? AND problem_id = ?
                ORDER BY version DESC LIMIT 1
                """,
                (source, problem_id),
            ).fetchone()
        return Attempt.from_row(dict(row)) if row else None

    def list(self, source: str, problem_id: int) -> List[Attempt]:
        """All attempts for a problem, oldest version first."""
        rows = self._conn.execute(
            """
            SELECT * FROM attempts
            WHERE source = ? AND problem_id = ?
            ORDER BY version ASC
            """,
            (source, problem_id),
        ).fetchall()
        return [Attempt.from_row(dict(row)) for row in rows]

    def update_status(
        self,
        source: str,
        problem_id: int,
        version: int,
        status: str,
    ) -> bool:
        """Record a grade on one attempt. Returns True if a row changed."""
        cursor = self._conn.execute(
            """
            UPDATE attempts SET status = ?
            WHERE source = ? AND problem_id = ? AND version = ?
            """,
            (status, source, problem_id, version),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def update_latest_status(self, source: str, problem_id: int, status: str) -> bool:
        """Grade the newest attempt; older versions keep their outcome."""
        cursor = self._conn.execute(
            """
            UPDATE attempts SET status = ?
            WHERE source = ? AND problem_id = ?
              AND version = (
                  SELECT MAX(version) FROM attempts
                  WHERE source = ? AND problem_id = ?
              )
            """,
            (status, source, problem_id, source, problem_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def increment_run_count(self, source: str, problem_id: int, version: int) -> bool:
        """Bump run_count for one attempt. Returns True if a row changed."""
        cursor = self._conn.execute(
            """
            UPDATE attempts SET run_count = run_count + 1
            WHERE source = ? AND problem_id = ? AND version = ?
            """,
            (source, problem_id, version),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def stats(self, source: str, problem_id: int) -> Optional[AttemptStats]:
        """Aggregate attempt counts for one problem, or None if no attempts."""
        row = self._conn.execute(
            self._STATS_QUERY + " WHERE source = ? AND problem_id = ?",
            (source, problem_id),
        ).fetchone()
        if row is None or row["total_attempts"] == 0:
            return None
        return self._stats_from_row(dict(row), source)

    def all_stats(self, source: str) -> dict[int, AttemptStats]:
        """Aggregate attempt counts for every problem with attempts."""
        rows = self._conn.execute(
            self._STATS_QUERY + " WHERE source = ? GROUP BY problem_id",
            (source,),
        ).fetchall()
        return {
            row["problem_id"]: self._stats_from_row(dict(row), source) for row in rows
        }

    _STATS_QUERY = """
        SELECT
            problem_id,
            COUNT(*) as total_attempts,
            MAX(version) as latest_version,
            SUM(run_count) as total_runs,
            SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as pass_count,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as fail_count,
            SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skip_count
        FROM attempts
    """

    def _stats_from_row(self, row: dict, source: str) -> AttemptStats:
        latest = self._conn.execute(
            """
            SELECT status, language FROM attempts
            WHERE source = ? AND problem_id = ? AND version = ?
            """,
            (source, row["problem_id"], row["latest_version"]),
        ).fetchone()
        return AttemptStats(
            problem_id=row["problem_id"],
            language=(
                CodeLanguage.from_string(latest["language"])
                if latest
                else CodeLanguage.UNKNOWN
            ),
            total_attempts=row["total_attempts"],
            latest_version=row["latest_version"],
            latest_status=(
                ProblemStatus.from_string(latest["status"])
                if latest
                else ProblemStatus.UNGRADED
            ),
            pass_count=row["pass_count"] or 0,
            fail_count=row["fail_count"] or 0,
            skip_count=row["skip_count"] or 0,
            total_runs=row["total_runs"] or 0,
        )
