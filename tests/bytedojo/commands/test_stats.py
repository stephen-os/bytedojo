"""
Tests for stats command.
"""

import pytest
import sqlite3
from click.testing import CliRunner
from pathlib import Path
from datetime import datetime

from bytedojo.commands.dojo import dojo
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import create_database_schema


@pytest.fixture
def initialized_repo(tmp_path):
    """Create an initialized repository for testing."""
    # Change to tmp_path directory
    import os
    original_dir = Path.cwd()
    os.chdir(tmp_path)
    
    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()
    
    yield tmp_path
    
    # Change back
    os.chdir(original_dir)


@pytest.fixture
def repo_with_problems(tmp_path):
    """Create a repository with some test problems."""
    import os
    original_dir = Path.cwd()
    os.chdir(tmp_path)
    
    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()
    
    db_path = tmp_path / ".dojo" / "db.sqlite"
    conn = sqlite3.connect(db_path)
    
    # Insert test problems
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, fetched_at)
        VALUES ('leetcode', '1', 'Two Sum', 'Easy', '2024-01-01 10:00:00')
    """)
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, fetched_at)
        VALUES ('leetcode', '2', 'Add Two Numbers', 'Medium', '2024-01-02 11:00:00')
    """)
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, fetched_at)
        VALUES ('leetcode', '3', 'Longest Substring', 'Medium', '2024-01-03 12:00:00')
    """)
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, fetched_at, file_path)
        VALUES ('leetcode', '4', 'Median of Arrays', 'Hard', '2024-01-04 13:00:00', 'problems/hard/0004-median.py')
    """)
    
    conn.commit()
    conn.close()
    
    yield tmp_path
    
    os.chdir(original_dir)


@pytest.fixture
def repo_with_attempts(tmp_path):
    """Create a repository with problems and attempts."""
    import os
    original_dir = Path.cwd()
    os.chdir(tmp_path)
    
    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()
    
    db_path = tmp_path / ".dojo" / "db.sqlite"
    conn = sqlite3.connect(db_path)
    
    # Insert test problems
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, fetched_at)
        VALUES ('leetcode', '1', 'Two Sum', 'Easy', '2024-01-01 10:00:00')
    """)
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, fetched_at)
        VALUES ('leetcode', '2', 'Add Two Numbers', 'Medium', '2024-01-02 11:00:00')
    """)
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, fetched_at)
        VALUES ('leetcode', '3', 'Longest Substring', 'Medium', '2024-01-03 12:00:00')
    """)
    conn.execute("""
        INSERT INTO problems (source, problem_id, title, difficulty, fetched_at, file_path)
        VALUES ('leetcode', '4', 'Median of Arrays', 'Hard', '2024-01-04 13:00:00', 'problems/hard/0004-median.py')
    """)
    
    # Add attempts for problem 1
    conn.execute("""
        INSERT INTO attempts (problem_id, attempted_at, passed, time_taken)
        VALUES (1, '2024-01-05 10:00:00', 0, 30)
    """)
    conn.execute("""
        INSERT INTO attempts (problem_id, attempted_at, passed, time_taken)
        VALUES (1, '2024-01-06 11:00:00', 1, 25)
    """)
    
    # Add attempts for problem 2
    conn.execute("""
        INSERT INTO attempts (problem_id, attempted_at, passed, time_taken)
        VALUES (2, '2024-01-07 12:00:00', 1, 45)
    """)
    
    conn.commit()
    conn.close()
    
    yield tmp_path
    
    os.chdir(original_dir)


class TestStatsCommandNoRepo:
    """Test stats command when no repository exists."""
    
    def test_stats_fails_without_repo(self, tmp_path):
        """Test that stats fails when no .dojo exists."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['stats'])
            
            assert result.exit_code != 0
            assert "No .dojo repository found" in result.output
            assert "Run 'dojo init' first" in result.output


class TestStatsCommandSummary:
    """Test stats command summary display."""
    
    def test_stats_shows_summary_by_default(self, repo_with_problems):
        """Test that stats shows summary without options."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats'])
        
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "ByteDojo Repository Statistics" in result.output
        assert "Total Problems: 4" in result.output
    
    def test_stats_shows_difficulty_breakdown(self, repo_with_problems):
        """Test that summary shows breakdown by difficulty."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats'])
        
        assert result.exit_code == 0
        assert "By Difficulty:" in result.output
        assert "Easy" in result.output
        assert "Medium" in result.output
        assert "Hard" in result.output
    
    def test_stats_shows_source_breakdown(self, repo_with_problems):
        """Test that summary shows breakdown by source."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats'])
        
        assert result.exit_code == 0
        assert "By Source:" in result.output
        assert "leetcode" in result.output
    
    def test_stats_empty_repo(self, initialized_repo):
        """Test stats with empty repository."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats'])
        
        assert result.exit_code == 0
        assert "Total Problems: 0" in result.output


