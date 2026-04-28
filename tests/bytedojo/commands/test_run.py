"""
Tests for run command.
"""

import pytest
import sqlite3
import os
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock

from bytedojo.commands.dojo import dojo
from bytedojo.core.repository import DojoRepository


@pytest.fixture
def initialized_repo(tmp_path):
    """Create an initialized repository for testing."""
    original_dir = Path.cwd()
    os.chdir(tmp_path)

    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()

    yield tmp_path

    os.chdir(original_dir)


@pytest.fixture
def repo_with_python_problem(tmp_path):
    """Create a repository with a runnable Python problem."""
    original_dir = Path.cwd()
    os.chdir(tmp_path)

    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()

    # Create leetcode directory and Python file
    leetcode_dir = tmp_path / "leetcode"
    leetcode_dir.mkdir()

    python_file = leetcode_dir / "0001-two-sum.py"
    python_file.write_text('''
print("Hello from Python!")
print("Test output")
''')

    # Insert problem into database
    db_path = tmp_path / ".dojo" / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO problems (source, problem_id, language, title, difficulty, file_path, fetched_at)
        VALUES ('leetcode', '1', 'python', 'Two Sum', 'Easy', 'leetcode/0001-two-sum.py', '2024-01-01 10:00:00')
    """)
    conn.commit()
    conn.close()

    yield tmp_path

    os.chdir(original_dir)


@pytest.fixture
def repo_with_java_problem(tmp_path):
    """Create a repository with a runnable Java problem."""
    original_dir = Path.cwd()
    os.chdir(tmp_path)

    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()

    # Create leetcode directory and Java file
    leetcode_dir = tmp_path / "leetcode"
    leetcode_dir.mkdir()

    java_file = leetcode_dir / "0001-two-sum.java"
    java_file.write_text('''
class Solution {
    public int[] twoSum(int[] nums, int target) {
        return new int[]{};
    }
}

class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
    }
}
''')

    # Insert problem into database
    db_path = tmp_path / ".dojo" / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO problems (source, problem_id, language, title, difficulty, file_path, fetched_at)
        VALUES ('leetcode', '1', 'java', 'Two Sum', 'Easy', 'leetcode/0001-two-sum.java', '2024-01-01 10:00:00')
    """)
    conn.commit()
    conn.close()

    yield tmp_path

    os.chdir(original_dir)


@pytest.fixture
def repo_with_cpp_problem(tmp_path):
    """Create a repository with a runnable C++ problem."""
    original_dir = Path.cwd()
    os.chdir(tmp_path)

    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()

    # Create leetcode directory and C++ file
    leetcode_dir = tmp_path / "leetcode"
    leetcode_dir.mkdir()

    cpp_file = leetcode_dir / "0001-two-sum.cpp"
    cpp_file.write_text('''
#include <iostream>
using namespace std;

int main() {
    cout << "Hello from C++!" << endl;
    return 0;
}
''')

    # Insert problem into database
    db_path = tmp_path / ".dojo" / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO problems (source, problem_id, language, title, difficulty, file_path, fetched_at)
        VALUES ('leetcode', '1', 'cpp', 'Two Sum', 'Easy', 'leetcode/0001-two-sum.cpp', '2024-01-01 10:00:00')
    """)
    conn.commit()
    conn.close()

    yield tmp_path

    os.chdir(original_dir)


@pytest.fixture
def repo_with_all_languages(tmp_path):
    """Create a repository with problems in all three languages."""
    original_dir = Path.cwd()
    os.chdir(tmp_path)

    repo = DojoRepository(root_dir=tmp_path)
    repo.initialize()

    # Create leetcode directory
    leetcode_dir = tmp_path / "leetcode"
    leetcode_dir.mkdir()

    # Python file
    python_file = leetcode_dir / "0001-two-sum.py"
    python_file.write_text('print("Python")')

    # Java file
    java_file = leetcode_dir / "0001-two-sum.java"
    java_file.write_text('''
class Main {
    public static void main(String[] args) {
        System.out.println("Java");
    }
}
''')

    # C++ file
    cpp_file = leetcode_dir / "0001-two-sum.cpp"
    cpp_file.write_text('''
#include <iostream>
int main() { std::cout << "C++" << std::endl; return 0; }
''')

    # Insert problems into database
    db_path = tmp_path / ".dojo" / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO problems (source, problem_id, language, title, difficulty, file_path, fetched_at)
        VALUES ('leetcode', '1', 'python', 'Two Sum', 'Easy', 'leetcode/0001-two-sum.py', '2024-01-01 10:00:00')
    """)
    conn.execute("""
        INSERT INTO problems (source, problem_id, language, title, difficulty, file_path, fetched_at)
        VALUES ('leetcode', '1', 'java', 'Two Sum', 'Easy', 'leetcode/0001-two-sum.java', '2024-01-01 11:00:00')
    """)
    conn.execute("""
        INSERT INTO problems (source, problem_id, language, title, difficulty, file_path, fetched_at)
        VALUES ('leetcode', '1', 'cpp', 'Two Sum', 'Easy', 'leetcode/0001-two-sum.cpp', '2024-01-01 12:00:00')
    """)
    conn.commit()
    conn.close()

    yield tmp_path

    os.chdir(original_dir)


