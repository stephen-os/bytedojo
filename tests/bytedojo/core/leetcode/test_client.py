"""
Tests for LeetCodeClient.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
import click

from bytedojo.core.leetcode.client import LeetCodeClient
from bytedojo.core.leetcode.models import Problem, CodeSnippet


class TestLeetCodeClientInit:
    """Test LeetCodeClient initialization."""
    
    def test_init_creates_session(self):
        """Test that initialization creates a requests session."""
        client = LeetCodeClient()
        
        assert hasattr(client, 'session')
        assert isinstance(client.session, requests.Session)
    
    def test_init_sets_headers(self):
        """Test that initialization sets correct headers."""
        client = LeetCodeClient()
        
        assert 'Content-Type' in client.session.headers
        assert client.session.headers['Content-Type'] == 'application/json'
        assert 'User-Agent' in client.session.headers
    
    def test_init_has_logger(self):
        """Test that client has a logger."""
        client = LeetCodeClient()
        
        assert hasattr(client, 'logger')
        assert client.logger is not None
    
    def test_class_has_constants(self):
        """Test that class has URL constants."""
        assert hasattr(LeetCodeClient, 'GRAPHQL_URL')
        assert hasattr(LeetCodeClient, 'PROBLEMSET_URL')
        assert hasattr(LeetCodeClient, 'QUERY')
        
        assert 'leetcode.com' in LeetCodeClient.GRAPHQL_URL
        assert 'leetcode.com' in LeetCodeClient.PROBLEMSET_URL


class TestGetProblemById:
    """Test get_problem_by_id method."""
    
    def test_get_problem_by_id_returns_none_for_zero(self):
        """Test that problem_id=0 returns None."""
        client = LeetCodeClient()
        result = client.get_problem_by_id(0)
        
        assert result is None
    
    def test_get_problem_by_id_returns_none_for_none(self):
        """Test that problem_id=None returns None."""
        client = LeetCodeClient()
        result = client.get_problem_by_id(None)
        
        assert result is None
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_get_problem_by_id_success(self, mock_session_class):
        """Test successful problem fetch by ID."""
        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock problem list response
        list_response = Mock()
        list_response.json.return_value = {
            'stat_status_pairs': [
                {'stat': {'question_id': 1, 'question__title_slug': 'two-sum'}}
            ]
        }
        
        # Mock GraphQL response
        graphql_response = Mock()
        graphql_response.json.return_value = {
            'data': {
                'question': {
                    'questionId': '1',
                    'title': 'Two Sum',
                    'titleSlug': 'two-sum',
                    'difficulty': 'Easy',
                    'content': '<p>Description</p>',
                    'exampleTestcases': '[2,7]\n9',
                    'codeSnippets': [
                        {'lang': 'Python3', 'code': 'class Solution: pass'}
                    ]
                }
            }
        }
        
        # Setup mock to return different responses for GET and POST
        mock_session.get.return_value = list_response
        mock_session.post.return_value = graphql_response
        
        client = LeetCodeClient()
        problem = client.get_problem_by_id(1)
        
        assert problem is not None
        assert isinstance(problem, Problem)
        assert problem.id == 1
        assert problem.title == 'Two Sum'
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_get_problem_by_id_not_found(self, mock_session_class):
        """Test problem not found by ID."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock empty problem list
        list_response = Mock()
        list_response.json.return_value = {
            'stat_status_pairs': []
        }
        mock_session.get.return_value = list_response
        
        client = LeetCodeClient()
        problem = client.get_problem_by_id(9999)
        
        assert problem is None
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_get_problem_by_id_network_error(self, mock_session_class):
        """Test network error handling."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock network error
        mock_session.get.side_effect = requests.RequestException("Network error")
        
        client = LeetCodeClient()
        
        with pytest.raises(click.ClickException) as exc_info:
            client.get_problem_by_id(1)
        
        assert "Failed to fetch problem 1" in str(exc_info.value)


class TestGetProblemByName:
    """Test get_problem_by_name method."""
    
    def test_get_problem_by_name_returns_none_for_empty(self):
        """Test that empty name returns None."""
        client = LeetCodeClient()
        result = client.get_problem_by_name("")
        
        assert result is None
    
    def test_get_problem_by_name_returns_none_for_none(self):
        """Test that None name returns None."""
        client = LeetCodeClient()
        result = client.get_problem_by_name(None)
        
        assert result is None
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_get_problem_by_name_success(self, mock_session_class):
        """Test successful problem fetch by name."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock GraphQL response
        graphql_response = Mock()
        graphql_response.json.return_value = {
            'data': {
                'question': {
                    'questionId': '1',
                    'title': 'Two Sum',
                    'titleSlug': 'two-sum',
                    'difficulty': 'Easy',
                    'content': '<p>Description</p>',
                    'exampleTestcases': '',
                    'codeSnippets': []
                }
            }
        }
        mock_session.post.return_value = graphql_response
        
        client = LeetCodeClient()
        problem = client.get_problem_by_name("two sum")
        
        assert problem is not None
        assert problem.title == 'Two Sum'
    
    def test_get_problem_by_name_converts_to_slug(self):
        """Test that name is converted to slug format."""
        client = LeetCodeClient()
        
        # Mock _fetch_problem to check what slug is passed
        with patch.object(client, '_fetch_problem') as mock_fetch:
            mock_fetch.return_value = None
            
            client.get_problem_by_name("Two Sum")
            
            # Should convert to lowercase with hyphens
            mock_fetch.assert_called_once_with('two-sum')
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_get_problem_by_name_network_error(self, mock_session_class):
        """Test network error handling for name lookup."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_session.post.side_effect = requests.RequestException("Network error")
        
        client = LeetCodeClient()
        
        with pytest.raises(click.ClickException):
            client.get_problem_by_name("two sum")


class TestFetchProblem:
    """Test _fetch_problem internal method."""
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_fetch_problem_creates_problem_object(self, mock_session_class):
        """Test that _fetch_problem creates a Problem object."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        graphql_response = Mock()
        graphql_response.json.return_value = {
            'data': {
                'question': {
                    'questionId': '1',
                    'title': 'Two Sum',
                    'titleSlug': 'two-sum',
                    'difficulty': 'Easy',
                    'content': '<p>Test</p>',
                    'exampleTestcases': 'test',
                    'codeSnippets': [
                        {'lang': 'Python3', 'code': 'code1'},
                        {'lang': 'Java', 'code': 'code2'}
                    ]
                }
            }
        }
        mock_session.post.return_value = graphql_response
        
        client = LeetCodeClient()
        problem = client._fetch_problem('two-sum')
        
        assert isinstance(problem, Problem)
        assert problem.id == 1
        assert problem.title == 'Two Sum'
        assert len(problem.code_snippets) == 2
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_fetch_problem_returns_none_for_no_data(self, mock_session_class):
        """Test that _fetch_problem returns None when no data."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        graphql_response = Mock()
        graphql_response.json.return_value = {'data': {}}
        mock_session.post.return_value = graphql_response
        
        client = LeetCodeClient()
        problem = client._fetch_problem('nonexistent')
        
        assert problem is None


class TestFetchRawData:
    """Test _fetch_raw_data internal method."""
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_fetch_raw_data_makes_graphql_request(self, mock_session_class):
        """Test that _fetch_raw_data makes GraphQL request."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        response = Mock()
        response.json.return_value = {
            'data': {
                'question': {'questionId': '1'}
            }
        }
        mock_session.post.return_value = response
        
        client = LeetCodeClient()
        result = client._fetch_raw_data('test-slug')
        
        # Should call POST with GraphQL query
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        
        assert LeetCodeClient.GRAPHQL_URL in call_args[0]
        assert 'json' in call_args[1]
        assert 'query' in call_args[1]['json']
        assert 'variables' in call_args[1]['json']
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_fetch_raw_data_returns_question_data(self, mock_session_class):
        """Test that _fetch_raw_data returns question data."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        expected_data = {
            'questionId': '1',
            'title': 'Test',
            'titleSlug': 'test'
        }
        
        response = Mock()
        response.json.return_value = {
            'data': {
                'question': expected_data
            }
        }
        mock_session.post.return_value = response
        
        client = LeetCodeClient()
        result = client._fetch_raw_data('test')
        
        assert result == expected_data
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_fetch_raw_data_returns_none_for_invalid(self, mock_session_class):
        """Test that _fetch_raw_data returns None for invalid response."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        response = Mock()
        response.json.return_value = {'error': 'not found'}
        mock_session.post.return_value = response
        
        client = LeetCodeClient()
        result = client._fetch_raw_data('invalid')
        
        assert result is None


