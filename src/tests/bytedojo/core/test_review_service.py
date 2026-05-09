"""
Tests for review_service module.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from bytedojo.core.review_service import (
    ReviewService,
    ReviewStats,
    ReviewProblem,
)


class TestReviewStats:
    """Test ReviewStats dataclass."""

    def test_review_stats_creation(self):
        """Test creating ReviewStats with all fields."""
        stats = ReviewStats(
            due_today=5,
            due_this_week=10,
            total_in_review=25,
            most_reviewed=[{"title": "Two Sum", "count": 10}],
            review_frequency_days=7
        )

        assert stats.due_today == 5
        assert stats.due_this_week == 10
        assert stats.total_in_review == 25
        assert len(stats.most_reviewed) == 1
        assert stats.most_reviewed[0]["title"] == "Two Sum"
        assert stats.review_frequency_days == 7

    def test_review_stats_empty_most_reviewed(self):
        """Test ReviewStats with empty most_reviewed list."""
        stats = ReviewStats(
            due_today=0,
            due_this_week=0,
            total_in_review=0,
            most_reviewed=[],
            review_frequency_days=7
        )

        assert stats.most_reviewed == []


class TestReviewProblem:
    """Test ReviewProblem dataclass."""

    def test_review_problem_creation(self):
        """Test creating ReviewProblem with all fields."""
        problem = ReviewProblem(
            id=1,
            problem_id="1",
            source="leetcode",
            title="Two Sum",
            difficulty="Easy",
            language="python",
            file_path="/path/to/file.py",
            next_review_date="2025-01-15",
            repetitions=3,
            days_until_due=5,
            is_overdue=False,
            is_due_today=False,
            url="https://leetcode.com/problems/two-sum/"
        )

        assert problem.id == 1
        assert problem.problem_id == "1"
        assert problem.source == "leetcode"
        assert problem.title == "Two Sum"
        assert problem.difficulty == "Easy"
        assert problem.language == "python"
        assert problem.file_path == "/path/to/file.py"
        assert problem.next_review_date == "2025-01-15"
        assert problem.repetitions == 3
        assert problem.days_until_due == 5
        assert problem.is_overdue is False
        assert problem.is_due_today is False
        assert problem.url == "https://leetcode.com/problems/two-sum/"

    def test_review_problem_url_optional(self):
        """Test ReviewProblem with url defaulting to None."""
        problem = ReviewProblem(
            id=1,
            problem_id="1",
            source="unknown",
            title="Test",
            difficulty="Easy",
            language="python",
            file_path="/path/to/file.py",
            next_review_date="2025-01-15",
            repetitions=0,
            days_until_due=0,
            is_overdue=False,
            is_due_today=True
        )

        assert problem.url is None

    def test_review_problem_overdue_state(self):
        """Test ReviewProblem with overdue state."""
        problem = ReviewProblem(
            id=1,
            problem_id="1",
            source="leetcode",
            title="Test",
            difficulty="Medium",
            language="python",
            file_path="/path/to/file.py",
            next_review_date="2025-01-01",
            repetitions=5,
            days_until_due=-10,
            is_overdue=True,
            is_due_today=False
        )

        assert problem.is_overdue is True
        assert problem.days_until_due == -10


class TestReviewService:
    """Test ReviewService class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a ReviewService instance with mock db."""
        return ReviewService(mock_db)

    def test_init(self, mock_db):
        """Test ReviewService initialization."""
        service = ReviewService(mock_db)
        assert service.db is mock_db


class TestGetDueReviews:
    """Test get_due_reviews method."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a ReviewService instance with mock db."""
        return ReviewService(mock_db)

    def test_get_due_reviews_empty(self, service, mock_db):
        """Test getting due reviews when none exist."""
        mock_db.get_due_reviews.return_value = []

        result = service.get_due_reviews()

        assert result == []
        mock_db.get_due_reviews.assert_called_once_with(include_future=False)

    def test_get_due_reviews_with_future(self, service, mock_db):
        """Test getting due reviews including future reviews."""
        mock_db.get_due_reviews.return_value = []

        service.get_due_reviews(include_future=True)

        mock_db.get_due_reviews.assert_called_once_with(include_future=True)

    def test_get_due_reviews_calculates_days_until_due(self, service, mock_db):
        """Test that days_until_due is calculated correctly."""
        today = date.today()
        future_date = today + timedelta(days=5)

        mock_db.get_due_reviews.return_value = [{
            'id': 1,
            'problem_id': '1',
            'source': 'leetcode',
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'language': 'python',
            'file_path': '/path/to/file.py',
            'next_review_date': future_date.isoformat(),
            'repetitions': 3
        }]

        result = service.get_due_reviews(include_future=True)

        assert len(result) == 1
        assert result[0].days_until_due == 5
        assert result[0].is_overdue is False
        assert result[0].is_due_today is False

    def test_get_due_reviews_overdue_problem(self, service, mock_db):
        """Test that overdue problems are correctly identified."""
        today = date.today()
        past_date = today - timedelta(days=3)

        mock_db.get_due_reviews.return_value = [{
            'id': 1,
            'problem_id': '1',
            'source': 'leetcode',
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'language': 'python',
            'file_path': '/path/to/file.py',
            'next_review_date': past_date.isoformat(),
            'repetitions': 2
        }]

        result = service.get_due_reviews()

        assert len(result) == 1
        assert result[0].days_until_due == -3
        assert result[0].is_overdue is True
        assert result[0].is_due_today is False

    def test_get_due_reviews_due_today(self, service, mock_db):
        """Test that problems due today are correctly identified."""
        today = date.today()

        mock_db.get_due_reviews.return_value = [{
            'id': 1,
            'problem_id': '1',
            'source': 'leetcode',
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'language': 'python',
            'file_path': '/path/to/file.py',
            'next_review_date': today.isoformat(),
            'repetitions': 1
        }]

        result = service.get_due_reviews()

        assert len(result) == 1
        assert result[0].days_until_due == 0
        assert result[0].is_overdue is False
        assert result[0].is_due_today is True

    def test_get_due_reviews_handles_missing_fields(self, service, mock_db):
        """Test that missing optional fields use defaults."""
        today = date.today()

        mock_db.get_due_reviews.return_value = [{
            'id': 1,
            'problem_id': '1',
            'source': 'unknown',
            'title': 'Test Problem',
            'next_review_date': today.isoformat(),
            'repetitions': 0
        }]

        result = service.get_due_reviews()

        assert len(result) == 1
        assert result[0].difficulty == 'Unknown'
        assert result[0].language == 'python'
        assert result[0].file_path == ''

    def test_get_due_reviews_generates_leetcode_url(self, service, mock_db):
        """Test that LeetCode URLs are generated correctly."""
        today = date.today()

        mock_db.get_due_reviews.return_value = [{
            'id': 1,
            'problem_id': '1',
            'source': 'leetcode',
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'language': 'python',
            'file_path': '/path/to/file.py',
            'next_review_date': today.isoformat(),
            'repetitions': 1
        }]

        result = service.get_due_reviews()

        assert result[0].url == "https://leetcode.com/problems/two-sum/"

    def test_get_due_reviews_multiple_problems(self, service, mock_db):
        """Test getting multiple due reviews."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        mock_db.get_due_reviews.return_value = [
            {
                'id': 1,
                'problem_id': '1',
                'source': 'leetcode',
                'title': 'Two Sum',
                'difficulty': 'Easy',
                'language': 'python',
                'file_path': '/path/1.py',
                'next_review_date': yesterday.isoformat(),
                'repetitions': 3
            },
            {
                'id': 2,
                'problem_id': '2',
                'source': 'leetcode',
                'title': 'Add Two Numbers',
                'difficulty': 'Medium',
                'language': 'python',
                'file_path': '/path/2.py',
                'next_review_date': today.isoformat(),
                'repetitions': 1
            },
            {
                'id': 3,
                'problem_id': '3',
                'source': 'leetcode',
                'title': 'Longest Substring',
                'difficulty': 'Medium',
                'language': 'python',
                'file_path': '/path/3.py',
                'next_review_date': tomorrow.isoformat(),
                'repetitions': 0
            }
        ]

        result = service.get_due_reviews(include_future=True)

        assert len(result) == 3
        assert result[0].is_overdue is True
        assert result[1].is_due_today is True
        assert result[2].is_overdue is False
        assert result[2].is_due_today is False


class TestGetDueCount:
    """Test get_due_count method."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a ReviewService instance with mock db."""
        return ReviewService(mock_db)

    def test_get_due_count_zero(self, service, mock_db):
        """Test due count when no reviews are due."""
        mock_db.get_due_reviews.return_value = []

        result = service.get_due_count()

        assert result == 0

    def test_get_due_count_multiple(self, service, mock_db):
        """Test due count with multiple due reviews."""
        today = date.today()

        mock_db.get_due_reviews.return_value = [
            {'id': 1, 'problem_id': '1', 'source': 'leetcode', 'title': 'P1',
             'next_review_date': today.isoformat(), 'repetitions': 1},
            {'id': 2, 'problem_id': '2', 'source': 'leetcode', 'title': 'P2',
             'next_review_date': today.isoformat(), 'repetitions': 2},
            {'id': 3, 'problem_id': '3', 'source': 'leetcode', 'title': 'P3',
             'next_review_date': today.isoformat(), 'repetitions': 3}
        ]

        result = service.get_due_count()

        assert result == 3


