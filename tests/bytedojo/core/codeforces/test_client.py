"""
Tests for CodeforcesClient.
"""

import pytest
import requests
from unittest.mock import Mock, patch
import click

from bytedojo.core.codeforces.client import CodeforcesClient
from bytedojo.core.codeforces.models import Problem, ProblemSummary


class TestCodeforcesClientInit:
    """Test CodeforcesClient initialization."""

    def test_init_creates_session(self):
        """Test that initialization creates a requests session."""
        client = CodeforcesClient()
        assert hasattr(client, 'session')
        assert isinstance(client.session, requests.Session)

    def test_init_sets_user_agent(self):
        """Test that initialization sets User-Agent header."""
        client = CodeforcesClient()
        assert 'User-Agent' in client.session.headers

    def test_init_has_logger(self):
        """Test that client has a logger."""
        client = CodeforcesClient()
        assert hasattr(client, 'logger')

    def test_class_has_constants(self):
        """Test that class has URL constants."""
        assert hasattr(CodeforcesClient, 'API_URL')
        assert hasattr(CodeforcesClient, 'PROBLEM_URL')
        assert 'codeforces.com' in CodeforcesClient.API_URL

    def test_init_has_problems_cache(self):
        """Test that client has problems cache."""
        client = CodeforcesClient()
        assert hasattr(client, '_problems_cache')
        assert client._problems_cache is None


class TestGetProblemById:
    """Test get_problem_by_id method."""

    def test_get_problem_by_id_invalid_format(self):
        """Test that invalid format returns None."""
        client = CodeforcesClient()
        result = client.get_problem_by_id('invalid')
        assert result is None

    def test_get_problem_by_id_empty_string(self):
        """Test that empty string returns None."""
        client = CodeforcesClient()
        result = client.get_problem_by_id('')
        assert result is None

    def test_get_problem_by_id_parses_correctly(self):
        """Test that problem ID is parsed correctly."""
        client = CodeforcesClient()

        with patch.object(client, 'get_problem') as mock_get:
            mock_get.return_value = None
            client.get_problem_by_id('1A')
            mock_get.assert_called_once_with(1, 'A')

    def test_get_problem_by_id_handles_multi_digit(self):
        """Test that multi-digit contest IDs are parsed."""
        client = CodeforcesClient()

        with patch.object(client, 'get_problem') as mock_get:
            mock_get.return_value = None
            client.get_problem_by_id('1850B')
            mock_get.assert_called_once_with(1850, 'B')


class TestQueryProblems:
    """Test query_problems method."""

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_query_problems_returns_list(self, mock_session_class):
        """Test that query_problems returns a list."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 1, 'index': 'A', 'name': 'Test', 'rating': 800, 'tags': []}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        results = client.query_problems()

        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], ProblemSummary)

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_query_problems_filters_by_rating_min(self, mock_session_class):
        """Test rating_min filter."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 1, 'index': 'A', 'name': 'Easy', 'rating': 800, 'tags': []},
                    {'contestId': 2, 'index': 'A', 'name': 'Medium', 'rating': 1500, 'tags': []}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        results = client.query_problems(rating_min=1200)

        assert len(results) == 1
        assert results[0].rating == 1500

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_query_problems_filters_by_rating_max(self, mock_session_class):
        """Test rating_max filter."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 1, 'index': 'A', 'name': 'Easy', 'rating': 800, 'tags': []},
                    {'contestId': 2, 'index': 'A', 'name': 'Hard', 'rating': 2000, 'tags': []}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        results = client.query_problems(rating_max=1500)

        assert len(results) == 1
        assert results[0].rating == 800

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_query_problems_filters_by_tags(self, mock_session_class):
        """Test tags filter."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 1, 'index': 'A', 'name': 'DP', 'rating': 1500, 'tags': ['dp']},
                    {'contestId': 2, 'index': 'A', 'name': 'Math', 'rating': 1500, 'tags': ['math']}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        results = client.query_problems(tags=['dp'])

        assert len(results) == 1
        assert 'dp' in results[0].tags

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_query_problems_sorted_by_id(self, mock_session_class):
        """Test that results are sorted by contest ID and index."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 10, 'index': 'B', 'name': 'Third', 'rating': 1000, 'tags': []},
                    {'contestId': 1, 'index': 'A', 'name': 'First', 'rating': 1000, 'tags': []},
                    {'contestId': 10, 'index': 'A', 'name': 'Second', 'rating': 1000, 'tags': []}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        results = client.query_problems()

        assert results[0].problem_id == '1A'
        assert results[1].problem_id == '10A'
        assert results[2].problem_id == '10B'

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_query_problems_network_error(self, mock_session_class):
        """Test network error handling."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = requests.RequestException("Network error")

        client = CodeforcesClient()

        with pytest.raises(click.ClickException):
            client.query_problems()


