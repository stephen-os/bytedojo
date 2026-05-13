"""
Database operations for .dojo repository.

Thin data access layer - handles SQLite interactions only.
Domain logic belongs in Repository or service modules.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List
from datetime import datetime, date, timedelta

from bytedojo.core.models.attempt import Attempt
from bytedojo.core.models.attempt_stats import AttemptStats
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.models.repository_stats import RepositoryStats
from bytedojo.core.models.review_stats import ReviewStats
from bytedojo.core.models.review_schedule import ReviewSchedule


def _row_to_attempt(row: dict) -> Attempt:
    """Thin wrapper around Attempt.from_row (kept for call-site clarity)."""
    return Attempt.from_row(row)


def _apply_migrations(conn: sqlite3.Connection) -> None:
    """
    Idempotently add columns that recent versions of the schema require.

    Existing .dojo databases were created with an older schema; running this
    on every connection (cheap — one PRAGMA per table) keeps them in sync
    without requiring the user to run an explicit `dojo migrate` command.
    """
    cursor = conn.cursor()

    def has_column(table: str, column: str) -> bool:
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())

    # Per-version test results on versioned_attempts.
    if not has_column("versioned_attempts", "test_status"):
        cursor.execute(
            "ALTER TABLE versioned_attempts "
            "ADD COLUMN test_status TEXT DEFAULT 'untested'"
        )
    if not has_column("versioned_attempts", "last_test_run"):
        cursor.execute(
            "ALTER TABLE versioned_attempts ADD COLUMN last_test_run TIMESTAMP"
        )
    if not has_column("versioned_attempts", "test_output"):
        cursor.execute(
            "ALTER TABLE versioned_attempts ADD COLUMN test_output TEXT"
        )

    conn.commit()


def create_database_schema(db_path: Path) -> None:
    """Create SQLite database with schema for tracking problems and stats."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Problems table - stores fetched problems
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'python',
            title TEXT NOT NULL,
            difficulty TEXT,
            category TEXT,
            tags TEXT,
            description TEXT,
            file_path TEXT,
            test_status TEXT DEFAULT 'ungraded',
            last_test_run TIMESTAMP,
            test_output TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, problem_id, language)
        )
    """)

    # Versioned attempts table - tracks solution versions per problem/language.
    # `status` is the manual grade (passed/failed/skipped/ungraded).
    # `test_status` / `last_test_run` / `test_output` capture per-version
    # `dojo test` results so testing v2 doesn't overwrite v1's recorded outcome.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS versioned_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL DEFAULT 'leetcode',
            problem_id INTEGER NOT NULL,
            language TEXT NOT NULL,
            version INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'ungraded',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            run_count INTEGER DEFAULT 0,
            notes TEXT,
            test_status TEXT DEFAULT 'untested',
            last_test_run TIMESTAMP,
            test_output TEXT,
            UNIQUE(source, problem_id, language, version)
        )
    """)

    # Review schedule table - spaced repetition
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER NOT NULL,
            next_review_date DATE NOT NULL,
            interval_days INTEGER DEFAULT 1,
            ease_factor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            FOREIGN KEY (problem_id) REFERENCES problems(id)
        )
    """)

    # Config table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Set default config values
    cursor.execute("""
        INSERT OR IGNORE INTO config (key, value) VALUES
        ('initialized_at', ?),
        ('default_language', 'python'),
        ('default_source', 'leetcode')
    """, (datetime.now().isoformat(),))

    conn.commit()
    conn.close()


class Database:
    """
    Thin data access layer for .dojo SQLite database.

    Usage:
        with Database(db_path) as db:
            problems = db.list_problems()
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> "Database":
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        _apply_migrations(self.conn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    # ------------------------------------------------------------------
    # Problems
    # ------------------------------------------------------------------

    def is_problem_registered(self, source: str, problem_id: int, language: str) -> bool:
        """Check if a problem is registered."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM problems WHERE source = ? AND problem_id = ? AND language = ?",
            (source, str(problem_id), language)
        )
        return cursor.fetchone() is not None

    def register_problem(
        self,
        problem: Problem,
        source: str,
        language: str,
        file_path: Optional[str] = None,
    ) -> None:
        """Register or update a problem in the database."""
        cursor = self.conn.cursor()
        detail = problem.problem_detail

        cursor.execute("""
            INSERT OR REPLACE INTO problems (
                source, problem_id, language, title, difficulty,
                description, file_path, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source,
            str(detail.id),
            language,
            detail.title,
            detail.difficulty.value if hasattr(detail.difficulty, 'value') else str(detail.difficulty),
            detail.description,
            file_path,
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def get_problem(self, source: str, problem_id: int, language: str) -> Optional[RegisteredProblem]:
        """Get a registered problem."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM problems WHERE source = ? AND problem_id = ? AND language = ?",
            (source, str(problem_id), language)
        )
        row = cursor.fetchone()
        return RegisteredProblem.from_row(dict(row)) if row else None

    def list_problems(
        self,
        source: Optional[str] = None,
        difficulty: Optional[str] = None,
        language: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[RegisteredProblem]:
        """List registered problems with optional filters."""
        cursor = self.conn.cursor()

        query = "SELECT * FROM problems WHERE 1=1"
        params = []

        if source:
            query += " AND source = ?"
            params.append(source)
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        if language:
            query += " AND language = ?"
            params.append(language)
        if status:
            if status == "ungraded":
                query += " AND test_status IN ('ungraded', 'untested')"
            else:
                query += " AND test_status = ?"
                params.append(status)

        query += " ORDER BY CAST(problem_id AS INTEGER) ASC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        return [RegisteredProblem.from_row(dict(row)) for row in cursor.fetchall()]

    def update_problem_status(self, problem_db_id: int, status: str, output: Optional[str] = None) -> None:
        """Update the status of a problem."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE problems
            SET test_status = ?, last_test_run = ?, test_output = ?
            WHERE id = ?
        """, (status, datetime.now().isoformat(), output, problem_db_id))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Attempts
    # ------------------------------------------------------------------

    def create_attempt(self, source: str, problem_id: int, language: str) -> Attempt:
        """Create a new versioned attempt."""
        cursor = self.conn.cursor()

        # Get next version
        cursor.execute("""
            SELECT COALESCE(MAX(version), 0) + 1
            FROM versioned_attempts
            WHERE source = ? AND problem_id = ? AND language = ?
        """, (source, problem_id, language))
        version = cursor.fetchone()[0]

        now = datetime.now()
        cursor.execute("""
            INSERT INTO versioned_attempts (source, problem_id, language, version, status, created_at)
            VALUES (?, ?, ?, ?, 'ungraded', ?)
        """, (source, problem_id, language, version, now.isoformat()))
        self.conn.commit()

        return Attempt(
            problem_id=problem_id,
            language=CodeLanguage.from_string(language),
            version=version,
            status=ProblemStatus.UNGRADED,
            created_at=now,
            run_count=0,
            notes="",
        )

    def get_attempt(
        self,
        source: str,
        problem_id: int,
        language: str,
        version: Optional[int] = None,
    ) -> Optional[Attempt]:
        """Get a specific attempt or the latest."""
        cursor = self.conn.cursor()

        if version is not None:
            cursor.execute("""
                SELECT * FROM versioned_attempts
                WHERE source = ? AND problem_id = ? AND language = ? AND version = ?
            """, (source, problem_id, language, version))
        else:
            cursor.execute("""
                SELECT * FROM versioned_attempts
                WHERE source = ? AND problem_id = ? AND language = ?
                ORDER BY version DESC LIMIT 1
            """, (source, problem_id, language))

        row = cursor.fetchone()
        if not row:
            return None
        return _row_to_attempt(dict(row))

    def list_attempts(self, source: str, problem_id: int, language: Optional[str] = None) -> List[Attempt]:
        """List all attempts for a problem."""
        cursor = self.conn.cursor()

        if language:
            cursor.execute("""
                SELECT * FROM versioned_attempts
                WHERE source = ? AND problem_id = ? AND language = ?
                ORDER BY version ASC
            """, (source, problem_id, language))
        else:
            cursor.execute("""
                SELECT * FROM versioned_attempts
                WHERE source = ? AND problem_id = ?
                ORDER BY language, version ASC
            """, (source, problem_id))

        return [_row_to_attempt(dict(row)) for row in cursor.fetchall()]

    def update_attempt_status(self, source: str, problem_id: int, language: str, version: int, status: str) -> bool:
        """Update the grade status (passed/failed/skipped/ungraded) of an attempt."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE versioned_attempts
            SET status = ?
            WHERE source = ? AND problem_id = ? AND language = ? AND version = ?
        """, (status, source, problem_id, language, version))
        self.conn.commit()
        return cursor.rowcount > 0

    def update_attempt_test_status(
        self,
        source: str,
        problem_id: int,
        language: str,
        version: int,
        status: str,
        output: Optional[str] = None,
    ) -> bool:
        """
        Persist `dojo test` results for a specific attempt version.

        Independent of `update_attempt_status` (which is for manual grades)
        — testing v2 no longer overwrites v1's recorded test outcome.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE versioned_attempts
            SET test_status = ?, last_test_run = ?, test_output = ?
            WHERE source = ? AND problem_id = ? AND language = ? AND version = ?
        """, (status, datetime.now().isoformat(), output,
              source, problem_id, language, version))
        self.conn.commit()
        return cursor.rowcount > 0

    def increment_run_count(self, source: str, problem_id: int, language: str, version: int) -> bool:
        """Increment run count for an attempt."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE versioned_attempts
            SET run_count = run_count + 1
            WHERE source = ? AND problem_id = ? AND language = ? AND version = ?
        """, (source, problem_id, language, version))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_attempt_stats(self, source: str, problem_id: int, language: Optional[str] = None) -> dict[str, AttemptStats]:
        """Get attempt stats per language for a problem."""
        cursor = self.conn.cursor()

        query = """
            SELECT
                language,
                COUNT(*) as total_attempts,
                MAX(version) as latest_version,
                SUM(run_count) as total_runs,
                SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as fail_count,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skip_count
            FROM versioned_attempts
            WHERE source = ? AND problem_id = ?
        """
        params = [source, problem_id]

        if language:
            query += " AND language = ?"
            params.append(language)

        query += " GROUP BY language"
        cursor.execute(query, params)

        results = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            lang = row_dict["language"]

            # Get latest status
            cursor.execute("""
                SELECT status FROM versioned_attempts
                WHERE source = ? AND problem_id = ? AND language = ? AND version = ?
            """, (source, problem_id, lang, row_dict["latest_version"]))
            latest = cursor.fetchone()

            results[lang] = AttemptStats(
                problem_id=problem_id,
                language=CodeLanguage.from_string(lang),
                total_attempts=row_dict["total_attempts"],
                latest_version=row_dict["latest_version"],
                latest_status=ProblemStatus.from_string(latest[0]) if latest else ProblemStatus.UNGRADED,
                pass_count=row_dict["pass_count"] or 0,
                fail_count=row_dict["fail_count"] or 0,
                skip_count=row_dict["skip_count"] or 0,
                total_runs=row_dict["total_runs"] or 0,
            )
        return results

    def get_all_attempt_stats(self, source: str) -> dict[int, dict[str, AttemptStats]]:
        """Get attempt stats for all problems."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                problem_id, language,
                COUNT(*) as total_attempts,
                MAX(version) as latest_version,
                SUM(run_count) as total_runs,
                SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as fail_count,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skip_count
            FROM versioned_attempts
            WHERE source = ?
            GROUP BY problem_id, language
        """, (source,))

        results: dict[int, dict[str, AttemptStats]] = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            pid = row_dict["problem_id"]
            lang = row_dict["language"]

            if pid not in results:
                results[pid] = {}

            # Get latest status
            cursor.execute("""
                SELECT status FROM versioned_attempts
                WHERE source = ? AND problem_id = ? AND language = ? AND version = ?
            """, (source, pid, lang, row_dict["latest_version"]))
            latest = cursor.fetchone()

            results[pid][lang] = AttemptStats(
                problem_id=pid,
                language=CodeLanguage.from_string(lang),
                total_attempts=row_dict["total_attempts"],
                latest_version=row_dict["latest_version"],
                latest_status=ProblemStatus.from_string(latest[0]) if latest else ProblemStatus.UNGRADED,
                pass_count=row_dict["pass_count"] or 0,
                fail_count=row_dict["fail_count"] or 0,
                skip_count=row_dict["skip_count"] or 0,
                total_runs=row_dict["total_runs"] or 0,
            )
        return results

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    def schedule_review(self, problem_db_id: int, days_from_now: int) -> None:
        """
        Schedule or reset a review at a fixed interval.

        Used by the initial-schedule path (e.g. on `dojo grade --pass` before
        an SRS track exists). For SM-2-style progression after a review,
        use upsert_review() with computed interval/ease/repetitions.
        """
        cursor = self.conn.cursor()
        next_review = date.today() + timedelta(days=days_from_now)

        cursor.execute("SELECT id, repetitions FROM reviews WHERE problem_id = ?", (problem_db_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE reviews
                SET next_review_date = ?, interval_days = ?, repetitions = repetitions + 1
                WHERE problem_id = ?
            """, (next_review.isoformat(), days_from_now, problem_db_id))
        else:
            cursor.execute("""
                INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
                VALUES (?, ?, ?, 1)
            """, (problem_db_id, next_review.isoformat(), days_from_now))

        self.conn.commit()

    def snooze_review(self, problem_db_id: int, days: int) -> bool:
        """
        Push `next_review_date` out to `today + days` without touching
        the SRS state (interval / ease / repetitions). Returns True if a
        row was updated.
        """
        cursor = self.conn.cursor()
        next_date = (date.today() + timedelta(days=days)).isoformat()
        cursor.execute(
            "UPDATE reviews SET next_review_date = ? WHERE problem_id = ?",
            (next_date, problem_db_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_review(self, problem_db_id: int) -> bool:
        """Drop the review track for a problem. Returns True if a row was deleted."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM reviews WHERE problem_id = ?", (problem_db_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_review(self, problem_db_id: int) -> Optional[ReviewSchedule]:
        """Fetch the review row for a problem (or None if no track exists)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                r.problem_id, r.next_review_date, r.interval_days, r.ease_factor, r.repetitions,
                p.problem_id as problem_num, p.source, p.title, p.difficulty, p.language, p.file_path
            FROM reviews r
            LEFT JOIN problems p ON r.problem_id = p.id
            WHERE r.problem_id = ?
        """, (problem_db_id,))
        row = cursor.fetchone()
        return ReviewSchedule.from_row(dict(row)) if row else None

    def upsert_review(
        self,
        problem_db_id: int,
        *,
        interval_days: int,
        ease_factor: float,
        repetitions: int,
    ) -> None:
        """
        Insert or update a review row with the exact SRS state to persist.

        Unlike schedule_review() which is fixed-interval, this lets the
        ReviewService apply the SM-2 algorithm and store the computed
        next_review_date / interval / ease / repetitions.
        """
        cursor = self.conn.cursor()
        next_review = date.today() + timedelta(days=interval_days)

        cursor.execute("SELECT id FROM reviews WHERE problem_id = ?", (problem_db_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE reviews
                SET next_review_date = ?,
                    interval_days = ?,
                    ease_factor = ?,
                    repetitions = ?
                WHERE problem_id = ?
            """, (next_review.isoformat(), interval_days, ease_factor, repetitions, problem_db_id))
        else:
            cursor.execute("""
                INSERT INTO reviews
                    (problem_id, next_review_date, interval_days, ease_factor, repetitions)
                VALUES (?, ?, ?, ?, ?)
            """, (problem_db_id, next_review.isoformat(), interval_days, ease_factor, repetitions))

        self.conn.commit()

    def get_due_reviews(self, include_future: bool = False) -> List[ReviewSchedule]:
        """Get reviews due for today (or all if include_future), with problem details."""
        cursor = self.conn.cursor()
        today = date.today().isoformat()

        query = """
            SELECT
                r.problem_id, r.next_review_date, r.interval_days, r.ease_factor, r.repetitions,
                p.problem_id as problem_num, p.source, p.title, p.difficulty, p.language, p.file_path
            FROM reviews r
            LEFT JOIN problems p ON r.problem_id = p.id
        """

        if include_future:
            query += " ORDER BY r.next_review_date ASC"
            cursor.execute(query)
        else:
            query += " WHERE r.next_review_date <= ? ORDER BY r.next_review_date ASC"
            cursor.execute(query, (today,))

        return [ReviewSchedule.from_row(dict(row)) for row in cursor.fetchall()]

    def remove_review(self, problem_db_id: int) -> None:
        """Remove a problem from review schedule."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM reviews WHERE problem_id = ?", (problem_db_id,))
        self.conn.commit()

    def get_review_stats(self) -> ReviewStats:
        """Get review statistics."""
        cursor = self.conn.cursor()
        today = date.today()
        week_end = today + timedelta(days=7)

        cursor.execute("SELECT COUNT(*) FROM reviews WHERE next_review_date <= ?", (today.isoformat(),))
        due_today = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reviews WHERE next_review_date <= ?", (week_end.isoformat(),))
        due_this_week = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reviews")
        total = cursor.fetchone()[0]

        return ReviewStats(due_today=due_today, due_this_week=due_this_week, total_in_review=total)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_summary_stats(self) -> RepositoryStats:
        """Get repository summary statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM problems")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT difficulty, COUNT(*) FROM problems GROUP BY difficulty")
        by_difficulty = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

        cursor.execute("SELECT source, COUNT(*) FROM problems GROUP BY source")
        by_source = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

        cursor.execute("SELECT language, COUNT(*) FROM problems GROUP BY language")
        by_language = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

        return RepositoryStats(
            total_problems=total,
            by_difficulty=by_difficulty,
            by_source=by_source,
            by_language=by_language,
        )

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a config value."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_config(self, key: str, value: str) -> None:
        """Set a config value."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_all_config(self) -> dict[str, str]:
        """Get all config values."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM config")
        return {row[0]: row[1] for row in cursor.fetchall()}
