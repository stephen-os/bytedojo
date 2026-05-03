"""
Tests for DatabaseManager and database operations.
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta

from bytedojo.core.database import DatabaseManager, create_database_schema
from bytedojo.core.models import Problem, CodeSnippet


class TestCreateDatabaseSchema:
    """Test create_database_schema function."""
    
    def test_creates_database_file(self, tmp_path):
        """Test that database file is created."""
        db_path = tmp_path / "test.db"
        
        create_database_schema(db_path)
        
        assert db_path.exists()
    
    def test_creates_all_tables(self, tmp_path):
        """Test that all required tables are created."""
        db_path = tmp_path / "test.db"
        
        create_database_schema(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name
        """)
        tables = {row[0] for row in cursor.fetchall()}
        
        assert 'problems' in tables
        assert 'attempts' in tables
        assert 'reviews' in tables
        assert 'stats' in tables
        assert 'config' in tables
        
        conn.close()
    
    def test_creates_default_config(self, tmp_path):
        """Test that default config values are inserted."""
        db_path = tmp_path / "test.db"
        
        create_database_schema(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM config")
        config = {row[0]: row[1] for row in cursor.fetchall()}
        
        assert 'initialized_at' in config
        assert 'default_language' in config
        assert config['default_language'] == 'python'
        assert 'default_source' in config
        assert config['default_source'] == 'leetcode'
        
        conn.close()
    
    def test_problems_table_has_test_fields(self, tmp_path):
        """Test that problems table has test-related fields."""
        db_path = tmp_path / "test.db"
        
        create_database_schema(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(problems)")
        columns = {row[1] for row in cursor.fetchall()}
        
        assert 'test_status' in columns
        assert 'last_test_run' in columns
        assert 'test_output' in columns
        
        conn.close()


class TestDatabaseManagerInit:
    """Test DatabaseManager initialization."""
    
    def test_init_sets_db_path(self, tmp_path):
        """Test that initialization sets db_path."""
        db_path = tmp_path / "test.db"
        db_path.touch()
        
        db = DatabaseManager(db_path)
        
        assert db.db_path == db_path
    
    def test_init_conn_is_none(self, tmp_path):
        """Test that connection is None initially."""
        db_path = tmp_path / "test.db"
        db_path.touch()
        
        db = DatabaseManager(db_path)
        
        assert db.conn is None


class TestDatabaseManagerConnection:
    """Test DatabaseManager connection methods."""
    
    def test_connect_opens_connection(self, tmp_path):
        """Test that connect opens a connection."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        db = DatabaseManager(db_path)
        db.connect()
        
        assert db.conn is not None
        assert isinstance(db.conn, sqlite3.Connection)
        
        db.close()
    
    def test_close_closes_connection(self, tmp_path):
        """Test that close closes the connection."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        db = DatabaseManager(db_path)
        db.connect()
        db.close()
        
        assert db.conn is None
    
    def test_context_manager(self, tmp_path):
        """Test using DatabaseManager as context manager."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        with DatabaseManager(db_path) as db:
            assert db.conn is not None
        
        # Connection should be closed after context
        assert db.conn is None


class TestDatabaseManagerIsProblemRegistered:
    """Test is_problem_registered method."""
    
    def test_returns_false_when_not_registered(self, tmp_path):
        """Test returns False when problem doesn't exist."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        with DatabaseManager(db_path) as db:
            result = db.is_problem_registered('leetcode', 1)
        
        assert result is False
    
    def test_returns_true_when_registered(self, tmp_path):
        """Test returns True when problem exists."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        # Insert a problem
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Two Sum', 'Easy')
        """)
        conn.commit()
        conn.close()
        
        with DatabaseManager(db_path) as db:
            result = db.is_problem_registered('leetcode', 1)
        
        assert result is True


class TestDatabaseManagerRegisterProblem:
    """Test register_problem method."""
    
    def test_register_problem_inserts_data(self, tmp_path):
        """Test that register_problem inserts problem data."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        problem = Problem(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            description="Test description",
            test_cases="test",
            code_snippets=[]
        )
        
        with DatabaseManager(db_path) as db:
            result = db.register_problem(problem, source='leetcode', file_path='/path/to/file.py')
        
        assert result is True
        
        # Verify data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM problems WHERE problem_id='1'")
        row = cursor.fetchone()
        
        assert row is not None
        conn.close()
    
    def test_register_problem_returns_false_when_exists(self, tmp_path):
        """Test returns False when problem already exists (no force)."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        problem = Problem(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            description="Test",
            test_cases="",
            code_snippets=[]
        )
        
        with DatabaseManager(db_path) as db:
            db.register_problem(problem)
            result = db.register_problem(problem)  # Try again
        
        assert result is False
    
    def test_register_problem_with_force_overwrites(self, tmp_path):
        """Test that force=True overwrites existing problem."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        problem = Problem(
            id=1,
            title="Original Title",
            title_slug="two-sum",
            difficulty="Easy",
            description="Original",
            test_cases="",
            code_snippets=[]
        )
        
        with DatabaseManager(db_path) as db:
            db.register_problem(problem)
            
            # Update problem
            problem.title = "Updated Title"
            result = db.register_problem(problem, force=True)
        
        assert result is True
        
        # Verify update
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM problems WHERE problem_id='1'")
        title = cursor.fetchone()[0]
        
        assert title == "Updated Title"
        conn.close()


class TestDatabaseManagerGetProblem:
    """Test get_problem method."""
    
    def test_get_problem_returns_none_when_not_exists(self, tmp_path):
        """Test returns None when problem doesn't exist."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        with DatabaseManager(db_path) as db:
            result = db.get_problem('leetcode', 1)
        
        assert result is None
    
    def test_get_problem_returns_data_when_exists(self, tmp_path):
        """Test returns problem data when exists."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        problem = Problem(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            description="Test",
            test_cases="",
            code_snippets=[]
        )
        
        with DatabaseManager(db_path) as db:
            db.register_problem(problem)
            result = db.get_problem('leetcode', 1)
        
        assert result is not None
        assert result['title'] == "Two Sum"
        assert result['difficulty'] == "Easy"


class TestDatabaseManagerListProblems:
    """Test list_problems method."""
    
    def test_list_problems_returns_all(self, tmp_path):
        """Test list_problems returns all problems."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        # Insert multiple problems
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty) VALUES ('leetcode', '1', 'One', 'Easy')")
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty) VALUES ('leetcode', '2', 'Two', 'Medium')")
        conn.commit()
        conn.close()
        
        with DatabaseManager(db_path) as db:
            results = db.list_problems()
        
        assert len(results) == 2
    
    def test_list_problems_filters_by_difficulty(self, tmp_path):
        """Test filtering by difficulty."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty) VALUES ('leetcode', '1', 'One', 'Easy')")
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty) VALUES ('leetcode', '2', 'Two', 'Hard')")
        conn.commit()
        conn.close()
        
        with DatabaseManager(db_path) as db:
            results = db.list_problems(difficulty='Easy')
        
        assert len(results) == 1
        assert results[0]['difficulty'] == 'Easy'


class TestDatabaseManagerUpdateTestStatus:
    """Test update_test_status method."""
    
    def test_update_test_status_sets_status(self, tmp_path):
        """Test that update_test_status updates the status."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        # Insert a problem
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Test', 'Easy')
        """)
        conn.commit()
        problem_id = cursor.lastrowid
        conn.close()
        
        # Update status
        with DatabaseManager(db_path) as db:
            result = db.update_test_status(problem_id, 'passed', 'All tests passed')
        
        assert result is True
        
        # Verify
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT test_status, test_output FROM problems WHERE id=?", (problem_id,))
        row = cursor.fetchone()
        
        assert row[0] == 'passed'
        assert row[1] == 'All tests passed'
        conn.close()
    
    def test_update_test_status_sets_timestamp(self, tmp_path):
        """Test that update_test_status sets timestamp."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        # Insert a problem
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Test', 'Easy')
        """)
        conn.commit()
        problem_id = cursor.lastrowid
        conn.close()
        
        # Update status
        with DatabaseManager(db_path) as db:
            db.update_test_status(problem_id, 'failed', 'Test failed')
        
        # Verify timestamp exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT last_test_run FROM problems WHERE id=?", (problem_id,))
        timestamp = cursor.fetchone()[0]
        
        assert timestamp is not None
        conn.close()


class TestDatabaseManagerGetProblemsByTestStatus:
    """Test get_problems_by_test_status method."""
    
    def test_get_problems_by_test_status_all(self, tmp_path):
        """Test getting all problems."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty, test_status) VALUES ('leetcode', '1', 'One', 'Easy', 'passed')")
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty, test_status) VALUES ('leetcode', '2', 'Two', 'Easy', 'failed')")
        conn.commit()
        conn.close()
        
        with DatabaseManager(db_path) as db:
            results = db.get_problems_by_test_status()
        
        assert len(results) == 2
    
    def test_get_problems_by_test_status_passed(self, tmp_path):
        """Test filtering by passed status."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty, test_status) VALUES ('leetcode', '1', 'One', 'Easy', 'passed')")
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty, test_status) VALUES ('leetcode', '2', 'Two', 'Easy', 'failed')")
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty, test_status) VALUES ('leetcode', '3', 'Three', 'Easy', 'passed')")
        conn.commit()
        conn.close()
        
        with DatabaseManager(db_path) as db:
            results = db.get_problems_by_test_status('passed')
        
        assert len(results) == 2
        assert all(r['test_status'] == 'passed' for r in results)
    
    def test_get_problems_by_test_status_failed(self, tmp_path):
        """Test filtering by failed status."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty, test_status) VALUES ('leetcode', '1', 'One', 'Easy', 'passed')")
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty, test_status) VALUES ('leetcode', '2', 'Two', 'Easy', 'failed')")
        conn.commit()
        conn.close()
        
        with DatabaseManager(db_path) as db:
            results = db.get_problems_by_test_status('failed')
        
        assert len(results) == 1
        assert results[0]['test_status'] == 'failed'


