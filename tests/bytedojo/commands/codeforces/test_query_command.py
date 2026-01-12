"""
Tests for the Codeforces query command.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from pathlib import Path

from bytedojo.commands.dojo import dojo
from bytedojo.core.codeforces.models import ProblemSummary


class TestQueryCommand:
    """Test the codeforces query command."""

    def test_query_help(self):
        """Test that query --help works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'query', '--help'])

        assert result.exit_code == 0
        assert 'Search Codeforces problems' in result.output
        assert '--difficulty' in result.output
        assert '--rating-min' in result.output
        assert '--rating-max' in result.output
        assert '--tag' in result.output
        assert '--page' in result.output

    @patch('bytedojo.commands.codeforces.query.DojoRepository')
    @patch('bytedojo.commands.codeforces.query.CodeforcesClient')
    def test_query_displays_problems(self, mock_client_class, mock_repo_class):
        """Test that query displays problems."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=1, index='A', name='Theatre Square',
                          rating=1000, tags=['math']),
            ProblemSummary(contest_id=4, index='A', name='Watermelon',
                          rating=800, tags=['math', 'brute force'])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'query'], input='q\n')

        assert result.exit_code == 0
        assert 'Theatre Square' in result.output or '1A' in result.output

    @patch('bytedojo.commands.codeforces.query.DojoRepository')
    @patch('bytedojo.commands.codeforces.query.CodeforcesClient')
    def test_query_with_difficulty_filter(self, mock_client_class, mock_repo_class):
        """Test query with difficulty filter."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'query', '-d', 'easy'])

        # Should call with rating range for easy (0-1199)
        mock_client.query_problems.assert_called()

    @patch('bytedojo.commands.codeforces.query.DojoRepository')
    @patch('bytedojo.commands.codeforces.query.CodeforcesClient')
    def test_query_with_rating_range(self, mock_client_class, mock_repo_class):
        """Test query with rating range filters."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['codeforces', 'query', '-r', '1200', '-R', '1600'])

        mock_client.query_problems.assert_called_once_with(
            rating_min=1200,
            rating_max=1600,
            tags=None
        )

    @patch('bytedojo.commands.codeforces.query.DojoRepository')
    @patch('bytedojo.commands.codeforces.query.CodeforcesClient')
    def test_query_with_tags(self, mock_client_class, mock_repo_class):
        """Test query with tag filter."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        runner.invoke(dojo, ['codeforces', 'query', '-t', 'dp', '-t', 'graphs'])

        mock_client.query_problems.assert_called_once_with(
            rating_min=None,
            rating_max=None,
            tags=['dp', 'graphs']
        )

    @patch('bytedojo.commands.codeforces.query.CodeforcesClient')
    def test_query_list_tags(self, mock_client_class):
        """Test query --list-tags option."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_available_tags.return_value = ['dp', 'graphs', 'math']

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'query', '--list-tags'])

        assert result.exit_code == 0
        assert 'dp' in result.output
        assert 'graphs' in result.output
        assert 'math' in result.output

    @patch('bytedojo.commands.codeforces.query.DojoRepository')
    @patch('bytedojo.commands.codeforces.query.CodeforcesClient')
    def test_query_no_results(self, mock_client_class, mock_repo_class):
        """Test query with no matching results."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_client.query_problems.return_value = []

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'query'])

        assert 'No problems found' in result.output


class TestQueryCommandWithDatabase:
    """Test query command database integration."""

    @patch('bytedojo.commands.codeforces.query.DatabaseManager')
    @patch('bytedojo.commands.codeforces.query.DojoRepository')
    @patch('bytedojo.commands.codeforces.query.CodeforcesClient')
    def test_query_shows_status_icons(self, mock_client_class, mock_repo_class, mock_db_class):
        """Test that query shows status icons from database."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        mock_db.get_problem.return_value = {'test_status': 'passed'}
        mock_db_class.return_value = mock_db

        mock_client.query_problems.return_value = [
            ProblemSummary(contest_id=1, index='A', name='Test',
                          rating=1000, tags=[])
        ]

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'query'], input='q\n')

        assert result.exit_code == 0


class TestQueryCommandValidation:
    """Test query command input validation."""

    def test_invalid_difficulty(self):
        """Test that invalid difficulty is rejected."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'query', '-d', 'invalid'])

        assert result.exit_code != 0


class TestQueryCommandIntegration:
    """Integration tests for query command."""

    def test_query_command_registered(self):
        """Test that query command is registered under codeforces."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', '--help'])

        assert result.exit_code == 0
        assert 'query' in result.output
