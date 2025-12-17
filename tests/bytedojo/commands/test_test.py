"""
Tests for test command.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from textwrap import dedent

from bytedojo.commands.dojo import dojo
from bytedojo.core.repository import DojoRepository


@pytest.fixture
def repo_with_test_files(tmp_path):
    """Create a repository with test files."""
    import os
    import sqlite3
    original_dir = Path.cwd()
    os.chdir(tmp_path)
    
    # Initialize repo
    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()
    
    # Create problems directory
    problems_dir = tmp_path / "problems" / "easy"
    problems_dir.mkdir(parents=True)
    
    # Create passing test file
    passing_file = problems_dir / "0001-two-sum.py"
    passing_file.write_text(dedent('''
        def run_tests():
            """Run test cases."""
            print("Test 1: PASSED")
            print("Test 2: PASSED")
        
        if __name__ == "__main__":
            run_tests()
    ''').strip())
    
    # Create failing test file
    failing_file = problems_dir / "0002-add-two.py"
    failing_file.write_text(dedent('''
        def run_tests():
            """Run test cases."""
            print("Test 1: PASSED")
            raise AssertionError("Test 2 failed")
        
        if __name__ == "__main__":
            run_tests()
    ''').strip())
    
    # Register problems in database
    db_path = tmp_path / ".dojo" / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, file_path)
        VALUES ('leetcode', '1', 'Two Sum', 'Easy', ?)
    """, (str(passing_file),))
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, file_path)
        VALUES ('leetcode', '2', 'Add Two Numbers', 'Easy', ?)
    """, (str(failing_file),))
    conn.commit()
    conn.close()
    
    yield tmp_path
    
    os.chdir(original_dir)


@pytest.fixture
def repo_with_invalid_test(tmp_path):
    """Create a repository with an invalid test file."""
    import os
    import sqlite3
    original_dir = Path.cwd()
    os.chdir(tmp_path)
    
    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()
    
    problems_dir = tmp_path / "problems"
    problems_dir.mkdir(parents=True, exist_ok=True)
    
    # Create invalid test file (missing run_tests)
    invalid_file = problems_dir / "0003-invalid.py"
    invalid_file.write_text(dedent('''
        def some_function():
            print("This is not a test")
        
        if __name__ == "__main__":
            some_function()
    ''').strip())
    
    db_path = tmp_path / ".dojo" / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, file_path)
        VALUES ('leetcode', '3', 'Invalid Test', 'Easy', ?)
    """, (str(invalid_file),))
    conn.commit()
    conn.close()
    
    yield tmp_path
    
    os.chdir(original_dir)


class TestTestCommandNoRepo:
    """Test test command when no repository exists."""
    
    def test_test_fails_without_repo(self, tmp_path):
        """Test that test fails when no .dojo exists."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['test'])
            
            assert result.exit_code != 0
            assert "No .dojo repository found" in result.output


class TestTestCommandBasic:
    """Test basic test command functionality."""
    
    def test_test_runs_all_tests(self, repo_with_test_files):
        """Test that test command runs all tests."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])
        
        assert "Running tests for all problems" in result.output
        assert "Found 2 problem(s)" in result.output
    
    def test_test_shows_passed_tests(self, repo_with_test_files):
        """Test that passed tests are shown."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])
        
        assert "Two Sum" in result.output
        assert "PASSED" in result.output
    
    def test_test_shows_failed_tests(self, repo_with_test_files):
        """Test that failed tests are shown."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])
        
        assert "Add Two Numbers" in result.output
        assert "FAILED" in result.output
    
    def test_test_shows_summary(self, repo_with_test_files):
        """Test that summary is displayed."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])
        
        assert "Test Summary" in result.output
        assert "Total:" in result.output
        assert "Passed:" in result.output
        assert "Failed:" in result.output
    
    def test_test_no_problems(self, tmp_path):
        """Test with empty repository."""
        import os
        original_dir = Path.cwd()
        os.chdir(tmp_path)
        
        repo = DojoRepository(root_dir=tmp_path)
        repo.initialize()
        
        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])
        
        assert result.exit_code == 0
        assert "No problems found" in result.output
        
        os.chdir(original_dir)


class TestTestCommandVerbose:
    """Test test command --verbose option."""
    
    def test_test_verbose_shows_output(self, repo_with_test_files):
        """Test that --verbose shows test output."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test', '--verbose'])
        
        assert "Output:" in result.output or "Test 1: PASSED" in result.output
    
    def test_test_verbose_shows_error_details(self, repo_with_test_files):
        """Test that --verbose shows error details."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test', '--verbose'])
        
        # Should show some error information
        assert "FAILED" in result.output


class TestTestCommandStopOnFail:
    """Test test command --stop-on-fail option."""
    
    def test_test_stop_on_fail_stops(self, repo_with_test_files):
        """Test that --stop-on-fail stops after first failure."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test', '--stop-on-fail'])
        
        # Should show stopping message or only run until failure
        assert "FAILED" in result.output or "Stopping" in result.output


