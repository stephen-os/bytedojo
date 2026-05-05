"""
Tests for models (Language, Difficulty, CodeSnippet, Problem, etc).
"""

from datetime import datetime

import pytest
from bytedojo.core.models import (
    Language, Difficulty, Status, CodeSnippet, Problem, ProblemSummary,
    Case, Attempt, AttemptStats
)


class TestLanguageEnum:
    """Test Language enum."""

    def test_language_values(self):
        """Test that language values are lowercase strings."""
        assert Language.PYTHON3.value == "python3"
        assert Language.JAVA.value == "java"
        assert Language.CPP.value == "cpp"

    def test_from_string_valid(self):
        """Test parsing valid language strings."""
        assert Language.from_string("python3") == Language.PYTHON3
        assert Language.from_string("java") == Language.JAVA
        assert Language.from_string("cpp") == Language.CPP

    def test_from_string_case_insensitive(self):
        """Test that from_string handles different cases."""
        assert Language.from_string("PYTHON3") == Language.PYTHON3
        assert Language.from_string("Python3") == Language.PYTHON3
        assert Language.from_string("JAVA") == Language.JAVA

    def test_from_string_unknown(self):
        """Test that unknown languages return None."""
        assert Language.from_string("unknown") is None
        assert Language.from_string("") is None
        assert Language.from_string("fortran") is None

    def test_extension_python(self):
        """Test Python file extensions."""
        assert Language.PYTHON.extension == ".py"
        assert Language.PYTHON3.extension == ".py"

    def test_extension_java(self):
        """Test Java file extension."""
        assert Language.JAVA.extension == ".java"

    def test_extension_cpp(self):
        """Test C++ file extension."""
        assert Language.CPP.extension == ".cpp"

    def test_extension_fallback(self):
        """Test that unknown extensions fall back to .txt."""
        assert Language.BASH.extension == ".txt"
        assert Language.MYSQL.extension == ".txt"


class TestDifficultyEnum:
    """Test Difficulty enum."""

    def test_difficulty_values(self):
        """Test difficulty values."""
        assert Difficulty.EASY.value == "Easy"
        assert Difficulty.MEDIUM.value == "Medium"
        assert Difficulty.HARD.value == "Hard"
        assert Difficulty.NONE.value == "None"

    def test_from_string_valid(self):
        """Test parsing valid difficulty strings."""
        assert Difficulty.from_string("Easy") == Difficulty.EASY
        assert Difficulty.from_string("Medium") == Difficulty.MEDIUM
        assert Difficulty.from_string("Hard") == Difficulty.HARD

    def test_from_string_case_insensitive(self):
        """Test that from_string handles case variations."""
        assert Difficulty.from_string("easy") == Difficulty.EASY
        assert Difficulty.from_string("MEDIUM") == Difficulty.MEDIUM
        assert Difficulty.from_string("hard") == Difficulty.HARD

    def test_from_string_empty(self):
        """Test that empty string returns NONE."""
        assert Difficulty.from_string("") == Difficulty.NONE
        assert Difficulty.from_string(None) == Difficulty.NONE

    def test_from_string_unknown(self):
        """Test that unknown difficulty returns NONE."""
        assert Difficulty.from_string("Unknown") == Difficulty.NONE
        assert Difficulty.from_string("invalid") == Difficulty.NONE


class TestStatusEnum:
    """Test Status enum."""

    def test_status_values(self):
        """Test status values are lowercase strings."""
        assert Status.NONE.value == "none"
        assert Status.PASSED.value == "passed"
        assert Status.FAILED.value == "failed"
        assert Status.SKIPPED.value == "skipped"
        assert Status.UNGRADED.value == "ungraded"

    def test_from_string_valid(self):
        """Test parsing valid status strings."""
        assert Status.from_string("passed") == Status.PASSED
        assert Status.from_string("failed") == Status.FAILED
        assert Status.from_string("skipped") == Status.SKIPPED
        assert Status.from_string("ungraded") == Status.UNGRADED

    def test_from_string_case_insensitive(self):
        """Test that from_string handles case variations."""
        assert Status.from_string("PASSED") == Status.PASSED
        assert Status.from_string("Failed") == Status.FAILED
        assert Status.from_string("SKIPPED") == Status.SKIPPED

    def test_from_string_empty(self):
        """Test that empty string returns NONE."""
        assert Status.from_string("") == Status.NONE
        assert Status.from_string(None) == Status.NONE

    def test_from_string_unknown(self):
        """Test that unknown status returns NONE."""
        assert Status.from_string("unknown") == Status.NONE
        assert Status.from_string("invalid") == Status.NONE


