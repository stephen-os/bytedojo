"""
Tests for test command.
"""

import pytest
import json
from click.testing import CliRunner
from pathlib import Path
from textwrap import dedent

from bytedojo.commands.dojo import dojo
from bytedojo.core.repository import DojoRepository
from bytedojo.core.test_store import TestStore, TestData


@pytest.fixture
def repo_with_test_files(tmp_path):
    """Create a repository with test files and JSON test data."""
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

    # Create passing solution file
    passing_file = problems_dir / "0001-two-sum.py"
    passing_file.write_text(dedent('''
        class Solution:
            def twoSum(self, nums, target):
                """Find two numbers that add up to target."""
                seen = {}
                for i, num in enumerate(nums):
                    complement = target - num
                    if complement in seen:
                        return [seen[complement], i]
                    seen[num] = i
                return []
    ''').strip())

    # Create failing solution file (with error)
    failing_file = problems_dir / "0002-add-two.py"
    failing_file.write_text(dedent('''
        class Solution:
            def addTwoNumbers(self, l1, l2):
                """Intentionally broken."""
                raise ValueError("Not implemented")
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

    # Create test data JSON files
    test_store = TestStore(tmp_path / ".dojo")

    test_data_1 = TestData(
        problem_id=1,
        source='leetcode',
        title='Two Sum',
        difficulty='Easy',
        class_name='Solution',
        method_name='twoSum',
        params=[{"name": "nums", "type": "List[int]"}, {"name": "target", "type": "int"}],
        return_type='List[int]',
        helpers_needed={'listnode': False, 'treenode': False},
        test_cases='[2,7,11,15]\n9',
        file_path=str(passing_file)
    )
    test_store.save(test_data_1)

    test_data_2 = TestData(
        problem_id=2,
        source='leetcode',
        title='Add Two Numbers',
        difficulty='Easy',
        class_name='Solution',
        method_name='addTwoNumbers',
        params=[{"name": "l1", "type": "ListNode"}, {"name": "l2", "type": "ListNode"}],
        return_type='ListNode',
        helpers_needed={'listnode': True, 'treenode': False},
        test_cases='[2,4,3]\n[5,6,4]',
        file_path=str(failing_file)
    )
    test_store.save(test_data_2)

    yield tmp_path

    os.chdir(original_dir)


@pytest.fixture
def repo_with_invalid_test(tmp_path):
    """Create a repository with an invalid solution file."""
    import os
    import sqlite3
    original_dir = Path.cwd()
    os.chdir(tmp_path)

    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()

    problems_dir = tmp_path / "problems"
    problems_dir.mkdir(parents=True, exist_ok=True)

    # Create invalid solution file (syntax error)
    invalid_file = problems_dir / "0003-invalid.py"
    invalid_file.write_text(dedent('''
        class Solution:
            def solve(self, x):
                # This has a syntax error
                return x +
    ''').strip())

    db_path = tmp_path / ".dojo" / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, file_path)
        VALUES ('leetcode', '3', 'Invalid Test', 'Easy', ?)
    """, (str(invalid_file),))
    conn.commit()
    conn.close()

    # Create test data
    test_store = TestStore(tmp_path / ".dojo")
    test_data = TestData(
        problem_id=3,
        source='leetcode',
        title='Invalid Test',
        difficulty='Easy',
        class_name='Solution',
        method_name='solve',
        params=[{"name": "x", "type": "int"}],
        return_type='int',
        helpers_needed={'listnode': False, 'treenode': False},
        test_cases='5',
        file_path=str(invalid_file)
    )
    test_store.save(test_data)

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

        assert "Running tests for" in result.output
        assert "2 problem(s)" in result.output

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
        # The test should either fail or error due to the broken implementation
        assert "FAILED" in result.output or "ERROR" in result.output

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
        assert "No tests found" in result.output

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
        # Should show FAILED for invalid syntax file
        assert "FAILED" in result.output or "ERROR" in result.output


class TestTestCommandEdgeCases:
    """Test edge cases."""

    def test_test_no_test_data(self, tmp_path):
        """Test when no test data JSON exists."""
        import os
        import sqlite3
        original_dir = Path.cwd()
        os.chdir(tmp_path)

        repo = DojoRepository(root_dir=tmp_path)
        repo.initialize()

        # Only create DB entry, no JSON test data
        db_path = tmp_path / ".dojo" / "db.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO problems (source, problem_id, title, difficulty)
            VALUES ('leetcode', '1', 'No Test Data', 'Easy')
        """)
        conn.commit()
        conn.close()

        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])

        # Should report no tests found since no JSON test data
        assert result.exit_code == 0
        assert "No tests found" in result.output

        os.chdir(original_dir)

    def test_test_file_not_found(self, tmp_path):
        """Test problem with file_path that doesn't exist."""
        import os
        original_dir = Path.cwd()
        os.chdir(tmp_path)

        repo = DojoRepository(root_dir=tmp_path)
        repo.initialize()

        # Create test data pointing to non-existent file
        test_store = TestStore(tmp_path / ".dojo")
        test_data = TestData(
            problem_id=1,
            source='leetcode',
            title='Missing File',
            difficulty='Easy',
            class_name='Solution',
            method_name='solve',
            params=[{"name": "x", "type": "int"}],
            return_type='int',
            helpers_needed={'listnode': False, 'treenode': False},
            test_cases='5',
            file_path='/nonexistent/file.py'
        )
        test_store.save(test_data)

        runner = CliRunner()
        result = runner.invoke(dojo, ['test'])

        # Should handle gracefully
        assert "ERROR" in result.output or "not found" in result.output

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


class TestTestLastCommand:
    """Test the 'dojo test last' subcommand."""

    def test_test_last_runs_most_recent(self, repo_with_test_files):
        """Test that 'test last' runs the most recently fetched problem."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test', 'last'])

        assert "Running test for last fetched problem" in result.output
        # Should test one of the problems
        assert "Testing #" in result.output

    def test_test_last_no_tests(self, tmp_path):
        """Test 'test last' with no tests."""
        import os
        original_dir = Path.cwd()
        os.chdir(tmp_path)

        repo = DojoRepository(root_dir=tmp_path)
        repo.initialize()

        runner = CliRunner()
        result = runner.invoke(dojo, ['test', 'last'])

        assert result.exit_code == 0
        assert "No tests found" in result.output

        os.chdir(original_dir)