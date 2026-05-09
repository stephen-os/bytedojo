"""
Tests for attempt_service module.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from bytedojo.core.attempt_service import AttemptService
from bytedojo.core.models import Attempt, AttemptStats, Language, Status


class TestAttemptServiceInit:
    """Test AttemptService initialization."""

    def test_init_with_repo(self):
        """Test initialization with provided repo."""
        mock_repo = MagicMock()
        service = AttemptService(repo=mock_repo)

        assert service.repo is mock_repo

    def test_init_without_repo(self):
        """Test initialization creates repo from cwd."""
        with patch('bytedojo.core.attempt_service.Repository') as mock_repo_class:
            mock_repo_class.return_value = MagicMock()
            service = AttemptService()

            mock_repo_class.assert_called_once()


class TestAttemptServiceCreateAttempt:
    """Test AttemptService.create_attempt method."""

    def test_create_attempt_repo_not_initialized(self):
        """Test create_attempt when repo not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        service = AttemptService(repo=mock_repo)
        result = service.create_attempt(1, Language.PYTHON3)

        assert result is None

    def test_create_attempt_problem_not_found(self):
        """Test create_attempt when problem doesn't exist."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True

        with patch('bytedojo.core.attempt_service.problem_service') as mock_ps:
            mock_ps.get_problem.return_value = None

            service = AttemptService(repo=mock_repo)
            result = service.create_attempt(99999, Language.PYTHON3)

            assert result is None

    def test_create_attempt_success(self, tmp_path):
        """Test successful attempt creation."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = tmp_path / "test.db"
        mock_repo.problems_dir = tmp_path / "problems"

        mock_problem = MagicMock()
        mock_problem.get_folder_name.return_value = "0001-test"
        mock_problem.get_snippet.return_value = "class Solution: pass"
        mock_problem.get_solution_filename.return_value = "solution.py"

        with patch('bytedojo.core.attempt_service.problem_service') as mock_ps:
            mock_ps.get_problem.return_value = mock_problem

            with patch('bytedojo.core.attempt_service.DatabaseManager') as mock_db_class:
                mock_db = MagicMock()
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=False)
                mock_db.create_attempt.return_value = {'version': 1}
                mock_db_class.return_value = mock_db

                service = AttemptService(repo=mock_repo)
                result = service.create_attempt(1, Language.PYTHON3)

                assert result is not None
                assert isinstance(result, Attempt)
                assert result.problem_id == 1
                assert result.language == Language.PYTHON3
                assert result.version == 1
                assert result.status == Status.UNGRADED