class TestPickRandomDue:
    """Test pick_random_due method."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a ReviewService instance with mock db."""
        return ReviewService(mock_db)

    def test_pick_random_due_none_available(self, service, mock_db):
        """Test picking random when no reviews are due."""
        mock_db.get_due_reviews.return_value = []

        result = service.pick_random_due()

        assert result is None

    def test_pick_random_due_single_review(self, service, mock_db):
        """Test picking random when only one review is due."""
        today = date.today()

        mock_db.get_due_reviews.return_value = [{
            'id': 1,
            'problem_id': '1',
            'source': 'leetcode',
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'language': 'python',
            'file_path': '/path/to/file.py',
            'next_review_date': today.isoformat(),
            'repetitions': 1
        }]

        result = service.pick_random_due()

        assert result is not None
        assert result.problem_id == '1'
        assert result.title == 'Two Sum'

    def test_pick_random_due_returns_review_problem(self, service, mock_db):
        """Test that pick_random_due returns a ReviewProblem instance."""
        today = date.today()

        mock_db.get_due_reviews.return_value = [{
            'id': 1,
            'problem_id': '1',
            'source': 'leetcode',
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'language': 'python',
            'file_path': '/path/to/file.py',
            'next_review_date': today.isoformat(),
            'repetitions': 1
        }]

        result = service.pick_random_due()

        assert isinstance(result, ReviewProblem)

    def test_pick_random_due_with_multiple(self, service, mock_db):
        """Test picking random from multiple due reviews."""
        today = date.today()

        mock_db.get_due_reviews.return_value = [
            {'id': 1, 'problem_id': '1', 'source': 'leetcode', 'title': 'P1',
             'next_review_date': today.isoformat(), 'repetitions': 1},
            {'id': 2, 'problem_id': '2', 'source': 'leetcode', 'title': 'P2',
             'next_review_date': today.isoformat(), 'repetitions': 2}
        ]

        with patch('bytedojo.core.review_service.random.choice') as mock_choice:
            mock_choice.return_value = ReviewProblem(
                id=2, problem_id='2', source='leetcode', title='P2',
                difficulty='Easy', language='python', file_path='/path',
                next_review_date=today.isoformat(), repetitions=2,
                days_until_due=0, is_overdue=False, is_due_today=True,
                url='https://leetcode.com/problems/p2/'
            )

            result = service.pick_random_due()

            assert mock_choice.called


