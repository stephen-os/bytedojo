"""
Test runner for executing problem tests.

Runs Python test files and captures results.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from bytedojo.core.logger import get_logger


@dataclass
class ExecutionResult:
    """Result from running a test."""
    passed: bool
    output: str
    error: Optional[str] = None
    status: str = 'untested'  # 'passed', 'failed', 'error', 'untested'


class Executor:
    """Runs tests for problem files."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize test runner.
        
        Args:
            timeout: Maximum seconds to run each test (default: 30)
        """
        self.timeout = timeout
        self.logger = get_logger()
    
    def run_test(self, file_path: Path) -> ExecutionResult:
        """
        Run tests for a problem file.
        
        Args:
            file_path: Path to the problem file
            
        Returns:
            ExecutionResult with execution details
        """
        if not file_path.exists():
            return ExecutionResult(
                passed=False,
                output="",
                error="File not found",
                status='error'
            )
        
        try:
            # Run the file as a Python script
            result = subprocess.run(
                [sys.executable, str(file_path.resolve())],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=file_path.parent
            )
            
            # Check exit code
            if result.returncode == 0:
                return ExecutionResult(
                    passed=True,
                    output=result.stdout,
                    error=None,
                    status='passed'
                )
            else:
                return ExecutionResult(
                    passed=False,
                    output=result.stdout,
                    error=result.stderr,
                    status='failed'
                )
        
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                passed=False,
                output="",
                error=f"Test timed out after {self.timeout} seconds",
                status='error'
            )
        
        except Exception as e:
            return ExecutionResult(
                passed=False,
                output="",
                error=f"Error running test: {str(e)}",
                status='error'
            )
    
    def validate_test_file(self, file_path: Path) -> bool:
        """
        Check if a file has a valid test structure.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file appears to have tests
        """
        if not file_path.exists():
            return False
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for test indicators
            has_run_tests = 'def run_tests():' in content
            has_main_guard = 'if __name__ == "__main__":' in content
            
            return has_run_tests and has_main_guard
        
        except Exception as e:
            self.logger.debug(f"Error validating test file: {e}")
            return False