class TestGetAvailableTags:
    """Test get_available_tags method."""

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_get_available_tags_returns_sorted_list(self, mock_session_class):
        """Test that tags are returned sorted."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 1, 'index': 'A', 'name': 'Test', 'tags': ['dp', 'math']},
                    {'contestId': 2, 'index': 'A', 'name': 'Test2', 'tags': ['graphs', 'dp']}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        tags = client.get_available_tags()

        assert isinstance(tags, list)
        assert 'dp' in tags
        assert 'math' in tags
        assert 'graphs' in tags
        # Should be sorted
        assert tags == sorted(tags)

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_get_available_tags_no_duplicates(self, mock_session_class):
        """Test that duplicate tags are removed."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 1, 'index': 'A', 'name': 'Test', 'tags': ['dp']},
                    {'contestId': 2, 'index': 'A', 'name': 'Test2', 'tags': ['dp']}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        tags = client.get_available_tags()

        assert tags.count('dp') == 1


class TestFetchAllProblems:
    """Test _fetch_all_problems internal method."""

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_fetch_all_problems_caches_result(self, mock_session_class):
        """Test that results are cached."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {'problems': [{'contestId': 1, 'index': 'A', 'name': 'Test'}]}
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()

        # First call
        result1 = client._fetch_all_problems()
        # Second call
        result2 = client._fetch_all_problems()

        # Should only call API once
        assert mock_session.get.call_count == 1
        assert result1 == result2

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_fetch_all_problems_returns_empty_on_non_ok_status(self, mock_session_class):
        """Test that non-OK status returns empty list."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {'status': 'FAILED'}
        mock_session.get.return_value = response

        client = CodeforcesClient()
        result = client._fetch_all_problems()

        assert result == []


class TestExtractPreText:
    """Test _extract_pre_text helper method."""

    def test_extract_pre_text_handles_br_tags(self):
        """Test that <br> tags are converted to newlines."""
        client = CodeforcesClient()

        from bs4 import BeautifulSoup
        html = '<pre>line1<br/>line2<br>line3</pre>'
        soup = BeautifulSoup(html, 'html.parser')
        pre = soup.find('pre')

        result = client._extract_pre_text(pre)
        assert 'line1' in result
        assert 'line2' in result
        assert 'line3' in result