class TestGetStats:
    """Test get_stats method."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a ReviewService instance with mock db."""
        return ReviewService(mock_db)

    def test_get_stats_returns_review_stats(self, service, mock_db):
        """Test that get_stats returns a ReviewStats object."""
        mock_db.get_review_stats.return_value = {
            'due_today': 5,
            'due_this_week': 10,
            'total_in_review': 25,
            'most_reviewed': []
        }
        mock_db.get_config.return_value = '7'

        result = service.get_stats()

        assert isinstance(result, ReviewStats)

    def test_get_stats_values(self, service, mock_db):
        """Test get_stats returns correct values."""
        most_reviewed = [
            {'title': 'Two Sum', 'count': 10},
            {'title': 'Add Two Numbers', 'count': 8}
        ]
        mock_db.get_review_stats.return_value = {
            'due_today': 3,
            'due_this_week': 15,
            'total_in_review': 50,
            'most_reviewed': most_reviewed
        }
        mock_db.get_config.return_value = '14'

        result = service.get_stats()

        assert result.due_today == 3
        assert result.due_this_week == 15
        assert result.total_in_review == 50
        assert result.most_reviewed == most_reviewed
        assert result.review_frequency_days == 14

    def test_get_stats_default_frequency(self, service, mock_db):
        """Test get_stats uses default frequency when not configured."""
        mock_db.get_review_stats.return_value = {
            'due_today': 0,
            'due_this_week': 0,
            'total_in_review': 0,
            'most_reviewed': []
        }
        mock_db.get_config.return_value = '7'

        result = service.get_stats()

        mock_db.get_config.assert_called_with('review_frequency_days', '7')
        assert result.review_frequency_days == 7


