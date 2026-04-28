"""
Database operations for .dojo repository.

Handles all SQLite interactions for problems, attempts, stats, etc.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from bytedojo.core.leetcode.models import Problem
from bytedojo.core.logger import get_logger


def create_database_schema(db_path: Path):
    """
    Create SQLite database with schema for tracking problems and stats.
    
    Args:
        db_path: Path to SQLite database file
    """
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
            test_status TEXT DEFAULT 'untested',
            last_test_run TIMESTAMP,
            test_output TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, problem_id, language)
        )
    """)

    # Migration: Add language column to existing databases
    try:
        cursor.execute("ALTER TABLE problems ADD COLUMN language TEXT NOT NULL DEFAULT 'python'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Attempts table - tracks solution attempts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER NOT NULL,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            passed BOOLEAN NOT NULL,
            time_taken INTEGER,
            notes TEXT,
            FOREIGN KEY (problem_id) REFERENCES problems(id)
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
    
    # Stats table - aggregate statistics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL UNIQUE,
            problems_attempted INTEGER DEFAULT 0,
            problems_solved INTEGER DEFAULT 0,
            total_time_minutes INTEGER DEFAULT 0
        )
    """)
    
    # User preferences
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
        ('default_source', 'leetcode'),
        ('problems_dir', 'problems'),
        ('review_frequency_days', '7')
    """, (datetime.now().isoformat(),))
    
    conn.commit()
    conn.close()