# ============================================================================
# HELP AND BASIC TESTS
# ============================================================================

class TestRunCommandHelp:
    """Test run command help output."""

    def test_run_help(self):
        """Test run --help output."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', '--help'])

        assert result.exit_code == 0
        assert "Run problem solutions" in result.output
        assert "problem" in result.output
        assert "last" in result.output

    def test_run_problem_help(self):
        """Test run problem --help output."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '--help'])

        assert result.exit_code == 0
        assert "--python" in result.output
        assert "--java" in result.output
        assert "--cpp" in result.output
        assert "--clean" in result.output

    def test_run_last_help(self):
        """Test run last --help output."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'last', '--help'])

        assert result.exit_code == 0
        assert "--python" in result.output
        assert "--java" in result.output
        assert "--cpp" in result.output
        assert "--clean" in result.output

    def test_run_without_subcommand_shows_help(self, initialized_repo):
        """Test that run without subcommand shows help."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run'])

        assert result.exit_code == 0
        assert "Usage:" in result.output


# ============================================================================
# NO REPO TESTS
# ============================================================================

class TestRunCommandNoRepo:
    """Test run command when no repository exists."""

    def test_run_problem_fails_without_repo(self, tmp_path):
        """Test that run problem fails when no .dojo exists."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['run', 'problem', '1'])

            assert result.exit_code != 0
            assert "No .dojo repository found" in result.output

    def test_run_last_fails_without_repo(self, tmp_path):
        """Test that run last fails when no .dojo exists."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['run', 'last'])

            assert result.exit_code != 0
            assert "No .dojo repository found" in result.output


# ============================================================================
# PROBLEM NOT FOUND TESTS
# ============================================================================

class TestRunCommandProblemNotFound:
    """Test run command when problem doesn't exist."""

    def test_run_problem_not_in_database(self, initialized_repo):
        """Test run with problem ID not in database."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '999'])

        assert result.exit_code != 0
        assert "not found in database" in result.output
        assert "Fetch it first" in result.output

    def test_run_last_no_problems(self, initialized_repo):
        """Test run last with no problems in database."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'last'])

        assert result.exit_code != 0
        assert "No python problems found" in result.output


# ============================================================================
# PYTHON EXECUTION TESTS
# ============================================================================

class TestRunPython:
    """Test running Python problems."""

    def test_run_python_problem(self, repo_with_python_problem):
        """Test running a Python problem."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1'])

        assert result.exit_code == 0
        assert "RUN PROBLEM" in result.output
        assert "Language: PYTHON" in result.output
        assert "Execution completed successfully" in result.output

    def test_run_python_with_explicit_flag(self, repo_with_python_problem):
        """Test running Python with --python flag."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1', '--python'])

        assert result.exit_code == 0
        assert "Execution completed successfully" in result.output

    def test_run_last_python(self, repo_with_python_problem):
        """Test run last with Python problem."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'last'])

        assert result.exit_code == 0
        assert "Execution completed successfully" in result.output


# ============================================================================
# JAVA EXECUTION TESTS
# ============================================================================

class TestRunJava:
    """Test running Java problems."""

    @pytest.mark.skipif(
        os.system('javac --version > nul 2>&1') != 0 if os.name == 'nt' else os.system('javac --version > /dev/null 2>&1') != 0,
        reason="Java compiler not available"
    )
    def test_run_java_problem(self, repo_with_java_problem):
        """Test running a Java problem."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1', '--java'])

        assert result.exit_code == 0
        assert "RUN PROBLEM" in result.output
        assert "Language: JAVA" in result.output
        assert "Execution completed successfully" in result.output

    @pytest.mark.skipif(
        os.system('javac --version > nul 2>&1') != 0 if os.name == 'nt' else os.system('javac --version > /dev/null 2>&1') != 0,
        reason="Java compiler not available"
    )
    def test_run_java_creates_class_files(self, repo_with_java_problem):
        """Test that running Java creates .class files."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1', '--java'])

        assert result.exit_code == 0

        # Check that class files were created
        leetcode_dir = repo_with_java_problem / "leetcode"
        class_files = list(leetcode_dir.glob("*.class"))
        assert len(class_files) > 0

    @pytest.mark.skipif(
        os.system('javac --version > nul 2>&1') != 0 if os.name == 'nt' else os.system('javac --version > /dev/null 2>&1') != 0,
        reason="Java compiler not available"
    )
    def test_run_java_clean_removes_class_files(self, repo_with_java_problem):
        """Test that --clean removes .class files."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1', '--java', '--clean'])

        assert result.exit_code == 0

        # Check that class files were removed
        leetcode_dir = repo_with_java_problem / "leetcode"
        class_files = list(leetcode_dir.glob("*.class"))
        assert len(class_files) == 0


# ============================================================================
# C++ EXECUTION TESTS
# ============================================================================

