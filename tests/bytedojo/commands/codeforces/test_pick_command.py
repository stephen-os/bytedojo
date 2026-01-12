"""
Tests for the Codeforces pick command.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from pathlib import Path

from bytedojo.commands.dojo import dojo
from bytedojo.core.codeforces.models import ProblemSummary


class TestPickCommand:
    """Test the codeforces pick command."""

    def test_pick_help(self):
        """Test that pick --help works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick', '--help'])

        assert result.exit_code == 0
        assert 'Pick a random' in result.output
        assert '--difficulty' in result.output
        assert '--tag' in result.output
        assert '--rating-min' in result.output

    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_selects_random_problem(self, mock_client_class, mock_repo_class):
        """Test that pick selects a random unsolved problem."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=1, index='A', name='Theatre Square',
                          rating=1000, tags=['math']),
            ProblemSummary(contest_id=4, index='A', name='Watermelon',
                          rating=800, tags=['math'])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick'])

        assert result.exit_code == 0
        assert 'PICKED FOR YOU' in result.output
        # Should show one of the problems
        assert 'Theatre Square' in result.output or 'Watermelon' in result.output

    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_filters_by_difficulty(self, mock_client_class, mock_repo_class):
        """Test that pick filters by difficulty."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['codeforces', 'pick', '-d', 'easy'])

        # Should be called with rating range for easy
        mock_client.query_problems.assert_called()

    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_filters_by_tag(self, mock_client_class, mock_repo_class):
        """Test that pick filters by tag."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['codeforces', 'pick', '-t', 'dp', '-t', 'graphs'])

        mock_client.query_problems.assert_called_once()
        call_kwargs = mock_client.query_problems.call_args[1]
        assert call_kwargs['tags'] == ['dp', 'graphs']

    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_with_rating_range(self, mock_client_class, mock_repo_class):
        """Test that pick accepts rating range filters."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['codeforces', 'pick', '-r', '1200', '-R', '1600'])

        mock_client.query_problems.assert_called_once_with(
            rating_min=1200,
            rating_max=1600,
            tags=None
        )

    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_no_problems_found(self, mock_client_class, mock_repo_class):
        """Test message when no problems match criteria."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick'])

        assert result.exit_code == 0
        assert 'No problems found' in result.output

    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_shows_url(self, mock_client_class, mock_repo_class):
        """Test that pick shows the Codeforces URL."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=4, index='A', name='Watermelon',
                          rating=800, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick'])

        assert 'https://codeforces.com/problemset/problem/4/A' in result.output

    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_shows_fetch_hint(self, mock_client_class, mock_repo_class):
        """Test that pick shows how to fetch the problem."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=4, index='A', name='Watermelon',
                          rating=800, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick'])

        assert 'dojo codeforces fetch 4A' in result.output

    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_shows_rating(self, mock_client_class, mock_repo_class):
        """Test that pick shows problem rating."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=1, index='A', name='Test',
                          rating=1500, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick'])

        assert '1500' in result.output

    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_shows_tags(self, mock_client_class, mock_repo_class):
        """Test that pick shows problem tags."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=1, index='A', name='Test',
                          rating=1500, tags=['dp', 'greedy'])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick'])

        assert 'dp' in result.output
        assert 'greedy' in result.output


class TestPickCommandWithDatabase:
    """Test pick command database integration."""

    @patch('bytedojo.commands.codeforces.pick.DatabaseManager')
    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
    def test_pick_excludes_fetched_problems(self, mock_client_class, mock_repo_class, mock_db_class):
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
        # Problem 1A is already fetched
        mock_db.list_problems.return_value = [{'problem_id': '1A'}]
        mock_db_class.return_value = mock_db

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=1, index='A', name='Already Fetched',
                          rating=1000, tags=[]),
            ProblemSummary(contest_id=4, index='A', name='Not Fetched',
                          rating=800, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick'])

        # Should only show "Not Fetched" since 1A is already done
        assert 'Not Fetched' in result.output
        assert 'Already Fetched' not in result.output

    @patch('bytedojo.commands.codeforces.pick.DatabaseManager')
    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
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
        mock_db.list_problems.return_value = [{'problem_id': '1A'}, {'problem_id': '4A'}]
        mock_db_class.return_value = mock_db

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=1, index='A', name='Problem 1',
                          rating=1000, tags=[]),
            ProblemSummary(contest_id=4, index='A', name='Problem 2',
                          rating=800, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick'])

        assert "You've solved all problems" in result.output

    @patch('bytedojo.commands.codeforces.pick.DatabaseManager')
    @patch('bytedojo.commands.codeforces.pick.DojoRepository')
    @patch('bytedojo.commands.codeforces.pick.CodeforcesClient')
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
        mock_db.list_problems.return_value = [{'problem_id': '1A'}]
        mock_db_class.return_value = mock_db

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=1, index='A', name='Solved',
                          rating=1000, tags=[]),
            ProblemSummary(contest_id=4, index='A', name='Unsolved',
                          rating=800, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick'])

        assert 'Unsolved: 1' in result.output
        assert 'Solved: 1' in result.output
        assert 'Total: 2' in result.output


class TestPickCommandValidation:
    """Test pick command input validation."""

    def test_invalid_difficulty(self):
        """Test that invalid difficulty is rejected."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick', '-d', 'invalid'])

        assert result.exit_code != 0


class TestPickCommandIntegration:
    """Integration tests for pick command."""

    def test_pick_command_registered(self):
        """Test that pick command is registered under codeforces."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', '--help'])

        assert result.exit_code == 0
        assert 'pick' in result.output

    def test_pick_accessible_via_dojo_codeforces_pick(self):
        """Test that command is accessible via full path."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'pick', '--help'])

        assert result.exit_code == 0
        assert 'random' in result.output.lower()