class TestAttemptServiceGetAttempt:
    """Test AttemptService.get_attempt method."""

    def test_get_attempt_repo_not_initialized(self):
        """Test get_attempt when repo not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        service = AttemptService(repo=mock_repo)
        result = service.get_attempt(1, Language.PYTHON3)

        assert result is None

    def test_get_attempt_not_found(self, tmp_path):
        """Test get_attempt when attempt doesn't exist."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = tmp_path / "test.db"

        with patch('bytedojo.core.attempt_service.DatabaseManager') as mock_db_class:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.get_attempt.return_value = None
            mock_db_class.return_value = mock_db

            service = AttemptService(repo=mock_repo)
            result = service.get_attempt(1, Language.PYTHON3)

            assert result is None

    def test_get_attempt_success(self, tmp_path):
        """Test successful get_attempt."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = tmp_path / "test.db"

        attempt_data = {
            'problem_id': 1,
            'language': 'python3',
            'version': 1,
            'status': 'passed',
            'created_at': '2024-01-01T12:00:00',
            'run_count': 5,
            'notes': 'test notes'
        }

        with patch('bytedojo.core.attempt_service.DatabaseManager') as mock_db_class:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.get_attempt.return_value = attempt_data
            mock_db_class.return_value = mock_db

            service = AttemptService(repo=mock_repo)
            result = service.get_attempt(1, Language.PYTHON3)

            assert result is not None
            assert result.problem_id == 1
            assert result.language == Language.PYTHON3
            assert result.version == 1
            assert result.status == Status.PASSED
            assert result.run_count == 5


class TestAttemptServiceListAttempts:
    """Test AttemptService.list_attempts method."""

    def test_list_attempts_repo_not_initialized(self):
        """Test list_attempts when repo not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        service = AttemptService(repo=mock_repo)
        result = service.list_attempts(1)

        assert result == []

    def test_list_attempts_empty(self, tmp_path):
        """Test list_attempts when no attempts exist."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = tmp_path / "test.db"

        with patch('bytedojo.core.attempt_service.DatabaseManager') as mock_db_class:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.list_attempts.return_value = []
            mock_db_class.return_value = mock_db

            service = AttemptService(repo=mock_repo)
            result = service.list_attempts(1)

            assert result == []

    def test_list_attempts_multiple(self, tmp_path):
        """Test list_attempts with multiple results."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = tmp_path / "test.db"

        attempts_data = [
            {'problem_id': 1, 'language': 'python3', 'version': 1, 'status': 'failed',
             'created_at': '2024-01-01T12:00:00', 'run_count': 1, 'notes': ''},
            {'problem_id': 1, 'language': 'python3', 'version': 2, 'status': 'passed',
             'created_at': '2024-01-02T12:00:00', 'run_count': 3, 'notes': ''}
        ]

        with patch('bytedojo.core.attempt_service.DatabaseManager') as mock_db_class:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.list_attempts.return_value = attempts_data
            mock_db_class.return_value = mock_db

            service = AttemptService(repo=mock_repo)
            result = service.list_attempts(1)

            assert len(result) == 2
            assert result[0].version == 1
            assert result[1].version == 2


class TestAttemptServiceUpdateStatus:
    """Test AttemptService.update_status method."""

    def test_update_status_repo_not_initialized(self):
        """Test update_status when repo not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        service = AttemptService(repo=mock_repo)
        result = service.update_status(1, Language.PYTHON3, 1, Status.PASSED)

        assert result is False

    def test_update_status_success(self, tmp_path):
        """Test successful status update."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = tmp_path / "test.db"

        with patch('bytedojo.core.attempt_service.DatabaseManager') as mock_db_class:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.update_attempt_status.return_value = True
            mock_db_class.return_value = mock_db

            service = AttemptService(repo=mock_repo)
            result = service.update_status(1, Language.PYTHON3, 1, Status.PASSED)

            assert result is True
            mock_db.update_attempt_status.assert_called_once_with(
                1, 'python3', 1, 'passed', 'leetcode'
            )


class TestAttemptServiceIncrementRunCount:
    """Test AttemptService.increment_run_count method."""

    def test_increment_repo_not_initialized(self):
        """Test increment when repo not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        service = AttemptService(repo=mock_repo)
        result = service.increment_run_count(1, Language.PYTHON3, 1)

        assert result is False

    def test_increment_success(self, tmp_path):
        """Test successful increment."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = tmp_path / "test.db"

        with patch('bytedojo.core.attempt_service.DatabaseManager') as mock_db_class:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.increment_run_count.return_value = True
            mock_db_class.return_value = mock_db

            service = AttemptService(repo=mock_repo)
            result = service.increment_run_count(1, Language.PYTHON3, 1)

            assert result is True


class TestAttemptServiceGetStats:
    """Test AttemptService.get_stats method."""

    def test_get_stats_repo_not_initialized(self):
        """Test get_stats when repo not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = False

        service = AttemptService(repo=mock_repo)
        result = service.get_stats(1)

        assert result == {}

    def test_get_stats_success(self, tmp_path):
        """Test successful get_stats."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = tmp_path / "test.db"

        raw_stats = {
            'python3': {
                'total_attempts': 3,
                'latest_version': 3,
                'latest_status': 'passed',
                'pass_count': 2,
                'fail_count': 1,
                'skip_count': 0,
                'total_runs': 10
            }
        }

        with patch('bytedojo.core.attempt_service.DatabaseManager') as mock_db_class:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.get_attempt_stats.return_value = raw_stats
            mock_db_class.return_value = mock_db

            service = AttemptService(repo=mock_repo)
            result = service.get_stats(1)

            assert Language.PYTHON3 in result
            stats = result[Language.PYTHON3]
            assert stats.total_attempts == 3
            assert stats.pass_count == 2


