"""
Tests for picker module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from bytedojo.core.picker import (
    DIFFICULTY_MAP,
    PickResult,
    ProblemPicker,
)
from bytedojo.core.models import ProblemSummary, Difficulty


class TestDifficultyMap:
    """Test DIFFICULTY_MAP constant."""

    def test_string_mappings(self):
        """Test string difficulty mappings."""
        assert DIFFICULTY_MAP['easy'] == 1
        assert DIFFICULTY_MAP['medium'] == 2
        assert DIFFICULTY_MAP['hard'] == 3

    def test_numeric_string_mappings(self):
        """Test numeric string difficulty mappings."""
        assert DIFFICULTY_MAP['1'] == 1
        assert DIFFICULTY_MAP['2'] == 2
        assert DIFFICULTY_MAP['3'] == 3


class TestPickResult:
    """Test PickResult dataclass."""

    def test_pick_result_with_problem(self):
        """Test PickResult with a picked problem."""
        problem = ProblemSummary(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty=Difficulty.EASY,
            tags=["Array", "Hash Table"]
        )
        result = PickResult(
            problem=problem,
            unsolved_count=10,
            solved_count=5,
            total_count=15
        )

        assert result.problem == problem
        assert result.unsolved_count == 10
        assert result.solved_count == 5
        assert result.total_count == 15

    def test_pick_result_no_problem(self):
        """Test PickResult when no problem is picked."""
        result = PickResult(
            problem=None,
            unsolved_count=0,
            solved_count=15,
            total_count=15
        )

        assert result.problem is None
        assert result.unsolved_count == 0
        assert result.solved_count == 15
        assert result.total_count == 15

    def test_pick_result_empty(self):
        """Test PickResult with empty state."""
        result = PickResult(
            problem=None,
            unsolved_count=0,
            solved_count=0,
            total_count=0
        )

        assert result.problem is None
        assert result.unsolved_count == 0
        assert result.solved_count == 0
        assert result.total_count == 0


class TestProblemPickerInit:
    """Test ProblemPicker initialization."""

    def test_init_with_repo(self):
        """Test initialization with provided repository."""
        mock_repo = MagicMock()
        picker = ProblemPicker(repo=mock_repo)

        assert picker.repo == mock_repo

    def test_init_without_repo(self):
        """Test initialization without repository creates one."""
        with patch('bytedojo.core.picker.Repository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            picker = ProblemPicker()

            mock_repo_class.assert_called_once_with(Path.cwd())
            assert picker.repo == mock_repo


class TestProblemPickerPick:
    """Test ProblemPicker.pick method."""

    def test_pick_no_problems_available(self):
        """Test picking when no problems match criteria."""
        mock_repo = MagicMock()

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=[]):
            picker = ProblemPicker(repo=mock_repo)
            result = picker.pick()

            assert result.problem is None
            assert result.unsolved_count == 0
            assert result.solved_count == 0
            assert result.total_count == 0

    def test_pick_all_solved(self):
        """Test picking when all problems are solved."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path("/fake/db.sqlite")

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[]),
            ProblemSummary(id=2, title="P2", title_slug="p2", difficulty=Difficulty.EASY, tags=[]),
        ]

        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1'},
            {'problem_id': '2'},
        ]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems):
            with patch('bytedojo.core.picker.DatabaseManager') as mock_db_manager:
                mock_db_manager.return_value.__enter__.return_value = mock_db

                picker = ProblemPicker(repo=mock_repo)
                result = picker.pick()

                assert result.problem is None
                assert result.unsolved_count == 0
                assert result.solved_count == 2
                assert result.total_count == 2

    def test_pick_returns_unsolved_problem(self):
        """Test picking returns an unsolved problem."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path("/fake/db.sqlite")

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[]),
            ProblemSummary(id=2, title="P2", title_slug="p2", difficulty=Difficulty.EASY, tags=[]),
            ProblemSummary(id=3, title="P3", title_slug="p3", difficulty=Difficulty.EASY, tags=[]),
        ]

        mock_db = MagicMock()
        mock_db.list_problems.return_value = [{'problem_id': '1'}]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems):
            with patch('bytedojo.core.picker.DatabaseManager') as mock_db_manager:
                mock_db_manager.return_value.__enter__.return_value = mock_db
                with patch('bytedojo.core.picker.random.choice') as mock_choice:
                    mock_choice.return_value = problems[1]

                    picker = ProblemPicker(repo=mock_repo)
                    result = picker.pick()

                    assert result.problem == problems[1]
                    assert result.unsolved_count == 2
                    assert result.solved_count == 1
                    assert result.total_count == 3

    def test_pick_with_easy_difficulty(self):
        """Test picking with easy difficulty filter."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problem = ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[])

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=[problem]) as mock_query:
            with patch('bytedojo.core.picker.random.choice', return_value=problem):
                picker = ProblemPicker(repo=mock_repo)
                result = picker.pick(difficulty='easy')

                mock_query.assert_called_once_with(difficulty=Difficulty.EASY, tags=None)
                assert result.problem == problem

    def test_pick_with_numeric_difficulty(self):
        """Test picking with numeric difficulty filter (1, 2, 3)."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problem = ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.MEDIUM, tags=[])

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=[problem]) as mock_query:
            with patch('bytedojo.core.picker.random.choice', return_value=problem):
                picker = ProblemPicker(repo=mock_repo)
                result = picker.pick(difficulty='2')

                mock_query.assert_called_once_with(difficulty=Difficulty.MEDIUM, tags=None)
                assert result.problem == problem

    def test_pick_with_hard_difficulty(self):
        """Test picking with hard difficulty filter."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problem = ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.HARD, tags=[])

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=[problem]) as mock_query:
            with patch('bytedojo.core.picker.random.choice', return_value=problem):
                picker = ProblemPicker(repo=mock_repo)
                result = picker.pick(difficulty='hard')

                mock_query.assert_called_once_with(difficulty=Difficulty.HARD, tags=None)
                assert result.problem == problem

    def test_pick_with_tags(self):
        """Test picking with tags filter."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problem = ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=["Array"])

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=[problem]) as mock_query:
            with patch('bytedojo.core.picker.random.choice', return_value=problem):
                picker = ProblemPicker(repo=mock_repo)
                result = picker.pick(tags=["Array", "Hash Table"])

                mock_query.assert_called_once_with(difficulty=Difficulty.NONE, tags=["Array", "Hash Table"])
                assert result.problem == problem

    def test_pick_with_difficulty_and_tags(self):
        """Test picking with both difficulty and tags filters."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problem = ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.MEDIUM, tags=["Tree"])

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=[problem]) as mock_query:
            with patch('bytedojo.core.picker.random.choice', return_value=problem):
                picker = ProblemPicker(repo=mock_repo)
                result = picker.pick(difficulty='medium', tags=["Tree"])

                mock_query.assert_called_once_with(difficulty=Difficulty.MEDIUM, tags=["Tree"])
                assert result.problem == problem

    def test_pick_difficulty_case_insensitive(self):
        """Test that difficulty filter is case insensitive."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problem = ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[])

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=[problem]) as mock_query:
            with patch('bytedojo.core.picker.random.choice', return_value=problem):
                picker = ProblemPicker(repo=mock_repo)

                picker.pick(difficulty='EASY')
                mock_query.assert_called_with(difficulty=Difficulty.EASY, tags=None)

                picker.pick(difficulty='Easy')
                mock_query.assert_called_with(difficulty=Difficulty.EASY, tags=None)

                picker.pick(difficulty='eAsY')
                mock_query.assert_called_with(difficulty=Difficulty.EASY, tags=None)

    def test_pick_with_unknown_difficulty(self):
        """Test picking with unknown difficulty defaults to NONE."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problem = ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[])

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=[problem]) as mock_query:
            with patch('bytedojo.core.picker.random.choice', return_value=problem):
                picker = ProblemPicker(repo=mock_repo)
                result = picker.pick(difficulty='unknown')

                mock_query.assert_called_once_with(difficulty=Difficulty.NONE, tags=None)