class TestGetReviewFrequency:
    """Test get_review_frequency method."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a ReviewService instance with mock db."""
        return ReviewService(mock_db)

    def test_get_review_frequency_default(self, service, mock_db):
        """Test getting default review frequency."""
        mock_db.get_config.return_value = '7'

        result = service.get_review_frequency()

        assert result == 7
        mock_db.get_config.assert_called_with('review_frequency_days', '7')

    def test_get_review_frequency_custom(self, service, mock_db):
        """Test getting custom review frequency."""
        mock_db.get_config.return_value = '14'

        result = service.get_review_frequency()

        assert result == 14

    def test_get_review_frequency_returns_int(self, service, mock_db):
        """Test that get_review_frequency returns an integer."""
        mock_db.get_config.return_value = '30'

        result = service.get_review_frequency()

        assert isinstance(result, int)
        assert result == 30


class TestGenerateUrl:
    """Test _generate_url method."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a ReviewService instance with mock db."""
        return ReviewService(mock_db)

    def test_generate_url_leetcode_simple(self, service):
        """Test generating LeetCode URL with simple title."""
        url = service._generate_url('leetcode', '1', 'Two Sum')

        assert url == 'https://leetcode.com/problems/two-sum/'

    def test_generate_url_leetcode_complex_title(self, service):
        """Test generating LeetCode URL with complex title."""
        url = service._generate_url('leetcode', '3', 'Longest Substring Without Repeating Characters')

        assert url == 'https://leetcode.com/problems/longest-substring-without-repeating-characters/'

    def test_generate_url_leetcode_special_characters(self, service):
        """Test generating LeetCode URL with special characters in title."""
        url = service._generate_url('leetcode', '10', "Regular Expression Matching")

        assert url == 'https://leetcode.com/problems/regular-expression-matching/'

    def test_generate_url_leetcode_numbers_in_title(self, service):
        """Test generating LeetCode URL with numbers in title."""
        url = service._generate_url('leetcode', '4', '3Sum')

        assert url == 'https://leetcode.com/problems/3sum/'

    def test_generate_url_codeforces_valid(self, service):
        """Test generating Codeforces URL with valid problem ID."""
        url = service._generate_url('codeforces', '1A', 'Theatre Square')

        assert url == 'https://codeforces.com/problemset/problem/1/A'

    def test_generate_url_codeforces_multi_digit_contest(self, service):
        """Test generating Codeforces URL with multi-digit contest ID."""
        url = service._generate_url('codeforces', '1234B', 'Some Problem')

        assert url == 'https://codeforces.com/problemset/problem/1234/B'

    def test_generate_url_codeforces_problem_with_number(self, service):
        """Test generating Codeforces URL with problem index containing number."""
        url = service._generate_url('codeforces', '100A1', 'Problem')

        assert url == 'https://codeforces.com/problemset/problem/100/A1'

    def test_generate_url_codeforces_invalid_format(self, service):
        """Test generating Codeforces URL with invalid problem ID format."""
        url = service._generate_url('codeforces', 'invalid', 'Problem')

        assert url is None

    def test_generate_url_unknown_source(self, service):
        """Test generating URL for unknown source."""
        url = service._generate_url('hackerrank', '123', 'Some Problem')

        assert url is None

    def test_generate_url_empty_source(self, service):
        """Test generating URL with empty source."""
        url = service._generate_url('', '1', 'Test')

        assert url is None


