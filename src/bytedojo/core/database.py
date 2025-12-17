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
            UNIQUE(source, problem_id)
        )
    """)
    
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
        ('problems_dir', 'problems')
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
    
    def is_problem_registered(self, source: str, problem_id: int) -> bool:
        """
        Check if problem is already registered.
        
        Args:
            source: Problem source (e.g., 'leetcode')
            problem_id: Problem ID number
            
        Returns:
            True if problem exists in database
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM problems WHERE source = ? AND problem_id = ?",
            (source, str(problem_id))
        )
        count = cursor.fetchone()[0]
        return count > 0
    
    def register_problem(
        self,
        problem: Problem,
        source: str = "leetcode",
        file_path: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """
        Register a problem in the database.
        
        Args:
            problem: Problem object to register
            source: Problem source (default: 'leetcode')
            file_path: Path to the problem file
            force: If True, overwrite existing entry
            
        Returns:
            True if registered successfully
        """
        cursor = self.conn.cursor()
        
        # Check if already exists
        if self.is_problem_registered(source, problem.id) and not force:
            return False
        
        # Insert or replace
        cursor.execute("""
            INSERT OR REPLACE INTO problems (
                source, problem_id, title, difficulty, category, 
                tags, description, file_path, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source,
            str(problem.id),
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
    
    def get_problem(self, source: str, problem_id: int) -> Optional[Dict[str, Any]]:
        """
        Get problem from database.
        
        Args:
            source: Problem source
            problem_id: Problem ID
            
        Returns:
            Problem data as dict or None
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM problems WHERE source = ? AND problem_id = ?",
            (source, str(problem_id))
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def list_problems(
        self,
        source: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List problems from database.
        
        Args:
            source: Filter by source (e.g., 'leetcode')
            difficulty: Filter by difficulty (e.g., 'Easy')
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