class TestDatabaseManagerGetSummaryStats:
    """Test get_summary_stats method."""
    
    def test_get_summary_stats(self, tmp_path):
        """Test getting summary statistics."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)
        
        # Insert test data
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty) VALUES ('leetcode', '1', 'One', 'Easy')")
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty) VALUES ('leetcode', '2', 'Two', 'Easy')")
        conn.execute("INSERT INTO problems (source, problem_id, title, difficulty) VALUES ('leetcode', '3', 'Three', 'Hard')")
        conn.commit()
        conn.close()
        
        with DatabaseManager(db_path) as db:
            stats = db.get_summary_stats()

        assert stats['total_problems'] == 3
        assert stats['by_difficulty']['Easy'] == 2
        assert stats['by_difficulty']['Hard'] == 1
        assert stats['by_source']['leetcode'] == 3


class TestDatabaseManagerConfig:
    """Test configuration methods."""

    def test_get_config_default_value(self, tmp_path):
        """Test get_config returns default when key not found."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        with DatabaseManager(db_path) as db:
            result = db.get_config('nonexistent_key', 'default_value')

        assert result == 'default_value'

    def test_get_config_existing_value(self, tmp_path):
        """Test get_config returns existing value."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        with DatabaseManager(db_path) as db:
            result = db.get_config('default_language')

        assert result == 'python'

    def test_get_config_review_frequency_default(self, tmp_path):
        """Test get_config returns default review frequency."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        with DatabaseManager(db_path) as db:
            result = db.get_config('review_frequency_days', '7')

        assert result == '7'

    def test_set_config_creates_new_key(self, tmp_path):
        """Test set_config creates a new config entry."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        with DatabaseManager(db_path) as db:
            db.set_config('new_key', 'new_value')
            result = db.get_config('new_key')

        assert result == 'new_value'

    def test_set_config_updates_existing_key(self, tmp_path):
        """Test set_config updates existing config entry."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        with DatabaseManager(db_path) as db:
            db.set_config('review_frequency_days', '14')
            result = db.get_config('review_frequency_days')

        assert result == '14'

    def test_get_all_config(self, tmp_path):
        """Test get_all_config returns all config values."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        with DatabaseManager(db_path) as db:
            config = db.get_all_config()

        assert 'default_language' in config
        assert 'default_source' in config
        assert 'review_frequency_days' in config
        assert config['default_language'] == 'python'


class TestDatabaseManagerReview:
    """Test review/spaced repetition methods."""

    def test_schedule_review_creates_entry(self, tmp_path):
        """Test schedule_review creates a new review entry."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        # Insert a problem
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Two Sum', 'Easy')
        """)
        conn.commit()
        problem_db_id = cursor.lastrowid
        conn.close()

        with DatabaseManager(db_path) as db:
            result = db.schedule_review(problem_db_id, days_from_now=7)

        assert result is True

        # Verify review entry exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reviews WHERE problem_id=?", (problem_db_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_schedule_review_uses_config_default(self, tmp_path):
        """Test schedule_review uses config default when days_from_now not specified."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        # Insert a problem
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Two Sum', 'Easy')
        """)
        conn.commit()
        problem_db_id = cursor.lastrowid
        conn.close()

        with DatabaseManager(db_path) as db:
            db.set_config('review_frequency_days', '14')
            db.schedule_review(problem_db_id)

        # Verify interval
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT interval_days FROM reviews WHERE problem_id=?", (problem_db_id,))
        interval = cursor.fetchone()[0]
        conn.close()

        assert interval == 14

    def test_schedule_review_increments_repetitions(self, tmp_path):
        """Test schedule_review increments repetitions on subsequent calls."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        # Insert a problem
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Two Sum', 'Easy')
        """)
        conn.commit()
        problem_db_id = cursor.lastrowid
        conn.close()

        with DatabaseManager(db_path) as db:
            db.schedule_review(problem_db_id, days_from_now=7)
            db.schedule_review(problem_db_id, days_from_now=7)
            db.schedule_review(problem_db_id, days_from_now=7)

        # Verify repetitions
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT repetitions FROM reviews WHERE problem_id=?", (problem_db_id,))
        reps = cursor.fetchone()[0]
        conn.close()

        assert reps == 3

    def test_get_due_reviews_returns_due_problems(self, tmp_path):
        """Test get_due_reviews returns problems due for review."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        # Insert problem and schedule past review
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Two Sum', 'Easy')
        """)
        problem_db_id = cursor.lastrowid

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        cursor.execute("""
            INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
            VALUES (?, ?, 7, 1)
        """, (problem_db_id, yesterday))
        conn.commit()
        conn.close()

        with DatabaseManager(db_path) as db:
            reviews = db.get_due_reviews(include_future=False)

        assert len(reviews) == 1
        assert reviews[0]['problem_id'] == '1'

    def test_get_due_reviews_excludes_future_reviews(self, tmp_path):
        """Test get_due_reviews excludes future reviews by default."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        # Insert problem and schedule future review
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Two Sum', 'Easy')
        """)
        problem_db_id = cursor.lastrowid

        future = (date.today() + timedelta(days=7)).isoformat()
        cursor.execute("""
            INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
            VALUES (?, ?, 7, 1)
        """, (problem_db_id, future))
        conn.commit()
        conn.close()

        with DatabaseManager(db_path) as db:
            reviews = db.get_due_reviews(include_future=False)

        assert len(reviews) == 0

    def test_get_due_reviews_includes_future_when_requested(self, tmp_path):
        """Test get_due_reviews includes future reviews when requested."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        # Insert problem and schedule future review
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Two Sum', 'Easy')
        """)
        problem_db_id = cursor.lastrowid

        future = (date.today() + timedelta(days=7)).isoformat()
        cursor.execute("""
            INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
            VALUES (?, ?, 7, 1)
        """, (problem_db_id, future))
        conn.commit()
        conn.close()

        with DatabaseManager(db_path) as db:
            reviews = db.get_due_reviews(include_future=True)

        assert len(reviews) == 1

    def test_get_review_stats(self, tmp_path):
        """Test get_review_stats returns correct statistics."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        # Insert problems and reviews
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Problem 1 - due today
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Two Sum', 'Easy')
        """)
        p1_id = cursor.lastrowid
        today = date.today().isoformat()
        cursor.execute("""
            INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
            VALUES (?, ?, 7, 3)
        """, (p1_id, today))

        # Problem 2 - due in 3 days
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '2', 'Add Two Numbers', 'Medium')
        """)
        p2_id = cursor.lastrowid
        in_3_days = (date.today() + timedelta(days=3)).isoformat()
        cursor.execute("""
            INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
            VALUES (?, ?, 7, 1)
        """, (p2_id, in_3_days))

        conn.commit()
        conn.close()

        with DatabaseManager(db_path) as db:
            stats = db.get_review_stats()

        assert stats['due_today'] == 1
        assert stats['due_this_week'] == 2
        assert stats['total_in_review'] == 2
        assert len(stats['most_reviewed']) > 0

    def test_remove_from_review(self, tmp_path):
        """Test remove_from_review removes the review entry."""
        db_path = tmp_path / "test.db"
        create_database_schema(db_path)

        # Insert a problem and schedule review
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'Two Sum', 'Easy')
        """)
        problem_db_id = cursor.lastrowid
        today = date.today().isoformat()
        cursor.execute("""
            INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
            VALUES (?, ?, 7, 1)
        """, (problem_db_id, today))
        conn.commit()
        conn.close()

        with DatabaseManager(db_path) as db:
            # Verify review exists
            reviews = db.get_due_reviews(include_future=True)
            assert len(reviews) == 1

            # Remove from review
            result = db.remove_from_review(problem_db_id)
            assert result is True

            # Verify removed
            reviews = db.get_due_reviews(include_future=True)
            assert len(reviews) == 0