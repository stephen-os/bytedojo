"""
Tests for grading module (GradeResult, GradingService).
"""

from unittest.mock import MagicMock, patch

import pytest

from bytedojo.core.grading import GradeResult, GradingService


class TestGradeResult:
    """Test GradeResult dataclass."""

    def test_create_grade_result(self):
        """Test creating a GradeResult."""
        result = GradeResult(
            success=True,
            status="passed",
            notes="Great job!",
            scheduled_review=True,
            review_frequency_days=7
        )

        assert result.success is True
        assert result.status == "passed"
        assert result.notes == "Great job!"
        assert result.scheduled_review is True
        assert result.review_frequency_days == 7

    def test_grade_result_with_none_notes(self):
        """Test GradeResult with None notes."""
        result = GradeResult(
            success=True,
            status="failed",
            notes=None,
            scheduled_review=False,
            review_frequency_days=7
        )

        assert result.notes is None

    def test_grade_result_equality(self):
        """Test that identical GradeResults are equal."""
        result1 = GradeResult(
            success=True,
            status="passed",
            notes="test",
            scheduled_review=True,
            review_frequency_days=7
        )
        result2 = GradeResult(
            success=True,
            status="passed",
            notes="test",
            scheduled_review=True,
            review_frequency_days=7
        )

        assert result1 == result2

    def test_grade_result_inequality(self):
        """Test that different GradeResults are not equal."""
        result1 = GradeResult(
            success=True,
            status="passed",
            notes="test",
            scheduled_review=True,
            review_frequency_days=7
        )
        result2 = GradeResult(
            success=True,
            status="failed",
            notes="test",
            scheduled_review=False,
            review_frequency_days=7
        )

        assert result1 != result2

    def test_grade_result_skipped_status(self):
        """Test GradeResult with skipped status."""
        result = GradeResult(
            success=True,
            status="skipped",
            notes="Will revisit later",
            scheduled_review=False,
            review_frequency_days=14
        )

        assert result.status == "skipped"
        assert result.scheduled_review is False


class TestGradingServiceInit:
    """Test GradingService initialization."""

    def test_init_with_database_manager(self):
        """Test initializing GradingService with a DatabaseManager."""
        mock_db = MagicMock()
        service = GradingService(db=mock_db)

        assert service.db is mock_db

    def test_init_stores_db_reference(self):
        """Test that init stores the database reference."""
        mock_db = MagicMock()
        service = GradingService(mock_db)

        assert service.db == mock_db


class TestGradingServiceGradeProblem:
    """Test GradingService.grade_problem method."""

    def test_grade_problem_passed(self):
        """Test grading a problem as passed."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'
        service = GradingService(db=mock_db)

        result = service.grade_problem(problem_id=1, status="passed")

        assert result.success is True
        assert result.status == "passed"
        assert result.scheduled_review is True
        assert result.review_frequency_days == 7
        mock_db.update_test_status.assert_called_once_with(1, "passed", None)
        mock_db.schedule_review.assert_called_once_with(1)

    def test_grade_problem_failed(self):
        """Test grading a problem as failed."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'
        service = GradingService(db=mock_db)

        result = service.grade_problem(problem_id=1, status="failed")

        assert result.success is True
        assert result.status == "failed"
        assert result.scheduled_review is False
        mock_db.update_test_status.assert_called_once_with(1, "failed", None)
        mock_db.schedule_review.assert_not_called()

    def test_grade_problem_skipped(self):
        """Test grading a problem as skipped."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'
        service = GradingService(db=mock_db)

        result = service.grade_problem(problem_id=1, status="skipped")

        assert result.success is True
        assert result.status == "skipped"
        assert result.scheduled_review is False
        mock_db.update_test_status.assert_called_once_with(1, "skipped", None)
        mock_db.schedule_review.assert_not_called()

    def test_grade_problem_with_notes(self):
        """Test grading a problem with notes."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'
        service = GradingService(db=mock_db)

        result = service.grade_problem(
            problem_id=1,
            status="passed",
            notes="Used dynamic programming approach"
        )

        assert result.notes == "Used dynamic programming approach"
        mock_db.update_test_status.assert_called_once_with(
            1, "passed", "Used dynamic programming approach"
        )

    def test_grade_problem_invalid_status(self):
        """Test that invalid status raises ValueError."""
        mock_db = MagicMock()
        service = GradingService(db=mock_db)

        with pytest.raises(ValueError) as exc_info:
            service.grade_problem(problem_id=1, status="invalid")

        assert "Invalid status 'invalid'" in str(exc_info.value)
        assert "passed" in str(exc_info.value)
        assert "failed" in str(exc_info.value)
        assert "skipped" in str(exc_info.value)

    def test_grade_problem_invalid_status_empty(self):
        """Test that empty status raises ValueError."""
        mock_db = MagicMock()
        service = GradingService(db=mock_db)

        with pytest.raises(ValueError) as exc_info:
            service.grade_problem(problem_id=1, status="")

        assert "Invalid status" in str(exc_info.value)

    def test_grade_problem_invalid_status_uppercase(self):
        """Test that uppercase status raises ValueError (case-sensitive)."""
        mock_db = MagicMock()
        service = GradingService(db=mock_db)

        with pytest.raises(ValueError) as exc_info:
            service.grade_problem(problem_id=1, status="PASSED")

        assert "Invalid status 'PASSED'" in str(exc_info.value)

    def test_grade_problem_custom_review_frequency(self):
        """Test grading with custom review frequency from config."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '14'
        service = GradingService(db=mock_db)

        result = service.grade_problem(problem_id=1, status="passed")

        assert result.review_frequency_days == 14
        mock_db.get_config.assert_called_once_with('review_frequency_days', '7')

    def test_grade_problem_default_review_frequency(self):
        """Test that default review frequency is 7 days."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'
        service = GradingService(db=mock_db)

        result = service.grade_problem(problem_id=1, status="failed")

        assert result.review_frequency_days == 7
        mock_db.get_config.assert_called_once_with('review_frequency_days', '7')

    def test_grade_problem_does_not_schedule_review_for_failed(self):
        """Test that failed problems do not schedule a review."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'
        service = GradingService(db=mock_db)

        result = service.grade_problem(problem_id=1, status="failed")

        assert result.scheduled_review is False
        mock_db.schedule_review.assert_not_called()

    def test_grade_problem_does_not_schedule_review_for_skipped(self):
        """Test that skipped problems do not schedule a review."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'
        service = GradingService(db=mock_db)

        result = service.grade_problem(problem_id=1, status="skipped")

        assert result.scheduled_review is False
        mock_db.schedule_review.assert_not_called()

    def test_grade_problem_with_large_problem_id(self):
        """Test grading with a large problem ID."""
        mock_db = MagicMock()
        mock_db.get_config.return_value = '7'
        service = GradingService(db=mock_db)

        result = service.grade_problem(problem_id=99999, status="passed")

        assert result.success is True
        mock_db.update_test_status.assert_called_once_with(99999, "passed", None)
        mock_db.schedule_review.assert_called_once_with(99999)


