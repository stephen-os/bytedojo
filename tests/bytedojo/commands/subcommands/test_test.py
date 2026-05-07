"""
Tests for the test command.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from bytedojo.commands.bytedojo import dojo
from bytedojo.commands.subcommands.test import (
    _display_test_header,
    _display_test_results,
    _truncate,
    test,
)
from bytedojo.core.test_runner import TestRunResult, TestCaseResult


class TestDisplayTestHeader:
    """Test the _display_test_header function."""

    def test_display_test_header_basic(self, capsys):
        """Test display with basic problem data."""
        problem = {
            'problem_id': '1',
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'language': 'python',
            'file_path': '/path/to/file.py',
        }

        _display_test_header(problem, 10)
        captured = capsys.readouterr()

        assert 'TEST PROBLEM' in captured.out
        assert '1' in captured.out
        assert 'Two Sum' in captured.out
        assert 'PYTHON' in captured.out
        assert 'Easy' in captured.out
        assert '/path/to/file.py' in captured.out
        assert '10' in captured.out


class TestDisplayTestResults:
    """Test the _display_test_results function."""

    def test_display_all_passed(self, capsys):
        """Test displaying all tests passed."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=10,
            passed_count=10,
            failed_count=0,
            error_count=0,
            case_results=[
                TestCaseResult(i, True, f"input {i}", f"output {i}", f"output {i}")
                for i in range(1, 11)
            ]
        )

        _display_test_results(result)
        captured = capsys.readouterr()

        assert 'ALL TESTS PASSED' in captured.out
        assert '10/10' in captured.out

    def test_display_some_failed(self, capsys):
        """Test displaying when some tests fail."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=10,
            passed_count=7,
            failed_count=3,
            error_count=0,
            case_results=[
                TestCaseResult(1, False, "nums = [1, 2]", "[0, 1]", "[1, 0]"),
                TestCaseResult(2, True, "nums = [3, 3]", "[0, 1]", "[0, 1]"),
                TestCaseResult(3, False, "nums = [5, 5]", "[0, 1]", "[1, 0]"),
            ]
        )

        _display_test_results(result)
        captured = capsys.readouterr()

        assert 'Passed:' in captured.out
        assert 'Failed:' in captured.out
        assert 'Case #1' in captured.out
        assert 'Case #3' in captured.out

    def test_display_compile_error(self, capsys):
        """Test displaying compile error."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=10,
            passed_count=0,
            failed_count=0,
            error_count=10,
            compile_error="SyntaxError: invalid syntax"
        )

        _display_test_results(result)
        captured = capsys.readouterr()

        assert 'COMPILE ERROR' in captured.out
        assert 'SyntaxError' in captured.out

    def test_display_runtime_error(self, capsys):
        """Test displaying runtime error."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=10,
            passed_count=0,
            failed_count=0,
            error_count=10,
            runtime_error="No test cases found"
        )

        _display_test_results(result)
        captured = capsys.readouterr()

        assert 'ERROR' in captured.out
        assert 'No test cases found' in captured.out


class TestTruncate:
    """Test the _truncate function."""

    def test_truncate_short_string(self):
        """Test that short strings are not truncated."""
        assert _truncate("hello", 10) == "hello"

    def test_truncate_exact_length(self):
        """Test string at exact max length."""
        assert _truncate("hello", 5) == "hello"

    def test_truncate_long_string(self):
        """Test that long strings are truncated."""
        result = _truncate("hello world", 8)
        assert len(result) == 8
        assert result.endswith("...")


class TestTestCommand:
    """Test the test CLI command."""

    def test_test_requires_init(self, tmp_path):
        """Test that test requires initialized repository."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['test', '1'])

            assert result.exit_code != 0
            assert 'not initialized' in result.output.lower() or 'init' in result.output.lower()

    def test_test_requires_identifier_or_flag(self, tmp_path):
        """Test that test requires an identifier or flag."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            result = runner.invoke(dojo, ['test'])

            assert result.exit_code != 0
            assert 'specify a problem' in result.output.lower() or 'specify' in result.output.lower()

    @patch('bytedojo.commands.subcommands.test.find_problems')
    @patch('bytedojo.commands.subcommands.test.get_default_language')
    @patch('bytedojo.commands.subcommands.test.DatabaseManager')
    @patch('bytedojo.commands.subcommands.test.get_initialized_repo')
    def test_test_problem_not_found(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find
    ):
        """Test when problem is not found."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'
        mock_find.return_value = []

        result = runner.invoke(test, ['999'])

        assert result.exit_code != 0
        assert 'No' in result.output and 'found' in result.output

    def test_test_java_not_supported(self, tmp_path):
        """Test that Java shows coming soon message."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            result = runner.invoke(dojo, ['test', '1', '--java'])

            # Java is not fully implemented yet
            assert 'coming soon' in result.output.lower() or result.exit_code != 0


class TestTestRunResult:
    """Test the TestRunResult dataclass."""

    def test_all_passed_property_true(self):
        """Test all_passed returns True when all tests pass."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=10,
            passed_count=10,
            failed_count=0,
            error_count=0
        )
        assert result.all_passed is True

    def test_all_passed_property_false(self):
        """Test all_passed returns False when some tests fail."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=10,
            passed_count=7,
            failed_count=3,
            error_count=0
        )
        assert result.all_passed is False

    def test_all_passed_property_no_cases(self):
        """Test all_passed returns False when no test cases."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=0,
            passed_count=0,
            failed_count=0,
            error_count=0
        )
        assert result.all_passed is False

    def test_status_passed(self):
        """Test status returns 'passed' when all tests pass."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=10,
            passed_count=10,
            failed_count=0,
            error_count=0
        )
        assert result.status == 'passed'

    def test_status_failed(self):
        """Test status returns 'failed' when some tests fail."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=10,
            passed_count=7,
            failed_count=3,
            error_count=0
        )
        assert result.status == 'failed'

    def test_status_error(self):
        """Test status returns 'error' when compile error."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=10,
            passed_count=0,
            failed_count=0,
            error_count=10,
            compile_error="SyntaxError"
        )
        assert result.status == 'error'

    def test_status_untested(self):
        """Test status returns 'untested' when no results."""
        result = TestRunResult(
            problem_id=1,
            language='python3',
            total_cases=0,
            passed_count=0,
            failed_count=0,
            error_count=0
        )
        assert result.status == 'untested'
