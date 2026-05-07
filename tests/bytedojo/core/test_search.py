"""
Tests for search module (fuzzy matching and problem selection utilities).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch, call

import click
import pytest

from bytedojo.core.search import (
    _normalize,
    _fuzzy_match,
    _score_match,
    find_problems,
    select_problem,
    resolve_problem,
)


class TestNormalize:
    """Test _normalize function."""

    def test_normalize_lowercase(self):
        """Test that normalize converts to lowercase."""
        assert _normalize("HELLO") == "hello"
        assert _normalize("HeLLo WoRLD") == "hello world"

    def test_normalize_strips_whitespace(self):
        """Test that normalize strips leading/trailing whitespace."""
        assert _normalize("  hello  ") == "hello"
        assert _normalize("\thello\n") == "hello"

    def test_normalize_empty_string(self):
        """Test normalize with empty string."""
        assert _normalize("") == ""

    def test_normalize_preserves_internal_spaces(self):
        """Test that internal spaces are preserved."""
        assert _normalize("  hello   world  ") == "hello   world"


class TestFuzzyMatch:
    """Test _fuzzy_match function."""

    def test_fuzzy_match_exact(self):
        """Test exact match returns True."""
        assert _fuzzy_match("Two Sum", "Two Sum") is True

    def test_fuzzy_match_case_insensitive(self):
        """Test case insensitive matching."""
        assert _fuzzy_match("two sum", "Two Sum") is True
        assert _fuzzy_match("TWO SUM", "two sum") is True

    def test_fuzzy_match_substring(self):
        """Test substring matching."""
        assert _fuzzy_match("sum", "Two Sum") is True
        assert _fuzzy_match("Two", "Two Sum") is True

    def test_fuzzy_match_word_by_word(self):
        """Test word-by-word matching where all query words must be present."""
        assert _fuzzy_match("two sum", "Two Sum Problem") is True
        assert _fuzzy_match("sum two", "Two Sum") is True  # Order doesn't matter

    def test_fuzzy_match_partial_words_as_substrings(self):
        """Test that partial words match if they are substrings of full words."""
        # "tw" is substring of "two", "su" is substring of "sum"
        assert _fuzzy_match("tw su", "Two Sum") is True
        # "xyz" is not a substring of any word
        assert _fuzzy_match("xyz abc", "Two Sum") is False

    def test_fuzzy_match_no_match(self):
        """Test no match returns False."""
        assert _fuzzy_match("array", "Two Sum") is False
        assert _fuzzy_match("xyz", "Two Sum") is False

    def test_fuzzy_match_empty_query(self):
        """Test empty query matches anything."""
        assert _fuzzy_match("", "Two Sum") is True

    def test_fuzzy_match_whitespace_handling(self):
        """Test whitespace is handled properly."""
        assert _fuzzy_match("  two  ", "Two Sum") is True
        assert _fuzzy_match("two   sum", "Two Sum") is True


class TestScoreMatch:
    """Test _score_match function."""

    def test_score_exact_match(self):
        """Test exact title match gets highest score."""
        problem = {'title': 'Two Sum'}
        score = _score_match("Two Sum", problem)
        assert score == 100

    def test_score_exact_match_case_insensitive(self):
        """Test exact match is case insensitive."""
        problem = {'title': 'Two Sum'}
        score = _score_match("two sum", problem)
        assert score == 100

    def test_score_starts_with(self):
        """Test title starts with query gets 80."""
        problem = {'title': 'Two Sum II'}
        score = _score_match("Two Sum", problem)
        assert score == 80

    def test_score_substring(self):
        """Test substring match gets 60."""
        problem = {'title': 'Best Two Sum Problem'}
        score = _score_match("Two Sum", problem)
        assert score == 60

    def test_score_all_words_present(self):
        """Test all query words in title gets 40."""
        problem = {'title': 'Sum of Two Numbers'}
        score = _score_match("two sum", problem)
        assert score == 40

    def test_score_partial_word_match(self):
        """Test partial word match gets 20."""
        problem = {'title': 'Array Sum'}
        score = _score_match("sum array", problem)  # Only 'sum' and 'array' match
        assert score == 40  # Actually all words match

    def test_score_single_word_partial(self):
        """Test single word partial match gets 20."""
        problem = {'title': 'Array Sum'}
        score = _score_match("array xyz", problem)  # Only 'array' matches
        assert score == 20

    def test_score_no_match(self):
        """Test no match gets 0."""
        problem = {'title': 'Two Sum'}
        score = _score_match("xyz abc", problem)
        assert score == 0

    def test_score_missing_title(self):
        """Test problem with missing title."""
        problem = {}
        score = _score_match("Two Sum", problem)
        assert score == 0

    def test_score_empty_title(self):
        """Test problem with empty title."""
        problem = {'title': ''}
        score = _score_match("Two Sum", problem)
        assert score == 0


class TestFindProblems:
    """Test find_problems function."""

    def test_find_by_numeric_identifier_exact_match(self):
        """Test finding problem by numeric ID with exact match."""
        mock_db = MagicMock()
        mock_db.get_problem.return_value = {
            'problem_id': '1',
            'title': 'Two Sum',
            'difficulty': 'Easy'
        }

        result = find_problems(mock_db, identifier='1')

        mock_db.get_problem.assert_called_once_with('leetcode', 1, 'python')
        assert len(result) == 1
        assert result[0]['title'] == 'Two Sum'

    def test_find_by_numeric_identifier_with_language(self):
        """Test finding problem by numeric ID with specific language."""
        mock_db = MagicMock()
        mock_db.get_problem.return_value = {
            'problem_id': '1',
            'title': 'Two Sum',
            'language': 'java'
        }

        result = find_problems(mock_db, identifier='1', language='java')

        mock_db.get_problem.assert_called_once_with('leetcode', 1, 'java')
        assert len(result) == 1

    def test_find_by_numeric_identifier_not_found_with_language(self):
        """Test finding problem by ID returns empty when language specified but not found."""
        mock_db = MagicMock()
        mock_db.get_problem.return_value = None

        result = find_problems(mock_db, identifier='999', language='java')

        assert result == []

    def test_find_by_numeric_identifier_not_found_search_all(self):
        """Test finding problem by ID searches all languages when not found."""
        mock_db = MagicMock()
        mock_db.get_problem.return_value = None
        mock_db.list_problems.return_value = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '999', 'title': 'Some Problem'},
        ]

        result = find_problems(mock_db, identifier='999')

        mock_db.list_problems.assert_called_once_with(source='leetcode')
        assert len(result) == 1
        assert result[0]['problem_id'] == '999'

    def test_find_by_name_fuzzy_match(self):
        """Test finding problems by name with fuzzy matching."""
        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '2', 'title': 'Three Sum'},
            {'problem_id': '3', 'title': 'Array Partition'},
        ]

        result = find_problems(mock_db, name='sum')

        assert len(result) == 2
        # Should be sorted by score
        titles = [p['title'] for p in result]
        assert 'Two Sum' in titles
        assert 'Three Sum' in titles

    def test_find_by_name_no_match(self):
        """Test finding problems by name with no matches."""
        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '2', 'title': 'Three Sum'},
        ]

        result = find_problems(mock_db, name='xyz')

        assert result == []

    def test_find_by_description(self):
        """Test finding problems by description keyword."""
        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1', 'title': 'Two Sum', 'description': 'Given an array of integers'},
            {'problem_id': '2', 'title': 'Three Sum', 'description': 'Find triplets in array'},
            {'problem_id': '3', 'title': 'Reverse String', 'description': 'Reverse a string'},
        ]

        result = find_problems(mock_db, desc='array')

        assert len(result) == 2
        problem_ids = [p['problem_id'] for p in result]
        assert '1' in problem_ids
        assert '2' in problem_ids

    def test_find_by_name_and_description(self):
        """Test finding problems by both name and description."""
        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1', 'title': 'Two Sum', 'description': 'Given an array'},
            {'problem_id': '2', 'title': 'Three Sum', 'description': 'Find triplets'},
            {'problem_id': '3', 'title': 'Array Sum', 'description': 'Sum of array'},
        ]

        result = find_problems(mock_db, name='sum', desc='array')

        # Only problems matching both name and description
        assert len(result) == 2
        problem_ids = [p['problem_id'] for p in result]
        assert '1' in problem_ids
        assert '3' in problem_ids

    def test_find_with_language_filter(self):
        """Test finding problems with language filter."""
        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1', 'title': 'Two Sum', 'language': 'python'},
        ]

        find_problems(mock_db, language='python')

        mock_db.list_problems.assert_called_once_with(source='leetcode', language='python')

    def test_find_with_custom_source(self):
        """Test finding problems with custom source."""
        mock_db = MagicMock()
        mock_db.list_problems.return_value = []

        find_problems(mock_db, source='hackerrank')

        mock_db.list_problems.assert_called_once_with(source='hackerrank', language=None)

    def test_find_all_problems_no_criteria(self):
        """Test finding all problems when no criteria specified."""
        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '2', 'title': 'Three Sum'},
        ]

        result = find_problems(mock_db)

        assert len(result) == 2

    def test_find_sorted_by_score_then_id(self):
        """Test that results are sorted by score descending, then by problem_id."""
        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '3', 'title': 'Sum Array'},
            {'problem_id': '1', 'title': 'Two Sum'},  # Exact match
            {'problem_id': '2', 'title': 'Two Sum Extended'},  # Starts with
        ]

        result = find_problems(mock_db, name='Two Sum')

        assert result[0]['problem_id'] == '1'  # Exact match first
        assert result[1]['problem_id'] == '2'  # Starts with second

    def test_find_handles_none_description(self):
        """Test finding problems when description is None."""
        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1', 'title': 'Two Sum', 'description': None},
        ]

        result = find_problems(mock_db, desc='array')

        assert result == []


class TestSelectProblem:
    """Test select_problem function."""

    def test_select_empty_list(self):
        """Test selecting from empty list returns None."""
        result = select_problem([])
        assert result is None

    def test_select_single_problem(self):
        """Test selecting from single problem returns that problem."""
        problems = [{'problem_id': '1', 'title': 'Two Sum'}]
        result = select_problem(problems)
        assert result == problems[0]

    @patch('bytedojo.core.search.click')
    def test_select_multiple_problems_user_selects(self, mock_click):
        """Test interactive selection when user makes a choice."""
        mock_click.prompt.return_value = '2'
        mock_click.echo = MagicMock()
        mock_click.style = MagicMock(side_effect=lambda x, **kwargs: x)
        mock_click.Choice = click.Choice

        problems = [
            {'problem_id': '1', 'title': 'Two Sum', 'difficulty': 'Easy', 'language': 'python'},
            {'problem_id': '2', 'title': 'Three Sum', 'difficulty': 'Medium', 'language': 'python'},
        ]

        result = select_problem(problems)

        assert result == problems[1]
        mock_click.echo.assert_called()

    @patch('bytedojo.core.search.click')
    def test_select_multiple_problems_user_quits(self, mock_click):
        """Test interactive selection when user quits."""
        mock_click.prompt.return_value = 'q'
        mock_click.echo = MagicMock()
        mock_click.style = MagicMock(side_effect=lambda x, **kwargs: x)
        mock_click.Choice = click.Choice

        problems = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '2', 'title': 'Three Sum'},
        ]

        result = select_problem(problems)

        assert result is None

    @patch('bytedojo.core.search.click')
    def test_select_handles_keyboard_interrupt(self, mock_click):
        """Test that KeyboardInterrupt returns None."""
        mock_click.prompt.side_effect = KeyboardInterrupt()
        mock_click.echo = MagicMock()
        mock_click.style = MagicMock(side_effect=lambda x, **kwargs: x)

        problems = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '2', 'title': 'Three Sum'},
        ]

        result = select_problem(problems)

        assert result is None

    @patch('bytedojo.core.search.click')
    def test_select_handles_eof_error(self, mock_click):
        """Test that EOFError returns None."""
        mock_click.prompt.side_effect = EOFError()
        mock_click.echo = MagicMock()
        mock_click.style = MagicMock(side_effect=lambda x, **kwargs: x)

        problems = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '2', 'title': 'Three Sum'},
        ]

        result = select_problem(problems)

        assert result is None

    @patch('bytedojo.core.search.click')
    def test_select_limits_to_10_options(self, mock_click):
        """Test that selection limits display to 10 options."""
        mock_click.prompt.return_value = '1'
        mock_click.echo = MagicMock()
        mock_click.style = MagicMock(side_effect=lambda x, **kwargs: x)
        mock_click.Choice = click.Choice

        problems = [
            {'problem_id': str(i), 'title': f'Problem {i}'}
            for i in range(1, 16)  # 15 problems
        ]

        select_problem(problems)

        # Check that "and X more" message was displayed
        echo_calls = [str(c) for c in mock_click.echo.call_args_list]
        assert any('5 more' in c for c in echo_calls)

    @patch('bytedojo.core.search.click')
    def test_select_displays_difficulty_colors(self, mock_click):
        """Test that difficulty is displayed with colors."""
        mock_click.prompt.return_value = '1'
        mock_click.echo = MagicMock()
        mock_click.style = MagicMock(side_effect=lambda x, **kwargs: x)
        mock_click.Choice = click.Choice

        problems = [
            {'problem_id': '1', 'title': 'Easy Problem', 'difficulty': 'Easy'},
            {'problem_id': '2', 'title': 'Medium Problem', 'difficulty': 'Medium'},
            {'problem_id': '3', 'title': 'Hard Problem', 'difficulty': 'Hard'},
        ]

        select_problem(problems)

        # Verify style was called with difficulty colors
        style_calls = mock_click.style.call_args_list
        colors_used = [c[1].get('fg') for c in style_calls if c[1]]
        assert 'green' in colors_used or 'yellow' in colors_used or 'red' in colors_used

    @patch('bytedojo.core.search.click')
    def test_select_handles_missing_fields(self, mock_click):
        """Test selection handles problems with missing fields."""
        mock_click.prompt.return_value = '1'
        mock_click.echo = MagicMock()
        mock_click.style = MagicMock(side_effect=lambda x, **kwargs: x)
        mock_click.Choice = click.Choice

        problems = [
            {'problem_id': '1'},  # Missing title, difficulty, language
            {'title': 'No ID'},  # Missing problem_id
        ]

        result = select_problem(problems)

        assert result == problems[0]

    @patch('bytedojo.core.search.click')
    def test_select_custom_prompt(self, mock_click):
        """Test selection with custom prompt text."""
        mock_click.prompt.return_value = '1'
        mock_click.echo = MagicMock()
        mock_click.style = MagicMock(side_effect=lambda x, **kwargs: x)
        mock_click.Choice = click.Choice

        problems = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '2', 'title': 'Three Sum'},
        ]

        select_problem(problems, prompt_text="Choose a problem")

        mock_click.prompt.assert_called_once()
        assert mock_click.prompt.call_args[0][0] == "Choose a problem"


class TestResolveProblem:
    """Test resolve_problem function."""

    @patch('bytedojo.core.search.Repository')
    @patch('bytedojo.core.search.DatabaseManager')
    @patch('bytedojo.core.search.find_problems')
    def test_resolve_single_match(self, mock_find, mock_db_class, mock_repo_class):
        """Test resolving when single problem matches."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = '/path/to/db'
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        expected_problem = {'problem_id': '1', 'title': 'Two Sum'}
        mock_find.return_value = [expected_problem]

        result = resolve_problem(identifier='1')

        assert result == expected_problem

    @patch('bytedojo.core.search.Repository')
    def test_resolve_repo_not_initialized(self, mock_repo_class):
        """Test resolve raises exception when repo not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False
        mock_repo_class.return_value = mock_repo

        with pytest.raises(click.ClickException) as exc_info:
            resolve_problem(identifier='1')

        assert "No .dojo repository found" in str(exc_info.value)

    @patch('bytedojo.core.search.Repository')
    @patch('bytedojo.core.search.DatabaseManager')
    @patch('bytedojo.core.search.find_problems')
    def test_resolve_no_matches(self, mock_find, mock_db_class, mock_repo_class):
        """Test resolve raises exception when no matches found."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = '/path/to/db'
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_find.return_value = []

        with pytest.raises(click.ClickException) as exc_info:
            resolve_problem(identifier='999')

        assert "No problems found" in str(exc_info.value)
        assert "ID '999'" in str(exc_info.value)

    @patch('bytedojo.core.search.Repository')
    @patch('bytedojo.core.search.DatabaseManager')
    @patch('bytedojo.core.search.find_problems')
    def test_resolve_no_matches_with_name(self, mock_find, mock_db_class, mock_repo_class):
        """Test resolve error message includes name criteria."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = '/path/to/db'
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_find.return_value = []

        with pytest.raises(click.ClickException) as exc_info:
            resolve_problem(name='xyz')

        assert "name 'xyz'" in str(exc_info.value)

    @patch('bytedojo.core.search.Repository')
    @patch('bytedojo.core.search.DatabaseManager')
    @patch('bytedojo.core.search.find_problems')
    def test_resolve_no_matches_with_multiple_criteria(self, mock_find, mock_db_class, mock_repo_class):
        """Test resolve error message includes all criteria."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = '/path/to/db'
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_find.return_value = []

        with pytest.raises(click.ClickException) as exc_info:
            resolve_problem(name='xyz', desc='abc', language='python')

        error_msg = str(exc_info.value)
        assert "name 'xyz'" in error_msg
        assert "description 'abc'" in error_msg
        assert "language 'python'" in error_msg

    @patch('bytedojo.core.search.Repository')
    @patch('bytedojo.core.search.DatabaseManager')
    @patch('bytedojo.core.search.find_problems')
    def test_resolve_no_matches_no_criteria(self, mock_find, mock_db_class, mock_repo_class):
        """Test resolve error message when no criteria specified."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = '/path/to/db'
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_find.return_value = []

        with pytest.raises(click.ClickException) as exc_info:
            resolve_problem()

        assert "given criteria" in str(exc_info.value)

    @patch('bytedojo.core.search.Repository')
    @patch('bytedojo.core.search.DatabaseManager')
    @patch('bytedojo.core.search.find_problems')
    def test_resolve_auto_select_first(self, mock_find, mock_db_class, mock_repo_class):
        """Test resolve with auto_select returns first match."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = '/path/to/db'
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        problems = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '2', 'title': 'Three Sum'},
        ]
        mock_find.return_value = problems

        result = resolve_problem(name='sum', auto_select=True)

        assert result == problems[0]

    @patch('bytedojo.core.search.Repository')
    @patch('bytedojo.core.search.DatabaseManager')
    @patch('bytedojo.core.search.find_problems')
    @patch('bytedojo.core.search.select_problem')
    def test_resolve_multiple_matches_prompts_selection(
        self, mock_select, mock_find, mock_db_class, mock_repo_class
    ):
        """Test resolve prompts for selection when multiple matches."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = '/path/to/db'
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        problems = [
            {'problem_id': '1', 'title': 'Two Sum'},
            {'problem_id': '2', 'title': 'Three Sum'},
        ]
        mock_find.return_value = problems
        mock_select.return_value = problems[1]

        result = resolve_problem(name='sum')

        mock_select.assert_called_once_with(problems)
        assert result == problems[1]

    @patch('bytedojo.core.search.Repository')
    @patch('bytedojo.core.search.DatabaseManager')
    @patch('bytedojo.core.search.find_problems')
    def test_resolve_passes_all_parameters(self, mock_find, mock_db_class, mock_repo_class):
        """Test resolve passes all parameters to find_problems."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = '/path/to/db'
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_find.return_value = [{'problem_id': '1', 'title': 'Test'}]

        resolve_problem(
            identifier='1',
            name='test',
            desc='description',
            language='python',
            source='hackerrank'
        )

        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['identifier'] == '1'
        assert call_kwargs['name'] == 'test'
        assert call_kwargs['desc'] == 'description'
        assert call_kwargs['language'] == 'python'
        assert call_kwargs['source'] == 'hackerrank'

    @patch('bytedojo.core.search.Repository')
    @patch('bytedojo.core.search.DatabaseManager')
    @patch('bytedojo.core.search.find_problems')
    def test_resolve_uses_default_source(self, mock_find, mock_db_class, mock_repo_class):
        """Test resolve uses 'leetcode' as default source."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = '/path/to/db'
        mock_repo_class.return_value = mock_repo

        mock_db = MagicMock()
        mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

        mock_find.return_value = [{'problem_id': '1', 'title': 'Test'}]

        resolve_problem(identifier='1')

        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['source'] == 'leetcode'

    @patch('bytedojo.core.search.Path')
    @patch('bytedojo.core.search.Repository')
    def test_resolve_uses_current_directory(self, mock_repo_class, mock_path):
        """Test resolve uses current working directory."""
        mock_cwd = MagicMock()
        mock_path.cwd.return_value = mock_cwd

        mock_repo = MagicMock()
        mock_repo.is_initialized = False
        mock_repo_class.return_value = mock_repo

        with pytest.raises(click.ClickException):
            resolve_problem(identifier='1')

        mock_path.cwd.assert_called_once()
        mock_repo_class.assert_called_once_with(mock_cwd)
