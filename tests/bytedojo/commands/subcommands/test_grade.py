"""
Tests for the grade command.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from click.testing import CliRunner

from bytedojo.commands.bytedojo import dojo
from bytedojo.commands.subcommands.grade import (
    _display_problem_header,
    _prompt_for_grade,
    _apply_grade,
    _display_grade_result,
    _grade_single_problem,
    _display_ungraded_page,
    _batch_grading_loop,
    grade,
)
from bytedojo.core.grading import GradeResult


class TestDisplayProblemHeader:
    """Test the _display_problem_header function."""

    def test_display_problem_header_basic(self, capsys):
        """Test display with basic problem data."""
        problem = {
            'problem_id': '1',
            'source': 'leetcode',
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'language': 'python',
            'file_path': '/path/to/file.py',
            'test_status': 'ungraded',
        }

        _display_problem_header(problem)
        captured = capsys.readouterr()

        assert 'GRADE PROBLEM' in captured.out
        assert '1' in captured.out
        assert 'Two Sum' in captured.out
        assert 'Leetcode' in captured.out
        assert 'PYTHON' in captured.out
        assert 'Easy' in captured.out
        assert 'ungraded' in captured.out
        assert '/path/to/file.py' in captured.out

    def test_display_problem_header_without_file_path(self, capsys):
        """Test display when file_path is empty."""
        problem = {
            'problem_id': '42',
            'source': 'leetcode',
            'title': 'Test Problem',
            'difficulty': 'Medium',
            'language': 'java',
            'file_path': '',
            'test_status': 'passed',
        }

        _display_problem_header(problem)
        captured = capsys.readouterr()

        assert 'Test Problem' in captured.out
        assert 'Medium' in captured.out
        # Should not show File: line when file_path is empty
        assert 'File:' not in captured.out

    def test_display_problem_header_unknown_difficulty(self, capsys):
        """Test display when difficulty is None."""
        problem = {
            'problem_id': '5',
            'source': 'leetcode',
            'title': 'Unknown Difficulty Problem',
            'difficulty': None,
            'language': 'cpp',
            'test_status': 'failed',
        }

        _display_problem_header(problem)
        captured = capsys.readouterr()

        assert 'Unknown' in captured.out


class TestPromptForGrade:
    """Test the _prompt_for_grade function."""

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_pass(self, mock_prompt):
        """Test selecting pass option."""
        mock_prompt.side_effect = ['p', '']

        status, notes = _prompt_for_grade()

        assert status == 'passed'
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_pass_full_word(self, mock_prompt):
        """Test selecting pass with full word."""
        mock_prompt.side_effect = ['pass', '']

        status, notes = _prompt_for_grade()

        assert status == 'passed'

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_fail(self, mock_prompt):
        """Test selecting fail option."""
        mock_prompt.side_effect = ['f', 'Time limit exceeded']

        status, notes = _prompt_for_grade()

        assert status == 'failed'
        assert notes == 'Time limit exceeded'

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_fail_full_word(self, mock_prompt):
        """Test selecting fail with full word."""
        mock_prompt.side_effect = ['fail', '']

        status, notes = _prompt_for_grade()

        assert status == 'failed'
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_skip(self, mock_prompt):
        """Test selecting skip option."""
        mock_prompt.side_effect = ['s', 'Will review later']

        status, notes = _prompt_for_grade()

        assert status == 'skipped'
        assert notes == 'Will review later'

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_skip_full_word(self, mock_prompt):
        """Test selecting skip with full word."""
        mock_prompt.side_effect = ['skip', '']

        status, notes = _prompt_for_grade()

        assert status == 'skipped'

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_quit(self, mock_prompt):
        """Test selecting quit option."""
        mock_prompt.return_value = 'q'

        status, notes = _prompt_for_grade()

        assert status is None
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_quit_full_word(self, mock_prompt):
        """Test selecting quit with full word."""
        mock_prompt.return_value = 'quit'

        status, notes = _prompt_for_grade()

        assert status is None
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_empty_input_quits(self, mock_prompt):
        """Test that empty input quits."""
        mock_prompt.return_value = ''

        status, notes = _prompt_for_grade()

        assert status is None
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_grade_invalid_then_valid(self, mock_prompt, capsys):
        """Test invalid input followed by valid input."""
        mock_prompt.side_effect = ['x', 'invalid', 'p', '']

        status, notes = _prompt_for_grade()

        assert status == 'passed'
        captured = capsys.readouterr()
        assert 'Invalid choice' in captured.out


class TestApplyGrade:
    """Test the _apply_grade function."""

    @patch('bytedojo.commands.subcommands.grade._display_grade_result')
    @patch('bytedojo.commands.subcommands.grade.GradingService')
    def test_apply_grade_passed(self, mock_service_class, mock_display):
        """Test applying a passing grade."""
        mock_db = MagicMock()
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_result = GradeResult(
            success=True,
            status='passed',
            notes=None,
            scheduled_review=True,
            review_frequency_days=7
        )
        mock_service.grade_problem.return_value = mock_result

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}

        _apply_grade(mock_db, problem, 'passed')

        mock_service.grade_problem.assert_called_once_with(1, 'passed', None)
        mock_display.assert_called_once_with(mock_result)

    @patch('bytedojo.commands.subcommands.grade._display_grade_result')
    @patch('bytedojo.commands.subcommands.grade.GradingService')
    def test_apply_grade_failed_with_notes(self, mock_service_class, mock_display):
        """Test applying a failing grade with notes."""
        mock_db = MagicMock()
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_result = GradeResult(
            success=True,
            status='failed',
            notes='TLE on test case 5',
            scheduled_review=False,
            review_frequency_days=7
        )
        mock_service.grade_problem.return_value = mock_result

        problem = {'id': 2, 'problem_id': '2', 'title': 'Add Two Numbers'}

        _apply_grade(mock_db, problem, 'failed', 'TLE on test case 5')

        mock_service.grade_problem.assert_called_once_with(2, 'failed', 'TLE on test case 5')

    @patch('bytedojo.commands.subcommands.grade._display_grade_result')
    @patch('bytedojo.commands.subcommands.grade.GradingService')
    def test_apply_grade_skipped(self, mock_service_class, mock_display):
        """Test applying a skipped grade."""
        mock_db = MagicMock()
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_result = GradeResult(
            success=True,
            status='skipped',
            notes='Too hard for now',
            scheduled_review=False,
            review_frequency_days=7
        )
        mock_service.grade_problem.return_value = mock_result

        problem = {'id': 3, 'problem_id': '3', 'title': 'Hard Problem'}

        _apply_grade(mock_db, problem, 'skipped', 'Too hard for now')

        mock_service.grade_problem.assert_called_once_with(3, 'skipped', 'Too hard for now')


class TestDisplayGradeResult:
    """Test the _display_grade_result function."""

    def test_display_passed_with_review(self, capsys):
        """Test displaying passed result with scheduled review."""
        result = GradeResult(
            success=True,
            status='passed',
            notes=None,
            scheduled_review=True,
            review_frequency_days=7
        )

        _display_grade_result(result)
        captured = capsys.readouterr()

        assert 'PASSED' in captured.out
        assert '7 days' in captured.out

    def test_display_passed_custom_review_frequency(self, capsys):
        """Test displaying passed result with custom review frequency."""
        result = GradeResult(
            success=True,
            status='passed',
            notes=None,
            scheduled_review=True,
            review_frequency_days=14
        )

        _display_grade_result(result)
        captured = capsys.readouterr()

        assert 'PASSED' in captured.out
        assert '14 days' in captured.out

    def test_display_failed_with_notes(self, capsys):
        """Test displaying failed result with notes."""
        result = GradeResult(
            success=True,
            status='failed',
            notes='Wrong approach, try dynamic programming',
            scheduled_review=False,
            review_frequency_days=7
        )

        _display_grade_result(result)
        captured = capsys.readouterr()

        assert 'FAILED' in captured.out
        assert 'Wrong approach' in captured.out

    def test_display_failed_without_notes(self, capsys):
        """Test displaying failed result without notes."""
        result = GradeResult(
            success=True,
            status='failed',
            notes=None,
            scheduled_review=False,
            review_frequency_days=7
        )

        _display_grade_result(result)
        captured = capsys.readouterr()

        assert 'FAILED' in captured.out
        assert 'Notes:' not in captured.out

    def test_display_skipped_with_notes(self, capsys):
        """Test displaying skipped result with notes."""
        result = GradeResult(
            success=True,
            status='skipped',
            notes='Will revisit after learning graphs',
            scheduled_review=False,
            review_frequency_days=7
        )

        _display_grade_result(result)
        captured = capsys.readouterr()

        assert 'SKIPPED' in captured.out
        assert 'revisit after learning' in captured.out

    def test_display_skipped_without_notes(self, capsys):
        """Test displaying skipped result without notes."""
        result = GradeResult(
            success=True,
            status='skipped',
            notes=None,
            scheduled_review=False,
            review_frequency_days=7
        )

        _display_grade_result(result)
        captured = capsys.readouterr()

        assert 'SKIPPED' in captured.out
        assert 'Notes:' not in captured.out


class TestGradeSingleProblem:
    """Test the _grade_single_problem function."""

    @patch('bytedojo.commands.subcommands.grade._apply_grade')
    @patch('bytedojo.commands.subcommands.grade._display_problem_header')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_single_problem_with_status(
        self, mock_get_repo, mock_db_class, mock_display, mock_apply
    ):
        """Test grading a problem with provided status."""
        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}

        result = _grade_single_problem(problem, status='passed', notes='Easy!')

        assert result is True
        mock_display.assert_called_once_with(problem)
        mock_apply.assert_called_once_with(mock_db, problem, 'passed', 'Easy!')

    @patch('bytedojo.commands.subcommands.grade._prompt_for_grade')
    @patch('bytedojo.commands.subcommands.grade._apply_grade')
    @patch('bytedojo.commands.subcommands.grade._display_problem_header')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_single_problem_interactive(
        self, mock_get_repo, mock_db_class, mock_display, mock_apply, mock_prompt
    ):
        """Test grading a problem interactively (no status provided)."""
        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_prompt.return_value = ('failed', 'Need more practice')

        problem = {'id': 2, 'problem_id': '2', 'title': 'Add Two Numbers'}

        result = _grade_single_problem(problem)

        assert result is True
        mock_prompt.assert_called_once()
        mock_apply.assert_called_once_with(mock_db, problem, 'failed', 'Need more practice')

    @patch('bytedojo.commands.subcommands.grade._prompt_for_grade')
    @patch('bytedojo.commands.subcommands.grade._apply_grade')
    @patch('bytedojo.commands.subcommands.grade._display_problem_header')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_single_problem_cancelled(
        self, mock_get_repo, mock_db_class, mock_display, mock_apply, mock_prompt, capsys
    ):
        """Test cancelling grading interactively."""
        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_prompt.return_value = (None, None)

        problem = {'id': 3, 'problem_id': '3', 'title': 'Test Problem'}

        result = _grade_single_problem(problem)

        assert result is False
        mock_apply.assert_not_called()
        captured = capsys.readouterr()
        assert 'Cancelled' in captured.out


class TestDisplayUngradedPage:
    """Test the _display_ungraded_page function."""

    def test_display_first_page(self, capsys):
        """Test displaying first page of ungraded problems."""
        problems = [
            {'problem_id': '1', 'title': 'Two Sum', 'language': 'python', 'difficulty': 'Easy'},
            {'problem_id': '2', 'title': 'Add Two Numbers', 'language': 'python', 'difficulty': 'Medium'},
            {'problem_id': '3', 'title': 'Longest Substring', 'language': 'python', 'difficulty': 'Medium'},
        ]

        page, total_pages, page_problems = _display_ungraded_page(problems, 1, 10)

        assert page == 1
        assert total_pages == 1
        assert len(page_problems) == 3

        captured = capsys.readouterr()
        assert 'UNGRADED PROBLEMS' in captured.out
        assert 'Two Sum' in captured.out
        assert 'Add Two Numbers' in captured.out
        assert 'Longest Substring' in captured.out
        assert 'Page 1/1' in captured.out

    def test_display_pagination(self, capsys):
        """Test pagination with multiple pages."""
        problems = [
            {'problem_id': str(i), 'title': f'Problem {i}', 'language': 'python', 'difficulty': 'Easy'}
            for i in range(1, 26)  # 25 problems
        ]

        page, total_pages, page_problems = _display_ungraded_page(problems, 2, 10)

        assert page == 2
        assert total_pages == 3
        assert len(page_problems) == 10

        captured = capsys.readouterr()
        assert 'Page 2/3' in captured.out
        assert 'Showing 11-20 of 25' in captured.out

    def test_display_last_page(self, capsys):
        """Test displaying last page with partial results."""
        problems = [
            {'problem_id': str(i), 'title': f'Problem {i}', 'language': 'java', 'difficulty': 'Hard'}
            for i in range(1, 16)  # 15 problems
        ]

        page, total_pages, page_problems = _display_ungraded_page(problems, 2, 10)

        assert page == 2
        assert total_pages == 2
        assert len(page_problems) == 5

        captured = capsys.readouterr()
        assert 'Showing 11-15 of 15' in captured.out

    def test_display_page_clamping(self, capsys):
        """Test that page numbers are clamped to valid range."""
        problems = [
            {'problem_id': '1', 'title': 'Only Problem', 'language': 'cpp', 'difficulty': 'Medium'}
        ]

        # Request page 100 of a 1-page list
        page, total_pages, page_problems = _display_ungraded_page(problems, 100, 10)

        assert page == 1  # Clamped to max
        assert total_pages == 1

    def test_display_truncates_long_titles(self, capsys):
        """Test that long titles are truncated."""
        problems = [
            {
                'problem_id': '1',
                'title': 'This Is A Very Long Problem Title That Should Be Truncated',
                'language': 'python',
                'difficulty': 'Easy'
            }
        ]

        _display_ungraded_page(problems, 1, 10)
        captured = capsys.readouterr()

        # Title should be truncated to 30 chars + '...'
        assert 'This Is A Very Long Problem Ti...' in captured.out


class TestBatchGradingLoop:
    """Test the _batch_grading_loop function."""

    def test_batch_grading_no_problems(self, capsys):
        """Test batch grading with no ungraded problems."""
        _batch_grading_loop([])

        captured = capsys.readouterr()
        assert 'No ungraded problems found' in captured.out
        assert 'All your problems have been graded' in captured.out

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    @patch('bytedojo.commands.subcommands.grade.GradingService')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_batch_grading_quit_immediately(
        self, mock_get_repo, mock_db_class, mock_service_class, mock_prompt
    ):
        """Test quitting batch grading immediately."""
        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_ungraded_problems.return_value = [
            {'problem_id': '1', 'title': 'Test', 'language': 'python', 'difficulty': 'Easy'}
        ]

        mock_prompt.return_value = 'q'

        problems = [
            {'problem_id': '1', 'title': 'Test', 'language': 'python', 'difficulty': 'Easy'}
        ]

        _batch_grading_loop(problems)

        # Should have displayed page and quit
        mock_prompt.assert_called()

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    @patch('bytedojo.commands.subcommands.grade.GradingService')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_batch_grading_all_problems_graded(
        self, mock_get_repo, mock_db_class, mock_service_class, mock_prompt, capsys
    ):
        """Test batch grading when all problems become graded."""
        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        # Return empty list to simulate all problems graded
        mock_service.get_ungraded_problems.return_value = []

        problems = [
            {'problem_id': '1', 'title': 'Test', 'language': 'python', 'difficulty': 'Easy'}
        ]

        _batch_grading_loop(problems)

        captured = capsys.readouterr()
        assert 'All problems graded' in captured.out


class TestGradeCommand:
    """Test the grade CLI command."""

    def test_grade_requires_init(self, tmp_path):
        """Test that grade requires initialized repository."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['grade'])

            assert result.exit_code != 0
            assert 'not initialized' in result.output.lower() or 'init' in result.output.lower()

    def test_grade_multiple_status_flags_error(self, tmp_path):
        """Test that multiple status flags raise an error."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize first
            runner.invoke(dojo, ['init'])

            result = runner.invoke(dojo, ['grade', '1', '--pass', '--fail'])

            assert result.exit_code != 0
            assert 'Cannot specify multiple status flags' in result.output

    def test_grade_pass_and_skip_error(self, tmp_path):
        """Test that --pass and --skip together raise an error."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])

            result = runner.invoke(dojo, ['grade', '1', '--pass', '--skip'])

            assert result.exit_code != 0
            assert 'Cannot specify multiple status flags' in result.output

    def test_grade_fail_and_skip_error(self, tmp_path):
        """Test that --fail and --skip together raise an error."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])

            result = runner.invoke(dojo, ['grade', '1', '--fail', '--skip'])

            assert result.exit_code != 0
            assert 'Cannot specify multiple status flags' in result.output

    @patch('bytedojo.commands.subcommands.grade._batch_grading_loop')
    @patch('bytedojo.commands.subcommands.grade.GradingService')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_batch_mode(
        self, mock_get_repo, mock_db_class, mock_service_class, mock_batch_loop
    ):
        """Test grade command enters batch mode when no identifier provided."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_ungraded_problems.return_value = []

        result = runner.invoke(grade, [])

        mock_batch_loop.assert_called_once()

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_by_identifier(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test grading a problem by identifier."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1'])

        mock_find.assert_called_once()
        mock_grade_single.assert_called_once_with(problem, None, None)

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_with_pass_flag(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test grading a problem with --pass flag."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '--pass'])

        mock_grade_single.assert_called_once_with(problem, 'passed', None)

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_with_fail_and_notes(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test grading a problem with --fail and --notes flags."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '--fail', '--notes', 'TLE'])

        mock_grade_single.assert_called_once_with(problem, 'failed', 'TLE')

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_with_skip_flag(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test grading a problem with --skip flag."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '--skip'])

        mock_grade_single.assert_called_once_with(problem, 'skipped', None)

    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_problem_not_found(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find
    ):
        """Test grading when problem is not found."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'
        mock_find.return_value = []

        result = runner.invoke(grade, ['999'])

        assert result.exit_code != 0
        assert 'No' in result.output and 'found' in result.output

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_last_problem(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_grade_single
    ):
        """Test grading the last fetched problem with --last flag."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'id': 1, 'problem_id': '1', 'title': 'Old Problem', 'fetched_at': '2024-01-01'},
            {'id': 2, 'problem_id': '2', 'title': 'Recent Problem', 'fetched_at': '2024-12-31'},
        ]
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        result = runner.invoke(grade, ['--last'])

        # Should select the most recent problem
        mock_grade_single.assert_called_once()
        called_problem = mock_grade_single.call_args[0][0]
        assert called_problem['title'] == 'Recent Problem'

    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_last_no_problems(
        self, mock_get_repo, mock_db_class, mock_get_lang
    ):
        """Test --last flag when no problems exist."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db.list_problems.return_value = []
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        result = runner.invoke(grade, ['--last'])

        assert result.exit_code != 0
        assert 'No' in result.output and 'found' in result.output

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_by_name_search(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test grading a problem by name search."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['--name', 'Two Sum'])

        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['name'] == 'Two Sum'

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_by_description_search(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test grading a problem by description search."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['--desc', 'array'])

        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['desc'] == 'array'

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_with_language_flag_java(
        self, mock_get_repo, mock_db_class, mock_find, mock_select, mock_grade_single
    ):
        """Test grading with --java language flag."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum', 'language': 'java'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '--java'])

        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['language'] == 'java'

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_with_language_flag_cpp(
        self, mock_get_repo, mock_db_class, mock_find, mock_select, mock_grade_single
    ):
        """Test grading with --cpp language flag."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum', 'language': 'cpp'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '--cpp'])

        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['language'] == 'cpp'

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_with_language_flag_python(
        self, mock_get_repo, mock_db_class, mock_find, mock_select, mock_grade_single
    ):
        """Test grading with --python language flag."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum', 'language': 'python'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '--python'])

        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['language'] == 'python'

    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_selection_cancelled(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find, mock_select
    ):
        """Test when user cancels problem selection."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'
        mock_find.return_value = [
            {'id': 1, 'problem_id': '1', 'title': 'Problem 1'},
            {'id': 2, 'problem_id': '2', 'title': 'Problem 2'},
        ]
        mock_select.return_value = None  # User cancelled

        result = runner.invoke(grade, ['--name', 'Problem'])

        # Should abort
        assert result.exit_code != 0

    @patch('bytedojo.commands.subcommands.grade._batch_grading_loop')
    @patch('bytedojo.commands.subcommands.grade.GradingService')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_batch_mode_custom_per_page(
        self, mock_get_repo, mock_db_class, mock_service_class, mock_batch_loop
    ):
        """Test batch grading with custom per-page setting."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_ungraded_problems.return_value = []

        result = runner.invoke(grade, ['--per-page', '20'])

        mock_batch_loop.assert_called_once()
        # Check that per_page was passed correctly
        call_args = mock_batch_loop.call_args
        assert call_args[0][1] == 20 or call_args[1].get('per_page') == 20


class TestGradeCommandShortOptions:
    """Test short option aliases for grade command."""

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_short_pass_flag(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test -p shorthand for --pass."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '-p'])

        mock_grade_single.assert_called_once_with(problem, 'passed', None)

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_short_fail_flag(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test -f shorthand for --fail."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '-f'])

        mock_grade_single.assert_called_once_with(problem, 'failed', None)

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_short_skip_flag(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test -s shorthand for --skip."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '-s'])

        mock_grade_single.assert_called_once_with(problem, 'skipped', None)

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_short_name_option(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test -n shorthand for --name."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['-n', 'Two Sum'])

        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['name'] == 'Two Sum'

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_short_desc_option(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_grade_single
    ):
        """Test -d shorthand for --desc."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_lang.return_value = 'python3'

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['-d', 'array'])

        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['desc'] == 'array'

    @patch('bytedojo.commands.subcommands.grade._grade_single_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_short_python_flag(
        self, mock_get_repo, mock_db_class, mock_find, mock_select, mock_grade_single
    ):
        """Test -py shorthand for --python."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        problem = {'id': 1, 'problem_id': '1', 'title': 'Two Sum', 'language': 'python'}
        mock_find.return_value = [problem]
        mock_select.return_value = problem

        result = runner.invoke(grade, ['1', '-py'])

        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['language'] == 'python'


class TestGradeResultDataclass:
    """Test the GradeResult dataclass."""

    def test_grade_result_passed_with_review(self):
        """Test GradeResult for a passed problem with review scheduled."""
        result = GradeResult(
            success=True,
            status='passed',
            notes=None,
            scheduled_review=True,
            review_frequency_days=7
        )

        assert result.success is True
        assert result.status == 'passed'
        assert result.notes is None
        assert result.scheduled_review is True
        assert result.review_frequency_days == 7

    def test_grade_result_failed_with_notes(self):
        """Test GradeResult for a failed problem with notes."""
        result = GradeResult(
            success=True,
            status='failed',
            notes='Time limit exceeded',
            scheduled_review=False,
            review_frequency_days=7
        )

        assert result.success is True
        assert result.status == 'failed'
        assert result.notes == 'Time limit exceeded'
        assert result.scheduled_review is False

    def test_grade_result_skipped(self):
        """Test GradeResult for a skipped problem."""
        result = GradeResult(
            success=True,
            status='skipped',
            notes='Will try later',
            scheduled_review=False,
            review_frequency_days=7
        )

        assert result.status == 'skipped'
        assert result.notes == 'Will try later'


class TestGradingService:
    """Test the GradingService class."""

    def test_grading_service_grade_passed(self):
        """Test grading a problem as passed."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'

        from bytedojo.core.grading import GradingService
        service = GradingService(mock_db)

        result = service.grade_problem(1, 'passed', None)

        mock_db.update_test_status.assert_called_once_with(1, 'passed', None)
        mock_db.schedule_review.assert_called_once_with(1)
        assert result.success is True
        assert result.status == 'passed'
        assert result.scheduled_review is True

    def test_grading_service_grade_failed(self):
        """Test grading a problem as failed."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'

        from bytedojo.core.grading import GradingService
        service = GradingService(mock_db)

        result = service.grade_problem(2, 'failed', 'TLE')

        mock_db.update_test_status.assert_called_once_with(2, 'failed', 'TLE')
        mock_db.schedule_review.assert_not_called()
        assert result.success is True
        assert result.status == 'failed'
        assert result.notes == 'TLE'
        assert result.scheduled_review is False

    def test_grading_service_grade_skipped(self):
        """Test grading a problem as skipped."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'

        from bytedojo.core.grading import GradingService
        service = GradingService(mock_db)

        result = service.grade_problem(3, 'skipped', 'Hard')

        mock_db.update_test_status.assert_called_once_with(3, 'skipped', 'Hard')
        mock_db.schedule_review.assert_not_called()
        assert result.status == 'skipped'
        assert result.scheduled_review is False

    def test_grading_service_invalid_status(self):
        """Test that invalid status raises ValueError."""
        mock_db = MagicMock()

        from bytedojo.core.grading import GradingService
        service = GradingService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service.grade_problem(1, 'invalid_status')

        assert 'Invalid status' in str(exc_info.value)

    def test_grading_service_get_ungraded_problems(self):
        """Test getting ungraded problems."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = [
            {'id': 1, 'title': 'Problem 1'},
            {'id': 2, 'title': 'Problem 2'},
        ]

        from bytedojo.core.grading import GradingService
        service = GradingService(mock_db)

        result = service.get_ungraded_problems()

        mock_db.get_problems_by_status.assert_called_once_with('ungraded')
        assert len(result) == 2

    def test_grading_service_get_problems_by_status(self):
        """Test getting problems by specific status."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = [
            {'id': 1, 'title': 'Problem 1', 'test_status': 'passed'},
        ]

        from bytedojo.core.grading import GradingService
        service = GradingService(mock_db)

        result = service.get_problems_by_status('passed')

        mock_db.get_problems_by_status.assert_called_once_with('passed')
        assert len(result) == 1

    def test_grading_service_custom_review_frequency(self):
        """Test grading with custom review frequency."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '14'  # Custom 14 days

        from bytedojo.core.grading import GradingService
        service = GradingService(mock_db)

        result = service.grade_problem(1, 'passed')

        assert result.review_frequency_days == 14
