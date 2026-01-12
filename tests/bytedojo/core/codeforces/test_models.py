"""
Tests for Codeforces models.
"""

import pytest
from bytedojo.core.codeforces.models import ProblemSummary, Problem


class TestProblemSummary:
    """Test ProblemSummary dataclass."""

    def test_problem_id_property(self):
        """Test that problem_id combines contest_id and index."""
        summary = ProblemSummary(
            contest_id=1,
            index='A',
            name='Test Problem',
            rating=800,
            tags=['math']
        )
        assert summary.problem_id == '1A'

    def test_problem_id_with_multi_digit_contest(self):
        """Test problem_id with multi-digit contest ID."""
        summary = ProblemSummary(
            contest_id=1850,
            index='B',
            name='Test',
            rating=1200,
            tags=[]
        )
        assert summary.problem_id == '1850B'

    def test_difficulty_easy(self):
        """Test difficulty returns Easy for rating < 1200."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=800, tags=[]
        )
        assert summary.difficulty == 'Easy'

    def test_difficulty_medium(self):
        """Test difficulty returns Medium for rating 1200-1599."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=1400, tags=[]
        )
        assert summary.difficulty == 'Medium'

    def test_difficulty_hard(self):
        """Test difficulty returns Hard for rating 1600-2099."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=1800, tags=[]
        )
        assert summary.difficulty == 'Hard'

    def test_difficulty_expert(self):
        """Test difficulty returns Expert for rating >= 2100."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=2500, tags=[]
        )
        assert summary.difficulty == 'Expert'

    def test_difficulty_unrated(self):
        """Test difficulty returns Unrated for None rating."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=None, tags=[]
        )
        assert summary.difficulty == 'Unrated'


class TestProblem:
    """Test Problem dataclass."""

    def test_problem_id_property(self):
        """Test that problem_id combines contest_id and index."""
        problem = Problem(
            contest_id=4,
            index='B',
            name='Watermelon',
            rating=800,
            tags=['math'],
            time_limit='1 second',
            memory_limit='256 megabytes',
            description='<p>Description</p>',
            input_spec='<p>Input</p>',
            output_spec='<p>Output</p>',
            sample_tests=[],
            note=''
        )
        assert problem.problem_id == '4B'

    def test_filename_property(self):
        """Test filename generation."""
        problem = Problem(
            contest_id=1,
            index='A',
            name='Theatre Square',
            rating=1000,
            tags=['math'],
            time_limit='1 second',
            memory_limit='256 megabytes',
            description='',
            input_spec='',
            output_spec='',
            sample_tests=[],
            note=''
        )
        assert problem.filename == '1A-theatre-square.py'

    def test_filename_removes_special_chars(self):
        """Test that filename removes special characters."""
        problem = Problem(
            contest_id=1,
            index='A',
            name='Test: Problem (Hard)',
            rating=1000,
            tags=[],
            time_limit='1 second',
            memory_limit='256 megabytes',
            description='',
            input_spec='',
            output_spec='',
            sample_tests=[],
            note=''
        )
        # Special chars should be removed
        assert ':' not in problem.filename
        assert '(' not in problem.filename
        assert ')' not in problem.filename

    def test_url_property(self):
        """Test URL generation."""
        problem = Problem(
            contest_id=4,
            index='A',
            name='Watermelon',
            rating=800,
            tags=[],
            time_limit='1 second',
            memory_limit='256 megabytes',
            description='',
            input_spec='',
            output_spec='',
            sample_tests=[],
            note=''
        )
        assert problem.url == 'https://codeforces.com/problemset/problem/4/A'

    def test_difficulty_same_as_summary(self):
        """Test that Problem.difficulty works like ProblemSummary."""
        problem = Problem(
            contest_id=1, index='A', name='Test', rating=1500,
            tags=[], time_limit='', memory_limit='',
            description='', input_spec='', output_spec='',
            sample_tests=[], note=''
        )
        assert problem.difficulty == 'Medium'

    def test_all_fields_stored(self):
        """Test that all fields are properly stored."""
        sample_tests = [{'input': '1', 'output': '2'}]
        problem = Problem(
            contest_id=100,
            index='C',
            name='Complex Problem',
            rating=2000,
            tags=['dp', 'graphs'],
            time_limit='2 seconds',
            memory_limit='512 megabytes',
            description='<p>Desc</p>',
            input_spec='<p>Input spec</p>',
            output_spec='<p>Output spec</p>',
            sample_tests=sample_tests,
            note='<p>Note</p>'
        )

        assert problem.contest_id == 100
        assert problem.index == 'C'
        assert problem.name == 'Complex Problem'
        assert problem.rating == 2000
        assert problem.tags == ['dp', 'graphs']
        assert problem.time_limit == '2 seconds'
        assert problem.memory_limit == '512 megabytes'
        assert problem.description == '<p>Desc</p>'
        assert problem.input_spec == '<p>Input spec</p>'
        assert problem.output_spec == '<p>Output spec</p>'
        assert problem.sample_tests == sample_tests
        assert problem.note == '<p>Note</p>'


class TestDifficultyBoundaries:
    """Test difficulty classification at exact boundaries."""

    def test_difficulty_at_1199(self):
        """Test rating 1199 is Easy."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=1199, tags=[]
        )
        assert summary.difficulty == 'Easy'

    def test_difficulty_at_1200(self):
        """Test rating 1200 is Medium."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=1200, tags=[]
        )
        assert summary.difficulty == 'Medium'

    def test_difficulty_at_1599(self):
        """Test rating 1599 is Medium."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=1599, tags=[]
        )
        assert summary.difficulty == 'Medium'

    def test_difficulty_at_1600(self):
        """Test rating 1600 is Hard."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=1600, tags=[]
        )
        assert summary.difficulty == 'Hard'

    def test_difficulty_at_2099(self):
        """Test rating 2099 is Hard."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=2099, tags=[]
        )
        assert summary.difficulty == 'Hard'

    def test_difficulty_at_2100(self):
        """Test rating 2100 is Expert."""
        summary = ProblemSummary(
            contest_id=1, index='A', name='Test', rating=2100, tags=[]
        )
        assert summary.difficulty == 'Expert'


