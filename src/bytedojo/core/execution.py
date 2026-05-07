"""
Problem execution - Run solutions and capture results.

This module handles executing problem solutions across different languages,
capturing output, and returning structured results for the CLI to display.
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from bytedojo.core.repository import Repository


# Default timeout for subprocess execution (5 minutes)
DEFAULT_TIMEOUT_SECONDS = 300


@dataclass
class ExecutionResult:
    """Result of executing a problem solution."""
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    language: str
    file_path: str
    compiled: bool = False
    compile_error: str = ""


class ProblemExecutor:
    """Executes problem solutions across different languages."""

    def __init__(self, repo: Repository):
        """
        Initialize executor with repository context.

        Args:
            repo: The Repository instance for build paths
        """
        self.repo = repo

    def execute(self, problem: dict, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> ExecutionResult:
        """
        Execute a problem solution and return the result.

        Args:
            problem: Problem dict with 'language', 'file_path', 'problem_id'
            timeout: Execution timeout in seconds

        Returns:
            ExecutionResult with exit code, output, and status

        Raises:
            ValueError: If file_path is missing or file doesn't exist
            ValueError: If language is unsupported
        """
        language = problem.get('language', 'python')
        file_path_str = problem.get('file_path')
        problem_id = problem.get('problem_id', 'unknown')

        if not file_path_str:
            raise ValueError("Problem has no associated file path")

        # Resolve relative path from current directory
        file_path = Path(file_path_str)
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        # Get build directory for compiled languages
        build_dir = self.repo.build_dir / problem_id

        # Execute based on language
        if language in ('python', 'python3'):
            return self._run_python(file_path, timeout)
        elif language == 'java':
            return self._run_java(file_path, build_dir, timeout)
        elif language == 'cpp':
            return self._run_cpp(file_path, build_dir, timeout)
        else:
            raise ValueError(f"Unsupported language: {language}")

    def _run_python(self, file_path: Path, timeout: int) -> ExecutionResult:
        """
        Run a Python file and return result.

        Args:
            file_path: Path to the Python file
            timeout: Execution timeout in seconds

        Returns:
            ExecutionResult with captured output
        """
        try:
            result = subprocess.run(
                ['python', str(file_path)],
                cwd=file_path.parent,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                timed_out=False,
                language='python',
                file_path=str(file_path)
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                timed_out=True,
                language='python',
                file_path=str(file_path)
            )

    def _run_java(self, file_path: Path, build_dir: Path, timeout: int) -> ExecutionResult:
        """
        Compile and run a Java file, return result.

        Args:
            file_path: Path to the Java file
            build_dir: Directory for compiled .class files
            timeout: Execution timeout in seconds

        Returns:
            ExecutionResult with captured output
        """
        # Ensure build directory exists
        build_dir.mkdir(parents=True, exist_ok=True)

        # Compile to build directory
        compile_result = subprocess.run(
            ['javac', '-d', str(build_dir), str(file_path)],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return ExecutionResult(
                exit_code=compile_result.returncode,
                stdout="",
                stderr=compile_result.stderr,
                timed_out=False,
                language='java',
                file_path=str(file_path),
                compiled=False,
                compile_error=compile_result.stderr
            )

        # Run from build directory
        try:
            run_result = subprocess.run(
                ['java', 'Main'],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return ExecutionResult(
                exit_code=run_result.returncode,
                stdout=run_result.stdout,
                stderr=run_result.stderr,
                timed_out=False,
                language='java',
                file_path=str(file_path),
                compiled=True
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                timed_out=True,
                language='java',
                file_path=str(file_path),
                compiled=True
            )

    def _run_cpp(self, file_path: Path, build_dir: Path, timeout: int) -> ExecutionResult:
        """
        Compile and run a C++ file, return result.

        Args:
            file_path: Path to the C++ file
            build_dir: Directory for compiled executable
            timeout: Execution timeout in seconds

        Returns:
            ExecutionResult with captured output
        """
        # Ensure build directory exists
        build_dir.mkdir(parents=True, exist_ok=True)

        # Determine output name
        stem = file_path.stem
        if os.name == 'nt':  # Windows
            output_name = f"{stem}.exe"
        else:
            output_name = stem

        output_path = build_dir / output_name

        # Compile to build directory
        compile_result = subprocess.run(
            ['g++', '-o', str(output_path), str(file_path)],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return ExecutionResult(
                exit_code=compile_result.returncode,
                stdout="",
                stderr=compile_result.stderr,
                timed_out=False,
                language='cpp',
                file_path=str(file_path),
                compiled=False,
                compile_error=compile_result.stderr
            )

        # Run
        try:
            run_result = subprocess.run(
                [str(output_path)],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return ExecutionResult(
                exit_code=run_result.returncode,
                stdout=run_result.stdout,
                stderr=run_result.stderr,
                timed_out=False,
                language='cpp',
                file_path=str(file_path),
                compiled=True
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                timed_out=True,
                language='cpp',
                file_path=str(file_path),
                compiled=True
            )