class DatabaseManager:
    """Manages database operations for .dojo repository."""
    
    def __init__(self, db_path: Path):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.logger = get_logger()
    
    def connect(self):
        """Open database connection."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def is_problem_registered(self, source: str, problem_id: int, language: str = 'python') -> bool:
        """
        Check if problem is already registered.

        Args:
            source: Problem source (e.g., 'leetcode')
            problem_id: Problem ID number
            language: Programming language (default: 'python')

        Returns:
            True if problem exists in database
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM problems WHERE source = ? AND problem_id = ? AND language = ?",
            (source, str(problem_id), language)
        )
        count = cursor.fetchone()[0]
        return count > 0
    
    def register_problem(
        self,
        problem: Problem,
        source: str = "leetcode",
        language: str = "python",
        file_path: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """
        Register a problem in the database.

        Args:
            problem: Problem object to register
            source: Problem source (default: 'leetcode')
            language: Programming language (default: 'python')
            file_path: Path to the problem file
            force: If True, overwrite existing entry

        Returns:
            True if registered successfully
        """
        cursor = self.conn.cursor()

        # Check if already exists
        if self.is_problem_registered(source, problem.id, language) and not force:
            return False

        # Insert or replace
        cursor.execute("""
            INSERT OR REPLACE INTO problems (
                source, problem_id, language, title, difficulty, category,
                tags, description, file_path, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source,
            str(problem.id),
            language,
            problem.title,
            problem.difficulty,
            None,  # category - TODO: extract from tags
            None,  # tags - TODO: extract from problem data
            problem.description,
            str(file_path) if file_path else None,
            datetime.now().isoformat()
        ))

        self.conn.commit()
        return True
    
    def get_problem(self, source: str, problem_id: int, language: str = 'python') -> Optional[Dict[str, Any]]:
        """
        Get problem from database.

        Args:
            source: Problem source
            problem_id: Problem ID
            language: Programming language (default: 'python')

        Returns:
            Problem data as dict or None
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM problems WHERE source = ? AND problem_id = ? AND language = ?",
            (source, str(problem_id), language)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def list_problems(
        self,
        source: Optional[str] = None,
        difficulty: Optional[str] = None,
        language: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List problems from database.

        Args:
            source: Filter by source (e.g., 'leetcode')
            difficulty: Filter by difficulty (e.g., 'Easy')
            language: Filter by language (e.g., 'python', 'java', 'cpp')
            limit: Maximum number of results

        Returns:
            List of problem dictionaries
        """
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

        query += " ORDER BY problem_id ASC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_problem_stats(self, problem_db_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific problem.
        
        Args:
            problem_db_id: Database ID of the problem
            
        Returns:
            Dictionary with attempt statistics
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) as passed_attempts,
                SUM(CASE WHEN passed = 0 THEN 1 ELSE 0 END) as failed_attempts,
                MAX(attempted_at) as last_attempt
            FROM attempts
            WHERE problem_id = ?
        """, (problem_db_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else {
            'total_attempts': 0,
            'passed_attempts': 0,
            'failed_attempts': 0,
            'last_attempt': None
        }
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for all problems.
        
        Returns:
            Dictionary with overall statistics
        """
        cursor = self.conn.cursor()
        
        # Total problems
        cursor.execute("SELECT COUNT(*) as total FROM problems")
        total = cursor.fetchone()[0]
        
        # By difficulty
        cursor.execute("""
            SELECT difficulty, COUNT(*) as count
            FROM problems
            GROUP BY difficulty
        """)
        by_difficulty = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By source
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM problems
            GROUP BY source
        """)
        by_source = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            'total_problems': total,
            'by_difficulty': by_difficulty,
            'by_source': by_source
        }
    
    def update_test_status(
        self,
        problem_db_id: int,
        status: str,
        output: Optional[str] = None
    ) -> bool:
        """
        Update test status for a problem.
        
        Args:
            problem_db_id: Database ID of the problem
            status: Test status ('passed', 'failed', 'error', 'untested')
            output: Test output/error message
            
        Returns:
            True if updated successfully
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE problems
            SET test_status = ?, last_test_run = ?, test_output = ?
            WHERE id = ?
        """, (status, datetime.now().isoformat(), output, problem_db_id))
        
        self.conn.commit()
        return True
    
    def get_problems_by_test_status(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get problems filtered by test status.

        Args:
            status: Filter by test status ('passed', 'failed', 'error', 'untested')
                None returns all problems

        Returns:
            List of problem dictionaries
        """
        cursor = self.conn.cursor()

        if status:
            cursor.execute(
                "SELECT * FROM problems WHERE test_status = ? ORDER BY problem_id ASC",
                (status,)
            )
        else:
            cursor.execute("SELECT * FROM problems ORDER BY problem_id ASC")

        return [dict(row) for row in cursor.fetchall()]

    def get_problems_by_status(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get problems filtered by grade status.

        Args:
            status: Filter by status ('passed', 'failed', 'skipped', 'ungraded')
                   Also accepts legacy values ('untested' -> 'ungraded')
                   None returns all problems

        Returns:
            List of problem dictionaries ordered by fetched_at descending
        """
        cursor = self.conn.cursor()

        # Map legacy status values
        if status == 'ungraded':
            # Match both 'ungraded' and legacy 'untested'
            cursor.execute(
                "SELECT * FROM problems WHERE test_status IN ('ungraded', 'untested') ORDER BY fetched_at DESC",
            )
        elif status:
            cursor.execute(
                "SELECT * FROM problems WHERE test_status = ? ORDER BY fetched_at DESC",
                (status,)
            )
        else:
            cursor.execute("SELECT * FROM problems ORDER BY fetched_at DESC")

        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # Configuration Methods
    # ========================================================================

    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_config(self, key: str, value: str) -> bool:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value

        Returns:
            True if set successfully
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()
        return True

    def get_all_config(self) -> Dict[str, str]:
        """
        Get all configuration values.

        Returns:
            Dictionary of all config key-value pairs
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM config")
        return {row[0]: row[1] for row in cursor.fetchall()}

    # ========================================================================
    # Review/Spaced Repetition Methods
    # ========================================================================

    def schedule_review(self, problem_db_id: int, days_from_now: Optional[int] = None) -> bool:
        """
        Schedule a problem for review.

        Args:
            problem_db_id: Database ID of the problem
            days_from_now: Days until next review (uses config default if None)

        Returns:
            True if scheduled successfully
        """
        cursor = self.conn.cursor()

        # Get review frequency from config if not specified
        if days_from_now is None:
            freq = self.get_config('review_frequency_days', '7')
            days_from_now = int(freq)

        # Calculate next review date
        from datetime import date, timedelta
        next_review = date.today() + timedelta(days=days_from_now)

        # Check if review entry exists
        cursor.execute(
            "SELECT id, repetitions FROM reviews WHERE problem_id = ?",
            (problem_db_id,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing review
            new_reps = existing[1] + 1
            cursor.execute("""
                UPDATE reviews
                SET next_review_date = ?, interval_days = ?, repetitions = ?
                WHERE problem_id = ?
            """, (next_review.isoformat(), days_from_now, new_reps, problem_db_id))
        else:
            # Create new review entry
            cursor.execute("""
                INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
                VALUES (?, ?, ?, 1)
            """, (problem_db_id, next_review.isoformat(), days_from_now))

        self.conn.commit()
        self.logger.debug(f"Scheduled review for problem {problem_db_id} on {next_review}")
        return True

    def get_due_reviews(self, include_future: bool = False) -> List[Dict[str, Any]]:
        """
        Get problems due for review.

        Args:
            include_future: If True, include future reviews with their dates

        Returns:
            List of problem dictionaries with review info
        """
        cursor = self.conn.cursor()
        from datetime import date
        today = date.today().isoformat()

        if include_future:
            query = """
                SELECT p.*, r.next_review_date, r.interval_days, r.repetitions
                FROM problems p
                INNER JOIN reviews r ON p.id = r.problem_id
                ORDER BY r.next_review_date ASC
            """
            cursor.execute(query)
        else:
            query = """
                SELECT p.*, r.next_review_date, r.interval_days, r.repetitions
                FROM problems p
                INNER JOIN reviews r ON p.id = r.problem_id
                WHERE r.next_review_date <= ?
                ORDER BY r.next_review_date ASC
            """
            cursor.execute(query, (today,))

        return [dict(row) for row in cursor.fetchall()]

    def get_review_stats(self) -> Dict[str, Any]:
        """
        Get review statistics.

        Returns:
            Dictionary with review statistics
        """
        cursor = self.conn.cursor()
        from datetime import date, timedelta
        today = date.today()

        # Due today
        cursor.execute(
            "SELECT COUNT(*) FROM reviews WHERE next_review_date <= ?",
            (today.isoformat(),)
        )
        due_today = cursor.fetchone()[0]

        # Due this week
        week_end = today + timedelta(days=7)
        cursor.execute(
            "SELECT COUNT(*) FROM reviews WHERE next_review_date <= ?",
            (week_end.isoformat(),)
        )
        due_this_week = cursor.fetchone()[0]

        # Total in review system
        cursor.execute("SELECT COUNT(*) FROM reviews")
        total_in_review = cursor.fetchone()[0]

        # Problems with most reviews
        cursor.execute("""
            SELECT p.problem_id, p.title, p.source, r.repetitions
            FROM problems p
            INNER JOIN reviews r ON p.id = r.problem_id
            ORDER BY r.repetitions DESC
            LIMIT 5
        """)
        most_reviewed = [dict(row) for row in cursor.fetchall()]

        return {
            'due_today': due_today,
            'due_this_week': due_this_week,
            'total_in_review': total_in_review,
            'most_reviewed': most_reviewed
        }

    def remove_from_review(self, problem_db_id: int) -> bool:
        """
        Remove a problem from the review schedule.

        Args:
            problem_db_id: Database ID of the problem

        Returns:
            True if removed successfully
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM reviews WHERE problem_id = ?", (problem_db_id,))
        self.conn.commit()
        return True