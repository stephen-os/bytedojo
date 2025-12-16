"""
Tests for LeetCode models (Problem and CodeSnippet).
"""

import pytest
from bytedojo.core.leetcode.models import CodeSnippet, Problem


class TestCodeSnippet:
    """Test CodeSnippet dataclass."""
    
    def test_create_code_snippet(self):
        """Test creating a CodeSnippet."""
        snippet = CodeSnippet(lang="Python3", code="print('hello')")
        
        assert snippet.lang == "Python3"
        assert snippet.code == "print('hello')"
    
    def test_code_snippet_has_lang_attribute(self):
        """Test that CodeSnippet has lang attribute."""
        snippet = CodeSnippet(lang="Java", code="")
        assert hasattr(snippet, 'lang')
    
    def test_code_snippet_has_code_attribute(self):
        """Test that CodeSnippet has code attribute."""
        snippet = CodeSnippet(lang="Python3", code="code here")
        assert hasattr(snippet, 'code')
    
    def test_code_snippet_with_empty_code(self):
        """Test CodeSnippet with empty code."""
        snippet = CodeSnippet(lang="Python3", code="")
        assert snippet.code == ""
    
    def test_code_snippet_with_multiline_code(self):
        """Test CodeSnippet with multiline code."""
        code = "def hello():\n    print('world')"
        snippet = CodeSnippet(lang="Python3", code=code)
        assert snippet.code == code
    
    def test_code_snippet_equality(self):
        """Test that two identical CodeSnippets are equal."""
        snippet1 = CodeSnippet(lang="Python3", code="test")
        snippet2 = CodeSnippet(lang="Python3", code="test")
        
        assert snippet1 == snippet2
    
    def test_code_snippet_inequality(self):
        """Test that different CodeSnippets are not equal."""
        snippet1 = CodeSnippet(lang="Python3", code="test1")
        snippet2 = CodeSnippet(lang="Python3", code="test2")
        
        assert snippet1 != snippet2


class TestProblemInit:
    """Test Problem dataclass initialization."""
    
    def test_create_problem(self):
        """Test creating a Problem."""
        problem = Problem(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            description="<p>Given an array...</p>",
            test_cases="[2,7,11,15]\n9",
            code_snippets=[
                CodeSnippet(lang="Python3", code="class Solution: pass")
            ]
        )
        
        assert problem.id == 1
        assert problem.title == "Two Sum"
        assert problem.title_slug == "two-sum"
        assert problem.difficulty == "Easy"
    
    def test_problem_with_multiple_snippets(self):
        """Test Problem with multiple code snippets."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="cases",
            code_snippets=[
                CodeSnippet(lang="Python3", code="python code"),
                CodeSnippet(lang="Java", code="java code"),
                CodeSnippet(lang="JavaScript", code="js code")
            ]
        )
        
        assert len(problem.code_snippets) == 3
    
    def test_problem_with_empty_snippets(self):
        """Test Problem with empty code snippets list."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        assert problem.code_snippets == []


class TestProblemGetSnippet:
    """Test Problem.get_snippet method."""
    
    def test_get_snippet_python3(self):
        """Test getting Python3 snippet."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[
                CodeSnippet(lang="Python3", code="python code"),
                CodeSnippet(lang="Java", code="java code")
            ]
        )
        
        code = problem.get_snippet("Python3")
        assert code == "python code"
    
    def test_get_snippet_case_insensitive(self):
        """Test that get_snippet is case-insensitive."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[
                CodeSnippet(lang="Python3", code="python code")
            ]
        )
        
        # Should work with different cases
        assert problem.get_snippet("python3") == "python code"
        assert problem.get_snippet("PYTHON3") == "python code"
        assert problem.get_snippet("Python3") == "python code"
    
    def test_get_snippet_not_found(self):
        """Test getting snippet for language that doesn't exist."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[
                CodeSnippet(lang="Python3", code="python code")
            ]
        )
        
        code = problem.get_snippet("Ruby")
        assert code is None
    
    def test_get_snippet_from_multiple(self):
        """Test getting specific snippet from multiple options."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[
                CodeSnippet(lang="Python3", code="python code"),
                CodeSnippet(lang="Java", code="java code"),
                CodeSnippet(lang="JavaScript", code="js code")
            ]
        )
        
        assert problem.get_snippet("Java") == "java code"
        assert problem.get_snippet("JavaScript") == "js code"
        assert problem.get_snippet("Python3") == "python code"
    
    def test_get_snippet_empty_list(self):
        """Test getting snippet when no snippets exist."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        code = problem.get_snippet("Python3")
        assert code is None


class TestProblemFilename:
    """Test Problem.filename property."""
    
    def test_filename_property(self):
        """Test that filename property generates correct filename."""
        problem = Problem(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        assert problem.filename == "0001-two-sum.py"
    
    def test_filename_with_large_id(self):
        """Test filename with large problem ID."""
        problem = Problem(
            id=2500,
            title="Test",
            title_slug="test-problem",
            difficulty="Hard",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        assert problem.filename == "2500-test-problem.py"
    
    def test_filename_pads_zeros(self):
        """Test that filename pads with zeros."""
        problem = Problem(
            id=5,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        assert problem.filename == "0005-test.py"
    
    def test_filename_always_ends_with_py(self):
        """Test that filename always ends with .py."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="any-slug",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        assert problem.filename.endswith(".py")


class TestProblemDifficulty:
    """Test Problem difficulty levels."""
    
    def test_easy_difficulty(self):
        """Test problem with Easy difficulty."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        assert problem.difficulty == "Easy"
    
    def test_medium_difficulty(self):
        """Test problem with Medium difficulty."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Medium",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        assert problem.difficulty == "Medium"
    
    def test_hard_difficulty(self):
        """Test problem with Hard difficulty."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Hard",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        assert problem.difficulty == "Hard"


class TestProblemEquality:
    """Test Problem equality."""
    
    def test_identical_problems_are_equal(self):
        """Test that identical problems are equal."""
        problem1 = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="cases",
            code_snippets=[CodeSnippet(lang="Python3", code="code")]
        )
        
        problem2 = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty="Easy",
            description="desc",
            test_cases="cases",
            code_snippets=[CodeSnippet(lang="Python3", code="code")]
        )
        
        assert problem1 == problem2
    
    def test_different_problems_are_not_equal(self):
        """Test that different problems are not equal."""
        problem1 = Problem(
            id=1,
            title="Test 1",
            title_slug="test-1",
            difficulty="Easy",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        problem2 = Problem(
            id=2,
            title="Test 2",
            title_slug="test-2",
            difficulty="Hard",
            description="desc",
            test_cases="",
            code_snippets=[]
        )
        
        assert problem1 != problem2


class TestProblemRealisticData:
    """Test Problem with realistic LeetCode data."""
    
    def test_two_sum_problem(self):
        """Test creating a realistic Two Sum problem."""
        problem = Problem(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            description="<p>Given an array of integers <code>nums</code>...</p>",
            test_cases="[2,7,11,15]\n9\n[0,1]",
            code_snippets=[
                CodeSnippet(
                    lang="Python3",
                    code="class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        pass"
                ),
                CodeSnippet(
                    lang="Java",
                    code="class Solution {\n    public int[] twoSum(int[] nums, int target) {\n    }\n}"
                )
            ]
        )
        
        assert problem.id == 1
        assert problem.title == "Two Sum"
        assert problem.filename == "0001-two-sum.py"
        assert len(problem.code_snippets) == 2
        assert problem.get_snippet("Python3") is not None
        assert problem.get_snippet("Java") is not None