class TestAttemptServiceGetAttemptPath:
    """Test AttemptService.get_attempt_path method."""

    def test_get_attempt_path_with_version(self, tmp_path):
        """Test get_attempt_path with explicit version."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.problems_dir = tmp_path / "problems"

        mock_problem = MagicMock()
        mock_problem.get_folder_name.return_value = "0001-two-sum"

        with patch('bytedojo.core.attempt_service.problem_service') as mock_ps:
            mock_ps.get_problem.return_value = mock_problem

            service = AttemptService(repo=mock_repo)
            result = service.get_attempt_path(1, Language.PYTHON3, version=1)

            assert result == tmp_path / "problems" / "0001-two-sum" / "python3" / "v001"

    def test_get_attempt_path_without_version(self, tmp_path):
        """Test get_attempt_path without version gets latest."""
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.db_path = tmp_path / "test.db"
        mock_repo.problems_dir = tmp_path / "problems"

        mock_problem = MagicMock()
        mock_problem.get_folder_name.return_value = "0001-two-sum"

        with patch('bytedojo.core.attempt_service.problem_service') as mock_ps:
            mock_ps.get_problem.return_value = mock_problem

            with patch('bytedojo.core.attempt_service.DatabaseManager') as mock_db_class:
                mock_db = MagicMock()
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=False)
                mock_db.get_attempt.return_value = {
                    'problem_id': 1,
                    'language': 'python3',
                    'version': 3,
                    'status': 'passed',
                    'created_at': '2024-01-01T12:00:00',
                    'run_count': 0,
                    'notes': ''
                }
                mock_db_class.return_value = mock_db

                service = AttemptService(repo=mock_repo)
                result = service.get_attempt_path(1, Language.PYTHON3)

                assert result == tmp_path / "problems" / "0001-two-sum" / "python3" / "v003"


class TestAttemptServiceDictToAttempt:
    """Test AttemptService._dict_to_attempt method."""

    def test_dict_to_attempt_basic(self):
        """Test converting dict to Attempt."""
        mock_repo = MagicMock()
        service = AttemptService(repo=mock_repo)

        data = {
            'problem_id': 1,
            'language': 'python3',
            'version': 1,
            'status': 'passed',
            'created_at': '2024-01-01T12:00:00',
            'run_count': 5,
            'notes': 'test notes'
        }

        result = service._dict_to_attempt(data)

        assert result.problem_id == 1
        assert result.language == Language.PYTHON3
        assert result.version == 1
        assert result.status == Status.PASSED
        assert result.run_count == 5
        assert result.notes == 'test notes'

    def test_dict_to_attempt_unknown_language_fallback(self):
        """Test that unknown language falls back to PYTHON3."""
        mock_repo = MagicMock()
        service = AttemptService(repo=mock_repo)

        data = {
            'problem_id': 1,
            'language': 'unknownlang',
            'version': 1,
            'status': 'passed',
            'created_at': '2024-01-01T12:00:00',
            'run_count': 0,
            'notes': ''
        }

        result = service._dict_to_attempt(data)

        assert result.language == Language.PYTHON3

    def test_dict_to_attempt_datetime_object(self):
        """Test handling datetime object in created_at."""
        mock_repo = MagicMock()
        service = AttemptService(repo=mock_repo)

        now = datetime.now()
        data = {
            'problem_id': 1,
            'language': 'java',
            'version': 1,
            'status': 'failed',
            'created_at': now,
            'run_count': 0,
            'notes': ''
        }

        result = service._dict_to_attempt(data)

        assert result.created_at == now
