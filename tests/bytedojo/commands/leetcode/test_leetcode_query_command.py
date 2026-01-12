"""
Tests for the LeetCode query command.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from pathlib import Path

from bytedojo.commands.dojo import dojo
from bytedojo.core.leetcode.models import ProblemSummary


class TestQueryCommand:
    """Test the leetcode query command."""

    def test_query_help(self):
        """Test that query --help works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query', '--help'])

        assert result.exit_code == 0
        assert 'Search LeetCode problems' in result.output
        assert '--difficulty' in result.output
        assert '--tag' in result.output
        assert '--page' in result.output
        assert '--per-page' in result.output
        assert '--list-tags' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_displays_problems(self, mock_client_class, mock_repo_class):
        """Test query displays problems in table format."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Two Sum', title_slug='two-sum',
                          difficulty='Easy', paid_only=False, tags=['Array'])
        ]

        runner = CliRunner()
        # Simulate pressing 'q' to quit interactive mode
        result = runner.invoke(dojo, ['leetcode', 'query'], input='q\n')

        assert result.exit_code == 0
        assert 'Two Sum' in result.output
        assert 'Page 1/1' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_by_difficulty(self, mock_client_class, mock_repo_class):
        """Test query filtering by difficulty."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['leetcode', 'query', '-d', 'easy'], input='q\n')

        mock_client.query_problems.assert_called_once_with(
            difficulty=1,
            tags=None
        )

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_by_tag(self, mock_client_class, mock_repo_class):
        """Test query filtering by tag."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['leetcode', 'query', '-t', 'array', '-t', 'tree'], input='q\n')

        mock_client.query_problems.assert_called_once_with(
            difficulty=None,
            tags=['array', 'tree']
        )

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_pagination_next(self, mock_client_class, mock_repo_class):
        """Test pagination with 'n' for next page."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        # Create 30 problems (2 pages with default 20 per page)
        problems = [
            ProblemSummary(id=i, title=f'Problem {i}', title_slug=f'problem-{i}',
                          difficulty='Easy', paid_only=False, tags=[])
            for i in range(1, 31)
        ]
        mock_client.query_problems.return_value = problems

        runner = CliRunner()
        # Navigate: show page 1, press 'n' for next, then 'q' to quit
        result = runner.invoke(dojo, ['leetcode', 'query'], input='n\nq\n')

        assert 'Page 1/2' in result.output
        assert 'Page 2/2' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_pagination_prev(self, mock_client_class, mock_repo_class):
        """Test pagination with 'p' for previous page."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        problems = [
            ProblemSummary(id=i, title=f'Problem {i}', title_slug=f'problem-{i}',
                          difficulty='Easy', paid_only=False, tags=[])
            for i in range(1, 31)
        ]
        mock_client.query_problems.return_value = problems

        runner = CliRunner()
        # Start at page 2, go back to page 1
        result = runner.invoke(dojo, ['leetcode', 'query', '-p', '2'], input='p\nq\n')

        assert 'Page 2/2' in result.output
        assert 'Page 1/2' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_pagination_jump_to_page(self, mock_client_class, mock_repo_class):
        """Test jumping to specific page number."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        problems = [
            ProblemSummary(id=i, title=f'Problem {i}', title_slug=f'problem-{i}',
                          difficulty='Easy', paid_only=False, tags=[])
            for i in range(1, 101)
        ]
        mock_client.query_problems.return_value = problems

        runner = CliRunner()
        # Jump directly to page 3
        result = runner.invoke(dojo, ['leetcode', 'query'], input='3\nq\n')

        assert 'Page 1/5' in result.output
        assert 'Page 3/5' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_already_on_last_page(self, mock_client_class, mock_repo_class):
        """Test message when trying to go past last page."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        problems = [
            ProblemSummary(id=1, title='Only Problem', title_slug='only',
                          difficulty='Easy', paid_only=False, tags=[])
        ]
        mock_client.query_problems.return_value = problems

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query'], input='n\nq\n')

        assert 'Already on last page' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_already_on_first_page(self, mock_client_class, mock_repo_class):
        """Test message when trying to go before first page."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        problems = [
            ProblemSummary(id=i, title=f'Problem {i}', title_slug=f'p{i}',
                          difficulty='Easy', paid_only=False, tags=[])
            for i in range(1, 31)
        ]
        mock_client.query_problems.return_value = problems

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query'], input='p\nq\n')

        assert 'Already on first page' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_shows_premium_marker(self, mock_client_class, mock_repo_class):
        """Test that premium problems show $ marker."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Premium Problem', title_slug='premium',
                          difficulty='Medium', paid_only=True, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query'], input='q\n')

        assert '$' in result.output

    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_list_tags(self, mock_client_class):
        """Test --list-tags option."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.get_available_tags.return_value = ['Array', 'Dynamic Programming', 'Tree']

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query', '--list-tags'])

        assert result.exit_code == 0
        assert 'Array' in result.output
        assert 'Dynamic Programming' in result.output
        assert 'Tree' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_no_results(self, mock_client_class, mock_repo_class):
        """Test query with no matching results."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = []

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query'])

        assert result.exit_code == 0
        assert 'No problems found' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_quit_with_empty_input(self, mock_client_class, mock_repo_class):
        """Test that empty input (just Enter) quits."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Test', title_slug='test',
                          difficulty='Easy', paid_only=False, tags=[])
        ]

        runner = CliRunner()
        # Just press Enter to quit
        result = runner.invoke(dojo, ['leetcode', 'query'], input='\n')

        assert result.exit_code == 0


