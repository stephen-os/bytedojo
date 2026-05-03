"""
Tests for the query command.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from pathlib import Path

from bytedojo.commands.bytedojo import dojo
from bytedojo.core.models import ProblemSummary
from bytedojo.core.query import QueryResult


class TestQueryCommand:
    """Test the query command."""

    def test_query_help(self):
        """Test that query --help works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['query', '--help'])

        assert result.exit_code == 0
        assert 'Search LeetCode problems' in result.output
        assert '--difficulty' in result.output
        assert '--tag' in result.output
        assert '--page' in result.output
        assert '--per-page' in result.output
        assert '--list-tags' in result.output

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_query_displays_problems(self, mock_service_class):
        """Test query displays problems in table format."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_service.query.return_value = QueryResult(
            problems=[
                ProblemSummary(id=1, title='Two Sum', title_slug='two-sum',
                              difficulty='Easy', paid_only=False, tags=['Array'])
            ],
            total=1,
            status_map={}
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['query'], input='q\n')

        assert result.exit_code == 0
        assert 'Two Sum' in result.output
        assert 'Page 1/1' in result.output

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_query_by_difficulty(self, mock_service_class):
        """Test query filtering by difficulty."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.query.return_value = QueryResult(problems=[], total=0, status_map={})

        runner = CliRunner()
        runner.invoke(dojo, ['query', '-d', 'easy'], input='q\n')

        mock_service.query.assert_called_once_with(
            difficulty='easy',
            tags=None,
            include_status=True
        )

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_query_by_tag(self, mock_service_class):
        """Test query filtering by tag."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.query.return_value = QueryResult(problems=[], total=0, status_map={})

        runner = CliRunner()
        runner.invoke(dojo, ['query', '-t', 'array', '-t', 'tree'], input='q\n')

        mock_service.query.assert_called_once_with(
            difficulty=None,
            tags=['array', 'tree'],
            include_status=True
        )

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_query_pagination_next(self, mock_service_class):
        """Test pagination with 'n' for next page."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        problems = [
            ProblemSummary(id=i, title=f'Problem {i}', title_slug=f'problem-{i}',
                          difficulty='Easy', paid_only=False, tags=[])
            for i in range(1, 31)
        ]
        mock_service.query.return_value = QueryResult(
            problems=problems, total=30, status_map={}
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['query'], input='n\nq\n')

        assert 'Page 1/2' in result.output
        assert 'Page 2/2' in result.output

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_query_already_on_last_page(self, mock_service_class):
        """Test message when trying to go past last page."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_service.query.return_value = QueryResult(
            problems=[
                ProblemSummary(id=1, title='Only Problem', title_slug='only',
                              difficulty='Easy', paid_only=False, tags=[])
            ],
            total=1,
            status_map={}
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['query'], input='n\nq\n')

        assert 'Already on last page' in result.output

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_query_shows_premium_marker(self, mock_service_class):
        """Test that premium problems show $ marker."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_service.query.return_value = QueryResult(
            problems=[
                ProblemSummary(id=1, title='Premium Problem', title_slug='premium',
                              difficulty='Medium', paid_only=True, tags=[])
            ],
            total=1,
            status_map={}
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['query'], input='q\n')

        assert '$' in result.output

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_list_tags(self, mock_service_class):
        """Test --list-tags option."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_service.get_available_tags.return_value = ['Array', 'Dynamic Programming', 'Tree']

        runner = CliRunner()
        result = runner.invoke(dojo, ['query', '--list-tags'])

        assert result.exit_code == 0
        assert 'Array' in result.output
        assert 'Dynamic Programming' in result.output
        assert 'Tree' in result.output

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_query_no_results(self, mock_service_class):
        """Test query with no matching results."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_service.query.return_value = QueryResult(problems=[], total=0, status_map={})

        runner = CliRunner()
        result = runner.invoke(dojo, ['query'])

        assert result.exit_code == 0
        assert 'No problems found' in result.output


class TestQueryCommandValidation:
    """Test query command input validation."""

    def test_invalid_difficulty(self):
        """Test that invalid difficulty is rejected."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['query', '-d', 'invalid'])

        assert result.exit_code != 0

    def test_invalid_page_type(self):
        """Test that non-integer page is rejected."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['query', '-p', 'abc'])

        assert result.exit_code != 0


class TestQueryCommandOutput:
    """Test query command output formatting."""

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_output_has_header(self, mock_service_class):
        """Test that output has proper header."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_service.query.return_value = QueryResult(
            problems=[
                ProblemSummary(id=1, title='Test', title_slug='test',
                              difficulty='Easy', paid_only=False, tags=[])
            ],
            total=1,
            status_map={}
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['query'], input='q\n')

        assert 'ID' in result.output
        assert 'Title' in result.output

    @patch('bytedojo.commands.subcommands.query.QueryService')
    def test_navigation_hints_shown(self, mock_service_class):
        """Test that navigation hints are displayed."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        problems = [
            ProblemSummary(id=i, title=f'Problem {i}', title_slug=f'p{i}',
                          difficulty='Easy', paid_only=False, tags=[])
            for i in range(1, 31)
        ]
        mock_service.query.return_value = QueryResult(
            problems=problems, total=30, status_map={}
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['query'], input='q\n')

        assert 'n=next' in result.output
        assert 'q=quit' in result.output


class TestQueryCommandIntegration:
    """Integration tests for query command."""

    def test_query_command_registered(self):
        """Test that query command is registered."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--help'])

        assert result.exit_code == 0
        assert 'query' in result.output

    def test_query_accessible_via_dojo_query(self):
        """Test that command is accessible via dojo query."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['query', '--help'])

        assert result.exit_code == 0
        assert 'difficulty' in result.output.lower()