class TestRunCpp:
    """Test running C++ problems."""

    @pytest.mark.skipif(
        os.system('g++ --version > nul 2>&1') != 0 if os.name == 'nt' else os.system('g++ --version > /dev/null 2>&1') != 0,
        reason="G++ compiler not available"
    )
    def test_run_cpp_problem(self, repo_with_cpp_problem):
        """Test running a C++ problem."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1', '--cpp'])

        assert result.exit_code == 0
        assert "RUN PROBLEM" in result.output
        assert "Language: CPP" in result.output
        assert "Execution completed successfully" in result.output

    @pytest.mark.skipif(
        os.system('g++ --version > nul 2>&1') != 0 if os.name == 'nt' else os.system('g++ --version > /dev/null 2>&1') != 0,
        reason="G++ compiler not available"
    )
    def test_run_cpp_creates_executable(self, repo_with_cpp_problem):
        """Test that running C++ creates executable."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1', '--cpp'])

        assert result.exit_code == 0

        # Check that executable was created
        leetcode_dir = repo_with_cpp_problem / "leetcode"
        if os.name == 'nt':
            exe_files = list(leetcode_dir.glob("*.exe"))
        else:
            exe_files = [f for f in leetcode_dir.iterdir() if f.is_file() and f.stat().st_mode & 0o111]
        assert len(exe_files) > 0

    @pytest.mark.skipif(
        os.system('g++ --version > nul 2>&1') != 0 if os.name == 'nt' else os.system('g++ --version > /dev/null 2>&1') != 0,
        reason="G++ compiler not available"
    )
    def test_run_cpp_clean_removes_executable(self, repo_with_cpp_problem):
        """Test that --clean removes executable."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1', '--cpp', '--clean'])

        assert result.exit_code == 0

        # Check that executable was removed
        leetcode_dir = repo_with_cpp_problem / "leetcode"
        exe_file = leetcode_dir / ("0001-two-sum.exe" if os.name == 'nt' else "0001-two-sum")
        assert not exe_file.exists()


# ============================================================================
# LANGUAGE SELECTION TESTS
# ============================================================================

class TestRunLanguageSelection:
    """Test language selection with flags."""

    def test_run_defaults_to_python(self, repo_with_all_languages):
        """Test that run defaults to Python."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1'])

        assert result.exit_code == 0
        assert "Language: PYTHON" in result.output
        assert "Execution completed successfully" in result.output

    def test_run_wrong_language_not_found(self, repo_with_python_problem):
        """Test running with language that wasn't fetched."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1', '--java'])

        assert result.exit_code != 0
        assert "not found in database" in result.output


# ============================================================================
# FILE NOT FOUND TESTS
# ============================================================================

class TestRunFileNotFound:
    """Test run command when file is missing."""

    def test_run_file_deleted(self, repo_with_python_problem):
        """Test run when file has been deleted."""
        # Delete the file
        file_path = repo_with_python_problem / "leetcode" / "0001-two-sum.py"
        file_path.unlink()

        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1'])

        assert result.exit_code != 0
        assert "File not found" in result.output


# ============================================================================
# OUTPUT DISPLAY TESTS
# ============================================================================

class TestRunOutputDisplay:
    """Test run command output formatting."""

    def test_run_shows_header(self, repo_with_python_problem):
        """Test that run shows problem header."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1'])

        assert "RUN PROBLEM" in result.output
        assert "Two Sum" in result.output
        assert "Language:" in result.output
        assert "File:" in result.output

    def test_run_shows_output_section(self, repo_with_python_problem):
        """Test that run shows OUTPUT section."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1'])

        assert "OUTPUT" in result.output

    def test_run_shows_success_message(self, repo_with_python_problem):
        """Test that successful run shows success message."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1'])

        assert "Execution completed successfully" in result.output


# ============================================================================
# COMPILATION ERROR TESTS
# ============================================================================

class TestRunCompilationErrors:
    """Test run command with compilation errors."""

    @pytest.mark.skipif(
        os.system('javac --version > nul 2>&1') != 0 if os.name == 'nt' else os.system('javac --version > /dev/null 2>&1') != 0,
        reason="Java compiler not available"
    )
    def test_run_java_compile_error(self, tmp_path):
        """Test running Java with compilation error."""
        original_dir = Path.cwd()
        os.chdir(tmp_path)

        repo = DojoRepository(root_dir=tmp_path)
        repo.initialize()

        # Create invalid Java file
        leetcode_dir = tmp_path / "leetcode"
        leetcode_dir.mkdir()
        java_file = leetcode_dir / "0001-bad.java"
        java_file.write_text('class Main { invalid syntax }')

        # Insert into database
        db_path = tmp_path / ".dojo" / "db.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO problems (source, problem_id, language, title, difficulty, file_path, fetched_at)
            VALUES ('leetcode', '1', 'java', 'Bad', 'Easy', 'leetcode/0001-bad.java', '2024-01-01')
        """)
        conn.commit()
        conn.close()

        runner = CliRunner()
        result = runner.invoke(dojo, ['run', 'problem', '1', '--java'])

        os.chdir(original_dir)

        assert "Compilation failed" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