class TestFormatDueDate:
    """Test format_due_date static method."""

    def test_format_due_date_empty_string(self):
        """Test formatting empty date string."""
        result = ReviewService.format_due_date('')

        assert result == 'N/A'

    def test_format_due_date_none(self):
        """Test formatting None date."""
        result = ReviewService.format_due_date(None)

        assert result == 'N/A'

    def test_format_due_date_overdue(self):
        """Test formatting overdue date."""
        past_date = date.today() - timedelta(days=5)

        result = ReviewService.format_due_date(past_date.isoformat())

        assert result == '5 days overdue'

    def test_format_due_date_overdue_single_day(self):
        """Test formatting date overdue by one day."""
        past_date = date.today() - timedelta(days=1)

        result = ReviewService.format_due_date(past_date.isoformat())

        assert result == '1 days overdue'

    def test_format_due_date_today(self):
        """Test formatting today's date."""
        today = date.today()

        result = ReviewService.format_due_date(today.isoformat())

        assert result == 'Today'

    def test_format_due_date_tomorrow(self):
        """Test formatting tomorrow's date."""
        tomorrow = date.today() + timedelta(days=1)

        result = ReviewService.format_due_date(tomorrow.isoformat())

        assert result == 'Tomorrow'

    def test_format_due_date_within_week(self):
        """Test formatting date within a week."""
        future_date = date.today() + timedelta(days=5)

        result = ReviewService.format_due_date(future_date.isoformat())

        assert result == 'In 5 days'

    def test_format_due_date_exactly_one_week(self):
        """Test formatting date exactly one week away."""
        future_date = date.today() + timedelta(days=7)

        result = ReviewService.format_due_date(future_date.isoformat())

        assert result == future_date.strftime("%Y-%m-%d")

    def test_format_due_date_far_future(self):
        """Test formatting date far in the future."""
        future_date = date.today() + timedelta(days=30)

        result = ReviewService.format_due_date(future_date.isoformat())

        assert result == future_date.strftime("%Y-%m-%d")

    def test_format_due_date_invalid_format(self):
        """Test formatting invalid date string."""
        result = ReviewService.format_due_date('not-a-date')

        assert result == 'not-a-date'

    def test_format_due_date_with_datetime(self):
        """Test formatting datetime string (with time component)."""
        today = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

        result = ReviewService.format_due_date(today.isoformat())

        assert result == 'Today'

    def test_format_due_date_two_days_future(self):
        """Test formatting date 2 days in future."""
        future_date = date.today() + timedelta(days=2)

        result = ReviewService.format_due_date(future_date.isoformat())

        assert result == 'In 2 days'

    def test_format_due_date_six_days_future(self):
        """Test formatting date 6 days in future (boundary case)."""
        future_date = date.today() + timedelta(days=6)

        result = ReviewService.format_due_date(future_date.isoformat())

        assert result == 'In 6 days'
