"""
Tests for query module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

from bytedojo.core.query import QueryService, QueryResult
from bytedojo.core.models import (
    ProblemSummary,
    Difficulty,
    Status,
    Language,
    AttemptStats,
)


class TestQueryResult:
    """Test QueryResult dataclass."""

    def test_query_result_basic(self):
        """Test creating a basic QueryResult."""
        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array", "Hash Table"],
            )
        ]
        status_map = {}

        result = QueryResult(problems=problems, total=1, status_map=status_map)

        assert result.problems == problems
        assert result.total == 1
        assert result.status_map == {}

    def test_query_result_with_status_map(self):
        """Test QueryResult with populated status map."""
        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array"],
            )
        ]
        stats = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=3,
            latest_version=3,
            latest_status=Status.PASSED,
            pass_count=2,
            fail_count=1,
            skip_count=0,
            total_runs=5,
        )
        status_map = {1: {Language.PYTHON3: stats}}

        result = QueryResult(problems=problems, total=1, status_map=status_map)

        assert 1 in result.status_map
        assert Language.PYTHON3 in result.status_map[1]
        assert result.status_map[1][Language.PYTHON3].latest_status == Status.PASSED

    def test_query_result_empty(self):
        """Test QueryResult with no problems."""
        result = QueryResult(problems=[], total=0, status_map={})

        assert result.problems == []
        assert result.total == 0
        assert result.status_map == {}


class TestQueryServiceInit:
    """Test QueryService initialization."""

    def test_init_with_repo(self):
        """Test initialization with provided repository."""
        mock_repo = MagicMock()

        service = QueryService(repo=mock_repo)

        assert service.repo == mock_repo

    def test_init_without_repo(self):
        """Test initialization creates default repository."""
        with patch("bytedojo.core.query.Repository") as mock_repo_class:
            mock_repo_instance = MagicMock()
            mock_repo_class.return_value = mock_repo_instance

            service = QueryService()

            mock_repo_class.assert_called_once_with(Path.cwd())
            assert service.repo == mock_repo_instance

    def test_init_creates_attempt_service(self):
        """Test initialization creates AttemptService."""
        mock_repo = MagicMock()

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempt_instance = MagicMock()
            mock_attempt_class.return_value = mock_attempt_instance

            service = QueryService(repo=mock_repo)

            mock_attempt_class.assert_called_once_with(mock_repo)
            assert service.attempts == mock_attempt_instance


class TestQueryServiceQuery:
    """Test QueryService.query method."""

    def test_query_no_filters(self):
        """Test query without any filters."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array"],
            ),
            ProblemSummary(
                id=2,
                title="Add Two Numbers",
                title_slug="add-two-numbers",
                difficulty=Difficulty.MEDIUM,
                tags=["Linked List"],
            ),
        ]

        with patch("bytedojo.core.query.problem_service") as mock_ps:
            mock_ps.query_problems.return_value = problems

            service = QueryService(repo=mock_repo)
            result = service.query()

            mock_ps.query_problems.assert_called_once_with(
                difficulty=Difficulty.NONE, tags=None
            )
            assert result.problems == problems
            assert result.total == 2
            assert result.status_map == {}

    def test_query_with_difficulty_filter(self):
        """Test query with difficulty filter."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array"],
            )
        ]

        with patch("bytedojo.core.query.problem_service") as mock_ps:
            mock_ps.query_problems.return_value = problems

            service = QueryService(repo=mock_repo)
            result = service.query(difficulty=Difficulty.EASY)

            mock_ps.query_problems.assert_called_once_with(
                difficulty=Difficulty.EASY, tags=None
            )
            assert len(result.problems) == 1

    def test_query_with_tags_filter(self):
        """Test query with tags filter."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array", "Hash Table"],
            )
        ]

        with patch("bytedojo.core.query.problem_service") as mock_ps:
            mock_ps.query_problems.return_value = problems

            service = QueryService(repo=mock_repo)
            result = service.query(tags=["Array"])

            mock_ps.query_problems.assert_called_once_with(
                difficulty=Difficulty.NONE, tags=["Array"]
            )
            assert len(result.problems) == 1

    def test_query_with_all_filters(self):
        """Test query with all filters combined."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array"],
            )
        ]

        with patch("bytedojo.core.query.problem_service") as mock_ps:
            mock_ps.query_problems.return_value = problems

            service = QueryService(repo=mock_repo)
            result = service.query(
                difficulty=Difficulty.EASY, tags=["Array"], include_status=False
            )

            mock_ps.query_problems.assert_called_once_with(
                difficulty=Difficulty.EASY, tags=["Array"]
            )
            assert result.status_map == {}

    def test_query_with_status_repo_initialized(self):
        """Test query includes status when repo is initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True

        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array"],
            )
        ]

        stats = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.PASSED,
            pass_count=1,
            fail_count=0,
            skip_count=0,
            total_runs=1,
        )

        with patch("bytedojo.core.query.problem_service") as mock_ps:
            mock_ps.query_problems.return_value = problems

            with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
                mock_attempts = MagicMock()
                mock_attempts.get_all_stats.return_value = {
                    1: {Language.PYTHON3: stats}
                }
                mock_attempt_class.return_value = mock_attempts

                service = QueryService(repo=mock_repo)
                result = service.query(include_status=True)

                assert 1 in result.status_map
                assert Language.PYTHON3 in result.status_map[1]

    def test_query_include_status_false(self):
        """Test query excludes status when include_status=False."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True

        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array"],
            )
        ]

        with patch("bytedojo.core.query.problem_service") as mock_ps:
            mock_ps.query_problems.return_value = problems

            service = QueryService(repo=mock_repo)
            result = service.query(include_status=False)

            assert result.status_map == {}

    def test_query_empty_results(self):
        """Test query returns empty results when no matches."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        with patch("bytedojo.core.query.problem_service") as mock_ps:
            mock_ps.query_problems.return_value = []

            service = QueryService(repo=mock_repo)
            result = service.query()

            assert result.problems == []
            assert result.total == 0
            assert result.status_map == {}