class TestGetTitleSlugById:
    """Test _get_title_slug_by_id internal method."""
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_get_title_slug_by_id_success(self, mock_session_class):
        """Test successful slug lookup."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        response = Mock()
        response.json.return_value = {
            'stat_status_pairs': [
                {'stat': {'question_id': 1, 'question__title_slug': 'two-sum'}},
                {'stat': {'question_id': 2, 'question__title_slug': 'add-two-numbers'}}
            ]
        }
        mock_session.get.return_value = response
        
        client = LeetCodeClient()
        slug = client._get_title_slug_by_id(1)
        
        assert slug == 'two-sum'
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_get_title_slug_by_id_not_found(self, mock_session_class):
        """Test slug lookup for non-existent ID."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        response = Mock()
        response.json.return_value = {
            'stat_status_pairs': [
                {'stat': {'question_id': 1, 'question__title_slug': 'two-sum'}}
            ]
        }
        mock_session.get.return_value = response
        
        client = LeetCodeClient()
        slug = client._get_title_slug_by_id(999)
        
        assert slug is None
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_get_title_slug_missing_stat_status_pairs(self, mock_session_class):
        """Test handling of malformed API response."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        response = Mock()
        response.json.return_value = {}
        mock_session.get.return_value = response
        
        client = LeetCodeClient()
        slug = client._get_title_slug_by_id(1)
        
        assert slug is None


class TestLeetCodeClientIntegration:
    """Integration tests for LeetCodeClient."""
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_full_fetch_workflow_by_id(self, mock_session_class):
        """Test complete workflow: ID -> slug -> problem."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock problem list
        list_response = Mock()
        list_response.json.return_value = {
            'stat_status_pairs': [
                {'stat': {'question_id': 42, 'question__title_slug': 'test-problem'}}
            ]
        }
        
        # Mock GraphQL
        graphql_response = Mock()
        graphql_response.json.return_value = {
            'data': {
                'question': {
                    'questionId': '42',
                    'title': 'Test Problem',
                    'titleSlug': 'test-problem',
                    'difficulty': 'Medium',
                    'content': 'Description',
                    'exampleTestcases': 'tests',
                    'codeSnippets': []
                }
            }
        }
        
        mock_session.get.return_value = list_response
        mock_session.post.return_value = graphql_response
        
        client = LeetCodeClient()
        problem = client.get_problem_by_id(42)
        
        assert problem.id == 42
        assert problem.title == 'Test Problem'
        assert problem.difficulty == 'Medium'
    
    @patch('bytedojo.core.leetcode.client.requests.Session')
    def test_multiple_fetches_same_client(self, mock_session_class):
        """Test multiple fetches with same client instance."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock responses for multiple problems
        def get_side_effect(*args, **kwargs):
            response = Mock()
            response.json.return_value = {
                'stat_status_pairs': [
                    {'stat': {'question_id': 1, 'question__title_slug': 'one'}},
                    {'stat': {'question_id': 2, 'question__title_slug': 'two'}}
                ]
            }
            return response
        
        def post_side_effect(*args, **kwargs):
            response = Mock()
            slug = kwargs['json']['variables']['titleSlug']
            response.json.return_value = {
                'data': {
                    'question': {
                        'questionId': '1' if slug == 'one' else '2',
                        'title': slug.title(),
                        'titleSlug': slug,
                        'difficulty': 'Easy',
                        'content': '',
                        'exampleTestcases': '',
                        'codeSnippets': []
                    }
                }
            }
            return response
        
        mock_session.get.side_effect = get_side_effect
        mock_session.post.side_effect = post_side_effect
        
        client = LeetCodeClient()
        
        problem1 = client.get_problem_by_id(1)
        problem2 = client.get_problem_by_id(2)
        
        assert problem1.id == 1
        assert problem2.id == 2