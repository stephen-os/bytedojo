"""
Tests for Executor.
"""

import pytest
from pathlib import Path
from textwrap import dedent

from bytedojo.core.executor import Executor, ExecutionResult


class TestExecutionResultDataclass:
    """Test ExecutionResult dataclass."""
    
    def test_execution_result_creation(self):
        """Test creating an ExecutionResult."""
        result = ExecutionResult(
            passed=True,
            output="Test output",
            error=None,
            status='passed'
        )
        
        assert result.passed is True
        assert result.output == "Test output"
        assert result.error is None
        assert result.status == 'passed'
    
    def test_execution_result_with_error(self):
        """Test ExecutionResult with error."""
        result = ExecutionResult(
            passed=False,
            output="",
            error="Error message",
            status='failed'
        )
        
        assert result.passed is False
        assert result.error == "Error message"
        assert result.status == 'failed'
    
    def test_execution_result_default_status(self):
        """Test ExecutionResult default status."""
        result = ExecutionResult(passed=False, output="")
        
        assert result.status == 'untested'


class ExecutorInit:
    """Test Executor initialization."""
    
    def test_init_with_default_timeout(self):
        """Test initialization with default timeout."""
        executor = Executor()
        
        assert executor.timeout == 30
    
    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        executor = Executor(timeout=60)
        
        assert executor.timeout == 60
    
    def test_init_has_logger(self):
        """Test that executor has a logger."""
        executor = Executor()
        
        assert hasattr(executor, 'logger')
        assert executor.logger is not None


