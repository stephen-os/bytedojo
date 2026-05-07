"""
Tests for the pick command.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from pathlib import Path

from bytedojo.commands.bytedojo import dojo
from bytedojo.core.models import ProblemSummary
from bytedojo.core.picker import PickResult


class TestPickCommand:
    """Test the pick command."""

    def test_pick_help(self):
        """Test that pick --help works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['pick', '--help'])

        assert result.exit_code == 0
        assert 'Pick a random problem' in result.output
        assert '--difficulty' in result.output
        assert '--tag' in result.output

    @patch('bytedojo.commands.subcommands.pick.ProblemPicker')
    def test_pick_selects_random_problem(self, mock_picker_class):
        """Test that pick selects a random unsolved problem."""
        mock_picker = Mock()
        mock_picker_class.return_value = mock_picker

        mock_picker.pick.return_value = PickResult(
            problem=ProblemSummary(id=1, title='Two Sum', title_slug='two-sum',
                                   difficulty='Easy', tags=['Array']),
            unsolved_count=1,
            solved_count=0,
            total_count=1
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['pick'])

        assert result.exit_code == 0
        assert 'PICKED FOR YOU' in result.output
        assert 'Two Sum' in result.output

    @patch('bytedojo.commands.subcommands.pick.ProblemPicker')
    def test_pick_filters_by_difficulty(self, mock_picker_class):
        """Test that pick filters by difficulty."""
        mock_picker = Mock()
        mock_picker_class.return_value = mock_picker
        mock_picker.pick.return_value = PickResult(
            problem=None, unsolved_count=0, solved_count=0, total_count=0
        )

        runner = CliRunner()
        runner.invoke(dojo, ['pick', '-d', 'easy'])

        mock_picker.pick.assert_called_once_with(
            difficulty='easy',
            tags=None
        )

    @patch('bytedojo.commands.subcommands.pick.ProblemPicker')
    def test_pick_filters_by_tag(self, mock_picker_class):
        """Test that pick filters by tag."""
        mock_picker = Mock()
        mock_picker_class.return_value = mock_picker
        mock_picker.pick.return_value = PickResult(
            problem=None, unsolved_count=0, solved_count=0, total_count=0
        )

        runner = CliRunner()
        runner.invoke(dojo, ['pick', '-t', 'array', '-t', 'tree'])

        mock_picker.pick.assert_called_once_with(
            difficulty=None,
            tags=['array', 'tree']
        )

    @patch('bytedojo.commands.subcommands.pick.ProblemPicker')
    def test_pick_no_problems_found(self, mock_picker_class):
        """Test message when no problems match criteria."""
        mock_picker = Mock()
        mock_picker_class.return_value = mock_picker
        mock_picker.pick.return_value = PickResult(
            problem=None, unsolved_count=0, solved_count=0, total_count=0
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['pick'])

        assert result.exit_code == 0
        assert 'No problems found' in result.output

    @patch('bytedojo.commands.subcommands.pick.ProblemPicker')
    def test_pick_all_solved(self, mock_picker_class):
        """Test message when all matching problems are solved."""
        mock_picker = Mock()
        mock_picker_class.return_value = mock_picker
        mock_picker.pick.return_value = PickResult(
            problem=None, unsolved_count=0, solved_count=5, total_count=5
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['pick'])

        assert "You've solved all problems" in result.output

    @patch('bytedojo.commands.subcommands.pick.ProblemPicker')
    def test_pick_shows_url(self, mock_picker_class):
        """Test that pick shows the LeetCode URL."""
        mock_picker = Mock()
        mock_picker_class.return_value = mock_picker
        mock_picker.pick.return_value = PickResult(
            problem=ProblemSummary(id=1, title='Two Sum', title_slug='two-sum',
                                   difficulty='Easy', tags=[]),
            unsolved_count=1, solved_count=0, total_count=1
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['pick'])

        assert 'https://leetcode.com/problems/two-sum/' in result.output

    @patch('bytedojo.commands.subcommands.pick.ProblemPicker')
    def test_pick_shows_fetch_hint(self, mock_picker_class):
        """Test that pick shows how to fetch the problem."""
        mock_picker = Mock()
        mock_picker_class.return_value = mock_picker
        mock_picker.pick.return_value = PickResult(
            problem=ProblemSummary(id=42, title='Test', title_slug='test',
                                   difficulty='Easy', tags=[]),
            unsolved_count=1, solved_count=0, total_count=1
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['pick'])

        assert 'dojo fetch 42' in result.output

    @patch('bytedojo.commands.subcommands.pick.ProblemPicker')
    def test_pick_shows_stats(self, mock_picker_class):
        """Test that pick shows unsolved/solved/total stats."""
        mock_picker = Mock()
        mock_picker_class.return_value = mock_picker
        mock_picker.pick.return_value = PickResult(
            problem=ProblemSummary(id=2, title='Unsolved', title_slug='unsolved',
                                   difficulty='Easy', tags=[]),
            unsolved_count=1, solved_count=1, total_count=2
        )

        runner = CliRunner()
        result = runner.invoke(dojo, ['pick'])

        assert 'Unsolved: 1' in result.output
        assert 'Solved: 1' in result.output
        assert 'Total: 2' in result.output


class TestPickCommandValidation:
    """Test pick command input validation."""

    def test_invalid_difficulty(self):
        """Test that invalid difficulty is rejected."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['pick', '-d', 'invalid'])

        assert result.exit_code != 0


class TestPickCommandIntegration:
    """Integration tests for pick command."""

    def test_pick_command_registered(self):
        """Test that pick command is registered."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--help'])

        assert result.exit_code == 0
        assert 'pick' in result.output

    def test_pick_accessible_via_dojo_pick(self):
        """Test that command is accessible via dojo pick."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['pick', '--help'])

        assert result.exit_code == 0
        assert 'random' in result.output.lower()
