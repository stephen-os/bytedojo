"""
Tests for LeetCodeClient query functionality.
"""

import pytest
import requests
from unittest.mock import Mock, patch
import click

from bytedojo.core.client import LeetCodeClient
from bytedojo.core.models import ProblemSummary


class TestQueryProblems:
    """Test query_problems method."""

    @patch('bytedojo.core.client.requests.Session')
    def test_query_problems_returns_list(self, mock_session_class):
        """Test that query_problems returns a list of ProblemSummary."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock problemset response
        problemset_response = Mock()
        problemset_response.json.return_value = {
            'stat_status_pairs': [
                {
                    'stat': {
                        'question_id': 1,
                        'question__title': 'Two Sum',
                        'question__title_slug': 'two-sum'
                    },
                    'difficulty': {'level': 1},
                    'paid_only': False
                }
            ]
        }

        # Mock tags response
        tags_response = Mock()
        tags_response.json.return_value = {
            'data': {
                'problemsetQuestionList': {
                    'questions': [
                        {
                            'questionFrontendId': '1',
                            'topicTags': [{'name': 'Array', 'slug': 'array'}]
                        }
                    ]
                }
            }
        }

        mock_session.get.return_value = problemset_response
        mock_session.post.return_value = tags_response

        client = LeetCodeClient()
        results = client.query_problems()

        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], ProblemSummary)
        assert results[0].id == 1
        assert results[0].title == 'Two Sum'

    @patch('bytedojo.core.client.requests.Session')
    def test_query_problems_sorted_by_id(self, mock_session_class):
        """Test that results are sorted by ID ascending."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Problems in reverse order
        problemset_response = Mock()
        problemset_response.json.return_value = {
            'stat_status_pairs': [
                {
                    'stat': {'question_id': 100, 'question__title': 'Problem 100', 'question__title_slug': 'p100'},
                    'difficulty': {'level': 1},
                    'paid_only': False
                },
                {
                    'stat': {'question_id': 1, 'question__title': 'Problem 1', 'question__title_slug': 'p1'},
                    'difficulty': {'level': 1},
                    'paid_only': False
                },
                {
                    'stat': {'question_id': 50, 'question__title': 'Problem 50', 'question__title_slug': 'p50'},
                    'difficulty': {'level': 1},
                    'paid_only': False
                }
            ]
        }

        tags_response = Mock()
        tags_response.json.return_value = {'data': {'problemsetQuestionList': {'questions': []}}}

        mock_session.get.return_value = problemset_response
        mock_session.post.return_value = tags_response

        client = LeetCodeClient()
        results = client.query_problems()

        assert len(results) == 3
        assert results[0].id == 1
        assert results[1].id == 50
        assert results[2].id == 100

    @patch('bytedojo.core.client.requests.Session')
    def test_query_problems_filter_by_difficulty(self, mock_session_class):
        """Test filtering by difficulty."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock problemset with multiple difficulties
        problemset_response = Mock()
        problemset_response.json.return_value = {
            'stat_status_pairs': [
                {
                    'stat': {'question_id': 1, 'question__title': 'Easy Problem', 'question__title_slug': 'easy'},
                    'difficulty': {'level': 1},
                    'paid_only': False
                },
                {
                    'stat': {'question_id': 2, 'question__title': 'Medium Problem', 'question__title_slug': 'medium'},
                    'difficulty': {'level': 2},
                    'paid_only': False
                },
                {
                    'stat': {'question_id': 3, 'question__title': 'Hard Problem', 'question__title_slug': 'hard'},
                    'difficulty': {'level': 3},
                    'paid_only': False
                }
            ]
        }

        tags_response = Mock()
        tags_response.json.return_value = {'data': {'problemsetQuestionList': {'questions': []}}}

        mock_session.get.return_value = problemset_response
        mock_session.post.return_value = tags_response

        client = LeetCodeClient()

        # Filter for easy (level 1)
        easy_results = client.query_problems(difficulty=1)
        assert len(easy_results) == 1
        assert easy_results[0].difficulty == 'Easy'

        # Filter for medium (level 2)
        medium_results = client.query_problems(difficulty=2)
        assert len(medium_results) == 1
        assert medium_results[0].difficulty == 'Medium'

        # Filter for hard (level 3)
        hard_results = client.query_problems(difficulty=3)
        assert len(hard_results) == 1
        assert hard_results[0].difficulty == 'Hard'

    @patch('bytedojo.core.client.requests.Session')
    def test_query_problems_filter_by_tag(self, mock_session_class):
        """Test filtering by tag."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        problemset_response = Mock()
        problemset_response.json.return_value = {
            'stat_status_pairs': [
                {
                    'stat': {'question_id': 1, 'question__title': 'Array Problem', 'question__title_slug': 'array-problem'},
                    'difficulty': {'level': 1},
                    'paid_only': False
                },
                {
                    'stat': {'question_id': 2, 'question__title': 'Tree Problem', 'question__title_slug': 'tree-problem'},
                    'difficulty': {'level': 2},
                    'paid_only': False
                }
            ]
        }

        tags_response = Mock()
        tags_response.json.return_value = {
            'data': {
                'problemsetQuestionList': {
                    'questions': [
                        {'questionFrontendId': '1', 'topicTags': [{'name': 'Array', 'slug': 'array'}]},
                        {'questionFrontendId': '2', 'topicTags': [{'name': 'Tree', 'slug': 'tree'}]}
                    ]
                }
            }
        }

        mock_session.get.return_value = problemset_response
        mock_session.post.return_value = tags_response

        client = LeetCodeClient()

        # Filter by array tag
        array_results = client.query_problems(tags=['array'])
        assert len(array_results) == 1
        assert array_results[0].title == 'Array Problem'

        # Filter by tree tag
        tree_results = client.query_problems(tags=['tree'])
        assert len(tree_results) == 1
        assert tree_results[0].title == 'Tree Problem'

    @patch('bytedojo.core.client.requests.Session')
    def test_query_problems_returns_all_matches(self, mock_session_class):
        """Test that all matching problems are returned (no internal limit)."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Create many problems
        problems = [
            {
                'stat': {'question_id': i, 'question__title': f'Problem {i}', 'question__title_slug': f'problem-{i}'},
                'difficulty': {'level': 1},
                'paid_only': False
            }
            for i in range(1, 101)
        ]

        problemset_response = Mock()
        problemset_response.json.return_value = {'stat_status_pairs': problems}

        tags_response = Mock()
        tags_response.json.return_value = {'data': {'problemsetQuestionList': {'questions': []}}}

        mock_session.get.return_value = problemset_response
        mock_session.post.return_value = tags_response

        client = LeetCodeClient()
        results = client.query_problems()

        # Should return all 100 problems
        assert len(results) == 100

    @patch('bytedojo.core.client.requests.Session')
    def test_query_problems_empty_results(self, mock_session_class):
        """Test query with no matching results."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        problemset_response = Mock()
        problemset_response.json.return_value = {'stat_status_pairs': []}

        tags_response = Mock()
        tags_response.json.return_value = {'data': {'problemsetQuestionList': {'questions': []}}}

        mock_session.get.return_value = problemset_response
        mock_session.post.return_value = tags_response

        client = LeetCodeClient()
        results = client.query_problems()

        assert results == []

    @patch('bytedojo.core.client.requests.Session')
    def test_query_problems_network_error(self, mock_session_class):
        """Test network error handling."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_session.get.side_effect = requests.RequestException("Network error")

        client = LeetCodeClient()

        with pytest.raises(click.ClickException) as exc_info:
            client.query_problems()

        assert "Failed to query problems" in str(exc_info.value)

    @patch('bytedojo.core.client.requests.Session')
    def test_query_problems_includes_paid_only(self, mock_session_class):
        """Test that paid_only flag is correctly captured."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        problemset_response = Mock()
        problemset_response.json.return_value = {
            'stat_status_pairs': [
                {
                    'stat': {'question_id': 1, 'question__title': 'Free Problem', 'question__title_slug': 'free'},
                    'difficulty': {'level': 1},
                    'paid_only': False
                },
                {
                    'stat': {'question_id': 2, 'question__title': 'Premium Problem', 'question__title_slug': 'premium'},
                    'difficulty': {'level': 2},
                    'paid_only': True
                }
            ]
        }

        tags_response = Mock()
        tags_response.json.return_value = {'data': {'problemsetQuestionList': {'questions': []}}}

        mock_session.get.return_value = problemset_response
        mock_session.post.return_value = tags_response

        client = LeetCodeClient()
        results = client.query_problems()

        assert results[0].paid_only is False
        assert results[1].paid_only is True