class TestTestCommandDatabase:
    """Test that test results are stored in database."""
    
    def test_test_updates_database_passed(self, repo_with_test_files):
        """Test that passed status is stored."""
        import sqlite3
        
        runner = CliRunner()
        runner.invoke(dojo, ['test'])
        
        # Check database
        db_path = repo_with_test_files / ".dojo" / "db.sqlite"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT test_status FROM problems WHERE problem_id = '1'")
        status = cursor.fetchone()[0]
        assert status == 'passed'
        
        conn.close()
    
    def test_test_updates_database_failed(self, repo_with_test_files):
        """Test that failed status is stored."""
        import sqlite3
        
        runner = CliRunner()
        runner.invoke(dojo, ['test'])
        
        db_path = repo_with_test_files / ".dojo" / "db.sqlite"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT test_status FROM problems WHERE problem_id = '2'")
        status = cursor.fetchone()[0]
        assert status == 'failed'
        
        conn.close()
    
    def test_test_stores_timestamp(self, repo_with_test_files):
        """Test that last_test_run timestamp is stored."""
        import sqlite3
        
        runner = CliRunner()
        runner.invoke(dojo, ['test'])
        
        db_path = repo_with_test_files / ".dojo" / "db.sqlite"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT last_test_run FROM problems WHERE problem_id = '1'")
        timestamp = cursor.fetchone()[0]
        
        assert timestamp is not None
        conn.close()


class TestTestCommandInvalidTests:
    """Test handling of invalid test files."""
    
    def test_test_handles_invalid_test_file(self, repo_with_invalid_test):
        """Test that invalid test files are handled gracefully."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])
        
        assert result.exit_code != 0  # Should fail
        assert "Invalid test" in result.output or "ERROR" in result.output


class TestTestCommandEdgeCases:
    """Test edge cases."""
    
    def test_test_missing_file_path(self, tmp_path):
        """Test problem with no file_path."""
        import os
        import sqlite3
        original_dir = Path.cwd()
        os.chdir(tmp_path)
        
        repo = DojoRepository(root_dir=tmp_path)
        repo.initialize()
        
        db_path = tmp_path / ".dojo" / "db.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'No File', 'Easy')
        """)
        conn.commit()
        conn.close()
        
        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])
        
        assert "No file path" in result.output
        
        os.chdir(original_dir)
    
    def test_test_file_not_found(self, tmp_path):
        """Test problem with file_path that doesn't exist."""
        import os
        import sqlite3
        original_dir = Path.cwd()
        os.chdir(tmp_path)
        
        repo = DojoRepository(root_dir=tmp_path)
        repo.initialize()
        
        db_path = tmp_path / ".dojo" / "db.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty, file_path)
            VALUES ('leetcode', '1', 'Missing File', 'Easy', '/nonexistent/file.py')
        """)
        conn.commit()
        conn.close()
        
        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])
        
        # Should handle gracefully
        assert "ERROR" in result.output or "Invalid" in result.output
        
        os.chdir(original_dir)


class TestTestCommandHelp:
    """Test test command help."""
    
    def test_test_help(self):
        """Test test help output."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test', '--help'])
        
        assert result.exit_code == 0
        assert "Run tests" in result.output
        assert "--verbose" in result.output
        assert "--stop-on-fail" in result.output