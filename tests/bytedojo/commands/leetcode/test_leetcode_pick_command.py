"""
Tests for the LeetCode pick command.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from pathlib import Path

from bytedojo.commands.dojo import dojo
from bytedojo.core.leetcode.models import ProblemSummary


class TestPickCommand:
    """Test the leetcode pick command."""

    def test_pick_help(self):
        """Test that pick --help works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick', '--help'])

        assert result.exit_code == 0
        assert 'Pick a random problem' in result.output
        assert '--difficulty' in result.output
        assert '--tag' in result.output
        assert '--include-premium' in result.output

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_selects_random_problem(self, mock_client_class, mock_repo_class):
        """Test that pick selects a random unsolved problem."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Two Sum', title_slug='two-sum',
                          difficulty='Easy', paid_only=False, tags=['Array']),
            ProblemSummary(id=2, title='Add Two Numbers', title_slug='add-two-numbers',
                          difficulty='Medium', paid_only=False, tags=['Linked List'])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick'])

        assert result.exit_code == 0
        assert 'PICKED FOR YOU' in result.output
        # Should show one of the problems
        assert 'Two Sum' in result.output or 'Add Two Numbers' in result.output

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_filters_by_difficulty(self, mock_client_class, mock_repo_class):
        """Test that pick filters by difficulty."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['leetcode', 'pick', '-d', 'easy'])

        mock_client.query_problems.assert_called_once_with(
            difficulty=1,
            tags=None
        )

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_filters_by_tag(self, mock_client_class, mock_repo_class):
        """Test that pick filters by tag."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['leetcode', 'pick', '-t', 'array', '-t', 'tree'])

        mock_client.query_problems.assert_called_once_with(
            difficulty=None,
            tags=['array', 'tree']
        )

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_combined_filters(self, mock_client_class, mock_repo_class):
        """Test that pick accepts combined filters."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['leetcode', 'pick', '-d', 'medium', '-t', 'dp'])

        mock_client.query_problems.assert_called_once_with(
            difficulty=2,
            tags=['dp']
        )

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_excludes_premium_by_default(self, mock_client_class, mock_repo_class):
        """Test that premium problems are excluded by default."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        # Only premium problems
        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Premium Only', title_slug='premium',
                          difficulty='Easy', paid_only=True, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick'])

        assert 'No free problems found' in result.output

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_includes_premium_with_flag(self, mock_client_class, mock_repo_class):
        """Test that premium problems are included with --include-premium."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Premium Problem', title_slug='premium',
                          difficulty='Easy', paid_only=True, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick', '--include-premium'])

        assert 'Premium Problem' in result.output

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_no_problems_found(self, mock_client_class, mock_repo_class):
        """Test message when no problems match criteria."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick'])

        assert result.exit_code == 0
        assert 'No problems found' in result.output

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_shows_url(self, mock_client_class, mock_repo_class):
        """Test that pick shows the LeetCode URL."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Two Sum', title_slug='two-sum',
                          difficulty='Easy', paid_only=False, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick'])

        assert 'https://leetcode.com/problems/two-sum/' in result.output

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_shows_fetch_hint(self, mock_client_class, mock_repo_class):
        """Test that pick shows how to fetch the problem."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(id=42, title='Test Problem', title_slug='test',
                          difficulty='Easy', paid_only=False, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick'])

        assert 'dojo leetcode fetch 42' in result.output

    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_shows_tags(self, mock_client_class, mock_repo_class):
        """Test that pick shows problem tags."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Tagged Problem', title_slug='tagged',
                          difficulty='Easy', paid_only=False,
                          tags=['Array', 'Hash Table', 'Two Pointers'])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick'])

        assert 'Array' in result.output
        assert 'Hash Table' in result.output


class TestPickCommandWithDatabase:
    """Test pick command database integration."""

    @patch('bytedojo.commands.leetcode.pick.DatabaseManager')
    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_excludes_solved_problems(self, mock_client_class, mock_repo_class, mock_db_class):
        """Test that pick excludes already fetched problems."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        # Problem 1 is already fetched
        mock_db.list_problems.return_value = [{'problem_id': '1'}]
        mock_db_class.return_value = mock_db

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Already Fetched', title_slug='fetched',
                          difficulty='Easy', paid_only=False, tags=[]),
            ProblemSummary(id=2, title='Not Fetched', title_slug='not-fetched',
                          difficulty='Easy', paid_only=False, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick'])

        # Should only show "Not Fetched" since problem 1 is already done
        assert 'Not Fetched' in result.output
        assert 'Already Fetched' not in result.output

    @patch('bytedojo.commands.leetcode.pick.DatabaseManager')
    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_all_solved_message(self, mock_client_class, mock_repo_class, mock_db_class):
        """Test message when all matching problems are solved."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        # All problems are fetched
        mock_db.list_problems.return_value = [{'problem_id': '1'}, {'problem_id': '2'}]
        mock_db_class.return_value = mock_db

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Problem 1', title_slug='p1',
                          difficulty='Easy', paid_only=False, tags=[]),
            ProblemSummary(id=2, title='Problem 2', title_slug='p2',
                          difficulty='Easy', paid_only=False, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick'])

        assert "You've solved all problems" in result.output

    @patch('bytedojo.commands.leetcode.pick.DatabaseManager')
    @patch('bytedojo.commands.leetcode.pick.DojoRepository')
    @patch('bytedojo.commands.leetcode.pick.LeetCodeClient')
    def test_pick_shows_stats(self, mock_client_class, mock_repo_class, mock_db_class):
        """Test that pick shows unsolved/solved/total stats."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        mock_db.list_problems.return_value = [{'problem_id': '1'}]
        mock_db_class.return_value = mock_db

        mock_client.query_problems.return_value = [
            ProblemSummary(id=1, title='Solved', title_slug='solved',
                          difficulty='Easy', paid_only=False, tags=[]),
            ProblemSummary(id=2, title='Unsolved', title_slug='unsolved',
                          difficulty='Easy', paid_only=False, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick'])

        assert 'Unsolved: 1' in result.output
        assert 'Solved: 1' in result.output
        assert 'Total: 2' in result.output


class TestPickCommandValidation:
    """Test pick command input validation."""

    def test_invalid_difficulty(self):
        """Test that invalid difficulty is rejected."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick', '-d', 'invalid'])

        assert result.exit_code != 0


class TestPickCommandIntegration:
    """Integration tests for pick command."""

    def test_pick_command_registered(self):
        """Test that pick command is registered under leetcode."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', '--help'])

        assert result.exit_code == 0
        assert 'pick' in result.output

    def test_pick_accessible_via_dojo_leetcode_pick(self):
        """Test that command is accessible via full path."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['leetcode', 'pick', '--help'])

        assert result.exit_code == 0
        assert 'random' in result.output.lower()
