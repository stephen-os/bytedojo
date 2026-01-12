"""
Tests for review command - spaced repetition system.
"""

import pytest
from click.testing import CliRunner
from datetime import date, timedelta
import sqlite3

from bytedojo.commands.dojo import dojo
from bytedojo.core.database import create_database_schema


@pytest.fixture
def initialized_repo(tmp_path, monkeypatch):
    """Create an initialized dojo repository."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Create .dojo directory and database
    dojo_dir = tmp_path / ".dojo"
    dojo_dir.mkdir()
    db_path = dojo_dir / "db.sqlite"
    create_database_schema(db_path)

    # Create settings.json
    settings_path = dojo_dir / "settings.json"
    settings_path.write_text('{"leetcode": {"organization": "difficulty"}}')

    return tmp_path


@pytest.fixture
def repo_with_reviews(initialized_repo):
    """Create a repo with problems and reviews."""
    db_path = initialized_repo / ".dojo" / "db.sqlite"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert problems
    cursor.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, file_path)
        VALUES ('leetcode', '1', 'Two Sum', 'Easy', 'problems/leetcode/easy/1-two-sum.py')
    """)
    p1_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, file_path)
        VALUES ('leetcode', '2', 'Add Two Numbers', 'Medium', 'problems/leetcode/medium/2-add-two-numbers.py')
    """)
    p2_id = cursor.lastrowid

    # Schedule reviews - one due yesterday, one due in 3 days
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    in_3_days = (date.today() + timedelta(days=3)).isoformat()

    cursor.execute("""
        INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
        VALUES (?, ?, 7, 2)
    """, (p1_id, yesterday))

    cursor.execute("""
        INSERT INTO reviews (problem_id, next_review_date, interval_days, repetitions)
        VALUES (?, ?, 7, 1)
    """, (p2_id, in_3_days))

    conn.commit()
    conn.close()

    return initialized_repo


class TestReviewCommand:
    """Test dojo review command."""

    def test_review_no_repo(self, tmp_path, monkeypatch):
        """Test review fails when repository not initialized."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(dojo, ['review'])

        assert result.exit_code != 0
        assert "Repository not initialized" in result.output or "No .dojo repository found" in result.output

    def test_review_no_reviews_scheduled(self, initialized_repo):
        """Test review with no scheduled reviews."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['review'])

        assert result.exit_code == 0
        assert "No problems due for review" in result.output or "No problems scheduled for review" in result.output

    def test_review_shows_due_problems(self, repo_with_reviews):
        """Test review shows problems due for review."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['review'])

        assert result.exit_code == 0
        assert "Two Sum" in result.output
        # Should only show due problem, not future one
        assert "PROBLEMS DUE" in result.output or "due" in result.output.lower()

    def test_review_all_shows_all_reviews(self, repo_with_reviews):
        """Test review --all shows all scheduled reviews."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['review', '--all'])

        assert result.exit_code == 0
        assert "Two Sum" in result.output
        assert "Add Two Numbers" in result.output


class TestReviewPickCommand:
    """Test dojo review pick command."""

    def test_review_pick_no_due_problems(self, initialized_repo):
        """Test review pick when no problems are due."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['review', 'pick'])

        assert result.exit_code == 0
        assert "No problems due for review" in result.output

    def test_review_pick_returns_problem(self, repo_with_reviews):
        """Test review pick returns a due problem."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['review', 'pick'])

        assert result.exit_code == 0
        # Should show problem details
        assert "Two Sum" in result.output
        assert "REVIEW THIS PROBLEM" in result.output


class TestReviewStatsCommand:
    """Test dojo review stats command."""

    def test_review_stats_empty(self, initialized_repo):
        """Test review stats with no reviews."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['review', 'stats'])

        assert result.exit_code == 0
        assert "REVIEW STATISTICS" in result.output
        assert "Due Today:" in result.output

    def test_review_stats_with_reviews(self, repo_with_reviews):
        """Test review stats with scheduled reviews."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['review', 'stats'])

        assert result.exit_code == 0
        assert "REVIEW STATISTICS" in result.output
        assert "Total in Review:" in result.output