class TestFetchAllProblems:
    """Test _fetch_all_problems method."""

    @patch('bytedojo.core.client.requests.Session')
    def test_fetch_all_problems_returns_list(self, mock_session_class):
        """Test that _fetch_all_problems returns stat_status_pairs."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        expected_problems = [{'stat': {'question_id': 1}}]
        response = Mock()
        response.json.return_value = {'stat_status_pairs': expected_problems}
        mock_session.get.return_value = response

        client = LeetCodeClient()
        result = client._fetch_all_problems()

        assert result == expected_problems

    @patch('bytedojo.core.client.requests.Session')
    def test_fetch_all_problems_empty(self, mock_session_class):
        """Test handling of empty response."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {}
        mock_session.get.return_value = response

        client = LeetCodeClient()
        result = client._fetch_all_problems()

        assert result == []


class TestFetchProblemTags:
    """Test _fetch_problem_tags method."""

    @patch('bytedojo.core.client.requests.Session')
    def test_fetch_problem_tags_returns_dict(self, mock_session_class):
        """Test that _fetch_problem_tags returns tag mapping."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'data': {
                'problemsetQuestionList': {
                    'questions': [
                        {
                            'questionFrontendId': '1',
                            'topicTags': [
                                {'name': 'Array', 'slug': 'array'},
                                {'name': 'Hash Table', 'slug': 'hash-table'}
                            ]
                        }
                    ]
                }
            }
        }
        mock_session.post.return_value = response

        client = LeetCodeClient()
        result = client._fetch_problem_tags()

        assert 1 in result
        assert 'Array' in result[1]
        assert 'Hash Table' in result[1]

    @patch('bytedojo.core.client.requests.Session')
    def test_fetch_problem_tags_handles_error(self, mock_session_class):
        """Test that errors are handled gracefully."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_session.post.side_effect = Exception("API Error")

        client = LeetCodeClient()
        result = client._fetch_problem_tags()

        assert result == {}