class TestQueryServiceGetAvailableTags:
    """Test QueryService.get_available_tags method."""

    def test_get_available_tags(self):
        """Test getting available tags."""
        mock_repo = MagicMock()
        expected_tags = ["Array", "Dynamic Programming", "Hash Table", "Tree"]

        with patch("bytedojo.core.query.problem_service") as mock_ps:
            mock_ps.get_all_tags.return_value = expected_tags

            service = QueryService(repo=mock_repo)
            result = service.get_available_tags()

            mock_ps.get_all_tags.assert_called_once()
            assert result == expected_tags

    def test_get_available_tags_empty(self):
        """Test getting available tags when none exist."""
        mock_repo = MagicMock()

        with patch("bytedojo.core.query.problem_service") as mock_ps:
            mock_ps.get_all_tags.return_value = []

            service = QueryService(repo=mock_repo)
            result = service.get_available_tags()

            assert result == []


class TestQueryServiceGetStatusMap:
    """Test QueryService._get_status_map method."""

    def test_get_status_map_repo_not_initialized(self):
        """Test _get_status_map returns empty dict when repo not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array"],
            )
        ]

        service = QueryService(repo=mock_repo)
        result = service._get_status_map(problems)

        assert result == {}

    def test_get_status_map_filters_to_requested_problems(self):
        """Test _get_status_map only returns stats for requested problems."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True

        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array"],
            )
        ]

        stats_1 = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.PASSED,
            pass_count=1,
            fail_count=0,
            skip_count=0,
            total_runs=1,
        )
        stats_2 = AttemptStats(
            problem_id=2,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.FAILED,
            pass_count=0,
            fail_count=1,
            skip_count=0,
            total_runs=1,
        )

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_all_stats.return_value = {
                1: {Language.PYTHON3: stats_1},
                2: {Language.PYTHON3: stats_2},
            }
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service._get_status_map(problems)

            assert 1 in result
            assert 2 not in result

    def test_get_status_map_multiple_languages(self):
        """Test _get_status_map handles multiple languages per problem."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True

        problems = [
            ProblemSummary(
                id=1,
                title="Two Sum",
                title_slug="two-sum",
                difficulty=Difficulty.EASY,
                tags=["Array"],
            )
        ]

        stats_python = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=2,
            latest_version=2,
            latest_status=Status.PASSED,
            pass_count=1,
            fail_count=1,
            skip_count=0,
            total_runs=3,
        )
        stats_java = AttemptStats(
            problem_id=1,
            language=Language.JAVA,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.FAILED,
            pass_count=0,
            fail_count=1,
            skip_count=0,
            total_runs=1,
        )

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_all_stats.return_value = {
                1: {Language.PYTHON3: stats_python, Language.JAVA: stats_java}
            }
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service._get_status_map(problems)

            assert Language.PYTHON3 in result[1]
            assert Language.JAVA in result[1]


class TestQueryServiceGetProblemStatus:
    """Test QueryService.get_problem_status method."""

    def test_get_problem_status_no_stats(self):
        """Test get_problem_status returns NONE when no stats exist."""
        mock_repo = MagicMock()

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = {}
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_status(1)

            assert result == Status.NONE

    def test_get_problem_status_passed(self):
        """Test get_problem_status returns PASSED when any language passed."""
        mock_repo = MagicMock()

        stats = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.PASSED,
            pass_count=1,
            fail_count=0,
            skip_count=0,
            total_runs=1,
        )

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = {Language.PYTHON3: stats}
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_status(1)

            assert result == Status.PASSED

    def test_get_problem_status_failed(self):
        """Test get_problem_status returns FAILED when best status is failed."""
        mock_repo = MagicMock()

        stats = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.FAILED,
            pass_count=0,
            fail_count=1,
            skip_count=0,
            total_runs=1,
        )

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = {Language.PYTHON3: stats}
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_status(1)

            assert result == Status.FAILED

    def test_get_problem_status_skipped(self):
        """Test get_problem_status returns SKIPPED when best status is skipped."""
        mock_repo = MagicMock()

        stats = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.SKIPPED,
            pass_count=0,
            fail_count=0,
            skip_count=1,
            total_runs=0,
        )

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = {Language.PYTHON3: stats}
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_status(1)

            assert result == Status.SKIPPED

    def test_get_problem_status_ungraded(self):
        """Test get_problem_status returns UNGRADED when best status is ungraded."""
        mock_repo = MagicMock()

        stats = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.UNGRADED,
            pass_count=0,
            fail_count=0,
            skip_count=0,
            total_runs=0,
        )

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = {Language.PYTHON3: stats}
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_status(1)

            assert result == Status.UNGRADED

    def test_get_problem_status_priority_passed_over_failed(self):
        """Test get_problem_status prioritizes PASSED over FAILED."""
        mock_repo = MagicMock()

        stats_passed = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.PASSED,
            pass_count=1,
            fail_count=0,
            skip_count=0,
            total_runs=1,
        )
        stats_failed = AttemptStats(
            problem_id=1,
            language=Language.JAVA,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.FAILED,
            pass_count=0,
            fail_count=1,
            skip_count=0,
            total_runs=1,
        )

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = {
                Language.PYTHON3: stats_passed,
                Language.JAVA: stats_failed,
            }
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_status(1)

            assert result == Status.PASSED

    def test_get_problem_status_priority_failed_over_skipped(self):
        """Test get_problem_status prioritizes FAILED over SKIPPED."""
        mock_repo = MagicMock()

        stats_failed = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.FAILED,
            pass_count=0,
            fail_count=1,
            skip_count=0,
            total_runs=1,
        )
        stats_skipped = AttemptStats(
            problem_id=1,
            language=Language.JAVA,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.SKIPPED,
            pass_count=0,
            fail_count=0,
            skip_count=1,
            total_runs=0,
        )

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = {
                Language.PYTHON3: stats_failed,
                Language.JAVA: stats_skipped,
            }
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_status(1)

            assert result == Status.FAILED

    def test_get_problem_status_priority_skipped_over_ungraded(self):
        """Test get_problem_status prioritizes SKIPPED over UNGRADED."""
        mock_repo = MagicMock()

        stats_skipped = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.SKIPPED,
            pass_count=0,
            fail_count=0,
            skip_count=1,
            total_runs=0,
        )
        stats_ungraded = AttemptStats(
            problem_id=1,
            language=Language.JAVA,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.UNGRADED,
            pass_count=0,
            fail_count=0,
            skip_count=0,
            total_runs=0,
        )

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = {
                Language.PYTHON3: stats_skipped,
                Language.JAVA: stats_ungraded,
            }
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_status(1)

            assert result == Status.SKIPPED


class TestQueryServiceGetProblemStats:
    """Test QueryService.get_problem_stats method."""

    def test_get_problem_stats_all_languages(self):
        """Test get_problem_stats returns all languages when none specified."""
        mock_repo = MagicMock()

        stats = {
            Language.PYTHON3: AttemptStats(
                problem_id=1,
                language=Language.PYTHON3,
                total_attempts=2,
                latest_version=2,
                latest_status=Status.PASSED,
                pass_count=1,
                fail_count=1,
                skip_count=0,
                total_runs=3,
            ),
            Language.JAVA: AttemptStats(
                problem_id=1,
                language=Language.JAVA,
                total_attempts=1,
                latest_version=1,
                latest_status=Status.FAILED,
                pass_count=0,
                fail_count=1,
                skip_count=0,
                total_runs=1,
            ),
        }

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = stats
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_stats(1)

            mock_attempts.get_stats.assert_called_once_with(1, None)
            assert result == stats

    def test_get_problem_stats_specific_language(self):
        """Test get_problem_stats with specific language filter."""
        mock_repo = MagicMock()

        stats = {
            Language.PYTHON3: AttemptStats(
                problem_id=1,
                language=Language.PYTHON3,
                total_attempts=2,
                latest_version=2,
                latest_status=Status.PASSED,
                pass_count=1,
                fail_count=1,
                skip_count=0,
                total_runs=3,
            )
        }

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = stats
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_stats(1, language=Language.PYTHON3)

            mock_attempts.get_stats.assert_called_once_with(1, Language.PYTHON3)
            assert result == stats

    def test_get_problem_stats_empty(self):
        """Test get_problem_stats returns empty dict when no stats exist."""
        mock_repo = MagicMock()

        with patch("bytedojo.core.query.AttemptService") as mock_attempt_class:
            mock_attempts = MagicMock()
            mock_attempts.get_stats.return_value = {}
            mock_attempt_class.return_value = mock_attempts

            service = QueryService(repo=mock_repo)
            result = service.get_problem_stats(99999)

            assert result == {}