class TestCodeSnippet:
    """Test CodeSnippet dataclass."""

    def test_create_code_snippet(self):
        """Test creating a CodeSnippet."""
        snippet = CodeSnippet(lang=Language.PYTHON3, code="print('hello')")

        assert snippet.lang == Language.PYTHON3
        assert snippet.code == "print('hello')"

    def test_code_snippet_with_empty_code(self):
        """Test CodeSnippet with empty code."""
        snippet = CodeSnippet(lang=Language.PYTHON3, code="")
        assert snippet.code == ""

    def test_code_snippet_with_multiline_code(self):
        """Test CodeSnippet with multiline code."""
        code = "def hello():\n    print('world')"
        snippet = CodeSnippet(lang=Language.PYTHON3, code=code)
        assert snippet.code == code

    def test_code_snippet_equality(self):
        """Test that two identical CodeSnippets are equal."""
        snippet1 = CodeSnippet(lang=Language.PYTHON3, code="test")
        snippet2 = CodeSnippet(lang=Language.PYTHON3, code="test")

        assert snippet1 == snippet2

    def test_code_snippet_inequality(self):
        """Test that different CodeSnippets are not equal."""
        snippet1 = CodeSnippet(lang=Language.PYTHON3, code="test1")
        snippet2 = CodeSnippet(lang=Language.PYTHON3, code="test2")

        assert snippet1 != snippet2


class TestCase:
    """Test Case dataclass."""

    def test_create_test_example(self):
        """Test creating a Case."""
        example = Case(input="nums = [1,2]", output="[0,1]")

        assert example.input == "nums = [1,2]"
        assert example.output == "[0,1]"

    def test_test_example_equality(self):
        """Test that identical Cases are equal."""
        ex1 = Case(input="x = 1", output="1")
        ex2 = Case(input="x = 1", output="1")

        assert ex1 == ex2


class TestProblemSummary:
    """Test ProblemSummary dataclass."""

    def test_create_problem_summary(self):
        """Test creating a ProblemSummary."""
        summary = ProblemSummary(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty=Difficulty.EASY,
            tags=["Array", "Hash Table"]
        )

        assert summary.id == 1
        assert summary.title == "Two Sum"
        assert summary.difficulty == Difficulty.EASY
        assert "Array" in summary.tags


class TestProblemInit:
    """Test Problem dataclass initialization."""

    def test_create_problem(self):
        """Test creating a Problem."""
        problem = Problem(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty=Difficulty.EASY,
            description="<p>Given an array...</p>",
            code_snippets=[
                CodeSnippet(lang=Language.PYTHON3, code="class Solution: pass")
            ],
            test_cases=[]
        )

        assert problem.id == 1
        assert problem.title == "Two Sum"
        assert problem.title_slug == "two-sum"
        assert problem.difficulty == Difficulty.EASY

    def test_problem_with_multiple_snippets(self):
        """Test Problem with multiple code snippets."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[
                CodeSnippet(lang=Language.PYTHON3, code="python code"),
                CodeSnippet(lang=Language.JAVA, code="java code"),
                CodeSnippet(lang=Language.JAVASCRIPT, code="js code")
            ],
            test_cases=[]
        )

        assert len(problem.code_snippets) == 3

    def test_problem_with_test_cases(self):
        """Test Problem with test examples."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[
                Case(input="nums = [1,2]", output="[0,1]"),
                Case(input="nums = [3,4]", output="[1,0]")
            ]
        )

        assert len(problem.test_cases) == 2
        assert problem.test_cases[0].input == "nums = [1,2]"