class TestGetAvailableTags:
    """Test get_available_tags method."""

    @patch('bytedojo.core.client.requests.Session')
    def test_get_available_tags_returns_sorted_list(self, mock_session_class):
        """Test that get_available_tags returns sorted unique tags."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'data': {
                'problemsetQuestionList': {
                    'questions': [
                        {'questionFrontendId': '1', 'topicTags': [{'name': 'Array', 'slug': 'array'}]},
                        {'questionFrontendId': '2', 'topicTags': [{'name': 'Tree', 'slug': 'tree'}, {'name': 'Array', 'slug': 'array'}]}
                    ]
                }
            }
        }
        mock_session.post.return_value = response

        client = LeetCodeClient()
        result = client.get_available_tags()

        assert result == ['Array', 'Tree']

    @patch('bytedojo.core.client.requests.Session')
    def test_get_available_tags_handles_error(self, mock_session_class):
        """Test that errors return empty list."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_session.post.side_effect = Exception("Error")

        client = LeetCodeClient()
        result = client.get_available_tags()

        assert result == []


class TestProblemSummaryModel:
    """Test ProblemSummary dataclass."""

    def test_problem_summary_creation(self):
        """Test creating a ProblemSummary."""
        summary = ProblemSummary(
            id=1,
            title='Two Sum',
            title_slug='two-sum',
            difficulty='Easy',
            paid_only=False,
            tags=['Array', 'Hash Table']
        )

        assert summary.id == 1
        assert summary.title == 'Two Sum'
        assert summary.title_slug == 'two-sum'
        assert summary.difficulty == 'Easy'
        assert summary.paid_only is False
        assert summary.tags == ['Array', 'Hash Table']