class TestStatsCommandList:
    """Test stats --list option."""
    
    def test_stats_list_shows_all_problems(self, repo_with_problems):
        """Test that --list shows all problems."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list'])
        
        assert result.exit_code == 0
        assert "Found 4 problem(s)" in result.output
        assert "Two Sum" in result.output
        assert "Add Two Numbers" in result.output
        assert "Longest Substring" in result.output
        assert "Median of Arrays" in result.output
    
    def test_stats_list_shows_problem_details(self, repo_with_problems):
        """Test that --list shows problem details."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list'])
        
        assert result.exit_code == 0
        assert "#1" in result.output
        assert "Source: leetcode" in result.output
        assert "Difficulty: Easy" in result.output
        assert "Fetched:" in result.output
    
    def test_stats_list_shows_file_path(self, repo_with_problems):
        """Test that --list shows file path when available."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list'])
        
        assert result.exit_code == 0
        assert "problems/hard/0004-median.py" in result.output
    
    def test_stats_list_empty(self, initialized_repo):
        """Test --list with no problems."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list'])
        
        assert result.exit_code == 0
        assert "No problems found" in result.output


class TestStatsCommandVerbose:
    """Test stats --verbose option."""
    
    def test_stats_verbose_shows_attempts(self, repo_with_attempts):
        """Test that --verbose shows attempt information."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list', '--verbose'])
        
        assert result.exit_code == 0
        assert "Attempts:" in result.output
    
    def test_stats_verbose_shows_passed_failed(self, repo_with_attempts):
        """Test that --verbose shows passed/failed counts."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list', '--verbose'])
        
        assert result.exit_code == 0
        # Problem 1 has 2 attempts (1 failed, 1 passed)
        output_lines = result.output.split('\n')
        
        # Find problem 1 section
        found_attempts = False
        for i, line in enumerate(output_lines):
            if '#1' in line and 'Two Sum' in line:
                # Check next few lines for attempt info
                section = '\n'.join(output_lines[i:i+10])
                if 'Attempts: 2' in section:
                    found_attempts = True
                    assert 'Passed: 1' in section
                    assert 'Failed: 1' in section
        
        assert found_attempts
    
    def test_stats_verbose_shows_no_attempts(self, repo_with_attempts):
        """Test that --verbose shows 'None' for problems with no attempts."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list', '--verbose'])
        
        assert result.exit_code == 0
        # Problem 4 has no attempts
        output_lines = result.output.split('\n')
        
        for i, line in enumerate(output_lines):
            if '#4' in line and 'Median' in line:
                section = '\n'.join(output_lines[i:i+10])
                assert 'Attempts: None' in section


class TestStatsCommandFilters:
    """Test stats filtering options."""
    
    def test_stats_filter_by_difficulty(self, repo_with_problems):
        """Test filtering by difficulty."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list', '--difficulty', 'Easy'])
        
        assert result.exit_code == 0
        assert "Found 1 problem(s)" in result.output
        assert "Two Sum" in result.output
        assert "Add Two Numbers" not in result.output
    
    def test_stats_filter_by_difficulty_medium(self, repo_with_problems):
        """Test filtering medium problems."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list', '--difficulty', 'Medium'])
        
        assert result.exit_code == 0
        assert "Found 2 problem(s)" in result.output
        assert "Add Two Numbers" in result.output
        assert "Longest Substring" in result.output
    
    def test_stats_filter_by_source(self, repo_with_problems):
        """Test filtering by source."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list', '--source', 'leetcode'])
        
        assert result.exit_code == 0
        assert "Found 4 problem(s)" in result.output
    
    def test_stats_filter_no_results(self, repo_with_problems):
        """Test filter that returns no results."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list', '--difficulty', 'Easy', '--source', 'hackerrank'])
        
        assert result.exit_code == 0
        assert "No problems found" in result.output


class TestStatsCommandCombinations:
    """Test combinations of stats options."""
    
    def test_stats_list_verbose_filtered(self, repo_with_attempts):
        """Test --list --verbose with filtering."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list', '--verbose', '--difficulty', 'Easy'])
        
        assert result.exit_code == 0
        assert "Two Sum" in result.output
        assert "Attempts:" in result.output
    
    def test_stats_help(self):
        """Test stats help output."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--help'])
        
        assert result.exit_code == 0
        assert "View statistics" in result.output
        assert "--list" in result.output
        assert "--verbose" in result.output
        assert "--source" in result.output
        assert "--difficulty" in result.output


class TestStatsCommandOutput:
    """Test stats output formatting."""
    
    def test_stats_summary_formatting(self, repo_with_problems):
        """Test that summary has proper formatting."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats'])
        
        assert result.exit_code == 0
        # Check for separator lines
        assert "=" * 60 in result.output
        # Check proper sections
        lines = result.output.split('\n')
        assert any("Total Problems:" in line for line in lines)
    
    def test_stats_list_formatting(self, repo_with_problems):
        """Test that list has proper formatting."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--list'])
        
        assert result.exit_code == 0
        # Each problem should have indented details
        assert "  Source:" in result.output
        assert "  Difficulty:" in result.output
        assert "  Fetched:" in result.output