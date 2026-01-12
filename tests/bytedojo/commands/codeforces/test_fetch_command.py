"""
Tests for the Codeforces fetch command.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from pathlib import Path

from bytedojo.commands.dojo import dojo
from bytedojo.core.codeforces.models import Problem


class TestFetchCommand:
    """Test the codeforces fetch command."""

    def test_fetch_help(self):
        """Test that fetch --help works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'fetch', '--help'])

        assert result.exit_code == 0
        assert 'Fetch Codeforces problems' in result.output
        assert 'PROBLEM_IDS' in result.output
        assert '--force' in result.output

    def test_fetch_requires_argument(self):
        """Test that fetch requires problem ID argument."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'fetch'])

        assert result.exit_code != 0
        assert 'Missing argument' in result.output or 'required' in result.output.lower()

    @patch('bytedojo.commands.codeforces.fetch.DojoRepository')
    def test_fetch_requires_initialized_repo(self, mock_repo_class):
        """Test that fetch requires initialized repository."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False
        mock_repo_class.return_value = mock_repo

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'fetch', '1A'])

        assert result.exit_code != 0
        assert 'init' in result.output.lower() or 'not initialized' in result.output.lower()

    @patch('bytedojo.commands.codeforces.fetch.FileWriter')
    @patch('bytedojo.commands.codeforces.fetch.PythonFormatter')
    @patch('bytedojo.commands.codeforces.fetch.DatabaseManager')
    @patch('bytedojo.commands.codeforces.fetch.DojoRepository')
    @patch('bytedojo.commands.codeforces.fetch.CodeforcesClient')
    def test_fetch_single_problem(self, mock_client_class, mock_repo_class,
                                   mock_db_class, mock_formatter_class,
                                   mock_writer_class):
        """Test fetching a single problem."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_client = Mock()
        mock_client.get_problem.return_value = Problem(
            contest_id=1, index='A', name='Theatre Square',
            rating=1000, tags=['math'], time_limit='1s',
            memory_limit='256MB', description='Test',
            input_spec='', output_spec='', sample_tests=[], note=''
        )
        mock_client_class.return_value = mock_client

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        mock_db.is_problem_registered.return_value = False
        mock_db_class.return_value = mock_db

        mock_formatter = Mock()
        mock_formatter.format.return_value = '# Problem content'
        mock_formatter_class.return_value = mock_formatter

        mock_writer = Mock()
        mock_writer_class.return_value = mock_writer

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'fetch', '1A'])

        assert result.exit_code == 0
        mock_client.get_problem.assert_called_once_with(1, 'A')

    @patch('bytedojo.commands.codeforces.fetch.DatabaseManager')
    @patch('bytedojo.commands.codeforces.fetch.DojoRepository')
    @patch('bytedojo.commands.codeforces.fetch.CodeforcesClient')
    def test_fetch_invalid_problem_id(self, mock_client_class, mock_repo_class, mock_db_class):
        """Test that invalid problem ID is rejected."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        mock_db_class.return_value = mock_db

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'fetch', 'invalid'])

        # Should log error but not crash
        assert 'Invalid problem ID' in result.output or result.exit_code == 0

    @patch('bytedojo.commands.codeforces.fetch.DatabaseManager')
    @patch('bytedojo.commands.codeforces.fetch.DojoRepository')
    @patch('bytedojo.commands.codeforces.fetch.CodeforcesClient')
    def test_fetch_skips_registered_problem(self, mock_client_class, mock_repo_class, mock_db_class):
        """Test that already registered problems are skipped."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_client = Mock()
        mock_client.get_problem.return_value = Problem(
            contest_id=1, index='A', name='Test',
            rating=1000, tags=[], time_limit='1s',
            memory_limit='256MB', description='',
            input_spec='', output_spec='', sample_tests=[], note=''
        )
        mock_client_class.return_value = mock_client

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        mock_db.is_problem_registered.return_value = True  # Already registered
        mock_db_class.return_value = mock_db

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'fetch', '1A'])

        assert 'already registered' in result.output.lower() or 'skipped' in result.output.lower()


class TestFetchCommandIntegration:
    """Integration tests for fetch command."""

    def test_fetch_command_registered(self):
        """Test that fetch command is registered under codeforces."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', '--help'])

        assert result.exit_code == 0
        assert 'fetch' in result.output

    def test_codeforces_group_registered(self):
        """Test that codeforces group is registered."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--help'])

        assert result.exit_code == 0
        assert 'codeforces' in result.output


class TestFetchCommandMultipleProblems:
    """Test fetching multiple problems."""

    @patch('bytedojo.commands.codeforces.fetch.FileWriter')
    @patch('bytedojo.commands.codeforces.fetch.PythonFormatter')
    @patch('bytedojo.commands.codeforces.fetch.DatabaseManager')
    @patch('bytedojo.commands.codeforces.fetch.DojoRepository')
    @patch('bytedojo.commands.codeforces.fetch.CodeforcesClient')
    def test_fetch_multiple_problems(self, mock_client_class, mock_repo_class,
                                      mock_db_class, mock_formatter_class,
                                      mock_writer_class):
        """Test fetching multiple problems at once."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_client = Mock()
        mock_client.get_problem.side_effect = [
            Problem(
                contest_id=1, index='A', name='Problem 1',
                rating=1000, tags=[], time_limit='1s',
                memory_limit='256MB', description='',
                input_spec='', output_spec='', sample_tests=[], note=''
            ),
            Problem(
                contest_id=4, index='A', name='Problem 2',
                rating=800, tags=[], time_limit='1s',
                memory_limit='256MB', description='',
                input_spec='', output_spec='', sample_tests=[], note=''
            )
        ]
        mock_client_class.return_value = mock_client

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        mock_db.is_problem_registered.return_value = False
        mock_db_class.return_value = mock_db

        mock_formatter = Mock()
        mock_formatter.format.return_value = '# Content'
        mock_formatter_class.return_value = mock_formatter

        mock_writer = Mock()
        mock_writer_class.return_value = mock_writer

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'fetch', '1A', '4A'])

        assert result.exit_code == 0
        assert mock_client.get_problem.call_count == 2
        assert '2 fetched' in result.output

    @patch('bytedojo.commands.codeforces.fetch.DatabaseManager')
    @patch('bytedojo.commands.codeforces.fetch.DojoRepository')
    @patch('bytedojo.commands.codeforces.fetch.CodeforcesClient')
    def test_fetch_problem_not_found_on_api(self, mock_client_class, mock_repo_class, mock_db_class):
        """Test when problem doesn't exist on Codeforces."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_client = Mock()
        mock_client.get_problem.return_value = None  # Problem not found
        mock_client_class.return_value = mock_client

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        mock_db_class.return_value = mock_db

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'fetch', '99999Z'])

        assert 'not found' in result.output.lower() or 'Invalid' in result.output


class TestFetchCommandForce:
    """Test force overwrite functionality."""

    @patch('bytedojo.commands.codeforces.fetch.FileWriter')
    @patch('bytedojo.commands.codeforces.fetch.PythonFormatter')
    @patch('bytedojo.commands.codeforces.fetch.DatabaseManager')
    @patch('bytedojo.commands.codeforces.fetch.DojoRepository')
    @patch('bytedojo.commands.codeforces.fetch.CodeforcesClient')
    def test_fetch_with_force_overwrites(self, mock_client_class, mock_repo_class,
                                          mock_db_class, mock_formatter_class,
                                          mock_writer_class):
        """Test that --force overwrites existing problems."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_db_path.return_value = Path('/fake/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_client = Mock()
        mock_client.get_problem.return_value = Problem(
            contest_id=1, index='A', name='Test',
            rating=1000, tags=[], time_limit='1s',
            memory_limit='256MB', description='',
            input_spec='', output_spec='', sample_tests=[], note=''
        )
        mock_client_class.return_value = mock_client

        mock_db = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=False)
        mock_db.is_problem_registered.return_value = True  # Already registered
        mock_db_class.return_value = mock_db

        mock_formatter = Mock()
        mock_formatter.format.return_value = '# Content'
        mock_formatter_class.return_value = mock_formatter

        mock_writer = Mock()
        mock_writer_class.return_value = mock_writer

        runner = CliRunner()
        result = runner.invoke(dojo, ['codeforces', 'fetch', '1A', '--force'])

        assert result.exit_code == 0
        # With --force, should fetch even if registered
        mock_formatter.format.assert_called_once()
        mock_writer.write.assert_called_once()


