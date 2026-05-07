"""
Tests for commands subcommands utils module.

Tests for shared utilities used across bytedojo command modules.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest

from bytedojo.commands.subcommands.utils import (
    # Constants
    SUPPORTED_LANGUAGES,
    LANGUAGE_TO_INTERNAL,
    DEFAULT_REVIEW_FREQUENCY_DAYS,
    LANGUAGE_COLORS,
    DIFFICULTY_COLORS,
    SOURCE_COLORS,
    STATUS_COLORS,
    # Functions
    get_initialized_repo,
    get_default_language,
    style_language,
    style_difficulty,
    style_status,
    style_source,
)


# ============================================================================
# CONSTANTS TESTS
# ============================================================================


class TestSupportedLanguages:
    """Test SUPPORTED_LANGUAGES constant."""

    def test_supported_languages_is_list(self):
        """Test that SUPPORTED_LANGUAGES is a list."""
        assert isinstance(SUPPORTED_LANGUAGES, list)

    def test_supported_languages_contains_python(self):
        """Test that Python is a supported language."""
        assert 'python' in SUPPORTED_LANGUAGES

    def test_supported_languages_contains_java(self):
        """Test that Java is a supported language."""
        assert 'java' in SUPPORTED_LANGUAGES

    def test_supported_languages_contains_cpp(self):
        """Test that C++ is a supported language."""
        assert 'cpp' in SUPPORTED_LANGUAGES

    def test_supported_languages_count(self):
        """Test expected number of supported languages."""
        assert len(SUPPORTED_LANGUAGES) == 3


class TestLanguageToInternal:
    """Test LANGUAGE_TO_INTERNAL mapping constant."""

    def test_language_to_internal_is_dict(self):
        """Test that LANGUAGE_TO_INTERNAL is a dictionary."""
        assert isinstance(LANGUAGE_TO_INTERNAL, dict)

    def test_python_maps_to_python3(self):
        """Test that python maps to python3 internally."""
        assert LANGUAGE_TO_INTERNAL['python'] == 'python3'

    def test_java_maps_to_java(self):
        """Test that java maps to java internally."""
        assert LANGUAGE_TO_INTERNAL['java'] == 'java'

    def test_cpp_maps_to_cpp(self):
        """Test that cpp maps to cpp internally."""
        assert LANGUAGE_TO_INTERNAL['cpp'] == 'cpp'

    def test_all_supported_languages_have_mappings(self):
        """Test that all supported languages have internal mappings."""
        for lang in SUPPORTED_LANGUAGES:
            assert lang in LANGUAGE_TO_INTERNAL


class TestDefaultReviewFrequencyDays:
    """Test DEFAULT_REVIEW_FREQUENCY_DAYS constant."""

    def test_default_review_frequency_is_int(self):
        """Test that default review frequency is an integer."""
        assert isinstance(DEFAULT_REVIEW_FREQUENCY_DAYS, int)

    def test_default_review_frequency_value(self):
        """Test that default review frequency is 7 days."""
        assert DEFAULT_REVIEW_FREQUENCY_DAYS == 7


class TestLanguageColors:
    """Test LANGUAGE_COLORS constant."""

    def test_language_colors_is_dict(self):
        """Test that LANGUAGE_COLORS is a dictionary."""
        assert isinstance(LANGUAGE_COLORS, dict)

    def test_python_color(self):
        """Test Python language color."""
        assert LANGUAGE_COLORS['python'] == 'blue'

    def test_java_color(self):
        """Test Java language color."""
        assert LANGUAGE_COLORS['java'] == 'red'

    def test_cpp_color(self):
        """Test C++ language color."""
        assert LANGUAGE_COLORS['cpp'] == 'cyan'

    def test_all_supported_languages_have_colors(self):
        """Test that all supported languages have color mappings."""
        for lang in SUPPORTED_LANGUAGES:
            assert lang in LANGUAGE_COLORS


class TestDifficultyColors:
    """Test DIFFICULTY_COLORS constant."""

    def test_difficulty_colors_is_dict(self):
        """Test that DIFFICULTY_COLORS is a dictionary."""
        assert isinstance(DIFFICULTY_COLORS, dict)

    def test_easy_color(self):
        """Test Easy difficulty color."""
        assert DIFFICULTY_COLORS['Easy'] == 'green'

    def test_medium_color(self):
        """Test Medium difficulty color."""
        assert DIFFICULTY_COLORS['Medium'] == 'yellow'

    def test_hard_color(self):
        """Test Hard difficulty color."""
        assert DIFFICULTY_COLORS['Hard'] == 'red'

    def test_difficulty_colors_count(self):
        """Test expected number of difficulty colors."""
        assert len(DIFFICULTY_COLORS) == 3


class TestSourceColors:
    """Test SOURCE_COLORS constant."""

    def test_source_colors_is_dict(self):
        """Test that SOURCE_COLORS is a dictionary."""
        assert isinstance(SOURCE_COLORS, dict)

    def test_leetcode_color(self):
        """Test LeetCode source color."""
        assert SOURCE_COLORS['leetcode'] == 'yellow'


class TestStatusColors:
    """Test STATUS_COLORS constant."""

    def test_status_colors_is_dict(self):
        """Test that STATUS_COLORS is a dictionary."""
        assert isinstance(STATUS_COLORS, dict)

    def test_passed_color(self):
        """Test passed status color."""
        assert STATUS_COLORS['passed'] == 'green'

    def test_failed_color(self):
        """Test failed status color."""
        assert STATUS_COLORS['failed'] == 'red'

    def test_skipped_color(self):
        """Test skipped status color."""
        assert STATUS_COLORS['skipped'] == 'yellow'

    def test_ungraded_color(self):
        """Test ungraded status color."""
        assert STATUS_COLORS['ungraded'] == 'bright_black'

    def test_untested_legacy_color(self):
        """Test untested (legacy) status color."""
        assert STATUS_COLORS['untested'] == 'bright_black'

    def test_status_colors_count(self):
        """Test expected number of status colors."""
        assert len(STATUS_COLORS) == 5


# ============================================================================
# REPOSITORY HELPER TESTS
# ============================================================================


class TestGetInitializedRepo:
    """Test get_initialized_repo function."""

    @patch('bytedojo.commands.subcommands.utils.Repository')
    @patch('bytedojo.commands.subcommands.utils.get_logger')
    @patch('bytedojo.commands.subcommands.utils.Path')
    def test_returns_repo_when_initialized(self, mock_path, mock_get_logger, mock_repo_class):
        """Test that function returns repository when initialized."""
        mock_path.cwd.return_value = Path('/test/path')
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo_class.return_value = mock_repo

        result = get_initialized_repo()

        assert result == mock_repo
        mock_repo_class.assert_called_once_with(Path('/test/path'))

    @patch('bytedojo.commands.subcommands.utils.Repository')
    @patch('bytedojo.commands.subcommands.utils.get_logger')
    @patch('bytedojo.commands.subcommands.utils.Path')
    def test_raises_click_exception_when_not_initialized(
        self, mock_path, mock_get_logger, mock_repo_class
    ):
        """Test that function raises ClickException when repo not initialized."""
        mock_path.cwd.return_value = Path('/test/path')
        mock_repo = MagicMock()
        mock_repo.is_initialized = False
        mock_repo_class.return_value = mock_repo
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with pytest.raises(click.ClickException) as exc_info:
            get_initialized_repo()

        assert "Repository not initialized" in str(exc_info.value)
        mock_logger.error.assert_called_once()

    @patch('bytedojo.commands.subcommands.utils.Repository')
    @patch('bytedojo.commands.subcommands.utils.get_logger')
    @patch('bytedojo.commands.subcommands.utils.Path')
    def test_logs_error_when_not_initialized(self, mock_path, mock_get_logger, mock_repo_class):
        """Test that function logs error message when repo not initialized."""
        mock_path.cwd.return_value = Path('/test/path')
        mock_repo = MagicMock()
        mock_repo.is_initialized = False
        mock_repo_class.return_value = mock_repo
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with pytest.raises(click.ClickException):
            get_initialized_repo()

        mock_logger.error.assert_called_once_with(
            "No .dojo repository found. Run 'dojo init' first."
        )


class TestGetDefaultLanguage:
    """Test get_default_language function."""

    @patch('bytedojo.commands.subcommands.utils.Repository')
    @patch('bytedojo.commands.subcommands.utils.Path')
    def test_returns_python3_when_repo_not_initialized(self, mock_path, mock_repo_class):
        """Test fallback to python3 when repository is not initialized."""
        mock_path.cwd.return_value = Path('/test/path')
        mock_repo = MagicMock()
        mock_repo.is_initialized = False
        mock_repo_class.return_value = mock_repo

        result = get_default_language()

        assert result == 'python3'

    @patch('bytedojo.commands.subcommands.utils.DatabaseManager')
    @patch('bytedojo.commands.subcommands.utils.Repository')
    @patch('bytedojo.commands.subcommands.utils.Path')
    def test_returns_configured_language_python(
        self, mock_path, mock_repo_class, mock_db_manager_class
    ):
        """Test returns python3 when default_language is python."""
        mock_path.cwd.return_value = Path('/test/path')
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path('/test/path/.dojo/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db.get_config.return_value = 'python'
        mock_db_manager_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_manager_class.return_value.__exit__ = MagicMock(return_value=False)

        result = get_default_language()

        assert result == 'python3'
        mock_db.get_config.assert_called_once_with('default_language', 'python')

    @patch('bytedojo.commands.subcommands.utils.DatabaseManager')
    @patch('bytedojo.commands.subcommands.utils.Repository')
    @patch('bytedojo.commands.subcommands.utils.Path')
    def test_returns_configured_language_java(
        self, mock_path, mock_repo_class, mock_db_manager_class
    ):
        """Test returns java when default_language is java."""
        mock_path.cwd.return_value = Path('/test/path')
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path('/test/path/.dojo/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db.get_config.return_value = 'java'
        mock_db_manager_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_manager_class.return_value.__exit__ = MagicMock(return_value=False)

        result = get_default_language()

        assert result == 'java'

    @patch('bytedojo.commands.subcommands.utils.DatabaseManager')
    @patch('bytedojo.commands.subcommands.utils.Repository')
    @patch('bytedojo.commands.subcommands.utils.Path')
    def test_returns_configured_language_cpp(
        self, mock_path, mock_repo_class, mock_db_manager_class
    ):
        """Test returns cpp when default_language is cpp."""
        mock_path.cwd.return_value = Path('/test/path')
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path('/test/path/.dojo/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db.get_config.return_value = 'cpp'
        mock_db_manager_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_manager_class.return_value.__exit__ = MagicMock(return_value=False)

        result = get_default_language()

        assert result == 'cpp'

    @patch('bytedojo.commands.subcommands.utils.DatabaseManager')
    @patch('bytedojo.commands.subcommands.utils.Repository')
    @patch('bytedojo.commands.subcommands.utils.Path')
    def test_returns_python3_for_unknown_language(
        self, mock_path, mock_repo_class, mock_db_manager_class
    ):
        """Test fallback to python3 for unknown language in config."""
        mock_path.cwd.return_value = Path('/test/path')
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path('/test/path/.dojo/db.sqlite')
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db.get_config.return_value = 'unknown_language'
        mock_db_manager_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_manager_class.return_value.__exit__ = MagicMock(return_value=False)

        result = get_default_language()

        assert result == 'python3'


# ============================================================================
# DISPLAY HELPER TESTS
# ============================================================================


class TestStyleLanguage:
    """Test style_language function."""

    def test_style_python(self):
        """Test styling Python language."""
        result = style_language('python')

        # Check that result contains styled content (uppercase)
        assert 'PYTHON' in result

    def test_style_java(self):
        """Test styling Java language."""
        result = style_language('java')

        assert 'JAVA' in result

    def test_style_cpp(self):
        """Test styling C++ language."""
        result = style_language('cpp')

        assert 'CPP' in result

    def test_style_unknown_language(self):
        """Test styling unknown language uses white color."""
        result = style_language('unknown')

        # Should still uppercase and return styled text
        assert 'UNKNOWN' in result

    def test_style_language_returns_string(self):
        """Test that style_language returns a string."""
        result = style_language('python')

        assert isinstance(result, str)

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_language_calls_click_style_with_correct_args(self, mock_style):
        """Test that click.style is called with correct arguments."""
        mock_style.return_value = 'styled'

        style_language('python')

        mock_style.assert_called_once_with('PYTHON', fg='blue')

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_language_uses_white_for_unknown(self, mock_style):
        """Test that unknown language uses white color."""
        mock_style.return_value = 'styled'

        style_language('fortran')

        mock_style.assert_called_once_with('FORTRAN', fg='white')


class TestStyleDifficulty:
    """Test style_difficulty function."""

    def test_style_easy(self):
        """Test styling Easy difficulty."""
        result = style_difficulty('Easy')

        assert 'Easy' in result

    def test_style_medium(self):
        """Test styling Medium difficulty."""
        result = style_difficulty('Medium')

        assert 'Medium' in result

    def test_style_hard(self):
        """Test styling Hard difficulty."""
        result = style_difficulty('Hard')

        assert 'Hard' in result

    def test_style_unknown_difficulty(self):
        """Test styling unknown difficulty uses white color."""
        result = style_difficulty('Unknown')

        assert 'Unknown' in result

    def test_style_difficulty_returns_string(self):
        """Test that style_difficulty returns a string."""
        result = style_difficulty('Easy')

        assert isinstance(result, str)

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_difficulty_calls_click_style_with_correct_args(self, mock_style):
        """Test that click.style is called with correct arguments."""
        mock_style.return_value = 'styled'

        style_difficulty('Easy')

        mock_style.assert_called_once_with('Easy', fg='green')

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_difficulty_uses_white_for_unknown(self, mock_style):
        """Test that unknown difficulty uses white color."""
        mock_style.return_value = 'styled'

        style_difficulty('Impossible')

        mock_style.assert_called_once_with('Impossible', fg='white')


class TestStyleStatus:
    """Test style_status function."""

    def test_style_passed(self):
        """Test styling passed status."""
        result = style_status('passed')

        assert 'passed' in result

    def test_style_failed(self):
        """Test styling failed status."""
        result = style_status('failed')

        assert 'failed' in result

    def test_style_skipped(self):
        """Test styling skipped status."""
        result = style_status('skipped')

        assert 'skipped' in result

    def test_style_ungraded(self):
        """Test styling ungraded status."""
        result = style_status('ungraded')

        assert 'ungraded' in result

    def test_style_untested_legacy(self):
        """Test styling untested (legacy) status."""
        result = style_status('untested')

        assert 'untested' in result

    def test_style_unknown_status(self):
        """Test styling unknown status uses white color."""
        result = style_status('unknown')

        assert 'unknown' in result

    def test_style_status_returns_string(self):
        """Test that style_status returns a string."""
        result = style_status('passed')

        assert isinstance(result, str)

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_status_calls_click_style_with_correct_args_passed(self, mock_style):
        """Test that click.style is called with correct arguments for passed."""
        mock_style.return_value = 'styled'

        style_status('passed')

        mock_style.assert_called_once_with('passed', fg='green')

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_status_calls_click_style_with_correct_args_failed(self, mock_style):
        """Test that click.style is called with correct arguments for failed."""
        mock_style.return_value = 'styled'

        style_status('failed')

        mock_style.assert_called_once_with('failed', fg='red')

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_status_uses_white_for_unknown(self, mock_style):
        """Test that unknown status uses white color."""
        mock_style.return_value = 'styled'

        style_status('unknown_status')

        mock_style.assert_called_once_with('unknown_status', fg='white')


class TestStyleSource:
    """Test style_source function."""

    def test_style_leetcode(self):
        """Test styling LeetCode source."""
        result = style_source('leetcode')

        # Should capitalize the source name
        assert 'Leetcode' in result

    def test_style_unknown_source(self):
        """Test styling unknown source uses white color."""
        result = style_source('hackerrank')

        # Should still capitalize
        assert 'Hackerrank' in result

    def test_style_source_returns_string(self):
        """Test that style_source returns a string."""
        result = style_source('leetcode')

        assert isinstance(result, str)

    def test_style_source_capitalizes(self):
        """Test that source name is capitalized."""
        result = style_source('leetcode')

        assert 'Leetcode' in result
        # 'leetcode' should not appear (should be capitalized)
        # Note: The styled string may contain ANSI codes so we check for capitalized version

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_source_calls_click_style_with_correct_args(self, mock_style):
        """Test that click.style is called with correct arguments."""
        mock_style.return_value = 'styled'

        style_source('leetcode')

        mock_style.assert_called_once_with('Leetcode', fg='yellow')

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_source_uses_white_for_unknown(self, mock_style):
        """Test that unknown source uses white color."""
        mock_style.return_value = 'styled'

        style_source('codewars')

        mock_style.assert_called_once_with('Codewars', fg='white')

    @patch('bytedojo.commands.subcommands.utils.click.style')
    def test_style_source_capitalizes_all_lowercase(self, mock_style):
        """Test that lowercase source names are capitalized."""
        mock_style.return_value = 'styled'

        style_source('github')

        mock_style.assert_called_once_with('Github', fg='white')


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestConstantsConsistency:
    """Test consistency across related constants."""

    def test_all_supported_languages_have_colors(self):
        """Test that every supported language has a color defined."""
        for lang in SUPPORTED_LANGUAGES:
            assert lang in LANGUAGE_COLORS, f"Missing color for language: {lang}"

    def test_all_supported_languages_have_internal_mappings(self):
        """Test that every supported language has an internal mapping."""
        for lang in SUPPORTED_LANGUAGES:
            assert lang in LANGUAGE_TO_INTERNAL, f"Missing internal mapping for: {lang}"

    def test_internal_language_values_are_valid(self):
        """Test that all internal language values are non-empty strings."""
        for user_lang, internal_lang in LANGUAGE_TO_INTERNAL.items():
            assert isinstance(internal_lang, str)
            assert len(internal_lang) > 0

    def test_color_values_are_valid(self):
        """Test that all color values in LANGUAGE_COLORS are valid click colors."""
        valid_colors = {
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
            'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
            'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'
        }
        for lang, color in LANGUAGE_COLORS.items():
            assert color in valid_colors, f"Invalid color '{color}' for language '{lang}'"

    def test_difficulty_color_values_are_valid(self):
        """Test that all color values in DIFFICULTY_COLORS are valid click colors."""
        valid_colors = {
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
            'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
            'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'
        }
        for difficulty, color in DIFFICULTY_COLORS.items():
            assert color in valid_colors, f"Invalid color '{color}' for difficulty '{difficulty}'"

    def test_status_color_values_are_valid(self):
        """Test that all color values in STATUS_COLORS are valid click colors."""
        valid_colors = {
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
            'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
            'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'
        }
        for status, color in STATUS_COLORS.items():
            assert color in valid_colors, f"Invalid color '{color}' for status '{status}'"
