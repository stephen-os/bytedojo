"""
Tests for problem_service module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from bytedojo.core.problem_service import (
    get_problem,
    get_problem_by_slug,
    problem_exists,
    query_problems,
    get_all_tags,
    parse_problem_ids,
    _load_index,
    _load_problem_file,
    _build_problem,
)
from bytedojo.core.models import Problem, ProblemSummary, Difficulty, Language


class TestParseProblemsIds:
    """Test parse_problem_ids function."""

    def test_single_id(self):
        """Test parsing a single ID."""
        assert parse_problem_ids(("1",)) == [1]
        assert parse_problem_ids(("42",)) == [42]

    def test_multiple_ids_comma_separated(self):
        """Test parsing comma-separated IDs."""
        assert parse_problem_ids(("1,2,3",)) == [1, 2, 3]
        assert parse_problem_ids(("10,20,30",)) == [10, 20, 30]

    def test_range(self):
        """Test parsing a range of IDs."""
        assert parse_problem_ids(("1..5",)) == [1, 2, 3, 4, 5]
        assert parse_problem_ids(("10..12",)) == [10, 11, 12]

    def test_mixed_format(self):
        """Test parsing mixed formats."""
        assert parse_problem_ids(("1,5..7,10",)) == [1, 5, 6, 7, 10]

    def test_multiple_arguments(self):
        """Test parsing multiple arguments."""
        assert parse_problem_ids(("1", "2", "3")) == [1, 2, 3]
        assert parse_problem_ids(("1,2", "3,4")) == [1, 2, 3, 4]

    def test_removes_duplicates(self):
        """Test that duplicates are removed."""
        assert parse_problem_ids(("1,1,1",)) == [1]
        assert parse_problem_ids(("1,2,1,3,2",)) == [1, 2, 3]

    def test_preserves_order(self):
        """Test that order is preserved after dedup."""
        assert parse_problem_ids(("3,1,2",)) == [3, 1, 2]

    def test_whitespace_handling(self):
        """Test that whitespace is handled."""
        assert parse_problem_ids((" 1 , 2 , 3 ",)) == [1, 2, 3]
        assert parse_problem_ids((" 1 .. 3 ",)) == [1, 2, 3]

    def test_empty_parts_ignored(self):
        """Test that empty parts are ignored."""
        assert parse_problem_ids(("1,,2",)) == [1, 2]
        assert parse_problem_ids((",1,2,",)) == [1, 2]

    def test_invalid_id_raises(self):
        """Test that invalid IDs raise ValueError."""
        with pytest.raises(ValueError, match="Invalid problem ID"):
            parse_problem_ids(("abc",))

    def test_invalid_range_format_raises(self):
        """Test that invalid range format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid range format"):
            parse_problem_ids(("1..2..3",))

    def test_invalid_range_values_raises(self):
        """Test that invalid range values raise ValueError."""
        with pytest.raises(ValueError, match="Invalid range values"):
            parse_problem_ids(("a..b",))

    def test_invalid_range_order_raises(self):
        """Test that start > end raises ValueError."""
        with pytest.raises(ValueError, match="Invalid range: start"):
            parse_problem_ids(("10..5",))


class TestBuildProblem:
    """Test _build_problem function."""

    def test_build_basic_problem(self):
        """Test building a basic problem."""
        data = {
            "id": 1,
            "title": "Two Sum",
            "slug": "two-sum",
            "difficulty": "Easy",
            "description": "<p>Test</p>",
            "code_snippets": {}
        }

        problem = _build_problem(data)

        assert problem.id == 1
        assert problem.title == "Two Sum"
        assert problem.title_slug == "two-sum"
        assert problem.difficulty == Difficulty.EASY
        assert problem.description == "<p>Test</p>"
        assert problem.code_snippets == []

    def test_build_problem_with_snippets(self):
        """Test building a problem with code snippets."""
        data = {
            "id": 1,
            "title": "Test",
            "slug": "test",
            "difficulty": "Medium",
            "description": "desc",
            "code_snippets": {
                "python3": "class Solution: pass",
                "java": "class Solution {}"
            }
        }

        problem = _build_problem(data)

        assert len(problem.code_snippets) == 2
        assert problem.get_snippet(Language.PYTHON3) == "class Solution: pass"
        assert problem.get_snippet(Language.JAVA) == "class Solution {}"

    def test_build_problem_filters_unknown_languages(self):
        """Test that unknown languages are filtered out."""
        data = {
            "id": 1,
            "title": "Test",
            "slug": "test",
            "difficulty": "Easy",
            "description": "desc",
            "code_snippets": {
                "python3": "code",
                "unknownlang": "code"
            }
        }

        problem = _build_problem(data)

        assert len(problem.code_snippets) == 1
        assert problem.get_snippet(Language.PYTHON3) == "code"

    def test_build_problem_missing_fields(self):
        """Test building problem with missing fields uses defaults."""
        data = {}

        problem = _build_problem(data)

        assert problem.id == 0
        assert problem.title == ""
        assert problem.title_slug == ""
        assert problem.difficulty == Difficulty.NONE
        assert problem.description == ""


class TestLoadIndex:
    """Test _load_index function."""

    def test_load_index_file_not_exists(self):
        """Test loading index when file doesn't exist."""
        with patch('bytedojo.core.problem_service.PROBLEMS_INDEX') as mock_path:
            mock_path.exists.return_value = False
            result = _load_index()
            assert result == {}

    def test_load_index_success(self, tmp_path):
        """Test loading index successfully."""
        index_data = {"two-sum": {"id": 1, "title": "Two Sum"}}
        index_file = tmp_path / "index.json"
        index_file.write_text(json.dumps(index_data))

        with patch('bytedojo.core.problem_service.PROBLEMS_INDEX', index_file):
            result = _load_index()
            assert result == index_data