class TestParseProblemId:
    """Test parse_problem_id function."""

    def test_parse_simple_id(self):
        """Test parsing simple ID like 1A."""
        from bytedojo.commands.codeforces.fetch import parse_problem_id
        contest_id, index = parse_problem_id('1A')
        assert contest_id == 1
        assert index == 'A'

    def test_parse_multi_digit_contest(self):
        """Test parsing multi-digit contest ID."""
        from bytedojo.commands.codeforces.fetch import parse_problem_id
        contest_id, index = parse_problem_id('1850B')
        assert contest_id == 1850
        assert index == 'B'

    def test_parse_index_with_number(self):
        """Test parsing index like A1."""
        from bytedojo.commands.codeforces.fetch import parse_problem_id
        contest_id, index = parse_problem_id('1A1')
        assert contest_id == 1
        assert index == 'A1'

    def test_parse_lowercase_converts_to_upper(self):
        """Test that lowercase index is converted to uppercase."""
        from bytedojo.commands.codeforces.fetch import parse_problem_id
        contest_id, index = parse_problem_id('1a')
        assert index == 'A'

    def test_parse_invalid_format(self):
        """Test parsing invalid format returns None."""
        from bytedojo.commands.codeforces.fetch import parse_problem_id
        contest_id, index = parse_problem_id('invalid')
        assert contest_id is None
        assert index is None

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        from bytedojo.commands.codeforces.fetch import parse_problem_id
        contest_id, index = parse_problem_id('')
        assert contest_id is None
        assert index is None

    def test_parse_with_whitespace(self):
        """Test parsing with surrounding whitespace."""
        from bytedojo.commands.codeforces.fetch import parse_problem_id
        contest_id, index = parse_problem_id('  4A  ')
        assert contest_id == 4
        assert index == 'A'