class TestProblemFilename:
    """Test filename generation edge cases."""

    def test_filename_with_numbers(self):
        """Test filename with numbers in name."""
        problem = Problem(
            contest_id=1, index='A', name='Problem 2023',
            rating=1000, tags=[], time_limit='', memory_limit='',
            description='', input_spec='', output_spec='',
            sample_tests=[], note=''
        )
        assert problem.filename == '1A-problem-2023.py'

    def test_filename_with_multiple_spaces(self):
        """Test filename with multiple spaces."""
        problem = Problem(
            contest_id=1, index='A', name='A   B   C',
            rating=1000, tags=[], time_limit='', memory_limit='',
            description='', input_spec='', output_spec='',
            sample_tests=[], note=''
        )
        assert '---' in problem.filename or 'a-b-c' in problem.filename

    def test_filename_lowercase(self):
        """Test filename is lowercase."""
        problem = Problem(
            contest_id=1, index='A', name='UPPERCASE',
            rating=1000, tags=[], time_limit='', memory_limit='',
            description='', input_spec='', output_spec='',
            sample_tests=[], note=''
        )
        assert 'uppercase' in problem.filename
        assert 'UPPERCASE' not in problem.filename


class TestProblemIndex:
    """Test different index formats."""

    def test_index_with_number(self):
        """Test index like A1, B2."""
        summary = ProblemSummary(
            contest_id=1, index='A1', name='Test', rating=1000, tags=[]
        )
        assert summary.problem_id == '1A1'

    def test_lowercase_index_handling(self):
        """Test that index preserves case."""
        problem = Problem(
            contest_id=1, index='a', name='Test',
            rating=1000, tags=[], time_limit='', memory_limit='',
            description='', input_spec='', output_spec='',
            sample_tests=[], note=''
        )
        assert problem.problem_id == '1a'