class TestProblemGetSnippet:
    """Test Problem.get_snippet method."""

    def test_get_snippet_python3(self):
        """Test getting Python3 snippet."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[
                CodeSnippet(lang=Language.PYTHON3, code="python code"),
                CodeSnippet(lang=Language.JAVA, code="java code")
            ],
            test_cases=[]
        )

        code = problem.get_snippet(Language.PYTHON3)
        assert code == "python code"

    def test_get_snippet_not_found(self):
        """Test getting snippet for language that doesn't exist."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[
                CodeSnippet(lang=Language.PYTHON3, code="python code")
            ],
            test_cases=[]
        )

        code = problem.get_snippet(Language.RUBY)
        assert code is None

    def test_get_snippet_from_multiple(self):
        """Test getting specific snippet from multiple options."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[
                CodeSnippet(lang=Language.PYTHON3, code="python code"),
                CodeSnippet(lang=Language.JAVA, code="java code"),
                CodeSnippet(lang=Language.JAVASCRIPT, code="js code")
            ],
            test_cases=[]
        )

        assert problem.get_snippet(Language.JAVA) == "java code"
        assert problem.get_snippet(Language.JAVASCRIPT) == "js code"
        assert problem.get_snippet(Language.PYTHON3) == "python code"

    def test_get_snippet_empty_list(self):
        """Test getting snippet when no snippets exist."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        code = problem.get_snippet(Language.PYTHON3)
        assert code is None


