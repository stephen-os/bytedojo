"""
Tests for execution module (ExecutionResult, ProblemExecutor).
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from bytedojo.core.execution import (
    DEFAULT_TIMEOUT_SECONDS,
    ExecutionResult,
    ProblemExecutor,
)
from bytedojo.core.repository import Repository


class TestExecutionResultDataclass:
    """Test ExecutionResult dataclass."""

    def test_create_execution_result(self):
        """Test creating an ExecutionResult with required fields."""
        result = ExecutionResult(
            exit_code=0,
            stdout="Hello, World!",
            stderr="",
            timed_out=False,
            language="python",
            file_path="/path/to/solution.py"
        )

        assert result.exit_code == 0
        assert result.stdout == "Hello, World!"
        assert result.stderr == ""
        assert result.timed_out is False
        assert result.language == "python"
        assert result.file_path == "/path/to/solution.py"

    def test_execution_result_defaults(self):
        """Test ExecutionResult default values."""
        result = ExecutionResult(
            exit_code=0,
            stdout="output",
            stderr="",
            timed_out=False,
            language="python",
            file_path="/path/to/file.py"
        )

        assert result.compiled is False
        assert result.compile_error == ""

    def test_execution_result_with_compile_info(self):
        """Test ExecutionResult with compilation fields."""
        result = ExecutionResult(
            exit_code=1,
            stdout="",
            stderr="compilation failed",
            timed_out=False,
            language="java",
            file_path="/path/to/Main.java",
            compiled=False,
            compile_error="Main.java:1: error: ';' expected"
        )

        assert result.compiled is False
        assert result.compile_error == "Main.java:1: error: ';' expected"

    def test_execution_result_timed_out(self):
        """Test ExecutionResult for timed out execution."""
        result = ExecutionResult(
            exit_code=1,
            stdout="",
            stderr="Execution timed out after 300 seconds",
            timed_out=True,
            language="python",
            file_path="/path/to/slow.py"
        )

        assert result.timed_out is True
        assert "timed out" in result.stderr

    def test_execution_result_equality(self):
        """Test that identical ExecutionResults are equal."""
        result1 = ExecutionResult(
            exit_code=0,
            stdout="test",
            stderr="",
            timed_out=False,
            language="python",
            file_path="/path/to/file.py"
        )
        result2 = ExecutionResult(
            exit_code=0,
            stdout="test",
            stderr="",
            timed_out=False,
            language="python",
            file_path="/path/to/file.py"
        )

        assert result1 == result2

    def test_execution_result_inequality(self):
        """Test that different ExecutionResults are not equal."""
        result1 = ExecutionResult(
            exit_code=0,
            stdout="test",
            stderr="",
            timed_out=False,
            language="python",
            file_path="/path/to/file.py"
        )
        result2 = ExecutionResult(
            exit_code=1,
            stdout="test",
            stderr="error",
            timed_out=False,
            language="python",
            file_path="/path/to/file.py"
        )

        assert result1 != result2


class TestDefaultTimeout:
    """Test DEFAULT_TIMEOUT_SECONDS constant."""

    def test_default_timeout_value(self):
        """Test that default timeout is 5 minutes (300 seconds)."""
        assert DEFAULT_TIMEOUT_SECONDS == 300


class TestProblemExecutorInit:
    """Test ProblemExecutor initialization."""

    def test_init_with_repository(self):
        """Test initializing ProblemExecutor with a Repository."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        assert executor.repo is mock_repo

    def test_init_stores_repo_reference(self):
        """Test that executor stores the repository reference."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = Path("/tmp/build")
        executor = ProblemExecutor(mock_repo)

        assert executor.repo.build_dir == Path("/tmp/build")


class TestProblemExecutorExecuteValidation:
    """Test ProblemExecutor.execute validation."""

    def test_execute_missing_file_path(self):
        """Test that execute raises ValueError when file_path is missing."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        problem = {'language': 'python', 'problem_id': 'test'}

        with pytest.raises(ValueError, match="Problem has no associated file path"):
            executor.execute(problem)

    def test_execute_empty_file_path(self):
        """Test that execute raises ValueError when file_path is empty."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        problem = {'language': 'python', 'file_path': '', 'problem_id': 'test'}

        with pytest.raises(ValueError, match="Problem has no associated file path"):
            executor.execute(problem)

    def test_execute_file_not_found(self, tmp_path):
        """Test that execute raises ValueError when file doesn't exist."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        non_existent_file = tmp_path / "non_existent.py"
        problem = {
            'language': 'python',
            'file_path': str(non_existent_file),
            'problem_id': 'test'
        }

        with pytest.raises(ValueError, match="File not found"):
            executor.execute(problem)

    def test_execute_unsupported_language(self, tmp_path):
        """Test that execute raises ValueError for unsupported language."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        # Create a temporary file
        test_file = tmp_path / "test.rb"
        test_file.write_text("puts 'Hello'")

        problem = {
            'language': 'ruby',
            'file_path': str(test_file),
            'problem_id': 'test'
        }

        with pytest.raises(ValueError, match="Unsupported language: ruby"):
            executor.execute(problem)


class TestProblemExecutorExecuteLanguageRouting:
    """Test ProblemExecutor.execute language routing."""

    def test_execute_routes_to_python(self, tmp_path):
        """Test that python language routes to _run_python."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"
        test_file.write_text("print('hello')")

        problem = {
            'language': 'python',
            'file_path': str(test_file),
            'problem_id': 'test'
        }

        with patch.object(executor, '_run_python') as mock_run:
            mock_run.return_value = ExecutionResult(
                exit_code=0, stdout="hello", stderr="",
                timed_out=False, language="python", file_path=str(test_file)
            )
            result = executor.execute(problem)
            mock_run.assert_called_once()

    def test_execute_routes_python3_to_python(self, tmp_path):
        """Test that python3 language also routes to _run_python."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"
        test_file.write_text("print('hello')")

        problem = {
            'language': 'python3',
            'file_path': str(test_file),
            'problem_id': 'test'
        }

        with patch.object(executor, '_run_python') as mock_run:
            mock_run.return_value = ExecutionResult(
                exit_code=0, stdout="hello", stderr="",
                timed_out=False, language="python", file_path=str(test_file)
            )
            result = executor.execute(problem)
            mock_run.assert_called_once()

    def test_execute_routes_to_java(self, tmp_path):
        """Test that java language routes to _run_java."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "Main.java"
        test_file.write_text("public class Main { public static void main(String[] args) {} }")

        problem = {
            'language': 'java',
            'file_path': str(test_file),
            'problem_id': 'test'
        }

        with patch.object(executor, '_run_java') as mock_run:
            mock_run.return_value = ExecutionResult(
                exit_code=0, stdout="", stderr="",
                timed_out=False, language="java", file_path=str(test_file),
                compiled=True
            )
            result = executor.execute(problem)
            mock_run.assert_called_once()

    def test_execute_routes_to_cpp(self, tmp_path):
        """Test that cpp language routes to _run_cpp."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.cpp"
        test_file.write_text("int main() { return 0; }")

        problem = {
            'language': 'cpp',
            'file_path': str(test_file),
            'problem_id': 'test'
        }

        with patch.object(executor, '_run_cpp') as mock_run:
            mock_run.return_value = ExecutionResult(
                exit_code=0, stdout="", stderr="",
                timed_out=False, language="cpp", file_path=str(test_file),
                compiled=True
            )
            result = executor.execute(problem)
            mock_run.assert_called_once()

    def test_execute_default_language_is_python(self, tmp_path):
        """Test that missing language defaults to python."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"
        test_file.write_text("print('hello')")

        problem = {
            'file_path': str(test_file),
            'problem_id': 'test'
        }

        with patch.object(executor, '_run_python') as mock_run:
            mock_run.return_value = ExecutionResult(
                exit_code=0, stdout="hello", stderr="",
                timed_out=False, language="python", file_path=str(test_file)
            )
            result = executor.execute(problem)
            mock_run.assert_called_once()

    def test_execute_default_problem_id_is_unknown(self, tmp_path):
        """Test that missing problem_id defaults to 'unknown'."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"
        test_file.write_text("print('hello')")

        problem = {
            'language': 'python',
            'file_path': str(test_file)
        }

        with patch.object(executor, '_run_python') as mock_run:
            mock_run.return_value = ExecutionResult(
                exit_code=0, stdout="hello", stderr="",
                timed_out=False, language="python", file_path=str(test_file)
            )
            executor.execute(problem)
            # Should not raise an error


class TestProblemExecutorRunPython:
    """Test ProblemExecutor._run_python method."""

    def test_run_python_success(self, tmp_path):
        """Test successful Python execution."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello, World!\n"
        mock_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', return_value=mock_result) as mock_run:
            result = executor._run_python(test_file, 300)

            mock_run.assert_called_once_with(
                ['python', str(test_file)],
                cwd=test_file.parent,
                capture_output=True,
                text=True,
                timeout=300
            )

            assert result.exit_code == 0
            assert result.stdout == "Hello, World!\n"
            assert result.stderr == ""
            assert result.timed_out is False
            assert result.language == "python"
            assert result.file_path == str(test_file)

    def test_run_python_with_error(self, tmp_path):
        """Test Python execution with non-zero exit code."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "NameError: name 'undefined' is not defined"

        with patch('bytedojo.core.execution.subprocess.run', return_value=mock_result):
            result = executor._run_python(test_file, 300)

            assert result.exit_code == 1
            assert result.stderr == "NameError: name 'undefined' is not defined"
            assert result.timed_out is False

    def test_run_python_timeout(self, tmp_path):
        """Test Python execution timeout."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"

        with patch('bytedojo.core.execution.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='python', timeout=10)):
            result = executor._run_python(test_file, 10)

            assert result.exit_code == 1
            assert result.timed_out is True
            assert "timed out after 10 seconds" in result.stderr
            assert result.language == "python"

    def test_run_python_custom_timeout(self, tmp_path):
        """Test Python execution with custom timeout value."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "done"
        mock_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', return_value=mock_result) as mock_run:
            executor._run_python(test_file, 60)

            # Verify custom timeout was passed
            call_args = mock_run.call_args
            assert call_args.kwargs['timeout'] == 60


class TestProblemExecutorRunJava:
    """Test ProblemExecutor._run_java method."""

    def test_run_java_compile_success_run_success(self, tmp_path):
        """Test successful Java compilation and execution."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "Main.java"
        build_dir = tmp_path / "build"

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        run_result = MagicMock()
        run_result.returncode = 0
        run_result.stdout = "Java output\n"
        run_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', side_effect=[compile_result, run_result]) as mock_run:
            result = executor._run_java(test_file, build_dir, 300)

            # Verify compile call
            compile_call = mock_run.call_args_list[0]
            assert compile_call[0][0] == ['javac', '-d', str(build_dir), str(test_file)]

            # Verify run call
            run_call = mock_run.call_args_list[1]
            assert run_call[0][0] == ['java', 'Main']
            assert run_call.kwargs['cwd'] == build_dir

            assert result.exit_code == 0
            assert result.stdout == "Java output\n"
            assert result.compiled is True
            assert result.language == "java"

    def test_run_java_compile_failure(self, tmp_path):
        """Test Java compilation failure."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "Main.java"
        build_dir = tmp_path / "build"

        compile_result = MagicMock()
        compile_result.returncode = 1
        compile_result.stderr = "Main.java:1: error: ';' expected"

        with patch('bytedojo.core.execution.subprocess.run', return_value=compile_result):
            result = executor._run_java(test_file, build_dir, 300)

            assert result.exit_code == 1
            assert result.compiled is False
            assert result.compile_error == "Main.java:1: error: ';' expected"
            assert result.stderr == "Main.java:1: error: ';' expected"
            assert result.language == "java"

    def test_run_java_execution_timeout(self, tmp_path):
        """Test Java execution timeout (after successful compilation)."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "Main.java"
        build_dir = tmp_path / "build"

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        def side_effect(*args, **kwargs):
            if 'javac' in args[0]:
                return compile_result
            raise subprocess.TimeoutExpired(cmd='java', timeout=300)

        with patch('bytedojo.core.execution.subprocess.run', side_effect=side_effect):
            result = executor._run_java(test_file, build_dir, 300)

            assert result.exit_code == 1
            assert result.timed_out is True
            assert result.compiled is True
            assert "timed out after 300 seconds" in result.stderr

    def test_run_java_creates_build_directory(self, tmp_path):
        """Test that _run_java creates build directory if it doesn't exist."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "Main.java"
        build_dir = tmp_path / "nested" / "build" / "dir"

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        run_result = MagicMock()
        run_result.returncode = 0
        run_result.stdout = ""
        run_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', side_effect=[compile_result, run_result]):
            executor._run_java(test_file, build_dir, 300)

            assert build_dir.exists()

    def test_run_java_runtime_error(self, tmp_path):
        """Test Java execution with runtime error."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "Main.java"
        build_dir = tmp_path / "build"

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        run_result = MagicMock()
        run_result.returncode = 1
        run_result.stdout = ""
        run_result.stderr = "Exception in thread \"main\" java.lang.NullPointerException"

        with patch('bytedojo.core.execution.subprocess.run', side_effect=[compile_result, run_result]):
            result = executor._run_java(test_file, build_dir, 300)

            assert result.exit_code == 1
            assert result.compiled is True
            assert "NullPointerException" in result.stderr


class TestProblemExecutorRunCpp:
    """Test ProblemExecutor._run_cpp method."""

    def test_run_cpp_compile_success_run_success_unix(self, tmp_path):
        """Test successful C++ compilation and execution on Unix."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.cpp"
        build_dir = tmp_path / "build"

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        run_result = MagicMock()
        run_result.returncode = 0
        run_result.stdout = "C++ output\n"
        run_result.stderr = ""

        with patch('bytedojo.core.execution.os.name', 'posix'):
            with patch('bytedojo.core.execution.subprocess.run', side_effect=[compile_result, run_result]) as mock_run:
                result = executor._run_cpp(test_file, build_dir, 300)

                # Verify compile call
                compile_call = mock_run.call_args_list[0]
                assert compile_call[0][0] == ['g++', '-o', str(build_dir / 'solution'), str(test_file)]

                assert result.exit_code == 0
                assert result.stdout == "C++ output\n"
                assert result.compiled is True
                assert result.language == "cpp"

    def test_run_cpp_compile_success_run_success_windows(self, tmp_path):
        """Test successful C++ compilation and execution on Windows."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.cpp"
        build_dir = tmp_path / "build"

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        run_result = MagicMock()
        run_result.returncode = 0
        run_result.stdout = "C++ output\n"
        run_result.stderr = ""

        with patch('bytedojo.core.execution.os.name', 'nt'):
            with patch('bytedojo.core.execution.subprocess.run', side_effect=[compile_result, run_result]) as mock_run:
                result = executor._run_cpp(test_file, build_dir, 300)

                # Verify compile call - should use .exe on Windows
                compile_call = mock_run.call_args_list[0]
                assert compile_call[0][0] == ['g++', '-o', str(build_dir / 'solution.exe'), str(test_file)]

                assert result.exit_code == 0
                assert result.compiled is True

    def test_run_cpp_compile_failure(self, tmp_path):
        """Test C++ compilation failure."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.cpp"
        build_dir = tmp_path / "build"

        compile_result = MagicMock()
        compile_result.returncode = 1
        compile_result.stderr = "error: expected ';' before '}'"

        with patch('bytedojo.core.execution.subprocess.run', return_value=compile_result):
            result = executor._run_cpp(test_file, build_dir, 300)

            assert result.exit_code == 1
            assert result.compiled is False
            assert result.compile_error == "error: expected ';' before '}'"
            assert result.language == "cpp"

    def test_run_cpp_execution_timeout(self, tmp_path):
        """Test C++ execution timeout (after successful compilation)."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.cpp"
        build_dir = tmp_path / "build"

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        def side_effect(*args, **kwargs):
            if 'g++' in args[0]:
                return compile_result
            raise subprocess.TimeoutExpired(cmd='./solution', timeout=300)

        with patch('bytedojo.core.execution.subprocess.run', side_effect=side_effect):
            result = executor._run_cpp(test_file, build_dir, 300)

            assert result.exit_code == 1
            assert result.timed_out is True
            assert result.compiled is True
            assert "timed out after 300 seconds" in result.stderr

    def test_run_cpp_creates_build_directory(self, tmp_path):
        """Test that _run_cpp creates build directory if it doesn't exist."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.cpp"
        build_dir = tmp_path / "nested" / "build" / "dir"

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        run_result = MagicMock()
        run_result.returncode = 0
        run_result.stdout = ""
        run_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', side_effect=[compile_result, run_result]):
            executor._run_cpp(test_file, build_dir, 300)

            assert build_dir.exists()

    def test_run_cpp_runtime_error(self, tmp_path):
        """Test C++ execution with runtime error."""
        mock_repo = MagicMock(spec=Repository)
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.cpp"
        build_dir = tmp_path / "build"

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        run_result = MagicMock()
        run_result.returncode = 139  # Segmentation fault
        run_result.stdout = ""
        run_result.stderr = "Segmentation fault (core dumped)"

        with patch('bytedojo.core.execution.subprocess.run', side_effect=[compile_result, run_result]):
            result = executor._run_cpp(test_file, build_dir, 300)

            assert result.exit_code == 139
            assert result.compiled is True
            assert "Segmentation fault" in result.stderr


class TestProblemExecutorExecuteIntegration:
    """Integration tests for ProblemExecutor.execute method."""

    def test_execute_with_relative_path(self, tmp_path, monkeypatch):
        """Test execute handles relative file paths."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        # Create file in tmp_path
        test_file = tmp_path / "solution.py"
        test_file.write_text("print('hello')")

        # Change cwd to tmp_path
        monkeypatch.chdir(tmp_path)

        problem = {
            'language': 'python',
            'file_path': 'solution.py',  # Relative path
            'problem_id': 'test'
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello\n"
        mock_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', return_value=mock_result):
            result = executor.execute(problem)

            assert result.exit_code == 0

    def test_execute_with_absolute_path(self, tmp_path):
        """Test execute handles absolute file paths."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"
        test_file.write_text("print('hello')")

        problem = {
            'language': 'python',
            'file_path': str(test_file),  # Absolute path
            'problem_id': 'test'
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello\n"
        mock_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', return_value=mock_result):
            result = executor.execute(problem)

            assert result.exit_code == 0

    def test_execute_passes_custom_timeout(self, tmp_path):
        """Test that custom timeout is passed through execute."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"
        test_file.write_text("print('hello')")

        problem = {
            'language': 'python',
            'file_path': str(test_file),
            'problem_id': 'test'
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello\n"
        mock_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', return_value=mock_result) as mock_run:
            executor.execute(problem, timeout=60)

            call_args = mock_run.call_args
            assert call_args.kwargs['timeout'] == 60

    def test_execute_uses_default_timeout(self, tmp_path):
        """Test that default timeout is used when not specified."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "solution.py"
        test_file.write_text("print('hello')")

        problem = {
            'language': 'python',
            'file_path': str(test_file),
            'problem_id': 'test'
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello\n"
        mock_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', return_value=mock_result) as mock_run:
            executor.execute(problem)

            call_args = mock_run.call_args
            assert call_args.kwargs['timeout'] == DEFAULT_TIMEOUT_SECONDS

    def test_execute_build_dir_uses_problem_id(self, tmp_path):
        """Test that build directory is created using problem_id."""
        mock_repo = MagicMock(spec=Repository)
        mock_repo.build_dir = tmp_path / "build"
        executor = ProblemExecutor(mock_repo)

        test_file = tmp_path / "Main.java"
        test_file.write_text("public class Main { public static void main(String[] args) {} }")

        problem = {
            'language': 'java',
            'file_path': str(test_file),
            'problem_id': 'two-sum'
        }

        compile_result = MagicMock()
        compile_result.returncode = 0
        compile_result.stderr = ""

        run_result = MagicMock()
        run_result.returncode = 0
        run_result.stdout = ""
        run_result.stderr = ""

        with patch('bytedojo.core.execution.subprocess.run', side_effect=[compile_result, run_result]) as mock_run:
            executor.execute(problem)

            # Check that build_dir/problem_id was used for compilation
            compile_call = mock_run.call_args_list[0]
            expected_build_dir = str(tmp_path / "build" / "two-sum")
            assert expected_build_dir in compile_call[0][0][2]