class TestGetProblem:
    """Test get_problem method."""

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_get_problem_success(self, mock_session_class):
        """Test successful problem fetch."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock API response
        api_response = Mock()
        api_response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 4, 'index': 'A', 'name': 'Watermelon',
                     'rating': 800, 'tags': ['math']}
                ]
            }
        }

        # Mock webpage scrape response
        html_response = Mock()
        html_response.text = '''
        <div class="problem-statement">
            <div class="time-limit">time limit per test1 second</div>
            <div class="memory-limit">memory limit per test256 megabytes</div>
            <div>Problem description here</div>
            <div class="input-specification">Input spec</div>
            <div class="output-specification">Output spec</div>
            <div class="sample-test">
                <div class="input"><pre>8</pre></div>
                <div class="output"><pre>YES</pre></div>
            </div>
        </div>
        '''

        mock_session.get.side_effect = [api_response, html_response]

        client = CodeforcesClient()
        problem = client.get_problem(4, 'A')

        assert problem is not None
        assert isinstance(problem, Problem)
        assert problem.contest_id == 4
        assert problem.index == 'A'
        assert problem.name == 'Watermelon'

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_get_problem_not_found(self, mock_session_class):
        """Test problem not found."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {'problems': []}
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        problem = client.get_problem(99999, 'Z')

        assert problem is None

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_get_problem_network_error(self, mock_session_class):
        """Test network error handling in get_problem."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = requests.RequestException("Network error")

        client = CodeforcesClient()

        with pytest.raises(click.ClickException):
            client.get_problem(1, 'A')


class TestScrapeProblem:
    """Test _scrape_problem method."""

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_scrape_problem_missing_statement(self, mock_session_class):
        """Test scraping when problem statement div is missing."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock webpage without problem-statement div
        html_response = Mock()
        html_response.text = '<html><body>No problem here</body></html>'
        mock_session.get.return_value = html_response

        client = CodeforcesClient()
        problem_info = {'name': 'Test', 'rating': 800, 'tags': []}
        problem = client._scrape_problem(1, 'A', problem_info)

        assert problem is not None
        assert problem.description == "Could not fetch problem description."
        assert problem.time_limit == "Unknown"

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_scrape_problem_extracts_sample_tests(self, mock_session_class):
        """Test that sample tests are extracted correctly."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        html_response = Mock()
        html_response.text = '''
        <div class="problem-statement">
            <div class="time-limit">time limit per test2 seconds</div>
            <div class="memory-limit">memory limit per test512 megabytes</div>
            <div class="sample-test">
                <div class="input"><pre>3<br>1 2 3</pre></div>
                <div class="output"><pre>6</pre></div>
                <div class="input"><pre>5<br>10 20 30 40 50</pre></div>
                <div class="output"><pre>150</pre></div>
            </div>
        </div>
        '''
        mock_session.get.return_value = html_response

        client = CodeforcesClient()
        problem_info = {'name': 'Sum', 'rating': 1000, 'tags': ['math']}
        problem = client._scrape_problem(1, 'A', problem_info)

        assert len(problem.sample_tests) == 2
        assert '3' in problem.sample_tests[0]['input']
        assert '6' in problem.sample_tests[0]['output']


class TestQueryProblemsEdgeCases:
    """Test edge cases in query_problems."""

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_query_problems_with_unrated_problems(self, mock_session_class):
        """Test filtering with unrated problems."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 1, 'index': 'A', 'name': 'Rated', 'rating': 1500, 'tags': []},
                    {'contestId': 2, 'index': 'A', 'name': 'Unrated', 'rating': None, 'tags': []}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()

        # Unrated problems should be excluded when rating filter is applied
        results = client.query_problems(rating_min=1000)
        assert len(results) == 1
        assert results[0].name == 'Rated'

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_query_problems_combined_filters(self, mock_session_class):
        """Test with multiple filters applied."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 1, 'index': 'A', 'name': 'Match', 'rating': 1500, 'tags': ['dp']},
                    {'contestId': 2, 'index': 'A', 'name': 'Too Easy', 'rating': 800, 'tags': ['dp']},
                    {'contestId': 3, 'index': 'A', 'name': 'Wrong Tag', 'rating': 1500, 'tags': ['math']},
                    {'contestId': 4, 'index': 'A', 'name': 'Too Hard', 'rating': 2500, 'tags': ['dp']}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        results = client.query_problems(rating_min=1200, rating_max=2000, tags=['dp'])

        assert len(results) == 1
        assert results[0].name == 'Match'

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_query_problems_case_insensitive_tags(self, mock_session_class):
        """Test that tag matching is case-insensitive."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': [
                    {'contestId': 1, 'index': 'A', 'name': 'Test', 'rating': 1000, 'tags': ['DP', 'Greedy']}
                ]
            }
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        results = client.query_problems(tags=['dp'])

        assert len(results) == 1


class TestGetAvailableTagsEdgeCases:
    """Test edge cases in get_available_tags."""

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_get_available_tags_empty_problems(self, mock_session_class):
        """Test when no problems are returned."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        response = Mock()
        response.json.return_value = {
            'status': 'OK',
            'result': {'problems': []}
        }
        mock_session.get.return_value = response

        client = CodeforcesClient()
        tags = client.get_available_tags()

        assert tags == []

    @patch('bytedojo.core.codeforces.client.requests.Session')
    def test_get_available_tags_handles_exception(self, mock_session_class):
        """Test that exceptions return empty list."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = Exception("Unexpected error")

        client = CodeforcesClient()
        tags = client.get_available_tags()

        assert tags == []
