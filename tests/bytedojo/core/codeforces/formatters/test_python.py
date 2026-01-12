"""
Tests for Codeforces Python formatter.
"""

import pytest
from bytedojo.core.codeforces.formatters.python import PythonFormatter
from bytedojo.core.codeforces.models import Problem


class TestPythonFormatter:
    """Test PythonFormatter class."""

    def create_sample_problem(self, **kwargs):
        """Create a sample problem for testing."""
        defaults = {
            'contest_id': 4,
            'index': 'A',
            'name': 'Watermelon',
            'rating': 800,
            'tags': ['math', 'brute force'],
            'time_limit': '1 second',
            'memory_limit': '64 megabytes',
            'description': '<p>Test description</p>',
            'input_spec': '<p>The first line contains n.</p>',
            'output_spec': '<p>Print YES or NO.</p>',
            'sample_tests': [
                {'input': '8', 'output': 'YES'}
            ],
            'note': '<p>Additional note.</p>'
        }
        defaults.update(kwargs)
        return Problem(**defaults)

    def test_format_returns_string(self):
        """Test that format returns a string."""
        formatter = PythonFormatter()
        problem = self.create_sample_problem()
        result = formatter.format(problem)
        assert isinstance(result, str)

    def test_format_includes_header(self):
        """Test that format includes problem header."""
        formatter = PythonFormatter()
        problem = self.create_sample_problem()
        result = formatter.format(problem)

        assert 'Codeforces Problem 4A: Watermelon' in result
        assert 'Difficulty: Easy (800)' in result
        assert 'https://codeforces.com/problemset/problem/4/A' in result
        assert 'Time Limit: 1 second' in result
        assert 'Memory Limit: 64 megabytes' in result
        assert 'math' in result

    def test_format_includes_solve_function(self):
        """Test that format includes solve function."""
        formatter = PythonFormatter()
        problem = self.create_sample_problem()
        result = formatter.format(problem)

        assert 'def solve():' in result
        assert 'if __name__ == "__main__":' in result

    def test_format_includes_test_section(self):
        """Test that format includes test section."""
        formatter = PythonFormatter()
        problem = self.create_sample_problem()
        result = formatter.format(problem)

        assert 'def run_tests():' in result
        assert 'test_cases' in result

    def test_format_includes_sample_tests(self):
        """Test that sample tests are included."""
        formatter = PythonFormatter()
        problem = self.create_sample_problem(
            sample_tests=[
                {'input': '8', 'output': 'YES'},
                {'input': '6', 'output': 'YES'}
            ]
        )
        result = formatter.format(problem)

        assert '8' in result
        assert 'YES' in result

    def test_format_no_sample_tests(self):
        """Test formatting with no sample tests."""
        formatter = PythonFormatter()
        problem = self.create_sample_problem(sample_tests=[])
        result = formatter.format(problem)

        assert 'No sample tests available' in result

    def test_format_includes_description(self):
        """Test that description is included."""
        formatter = PythonFormatter()
        problem = self.create_sample_problem(
            description='<p>This is the problem description.</p>'
        )
        result = formatter.format(problem)

        assert 'PROBLEM DESCRIPTION' in result

    def test_format_unrated_problem(self):
        """Test formatting unrated problem."""
        formatter = PythonFormatter()
        problem = self.create_sample_problem(rating=None)
        result = formatter.format(problem)

        assert 'Unrated' in result


class TestHtmlToText:
    """Test _html_to_text method."""

    def test_html_to_text_removes_tags(self):
        """Test that HTML tags are removed."""
        formatter = PythonFormatter()
        result = formatter._html_to_text('<p>Hello <b>world</b></p>')
        assert '<p>' not in result
        assert '<b>' not in result
        assert 'Hello' in result
        assert 'world' in result

    def test_html_to_text_converts_br_to_newline(self):
        """Test that <br> converts to newline."""
        formatter = PythonFormatter()
        result = formatter._html_to_text('Line 1<br>Line 2')
        lines = result.split('\n')
        assert len(lines) >= 2

    def test_html_to_text_unescapes_entities(self):
        """Test that HTML entities are unescaped."""
        formatter = PythonFormatter()
        result = formatter._html_to_text('5 &lt; 10 &amp; 20 &gt; 15')
        assert '<' in result
        assert '&' in result
        assert '>' in result

    def test_html_to_text_empty_input(self):
        """Test with empty input."""
        formatter = PythonFormatter()
        result = formatter._html_to_text('')
        assert result == ''

    def test_html_to_text_none_input(self):
        """Test with None input."""
        formatter = PythonFormatter()
        result = formatter._html_to_text(None)
        assert result == ''


class TestFormatHeader:
    """Test _format_header method."""

    def test_format_header_includes_problem_id(self):
        """Test that header includes problem ID."""
        formatter = PythonFormatter()
        problem = Problem(
            contest_id=1850, index='A', name='To My Critics',
            rating=800, tags=[], time_limit='1s', memory_limit='256MB',
            description='', input_spec='', output_spec='',
            sample_tests=[], note=''
        )
        result = formatter._format_header(problem)
        assert '1850A' in result
        assert 'To My Critics' in result

    def test_format_header_includes_tags(self):
        """Test that header includes tags."""
        formatter = PythonFormatter()
        problem = Problem(
            contest_id=1, index='A', name='Test',
            rating=1500, tags=['dp', 'greedy'], time_limit='1s',
            memory_limit='256MB', description='', input_spec='',
            output_spec='', sample_tests=[], note=''
        )
        result = formatter._format_header(problem)
        assert 'dp' in result
        assert 'greedy' in result


class TestFormatTests:
    """Test _format_tests method."""

    def test_format_tests_with_samples(self):
        """Test test section with sample tests."""
        formatter = PythonFormatter()
        problem = Problem(
            contest_id=1, index='A', name='Test',
            rating=1000, tags=[], time_limit='1s', memory_limit='256MB',
            description='', input_spec='', output_spec='',
            sample_tests=[
                {'input': '3\n1 2 3', 'output': '6'}
            ],
            note=''
        )
        result = formatter._format_tests(problem)

        assert 'test_cases' in result
        assert 'import io' in result
        assert 'import sys' in result

    def test_format_tests_escapes_strings(self):
        """Test that strings are properly escaped."""
        formatter = PythonFormatter()
        problem = Problem(
            contest_id=1, index='A', name='Test',
            rating=1000, tags=[], time_limit='1s', memory_limit='256MB',
            description='', input_spec='', output_spec='',
            sample_tests=[
                {'input': 'line1\nline2', 'output': 'result'}
            ],
            note=''
        )
        result = formatter._format_tests(problem)
        # Newlines should be escaped in the test cases
        assert '\\n' in result