class TestGradingServiceGetUngradedProblems:
    """Test GradingService.get_ungraded_problems method."""

    def test_get_ungraded_problems(self):
        """Test getting ungraded problems."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = [
            {"id": 1, "title": "Two Sum", "status": "ungraded"},
            {"id": 2, "title": "Add Two Numbers", "status": "ungraded"}
        ]
        service = GradingService(db=mock_db)

        result = service.get_ungraded_problems()

        assert len(result) == 2
        assert result[0]["title"] == "Two Sum"
        assert result[1]["title"] == "Add Two Numbers"
        mock_db.get_problems_by_status.assert_called_once_with("ungraded")

    def test_get_ungraded_problems_empty(self):
        """Test getting ungraded problems when none exist."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = []
        service = GradingService(db=mock_db)

        result = service.get_ungraded_problems()

        assert result == []
        mock_db.get_problems_by_status.assert_called_once_with("ungraded")

    def test_get_ungraded_problems_single(self):
        """Test getting a single ungraded problem."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = [
            {"id": 1, "title": "Two Sum", "status": "ungraded"}
        ]
        service = GradingService(db=mock_db)

        result = service.get_ungraded_problems()

        assert len(result) == 1
        assert result[0]["id"] == 1


class TestGradingServiceGetProblemsByStatus:
    """Test GradingService.get_problems_by_status method."""

    def test_get_problems_by_status_passed(self):
        """Test getting problems with passed status."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = [
            {"id": 1, "title": "Two Sum", "status": "passed"},
            {"id": 3, "title": "Longest Substring", "status": "passed"}
        ]
        service = GradingService(db=mock_db)

        result = service.get_problems_by_status("passed")

        assert len(result) == 2
        mock_db.get_problems_by_status.assert_called_once_with("passed")

    def test_get_problems_by_status_failed(self):
        """Test getting problems with failed status."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = [
            {"id": 2, "title": "Add Two Numbers", "status": "failed"}
        ]
        service = GradingService(db=mock_db)

        result = service.get_problems_by_status("failed")

        assert len(result) == 1
        assert result[0]["status"] == "failed"
        mock_db.get_problems_by_status.assert_called_once_with("failed")

    def test_get_problems_by_status_skipped(self):
        """Test getting problems with skipped status."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = [
            {"id": 4, "title": "Median of Two Sorted Arrays", "status": "skipped"}
        ]
        service = GradingService(db=mock_db)

        result = service.get_problems_by_status("skipped")

        assert len(result) == 1
        mock_db.get_problems_by_status.assert_called_once_with("skipped")

    def test_get_problems_by_status_ungraded(self):
        """Test getting problems with ungraded status."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = [
            {"id": 5, "title": "Longest Palindromic Substring", "status": "ungraded"}
        ]
        service = GradingService(db=mock_db)

        result = service.get_problems_by_status("ungraded")

        assert len(result) == 1
        mock_db.get_problems_by_status.assert_called_once_with("ungraded")

    def test_get_problems_by_status_empty(self):
        """Test getting problems when none match the status."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = []
        service = GradingService(db=mock_db)

        result = service.get_problems_by_status("passed")

        assert result == []
        mock_db.get_problems_by_status.assert_called_once_with("passed")

    def test_get_problems_by_status_returns_list_type(self):
        """Test that get_problems_by_status returns a list."""
        mock_db = MagicMock()
        mock_db.get_problems_by_status.return_value = []
        service = GradingService(db=mock_db)

        result = service.get_problems_by_status("passed")

        assert isinstance(result, list)