class ExecutorRunTest:
    """Test Executor.run_test method."""
    
    def test_run_test_file_not_found(self, tmp_path):
        """Test running a non-existent file."""
        executor = Executor()
        file_path = tmp_path / "nonexistent.py"
        
        result = executor.run_test(file_path)
        
        assert result.passed is False
        assert result.status == 'error'
        assert "File not found" in result.error
    
    def test_run_test_passing(self, tmp_path):
        """Test running a passing test."""
        executor = Executor()
        
        # Create passing test file
        test_file = tmp_path / "test_passing.py"
        test_file.write_text(dedent('''
            def run_tests():
                print("Test 1: PASSED")
                print("Test 2: PASSED")
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        result = executor.run_test(test_file)
        
        assert result.passed is True
        assert result.status == 'passed'
        assert result.error is None
        assert "Test 1: PASSED" in result.output
    
    def test_run_test_failing(self, tmp_path):
        """Test running a failing test."""
        executor = Executor()
        
        # Create failing test file
        test_file = tmp_path / "test_failing.py"
        test_file.write_text(dedent('''
            def run_tests():
                print("Test 1: PASSED")
                raise AssertionError("Test 2 failed")
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        result = executor.run_test(test_file)
        
        assert result.passed is False
        assert result.status == 'failed'
        assert result.error is not None
        assert "AssertionError" in result.error
    
    def test_run_test_with_syntax_error(self, tmp_path):
        """Test running a file with syntax error."""
        executor = Executor()
        
        # Create file with syntax error
        test_file = tmp_path / "test_syntax_error.py"
        test_file.write_text("def broken syntax here")
        
        result = executor.run_test(test_file)
        
        assert result.passed is False
        assert result.status == 'failed'
        assert result.error is not None
    
    def test_run_test_with_import_error(self, tmp_path):
        """Test running a file with import error."""
        executor = Executor()
        
        # Create file with import error
        test_file = tmp_path / "test_import_error.py"
        test_file.write_text(dedent('''
            import nonexistent_module
            
            def run_tests():
                pass
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        result = executor.run_test(test_file)
        
        assert result.passed is False
        assert result.status == 'failed'
    
    def test_run_test_timeout(self, tmp_path):
        """Test that long-running tests timeout."""
        executor = Executor(timeout=1)  # 1 second timeout
        
        # Create long-running test
        test_file = tmp_path / "test_timeout.py"
        test_file.write_text(dedent('''
            import time
            
            def run_tests():
                time.sleep(10)  # Sleep longer than timeout
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        result = executor.run_test(test_file)
        
        assert result.passed is False
        assert result.status == 'error'
        assert "timed out" in result.error.lower()
    
    def test_run_test_with_output(self, tmp_path):
        """Test that output is captured."""
        executor = Executor()
        
        test_file = tmp_path / "test_output.py"
        test_file.write_text(dedent('''
            def run_tests():
                print("Line 1")
                print("Line 2")
                print("Line 3")
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        result = executor.run_test(test_file)
        
        assert result.passed is True
        assert "Line 1" in result.output
        assert "Line 2" in result.output
        assert "Line 3" in result.output
    
    def test_run_test_empty_file(self, tmp_path):
        """Test running an empty file."""
        executor = Executor()
        
        test_file = tmp_path / "test_empty.py"
        test_file.write_text("")
        
        result = executor.run_test(test_file)
        
        # Empty file should run successfully (exit code 0)
        assert result.passed is True
        assert result.status == 'passed'


class ExecutorValidateTestFile:
    """Test Executor.validate_test_file method."""
    
    def test_validate_file_not_found(self, tmp_path):
        """Test validating non-existent file."""
        executor = Executor()
        file_path = tmp_path / "nonexistent.py"
        
        result = executor.validate_test_file(file_path)
        
        assert result is False
    
    def test_validate_valid_test_file(self, tmp_path):
        """Test validating a valid test file."""
        executor = Executor()
        
        test_file = tmp_path / "test_valid.py"
        test_file.write_text(dedent('''
            def run_tests():
                print("Testing...")
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        result = executor.validate_test_file(test_file)
        
        assert result is True
    
    def test_validate_missing_run_tests(self, tmp_path):
        """Test validating file without run_tests function."""
        executor = Executor()
        
        test_file = tmp_path / "test_invalid.py"
        test_file.write_text(dedent('''
            def some_function():
                pass
            
            if __name__ == "__main__":
                some_function()
        ''').strip())
        
        result = executor.validate_test_file(test_file)
        
        assert result is False
    
    def test_validate_missing_main_guard(self, tmp_path):
        """Test validating file without __main__ guard."""
        executor = Executor()
        
        test_file = tmp_path / "test_no_guard.py"
        test_file.write_text(dedent('''
            def run_tests():
                print("Testing...")
        ''').strip())
        
        result = executor.validate_test_file(test_file)
        
        assert result is False
    
    def test_validate_unreadable_file(self, tmp_path):
        """Test validating a file that cannot be read."""
        executor = Executor()
        
        # Create a binary file
        test_file = tmp_path / "test_binary.dat"
        test_file.write_bytes(b'\x00\x01\x02\x03')
        
        # Should handle gracefully
        result = executor.validate_test_file(test_file)
        
        # Binary files might not have the required strings
        assert isinstance(result, bool)


class ExecutorIntegration:
    """Integration tests for Executor."""
    
    def test_run_multiple_tests(self, tmp_path):
        """Test running multiple test files."""
        executor = Executor()
        
        # Create multiple test files
        test1 = tmp_path / "test1.py"
        test1.write_text(dedent('''
            def run_tests():
                print("Test 1 passed")
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        test2 = tmp_path / "test2.py"
        test2.write_text(dedent('''
            def run_tests():
                print("Test 2 passed")
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        result1 = executor.run_test(test1)
        result2 = executor.run_test(test2)
        
        assert result1.passed is True
        assert result2.passed is True
    
    def test_validate_and_run_workflow(self, tmp_path):
        """Test complete workflow: validate then run."""
        executor = Executor()
        
        test_file = tmp_path / "test_workflow.py"
        test_file.write_text(dedent('''
            def run_tests():
                assert 1 + 1 == 2
                print("Math works!")
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        # Validate first
        is_valid = executor.validate_test_file(test_file)
        assert is_valid is True
        
        # Then run
        result = executor.run_test(test_file)
        assert result.passed is True
        assert "Math works!" in result.output
    
    def test_realistic_leetcode_test(self, tmp_path):
        """Test with a realistic LeetCode-style test file."""
        executor = Executor()
        
        test_file = tmp_path / "0001-two-sum.py"
        test_file.write_text(dedent('''
            from typing import List
            
            class Solution:
                def twoSum(self, nums: List[int], target: int) -> List[int]:
                    seen = {}
                    for i, num in enumerate(nums):
                        complement = target - num
                        if complement in seen:
                            return [seen[complement], i]
                        seen[num] = i
                    return []
            
            def run_tests():
                solution = Solution()
                
                result1 = solution.twoSum([2,7,11,15], 9)
                expected1 = [0, 1]
                print(f"Test 1: Expected {expected1}, Got {result1}")
                assert result1 == expected1
                
                result2 = solution.twoSum([3,2,4], 6)
                expected2 = [1, 2]
                print(f"Test 2: Expected {expected2}, Got {result2}")
                assert result2 == expected2
                
                print("All tests passed!")
            
            if __name__ == "__main__":
                run_tests()
        ''').strip())
        
        is_valid = executor.validate_test_file(test_file)
        assert is_valid is True
        
        result = executor.run_test(test_file)
        assert result.passed is True
        assert "All tests passed!" in result.output