class TestGetProblem:
    """Test get_problem function."""

    def test_get_problem_not_found(self):
        """Test getting a problem that doesn't exist."""
        with patch('bytedojo.core.problem_service._load_problem_file', return_value=None):
            result = get_problem(99999)
            assert result is None

    def test_get_problem_success(self):
        """Test getting a problem successfully."""
        mock_data = {
            "id": 1,
            "title": "Two Sum",
            "slug": "two-sum",
            "difficulty": "Easy",
            "description": "Test",
            "code_snippets": {"python3": "code"}
        }

        with patch('bytedojo.core.problem_service._load_problem_file', return_value=mock_data):
            result = get_problem(1)

            assert result is not None
            assert result.id == 1
            assert result.title == "Two Sum"


class TestGetProblemBySlug:
    """Test get_problem_by_slug function."""

    def test_get_by_slug_not_in_index(self):
        """Test getting problem with slug not in index."""
        with patch('bytedojo.core.problem_service._load_index', return_value={}):
            result = get_problem_by_slug("nonexistent")
            assert result is None

    def test_get_by_slug_success(self):
        """Test getting problem by slug successfully."""
        mock_index = {"two-sum": {"id": 1}}
        mock_data = {
            "id": 1,
            "title": "Two Sum",
            "slug": "two-sum",
            "difficulty": "Easy",
            "description": "Test",
            "code_snippets": {}
        }

        with patch('bytedojo.core.problem_service._load_index', return_value=mock_index):
            with patch('bytedojo.core.problem_service._load_problem_file', return_value=mock_data):
                result = get_problem_by_slug("two-sum")

                assert result is not None
                assert result.id == 1


class TestProblemExists:
    """Test problem_exists function."""

    def test_problem_exists_true(self, tmp_path):
        """Test when problem file exists."""
        problem_file = tmp_path / "1.json"
        problem_file.write_text("{}")

        with patch('bytedojo.core.problem_service.get_problem_file', return_value=problem_file):
            assert problem_exists(1) is True

    def test_problem_exists_false(self, tmp_path):
        """Test when problem file doesn't exist."""
        problem_file = tmp_path / "nonexistent.json"

        with patch('bytedojo.core.problem_service.get_problem_file', return_value=problem_file):
            assert problem_exists(99999) is False


class TestQueryProblems:
    """Test query_problems function."""

    def test_query_no_filters(self):
        """Test querying without filters."""
        mock_index = {
            "two-sum": {"id": 1, "title": "Two Sum", "difficulty": "Easy", "topics": ["Array"]},
            "add-two": {"id": 2, "title": "Add Two", "difficulty": "Medium", "topics": ["Math"]}
        }

        with patch('bytedojo.core.problem_service._load_index', return_value=mock_index):
            results = query_problems()

            assert len(results) == 2
            assert results[0].id == 1
            assert results[1].id == 2

    def test_query_by_difficulty(self):
        """Test querying by difficulty."""
        mock_index = {
            "easy": {"id": 1, "title": "Easy", "difficulty": "Easy", "topics": []},
            "medium": {"id": 2, "title": "Medium", "difficulty": "Medium", "topics": []}
        }

        with patch('bytedojo.core.problem_service._load_index', return_value=mock_index):
            results = query_problems(difficulty=Difficulty.EASY)

            assert len(results) == 1
            assert results[0].difficulty == Difficulty.EASY

    def test_query_by_tags(self):
        """Test querying by tags."""
        mock_index = {
            "p1": {"id": 1, "title": "P1", "difficulty": "Easy", "topics": ["Array", "Hash Table"]},
            "p2": {"id": 2, "title": "P2", "difficulty": "Easy", "topics": ["Tree"]}
        }

        with patch('bytedojo.core.problem_service._load_index', return_value=mock_index):
            results = query_problems(tags=["Array"])

            assert len(results) == 1
            assert results[0].id == 1

    def test_query_with_limit(self):
        """Test querying with limit."""
        mock_index = {
            "p1": {"id": 1, "title": "P1", "difficulty": "Easy", "topics": []},
            "p2": {"id": 2, "title": "P2", "difficulty": "Easy", "topics": []},
            "p3": {"id": 3, "title": "P3", "difficulty": "Easy", "topics": []}
        }

        with patch('bytedojo.core.problem_service._load_index', return_value=mock_index):
            results = query_problems(limit=2)

            assert len(results) == 2

    def test_query_results_sorted_by_id(self):
        """Test that results are sorted by ID."""
        mock_index = {
            "p3": {"id": 3, "title": "P3", "difficulty": "Easy", "topics": []},
            "p1": {"id": 1, "title": "P1", "difficulty": "Easy", "topics": []},
            "p2": {"id": 2, "title": "P2", "difficulty": "Easy", "topics": []}
        }

        with patch('bytedojo.core.problem_service._load_index', return_value=mock_index):
            results = query_problems()

            assert [r.id for r in results] == [1, 2, 3]


class TestGetAllTags:
    """Test get_all_tags function."""

    def test_get_all_tags_empty_index(self):
        """Test getting tags from empty index."""
        with patch('bytedojo.core.problem_service._load_index', return_value={}):
            result = get_all_tags()
            assert result == []

    def test_get_all_tags_unique_sorted(self):
        """Test that tags are unique and sorted."""
        mock_index = {
            "p1": {"topics": ["Array", "Hash Table"]},
            "p2": {"topics": ["Array", "Tree"]},
            "p3": {"topics": ["Dynamic Programming"]}
        }

        with patch('bytedojo.core.problem_service._load_index', return_value=mock_index):
            result = get_all_tags()

            assert result == ["Array", "Dynamic Programming", "Hash Table", "Tree"]
