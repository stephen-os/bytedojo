"""
Tests for the grade command.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from click.testing import CliRunner

from bytedojo.commands.bytedojo import dojo
from bytedojo.commands.subcommands.grade import (
    _display_problem_status,
    _prompt_for_manual_grade,
    _apply_grade,
    _display_grade_result,
    _view_and_grade_problem,
    _display_problems_page,
    _batch_view_loop,
    grade,
)
from bytedojo.core.grading import GradeResult


class TestDisplayProblemStatus:
    """Test the _display_problem_status function."""

    def test_display_problem_status_basic(self, capsys):
        """Test display with basic problem data."""
        problem = {
            'problem_id': '1',
            'source': 'leetcode',
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'language': 'python',
            'file_path': '/path/to/file.py',
            'test_status': 'passed',
            'last_test_run': '2024-01-01T12:00:00',
            'test_output': 'Passed: 10/10',
        }

        _display_problem_status(problem)
        captured = capsys.readouterr()

        assert 'PROBLEM STATUS' in captured.out
        assert '1' in captured.out
        assert 'Two Sum' in captured.out
        assert 'Leetcode' in captured.out
        assert 'PYTHON' in captured.out
        assert 'Easy' in captured.out
        assert 'PASSED' in captured.out
        assert '/path/to/file.py' in captured.out

    def test_display_problem_status_without_file_path(self, capsys):
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

        _display_problem_status(problem)
        captured = capsys.readouterr()

        assert 'Test Problem' in captured.out
        assert 'Medium' in captured.out
        # Should not show File: line when file_path is empty
        assert 'File:' not in captured.out

    def test_display_problem_status_unknown_difficulty(self, capsys):
        """Test display when difficulty is None."""
        problem = {
            'problem_id': '5',
            'source': 'leetcode',
            'title': 'Unknown Difficulty Problem',
            'difficulty': None,
            'language': 'cpp',
            'test_status': 'failed',
        }

        _display_problem_status(problem)
        captured = capsys.readouterr()

        assert 'Unknown' in captured.out

    def test_display_problem_status_untested(self, capsys):
        """Test display when problem is untested."""
        problem = {
            'problem_id': '10',
            'source': 'leetcode',
            'title': 'Untested Problem',
            'difficulty': 'Easy',
            'language': 'python',
            'test_status': 'untested',
        }

        _display_problem_status(problem, show_test_hint=True)
        captured = capsys.readouterr()

        assert 'NOT TESTED' in captured.out
        assert 'dojo test' in captured.out


class TestPromptForManualGrade:
    """Test the _prompt_for_manual_grade function."""

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_pass(self, mock_prompt):
        """Test selecting pass option."""
        mock_prompt.side_effect = ['p', '']

        status, notes = _prompt_for_manual_grade()

        assert status == 'passed'
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_pass_full_word(self, mock_prompt):
        """Test selecting pass with full word."""
        mock_prompt.side_effect = ['pass', '']

        status, notes = _prompt_for_manual_grade()

        assert status == 'passed'

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_fail(self, mock_prompt):
        """Test selecting fail option."""
        mock_prompt.side_effect = ['f', 'Time limit exceeded']

        status, notes = _prompt_for_manual_grade()

        assert status == 'failed'
        assert notes == 'Time limit exceeded'

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_fail_full_word(self, mock_prompt):
        """Test selecting fail with full word."""
        mock_prompt.side_effect = ['fail', '']

        status, notes = _prompt_for_manual_grade()

        assert status == 'failed'
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_skip(self, mock_prompt):
        """Test selecting skip option."""
        mock_prompt.side_effect = ['s', 'Will review later']

        status, notes = _prompt_for_manual_grade()

        assert status == 'skipped'
        assert notes == 'Will review later'

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_skip_full_word(self, mock_prompt):
        """Test selecting skip with full word."""
        mock_prompt.side_effect = ['skip', '']

        status, notes = _prompt_for_manual_grade()

        assert status == 'skipped'

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_quit(self, mock_prompt):
        """Test selecting quit option."""
        mock_prompt.return_value = 'q'

        status, notes = _prompt_for_manual_grade()

        assert status is None
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_quit_full_word(self, mock_prompt):
        """Test selecting quit with full word."""
        mock_prompt.return_value = 'quit'

        status, notes = _prompt_for_manual_grade()

        assert status is None
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_empty_input_quits(self, mock_prompt):
        """Test that empty input quits."""
        mock_prompt.return_value = ''

        status, notes = _prompt_for_manual_grade()

        assert status is None
        assert notes is None

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_prompt_for_manual_grade_invalid_then_valid(self, mock_prompt, capsys):
        """Test invalid input followed by valid input."""
        mock_prompt.side_effect = ['x', 'invalid', 'p', '']

        status, notes = _prompt_for_manual_grade()

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

        assert 'MARKED AS PASSED' in captured.out
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

        assert 'MARKED AS PASSED' in captured.out
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

        assert 'MARKED AS FAILED' in captured.out
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

        assert 'MARKED AS FAILED' in captured.out
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

        assert 'MARKED AS SKIPPED' in captured.out
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

        assert 'MARKED AS SKIPPED' in captured.out
        assert 'Notes:' not in captured.out


class TestDisplayProblemsPage:
    """Test the _display_problems_page function."""

    def test_display_first_page(self, capsys):
        """Test displaying first page of problems."""
        problems = [
            {'problem_id': '1', 'title': 'Two Sum', 'language': 'python', 'difficulty': 'Easy', 'test_status': 'passed'},
            {'problem_id': '2', 'title': 'Add Two Numbers', 'language': 'python', 'difficulty': 'Medium', 'test_status': 'failed'},
            {'problem_id': '3', 'title': 'Longest Substring', 'language': 'python', 'difficulty': 'Medium', 'test_status': 'untested'},
        ]

        page, total_pages, page_problems = _display_problems_page(problems, 1, 10, "PROBLEM STATUS")

        assert page == 1
        assert total_pages == 1
        assert len(page_problems) == 3

        captured = capsys.readouterr()
        assert 'PROBLEM STATUS' in captured.out
        assert 'Two Sum' in captured.out
        assert 'Add Two Numbers' in captured.out
        assert 'Longest Substring' in captured.out
        assert 'Page 1/1' in captured.out

    def test_display_pagination(self, capsys):
        """Test pagination with multiple pages."""
        problems = [
            {'problem_id': str(i), 'title': f'Problem {i}', 'language': 'python', 'difficulty': 'Easy', 'test_status': 'untested'}
            for i in range(1, 26)  # 25 problems
        ]

        page, total_pages, page_problems = _display_problems_page(problems, 2, 10, "PROBLEM STATUS")

        assert page == 2
        assert total_pages == 3
        assert len(page_problems) == 10

        captured = capsys.readouterr()
        assert 'Page 2/3' in captured.out
        assert 'Showing 11-20 of 25' in captured.out

    def test_display_last_page(self, capsys):
        """Test displaying last page with partial results."""
        problems = [
            {'problem_id': str(i), 'title': f'Problem {i}', 'language': 'java', 'difficulty': 'Hard', 'test_status': 'passed'}
            for i in range(1, 16)  # 15 problems
        ]

        page, total_pages, page_problems = _display_problems_page(problems, 2, 10, "PROBLEM STATUS")

        assert page == 2
        assert total_pages == 2
        assert len(page_problems) == 5

        captured = capsys.readouterr()
        assert 'Showing 11-15 of 15' in captured.out

    def test_display_page_clamping(self, capsys):
        """Test that page numbers are clamped to valid range."""
        problems = [
            {'problem_id': '1', 'title': 'Only Problem', 'language': 'cpp', 'difficulty': 'Medium', 'test_status': 'untested'}
        ]

        # Request page 100 of a 1-page list
        page, total_pages, page_problems = _display_problems_page(problems, 100, 10, "PROBLEM STATUS")

        assert page == 1  # Clamped to max
        assert total_pages == 1

    def test_display_truncates_long_titles(self, capsys):
        """Test that long titles are truncated."""
        problems = [
            {
                'problem_id': '1',
                'title': 'This Is A Very Long Problem Title That Should Be Truncated',
                'language': 'python',
                'difficulty': 'Easy',
                'test_status': 'untested'
            }
        ]

        _display_problems_page(problems, 1, 10, "PROBLEM STATUS")
        captured = capsys.readouterr()

        # Title should be truncated to 25 chars + '...'
        assert 'This Is A Very Long Probl...' in captured.out


class TestBatchViewLoop:
    """Test the _batch_view_loop function."""

    def test_batch_view_no_problems(self, capsys):
        """Test batch view with no problems."""
        _batch_view_loop([])

        captured = capsys.readouterr()
        assert 'No problems found' in captured.out

    @patch('bytedojo.commands.subcommands.grade.click.prompt')
    def test_batch_view_quit_immediately(self, mock_prompt, capsys):
        """Test quitting batch view immediately."""
        mock_prompt.return_value = 'q'

        problems = [
            {'problem_id': '1', 'title': 'Test', 'language': 'python', 'difficulty': 'Easy', 'test_status': 'untested'}
        ]

        _batch_view_loop(problems)

        # Should have displayed page and quit
        mock_prompt.assert_called()


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

    @patch('bytedojo.commands.subcommands.grade._batch_view_loop')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_batch_mode(
        self, mock_get_repo, mock_db_class, mock_batch_loop
    ):
        """Test grade command enters batch mode when no identifier provided."""
        runner = CliRunner()

        mock_repo = MagicMock()
        mock_repo.db_path = '/path/to/db.sqlite'
        mock_get_repo.return_value = mock_repo

        mock_db = MagicMock()
        mock_db.list_problems.return_value = []
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        result = runner.invoke(grade, [])

        mock_batch_loop.assert_called_once()

    @patch('bytedojo.commands.subcommands.grade._view_and_grade_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_by_identifier(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_view_grade
    ):
        """Test viewing a problem by identifier."""
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
        mock_view_grade.assert_called_once()

    @patch('bytedojo.commands.subcommands.grade._view_and_grade_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_with_pass_flag(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_view_grade
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

        mock_view_grade.assert_called_once_with(problem, 'passed', None, manual=True)

    @patch('bytedojo.commands.subcommands.grade._view_and_grade_problem')
    @patch('bytedojo.commands.subcommands.grade.select_problem')
    @patch('bytedojo.commands.subcommands.grade.find_problems')
    @patch('bytedojo.commands.subcommands.grade.get_default_language')
    @patch('bytedojo.commands.subcommands.grade.DatabaseManager')
    @patch('bytedojo.commands.subcommands.grade.get_initialized_repo')
    def test_grade_with_fail_and_notes(
        self, mock_get_repo, mock_db_class, mock_get_lang, mock_find,
        mock_select, mock_view_grade
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

        mock_view_grade.assert_called_once_with(problem, 'failed', 'TLE', manual=True)

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
