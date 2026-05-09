"""
Tests for the fetch command.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from bytedojo.commands.bytedojo import dojo
from bytedojo.core.models import Language
from bytedojo.core.problem_service import PlaceResult


class TestFetchCommand:
    """Test the fetch command basic functionality."""

    def test_fetch_requires_arguments(self, tmp_path):
        """Test that fetch requires at least one argument."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize repo first
            runner.invoke(dojo, ['init'])

            # Fetch without arguments should fail
            result = runner.invoke(dojo, ['fetch'])

            assert result.exit_code != 0
            assert 'Missing argument' in result.output or 'required' in result.output.lower()

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_single_problem_success(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching a single problem successfully."""
        runner = CliRunner()

        # Setup mocks
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.PYTHON3,
            version=1,
            file_path=Path('/problems/0001-two-sum/python3/v001/solution.py')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1'])

            assert result.exit_code == 0
            assert 'Two Sum' in result.output
            assert '1 fetched' in result.output
            mock_service.place_problem.assert_called_once()

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_multiple_problems(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching multiple problems."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1, 2, 3]

        def place_problem_side_effect(problem_id, language, repo, force):
            return PlaceResult(
                problem_id=problem_id,
                title=f'Problem {problem_id}',
                language=language,
                version=1,
                file_path=Path(f'/problems/{problem_id:04d}-problem/python3/v001/solution.py')
            )

        mock_service.place_problem.side_effect = place_problem_side_effect

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1,2,3'])

            assert result.exit_code == 0
            assert '3 fetched' in result.output
            assert mock_service.place_problem.call_count == 3

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_range_of_problems(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching a range of problems."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1, 2, 3, 4, 5]

        def place_problem_side_effect(problem_id, language, repo, force):
            return PlaceResult(
                problem_id=problem_id,
                title=f'Problem {problem_id}',
                language=language,
                version=1,
                file_path=Path(f'/problems/{problem_id:04d}-problem/python3/v001/solution.py')
            )

        mock_service.place_problem.side_effect = place_problem_side_effect

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1..5'])

            assert result.exit_code == 0
            assert '5 fetched' in result.output
            mock_service.parse_problem_ids.assert_called_once()


class TestFetchCommandLanguageOptions:
    """Test the fetch command language options."""

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_with_python_flag(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching with --python flag."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'java'  # Different default
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.PYTHON3,
            version=1,
            file_path=Path('/problems/0001-two-sum/python3/v001/solution.py')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1', '--python'])

            assert result.exit_code == 0
            # Verify place_problem was called with Python language
            call_args = mock_service.place_problem.call_args
            assert call_args.kwargs['language'] == Language.PYTHON3

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_with_py_short_flag(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching with -py short flag."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'java'
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.PYTHON3,
            version=1,
            file_path=Path('/problems/0001-two-sum/python3/v001/solution.py')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1', '-py'])

            assert result.exit_code == 0
            call_args = mock_service.place_problem.call_args
            assert call_args.kwargs['language'] == Language.PYTHON3

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_with_java_flag(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching with --java flag."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.JAVA,
            version=1,
            file_path=Path('/problems/0001-two-sum/java/v001/Solution.java')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1', '--java'])

            assert result.exit_code == 0
            call_args = mock_service.place_problem.call_args
            assert call_args.kwargs['language'] == Language.JAVA

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_with_cpp_flag(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching with --cpp flag."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.CPP,
            version=1,
            file_path=Path('/problems/0001-two-sum/cpp/v001/solution.cpp')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1', '--cpp'])

            assert result.exit_code == 0
            call_args = mock_service.place_problem.call_args
            assert call_args.kwargs['language'] == Language.CPP

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_uses_default_language(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test that fetch uses default language when no flag specified."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'java'  # Set default to java
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.JAVA,
            version=1,
            file_path=Path('/problems/0001-two-sum/java/v001/Solution.java')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1'])

            assert result.exit_code == 0
            call_args = mock_service.place_problem.call_args
            assert call_args.kwargs['language'] == Language.JAVA


class TestFetchCommandForceOption:
    """Test the fetch command --force option."""

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_with_force_flag(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching with --force flag."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.PYTHON3,
            version=2,  # Version 2 since forced
            file_path=Path('/problems/0001-two-sum/python3/v002/solution.py')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1', '--force'])

            assert result.exit_code == 0
            call_args = mock_service.place_problem.call_args
            assert call_args.kwargs['force'] is True

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_without_force_skips_existing(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test that fetch without --force skips existing problems."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.PYTHON3,
            version=0,
            file_path=Path(),
            skipped=True
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1'])

            assert result.exit_code == 0
            assert 'already registered' in result.output or 'skipped' in result.output.lower()
            assert '0 fetched' in result.output
            assert '1 skipped' in result.output


class TestFetchCommandErrorHandling:
    """Test the fetch command error handling."""

    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    def test_fetch_fails_if_repo_not_initialized(self, mock_get_repo, tmp_path):
        """Test that fetch fails if repository is not initialized."""
        runner = CliRunner()

        import click
        mock_get_repo.side_effect = click.ClickException("Repository not initialized")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1'])

            assert result.exit_code != 0
            assert 'not initialized' in result.output.lower() or 'error' in result.output.lower()

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_handles_unknown_language(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test that fetch handles unknown language gracefully."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'invalid_language'
        mock_service.parse_problem_ids.return_value = [1]

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1'])

            assert result.exit_code != 0
            assert 'unknown language' in result.output.lower()

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_handles_problem_not_found(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test that fetch handles problem not found error."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [99999]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=99999,
            title='',
            language=Language.PYTHON3,
            version=0,
            file_path=Path(),
            error='Problem 99999 not found'
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '99999'])

            assert result.exit_code == 0  # Command completes but reports error
            assert 'not found' in result.output.lower() or 'error' in result.output.lower()
            assert '0 fetched' in result.output
            assert '1 error' in result.output

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_handles_empty_problem_ids(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test that fetch handles empty problem IDs."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = []  # No IDs parsed

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', ''])

            assert result.exit_code != 0
            assert 'no problem' in result.output.lower() or 'error' in result.output.lower()


class TestFetchCommandMixedResults:
    """Test the fetch command with mixed results (success, skip, error)."""

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_mixed_results(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetch with mix of success, skip, and error."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1, 2, 3]

        results = [
            # Success
            PlaceResult(
                problem_id=1,
                title='Two Sum',
                language=Language.PYTHON3,
                version=1,
                file_path=Path('/problems/0001-two-sum/python3/v001/solution.py')
            ),
            # Skipped
            PlaceResult(
                problem_id=2,
                title='Add Two Numbers',
                language=Language.PYTHON3,
                version=0,
                file_path=Path(),
                skipped=True
            ),
            # Error
            PlaceResult(
                problem_id=3,
                title='',
                language=Language.PYTHON3,
                version=0,
                file_path=Path(),
                error='Problem 3 not found'
            ),
        ]

        mock_service.place_problem.side_effect = results

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1,2,3'])

            assert result.exit_code == 0
            assert '1 fetched' in result.output
            assert '1 skipped' in result.output
            assert '1 error' in result.output


class TestFetchCommandOutputMessages:
    """Test the fetch command output messages."""

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_shows_problem_count_message(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test that fetch shows the count of problems being fetched."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1, 2, 3]

        def place_problem_side_effect(problem_id, language, repo, force):
            return PlaceResult(
                problem_id=problem_id,
                title=f'Problem {problem_id}',
                language=language,
                version=1,
                file_path=Path(f'/problems/{problem_id:04d}-problem/python3/v001/solution.py')
            )

        mock_service.place_problem.side_effect = place_problem_side_effect

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1,2,3'])

            assert result.exit_code == 0
            assert 'Fetching 3 problem(s)' in result.output
            assert 'PYTHON3' in result.output.upper()

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_shows_file_path_for_success(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test that fetch shows file path for successful fetches."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.PYTHON3,
            version=1,
            file_path=Path('/problems/0001-two-sum/python3/v001/solution.py')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1'])

            assert result.exit_code == 0
            assert 'Saved to:' in result.output
            assert 'solution.py' in result.output

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_shows_summary_at_end(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test that fetch shows summary at the end."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.PYTHON3,
            version=1,
            file_path=Path('/problems/0001-two-sum/python3/v001/solution.py')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1'])

            assert result.exit_code == 0
            assert 'Fetch complete' in result.output


class TestParseProblemIds:
    """Test the parse_problem_ids function directly."""

    def test_parse_single_id(self):
        """Test parsing a single problem ID."""
        from bytedojo.core.problem_service import parse_problem_ids

        result = parse_problem_ids(('1',))
        assert result == [1]

    def test_parse_multiple_comma_separated(self):
        """Test parsing comma-separated IDs."""
        from bytedojo.core.problem_service import parse_problem_ids

        result = parse_problem_ids(('1,2,3',))
        assert result == [1, 2, 3]

    def test_parse_range(self):
        """Test parsing a range of IDs."""
        from bytedojo.core.problem_service import parse_problem_ids

        result = parse_problem_ids(('1..5',))
        assert result == [1, 2, 3, 4, 5]

    def test_parse_mixed_format(self):
        """Test parsing mixed formats."""
        from bytedojo.core.problem_service import parse_problem_ids

        result = parse_problem_ids(('1,5..7,10',))
        assert result == [1, 5, 6, 7, 10]

    def test_parse_multiple_arguments(self):
        """Test parsing multiple argument strings."""
        from bytedojo.core.problem_service import parse_problem_ids

        result = parse_problem_ids(('1', '2', '3'))
        assert result == [1, 2, 3]

    def test_parse_removes_duplicates(self):
        """Test that duplicate IDs are removed."""
        from bytedojo.core.problem_service import parse_problem_ids

        result = parse_problem_ids(('1,1,2,2,3',))
        assert result == [1, 2, 3]

    def test_parse_preserves_order(self):
        """Test that order is preserved after deduplication."""
        from bytedojo.core.problem_service import parse_problem_ids

        result = parse_problem_ids(('3,1,2',))
        assert result == [3, 1, 2]

    def test_parse_invalid_id_raises_error(self):
        """Test that invalid IDs raise ValueError."""
        from bytedojo.core.problem_service import parse_problem_ids

        with pytest.raises(ValueError):
            parse_problem_ids(('abc',))

    def test_parse_invalid_range_raises_error(self):
        """Test that invalid ranges raise ValueError."""
        from bytedojo.core.problem_service import parse_problem_ids

        with pytest.raises(ValueError):
            parse_problem_ids(('5..1',))  # Start > End

    def test_parse_malformed_range_raises_error(self):
        """Test that malformed ranges raise ValueError."""
        from bytedojo.core.problem_service import parse_problem_ids

        with pytest.raises(ValueError):
            parse_problem_ids(('1..2..3',))

    def test_parse_empty_returns_empty_list(self):
        """Test that empty input returns empty list."""
        from bytedojo.core.problem_service import parse_problem_ids

        result = parse_problem_ids(())
        assert result == []

    def test_parse_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        from bytedojo.core.problem_service import parse_problem_ids

        result = parse_problem_ids((' 1 , 2 , 3 ',))
        assert result == [1, 2, 3]


class TestLanguageModel:
    """Test the Language model used by fetch command."""

    def test_language_from_string_python3(self):
        """Test parsing python3 language."""
        lang = Language.from_string('python3')
        assert lang == Language.PYTHON3

    def test_language_from_string_java(self):
        """Test parsing java language."""
        lang = Language.from_string('java')
        assert lang == Language.JAVA

    def test_language_from_string_cpp(self):
        """Test parsing cpp language."""
        lang = Language.from_string('cpp')
        assert lang == Language.CPP

    def test_language_from_string_case_insensitive(self):
        """Test that language parsing is case insensitive."""
        lang = Language.from_string('PYTHON3')
        assert lang == Language.PYTHON3

    def test_language_from_string_unknown(self):
        """Test that unknown languages return UNKNOWN."""
        lang = Language.from_string('invalid')
        assert lang == Language.UNKNOWN

    def test_language_from_string_empty(self):
        """Test that empty string returns UNKNOWN."""
        lang = Language.from_string('')
        assert lang == Language.UNKNOWN

    def test_language_from_string_none(self):
        """Test that None returns UNKNOWN."""
        lang = Language.from_string(None)
        assert lang == Language.UNKNOWN


class TestFetchCommandIntegration:
    """Integration tests for fetch command (with actual repo init)."""

    def test_fetch_integration_without_init(self, tmp_path):
        """Test fetch fails gracefully when repo is not initialized."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1'])

            assert result.exit_code != 0
            # Should mention initialization
            assert 'init' in result.output.lower() or 'not initialized' in result.output.lower()

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    def test_fetch_integration_after_init(self, mock_service, tmp_path):
        """Test fetch works after repo initialization."""
        runner = CliRunner()

        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.PYTHON3,
            version=1,
            file_path=Path('problems/0001-two-sum/python3/v001/solution.py')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize first
            init_result = runner.invoke(dojo, ['init'])
            assert init_result.exit_code == 0

            # Now fetch
            result = runner.invoke(dojo, ['fetch', '1'])

            assert result.exit_code == 0
            mock_service.place_problem.assert_called_once()


class TestFetchCommandEdgeCases:
    """Test edge cases for the fetch command."""

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_large_range(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching a large range of problems."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = list(range(1, 101))  # 100 problems

        def place_problem_side_effect(problem_id, language, repo, force):
            return PlaceResult(
                problem_id=problem_id,
                title=f'Problem {problem_id}',
                language=language,
                version=1,
                file_path=Path(f'/problems/{problem_id:04d}-problem/python3/v001/solution.py')
            )

        mock_service.place_problem.side_effect = place_problem_side_effect

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1..100'])

            assert result.exit_code == 0
            assert '100 fetched' in result.output

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_with_force_and_language(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetching with both --force and language flags."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1]
        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.JAVA,
            version=2,
            file_path=Path('/problems/0001-two-sum/java/v002/Solution.java')
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1', '--force', '--java'])

            assert result.exit_code == 0
            call_args = mock_service.place_problem.call_args
            assert call_args.kwargs['force'] is True
            assert call_args.kwargs['language'] == Language.JAVA

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_all_errors(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetch when all problems result in errors."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [99998, 99999]

        mock_service.place_problem.return_value = PlaceResult(
            problem_id=99999,
            title='',
            language=Language.PYTHON3,
            version=0,
            file_path=Path(),
            error='Problem not found'
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '99998,99999'])

            assert result.exit_code == 0  # Command completes
            assert '0 fetched' in result.output
            assert '2 error' in result.output

    @patch('bytedojo.commands.subcommands.fetch.problem_service')
    @patch('bytedojo.commands.subcommands.fetch.get_initialized_repo')
    @patch('bytedojo.commands.subcommands.fetch.get_default_language')
    def test_fetch_all_skipped(self, mock_default_lang, mock_get_repo, mock_service, tmp_path):
        """Test fetch when all problems are skipped."""
        runner = CliRunner()

        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_default_lang.return_value = 'python3'
        mock_service.parse_problem_ids.return_value = [1, 2]

        mock_service.place_problem.return_value = PlaceResult(
            problem_id=1,
            title='Two Sum',
            language=Language.PYTHON3,
            version=0,
            file_path=Path(),
            skipped=True
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['fetch', '1,2'])

            assert result.exit_code == 0
            assert '0 fetched' in result.output
            assert '2 skipped' in result.output