class TestProblemPickerGetFetchedProblemIds:
    """Test ProblemPicker._get_fetched_problem_ids method."""

    def test_get_fetched_ids_repo_not_initialized(self):
        """Test getting fetched IDs when repo is not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        picker = ProblemPicker(repo=mock_repo)
        result = picker._get_fetched_problem_ids()

        assert result == set()

    def test_get_fetched_ids_repo_initialized(self):
        """Test getting fetched IDs when repo is initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path("/fake/db.sqlite")

        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1'},
            {'problem_id': '5'},
            {'problem_id': '10'},
        ]

        with patch('bytedojo.core.picker.DatabaseManager') as mock_db_manager:
            mock_db_manager.return_value.__enter__.return_value = mock_db

            picker = ProblemPicker(repo=mock_repo)
            result = picker._get_fetched_problem_ids()

            mock_db.list_problems.assert_called_once_with(source='leetcode')
            assert result == {1, 5, 10}

    def test_get_fetched_ids_empty_database(self):
        """Test getting fetched IDs when database is empty."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path("/fake/db.sqlite")

        mock_db = MagicMock()
        mock_db.list_problems.return_value = []

        with patch('bytedojo.core.picker.DatabaseManager') as mock_db_manager:
            mock_db_manager.return_value.__enter__.return_value = mock_db

            picker = ProblemPicker(repo=mock_repo)
            result = picker._get_fetched_problem_ids()

            assert result == set()


class TestProblemPickerGetUnsolvedProblems:
    """Test ProblemPicker.get_unsolved_problems method."""

    def test_get_unsolved_no_problems(self):
        """Test getting unsolved problems when none available."""
        mock_repo = MagicMock()

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=[]):
            picker = ProblemPicker(repo=mock_repo)
            result = picker.get_unsolved_problems()

            assert result == []

    def test_get_unsolved_all_solved(self):
        """Test getting unsolved problems when all are solved."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path("/fake/db.sqlite")

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[]),
            ProblemSummary(id=2, title="P2", title_slug="p2", difficulty=Difficulty.EASY, tags=[]),
        ]

        mock_db = MagicMock()
        mock_db.list_problems.return_value = [
            {'problem_id': '1'},
            {'problem_id': '2'},
        ]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems):
            with patch('bytedojo.core.picker.DatabaseManager') as mock_db_manager:
                mock_db_manager.return_value.__enter__.return_value = mock_db

                picker = ProblemPicker(repo=mock_repo)
                result = picker.get_unsolved_problems()

                assert result == []

    def test_get_unsolved_some_solved(self):
        """Test getting unsolved problems when some are solved."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = Path("/fake/db.sqlite")

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[]),
            ProblemSummary(id=2, title="P2", title_slug="p2", difficulty=Difficulty.MEDIUM, tags=[]),
            ProblemSummary(id=3, title="P3", title_slug="p3", difficulty=Difficulty.HARD, tags=[]),
        ]

        mock_db = MagicMock()
        mock_db.list_problems.return_value = [{'problem_id': '1'}]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems):
            with patch('bytedojo.core.picker.DatabaseManager') as mock_db_manager:
                mock_db_manager.return_value.__enter__.return_value = mock_db

                picker = ProblemPicker(repo=mock_repo)
                result = picker.get_unsolved_problems()

                assert len(result) == 2
                assert result[0].id == 2
                assert result[1].id == 3

    def test_get_unsolved_none_solved(self):
        """Test getting unsolved problems when none are solved."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[]),
            ProblemSummary(id=2, title="P2", title_slug="p2", difficulty=Difficulty.MEDIUM, tags=[]),
        ]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems):
            picker = ProblemPicker(repo=mock_repo)
            result = picker.get_unsolved_problems()

            assert len(result) == 2
            assert result[0].id == 1
            assert result[1].id == 2

    def test_get_unsolved_with_easy_difficulty(self):
        """Test getting unsolved problems with easy difficulty filter."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[]),
        ]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems) as mock_query:
            picker = ProblemPicker(repo=mock_repo)
            result = picker.get_unsolved_problems(difficulty='easy')

            mock_query.assert_called_once_with(difficulty=Difficulty.EASY, tags=None)
            assert len(result) == 1

    def test_get_unsolved_with_numeric_difficulty(self):
        """Test getting unsolved problems with numeric difficulty (1, 2, 3)."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.HARD, tags=[]),
        ]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems) as mock_query:
            picker = ProblemPicker(repo=mock_repo)
            result = picker.get_unsolved_problems(difficulty='3')

            mock_query.assert_called_once_with(difficulty=Difficulty.HARD, tags=None)
            assert len(result) == 1

    def test_get_unsolved_with_tags(self):
        """Test getting unsolved problems with tags filter."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=["Array"]),
        ]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems) as mock_query:
            picker = ProblemPicker(repo=mock_repo)
            result = picker.get_unsolved_problems(tags=["Array"])

            mock_query.assert_called_once_with(difficulty=Difficulty.NONE, tags=["Array"])
            assert len(result) == 1

    def test_get_unsolved_with_difficulty_and_tags(self):
        """Test getting unsolved problems with both filters."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.MEDIUM, tags=["Tree"]),
        ]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems) as mock_query:
            picker = ProblemPicker(repo=mock_repo)
            result = picker.get_unsolved_problems(difficulty='medium', tags=["Tree"])

            mock_query.assert_called_once_with(difficulty=Difficulty.MEDIUM, tags=["Tree"])
            assert len(result) == 1

    def test_get_unsolved_difficulty_case_insensitive(self):
        """Test that difficulty filter is case insensitive."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[]),
        ]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems) as mock_query:
            picker = ProblemPicker(repo=mock_repo)

            picker.get_unsolved_problems(difficulty='MEDIUM')
            mock_query.assert_called_with(difficulty=Difficulty.MEDIUM, tags=None)

            picker.get_unsolved_problems(difficulty='Medium')
            mock_query.assert_called_with(difficulty=Difficulty.MEDIUM, tags=None)

    def test_get_unsolved_with_unknown_difficulty(self):
        """Test getting unsolved with unknown difficulty defaults to NONE."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(id=1, title="P1", title_slug="p1", difficulty=Difficulty.EASY, tags=[]),
        ]

        with patch('bytedojo.core.picker.problem_service.query_problems', return_value=problems) as mock_query:
            picker = ProblemPicker(repo=mock_repo)
            result = picker.get_unsolved_problems(difficulty='invalid')

            mock_query.assert_called_once_with(difficulty=Difficulty.NONE, tags=None)