class TestProblemFolderName:
    """Test Problem.get_folder_name method."""

    def test_folder_name(self):
        """Test that folder name is generated correctly."""
        problem = Problem(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.get_folder_name() == "0001-two-sum"

    def test_folder_name_large_id(self):
        """Test folder name with large problem ID."""
        problem = Problem(
            id=2500,
            title="Test",
            title_slug="test-problem",
            difficulty=Difficulty.HARD,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.get_folder_name() == "2500-test-problem"

    def test_folder_name_pads_zeros(self):
        """Test that folder name pads with zeros."""
        problem = Problem(
            id=5,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.get_folder_name() == "0005-test"


class TestProblemSolutionFilename:
    """Test Problem.get_solution_filename method."""

    def test_solution_filename_python(self):
        """Test solution filename for Python."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.get_solution_filename(Language.PYTHON3) == "solution.py"

    def test_solution_filename_java(self):
        """Test solution filename for Java."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.get_solution_filename(Language.JAVA) == "solution.java"

    def test_solution_filename_cpp(self):
        """Test solution filename for C++."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.get_solution_filename(Language.CPP) == "solution.cpp"

    def test_solution_filename_none(self):
        """Test solution filename returns None for None input."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.get_solution_filename(None) is None

    def test_solution_filename_default(self):
        """Test solution filename defaults to Python3."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.get_solution_filename() == "solution.py"


class TestProblemDifficulty:
    """Test Problem difficulty levels."""

    def test_easy_difficulty(self):
        """Test problem with Easy difficulty."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.difficulty == Difficulty.EASY

    def test_medium_difficulty(self):
        """Test problem with Medium difficulty."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.MEDIUM,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.difficulty == Difficulty.MEDIUM

    def test_hard_difficulty(self):
        """Test problem with Hard difficulty."""
        problem = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.HARD,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem.difficulty == Difficulty.HARD


class TestProblemEquality:
    """Test Problem equality."""

    def test_identical_problems_are_equal(self):
        """Test that identical problems are equal."""
        problem1 = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[CodeSnippet(lang=Language.PYTHON3, code="code")],
            test_cases=[]
        )

        problem2 = Problem(
            id=1,
            title="Test",
            title_slug="test",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[CodeSnippet(lang=Language.PYTHON3, code="code")],
            test_cases=[]
        )

        assert problem1 == problem2

    def test_different_problems_are_not_equal(self):
        """Test that different problems are not equal."""
        problem1 = Problem(
            id=1,
            title="Test 1",
            title_slug="test-1",
            difficulty=Difficulty.EASY,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        problem2 = Problem(
            id=2,
            title="Test 2",
            title_slug="test-2",
            difficulty=Difficulty.HARD,
            description="desc",
            code_snippets=[],
            test_cases=[]
        )

        assert problem1 != problem2


class TestAttempt:
    """Test Attempt dataclass."""

    def test_create_attempt(self):
        """Test creating an Attempt."""
        now = datetime.now()
        attempt = Attempt(
            problem_id=1,
            language=Language.PYTHON3,
            version=1,
            status=Status.UNGRADED,
            created_at=now,
            run_count=0,
            notes=""
        )

        assert attempt.problem_id == 1
        assert attempt.language == Language.PYTHON3
        assert attempt.version == 1
        assert attempt.status == Status.UNGRADED
        assert attempt.created_at == now
        assert attempt.run_count == 0
        assert attempt.notes == ""

    def test_attempt_defaults(self):
        """Test Attempt default values."""
        attempt = Attempt(
            problem_id=1,
            language=Language.JAVA,
            version=2,
            status=Status.PASSED,
            created_at=datetime.now()
        )

        assert attempt.run_count == 0
        assert attempt.notes == ""

    def test_get_version_string(self):
        """Test version string formatting."""
        attempt = Attempt(
            problem_id=1,
            language=Language.PYTHON3,
            version=1,
            status=Status.UNGRADED,
            created_at=datetime.now()
        )
        assert attempt.get_version_string() == "v001"

    def test_get_version_string_double_digit(self):
        """Test version string with double digits."""
        attempt = Attempt(
            problem_id=1,
            language=Language.PYTHON3,
            version=42,
            status=Status.PASSED,
            created_at=datetime.now()
        )
        assert attempt.get_version_string() == "v042"

    def test_get_version_string_triple_digit(self):
        """Test version string with triple digits."""
        attempt = Attempt(
            problem_id=1,
            language=Language.PYTHON3,
            version=100,
            status=Status.PASSED,
            created_at=datetime.now()
        )
        assert attempt.get_version_string() == "v100"

    def test_attempt_equality(self):
        """Test that identical attempts are equal."""
        now = datetime.now()
        attempt1 = Attempt(
            problem_id=1,
            language=Language.PYTHON3,
            version=1,
            status=Status.PASSED,
            created_at=now
        )
        attempt2 = Attempt(
            problem_id=1,
            language=Language.PYTHON3,
            version=1,
            status=Status.PASSED,
            created_at=now
        )
        assert attempt1 == attempt2


class TestAttemptStats:
    """Test AttemptStats dataclass."""

    def test_create_attempt_stats(self):
        """Test creating AttemptStats."""
        stats = AttemptStats(
            problem_id=1,
            language=Language.PYTHON3,
            total_attempts=3,
            latest_version=3,
            latest_status=Status.PASSED,
            pass_count=2,
            fail_count=1,
            skip_count=0,
            total_runs=15
        )

        assert stats.problem_id == 1
        assert stats.language == Language.PYTHON3
        assert stats.total_attempts == 3
        assert stats.latest_version == 3
        assert stats.latest_status == Status.PASSED
        assert stats.pass_count == 2
        assert stats.fail_count == 1
        assert stats.skip_count == 0
        assert stats.total_runs == 15

    def test_attempt_stats_equality(self):
        """Test that identical AttemptStats are equal."""
        stats1 = AttemptStats(
            problem_id=1,
            language=Language.JAVA,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.UNGRADED,
            pass_count=0,
            fail_count=0,
            skip_count=0,
            total_runs=0
        )
        stats2 = AttemptStats(
            problem_id=1,
            language=Language.JAVA,
            total_attempts=1,
            latest_version=1,
            latest_status=Status.UNGRADED,
            pass_count=0,
            fail_count=0,
            skip_count=0,
            total_runs=0
        )
        assert stats1 == stats2