class TestQueryCommandWithDatabase:
    """Test query command database integration."""

    @patch('bytedojo.commands.leetcode.query.DatabaseManager')
    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_query_shows_status_from_db(self, mock_client_class, mock_repo_class, mock_db_class):
        """Test that problem status from database is displayed."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        mock_db.get_problem.side_effect = lambda source, pid: (
            {'test_status': 'passed'} if pid == 1 else
            {'test_status': 'failed'} if pid == 2 else
            None
        )
        mock_db_class.return_value = mock_db

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Passed Problem', title_slug='passed',
                          difficulty='Easy', paid_only=False, tags=[]),
            ProblemSummary(id=2, title='Failed Problem', title_slug='failed',
                          difficulty='Medium', paid_only=False, tags=[]),
            ProblemSummary(id=3, title='Not Fetched', title_slug='not-fetched',
                          difficulty='Hard', paid_only=False, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query'], input='q\n')

        assert result.exit_code == 0
        assert 'Passed Problem' in result.output
        assert 'Failed Problem' in result.output
        assert 'Not Fetched' in result.output


class TestQueryCommandValidation:
    """Test query command input validation."""

    def test_invalid_difficulty(self):
        """Test that invalid difficulty is rejected."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query', '-d', 'invalid'])

        assert result.exit_code != 0

    def test_invalid_page_type(self):
        """Test that non-integer page is rejected."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query', '-p', 'abc'])

        assert result.exit_code != 0

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_invalid_page_number_in_interactive(self, mock_client_class, mock_repo_class):
        """Test that invalid page number shows error message."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        problems = [
            ProblemSummary(id=i, title=f'Problem {i}', title_slug=f'p{i}',
                          difficulty='Easy', paid_only=False, tags=[])
            for i in range(1, 21)
        ]
        mock_client.query_problems.return_value = problems

        runner = CliRunner()
        # Try to go to page 100 when only 1 page exists
        result = runner.invoke(dojo, ['leetcode', 'query'], input='100\nq\n')

        assert 'Invalid page' in result.output


class TestQueryCommandOutput:
    """Test query command output formatting."""

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_output_has_header(self, mock_client_class, mock_repo_class):
        """Test that output has proper header."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Test', title_slug='test',
                          difficulty='Easy', paid_only=False, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query'], input='q\n')

        assert 'ID' in result.output
        assert 'Title' in result.output

    @patch('bytedojo.commands.leetcode.query.DojoRepository')
    @patch('bytedojo.commands.leetcode.query.LeetCodeClient')
    def test_navigation_hints_shown(self, mock_client_class, mock_repo_class):
        """Test that navigation hints are displayed."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        problems = [
            ProblemSummary(id=i, title=f'Problem {i}', title_slug=f'p{i}',
                          difficulty='Easy', paid_only=False, tags=[])
            for i in range(1, 31)
        ]
        mock_client.query_problems.return_value = problems

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query'], input='q\n')

        assert 'n=next' in result.output
        assert 'q=quit' in result.output


class TestQueryCommandIntegration:
    """Integration tests for query command."""

    def test_query_command_registered(self):
        """Test that query command is registered under leetcode."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', '--help'])

        assert result.exit_code == 0
        assert 'query' in result.output

    def test_query_accessible_via_dojo_leetcode_query(self):
        """Test that command is accessible via full path."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'query', '--help'])

        assert result.exit_code == 0
        assert 'difficulty' in result.output.lower()
