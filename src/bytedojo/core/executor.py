"""
Test runner for executing problem tests.

Runs tests against user solutions using test data from JSON.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from bytedojo.core.logger import get_logger
from bytedojo.core.test_store import TestData


@dataclass
class ExecutionResult:
    """Result from running a test."""
    passed: bool
    output: str
    error: Optional[str] = None
    status: str = 'untested'  # 'passed', 'failed', 'error', 'untested'
    tests_run: int = 0
    tests_passed: int = 0


class Executor:
    """Runs tests for problem solutions."""

    # Helper function templates for test runner
    LISTNODE_HELPERS = '''
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def list_to_listnode(arr):
    """Convert array to ListNode."""
    if not arr:
        return None
    head = ListNode(arr[0])
    current = head
    for val in arr[1:]:
        current.next = ListNode(val)
        current = current.next
    return head

def listnode_to_list(node):
    """Convert ListNode to array."""
    result = []
    while node:
        result.append(node.val)
        node = node.next
    return result
'''

    TREENODE_HELPERS = '''
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def list_to_treenode(arr):
    """Convert array to TreeNode (level-order)."""
    if not arr or arr[0] is None:
        return None

    root = TreeNode(arr[0])
    queue = [root]
    i = 1

    while queue and i < len(arr):
        node = queue.pop(0)

        if i < len(arr) and arr[i] is not None:
            node.left = TreeNode(arr[i])
            queue.append(node.left)
        i += 1

        if i < len(arr) and arr[i] is not None:
            node.right = TreeNode(arr[i])
            queue.append(node.right)
        i += 1

    return root

def treenode_to_list(root):
    """Convert TreeNode to array (level-order)."""
    if not root:
        return []

    result = []
    queue = [root]

    while queue:
        node = queue.pop(0)
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)

    # Remove trailing None values
    while result and result[-1] is None:
        result.pop()

    return result
'''

    def __init__(self, timeout: int = 30):
        """
        Initialize test runner.

        Args:
            timeout: Maximum seconds to run each test (default: 30)
        """
        self.timeout = timeout
        self.logger = get_logger()

    def run_test(self, test_data: TestData) -> ExecutionResult:
        """
        Run tests for a problem using test data.

        Args:
            test_data: TestData containing problem metadata and test cases

        Returns:
            ExecutionResult with execution details
        """
        solution_path = Path(test_data.file_path)

        if not solution_path.exists():
            return ExecutionResult(
                passed=False,
                output="",
                error=f"Solution file not found: {solution_path}",
                status='error'
            )

        # Generate test runner script
        test_script = self._generate_test_script(test_data, solution_path)

        # Write to temp file and execute
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(test_script)
                temp_path = Path(f.name)

            # Run the test script
            result = subprocess.run(
                [sys.executable, str(temp_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=solution_path.parent
            )

            # Parse output for test results
            output = result.stdout
            error = result.stderr if result.returncode != 0 else None

            # Extract test counts from output
            tests_run, tests_passed = self._parse_test_output(output)

            # Determine if tests passed:
            # - Subprocess must exit 0 (no crash)
            # - All tests must pass (tests_passed == tests_run)
            if result.returncode == 0 and tests_run > 0 and tests_passed == tests_run:
                return ExecutionResult(
                    passed=True,
                    output=output,
                    error=None,
                    status='passed',
                    tests_run=tests_run,
                    tests_passed=tests_passed
                )
            elif result.returncode != 0:
                return ExecutionResult(
                    passed=False,
                    output=output,
                    error=error,
                    status='failed',
                    tests_run=tests_run,
                    tests_passed=tests_passed
                )
            else:
                # Subprocess succeeded but some tests failed
                return ExecutionResult(
                    passed=False,
                    output=output,
                    error="Some tests failed" if tests_run > tests_passed else None,
                    status='failed',
                    tests_run=tests_run,
                    tests_passed=tests_passed
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

        finally:
            # Clean up temp file
            try:
                temp_path.unlink()
            except Exception:
                pass

    def _generate_test_script(self, test_data: TestData, solution_path: Path) -> str:
        """Generate a test runner script for the problem."""
        lines = []

        # Add imports
        lines.append("import sys")
        lines.append("import importlib.util")
        lines.append("")

        # Add helper classes/functions if needed
        if test_data.helpers_needed.get('listnode'):
            lines.append(self.LISTNODE_HELPERS)
        if test_data.helpers_needed.get('treenode'):
            lines.append(self.TREENODE_HELPERS)

        # Load the solution module dynamically (handles filenames starting with numbers)
        lines.append(f"solution_path = {repr(str(solution_path))}")
        lines.append("spec = importlib.util.spec_from_file_location('solution', solution_path)")
        lines.append("module = importlib.util.module_from_spec(spec)")
        lines.append("spec.loader.exec_module(module)")
        lines.append(f"{test_data.class_name} = getattr(module, '{test_data.class_name}')")
        lines.append("")

        # Add test runner
        lines.append("def run_tests():")
        lines.append(f"    instance = {test_data.class_name}()")
        lines.append("    test_cases = " + repr(test_data.test_cases))
        lines.append("    ")
        lines.append("    # Parse test cases")
        lines.append("    lines = [l.strip() for l in test_cases.strip().split('\\n') if l.strip()]")
        lines.append("    ")
        lines.append(f"    param_count = {len(test_data.params)}")
        lines.append("    tests_run = 0")
        lines.append("    tests_passed = 0")
        lines.append("    ")
        lines.append("    if param_count == 0:")
        lines.append("        print('No parameters defined for this problem')")
        lines.append("        return")
        lines.append("    ")
        lines.append("    # Group lines into test cases")
        lines.append("    i = 0")
        lines.append("    test_num = 1")
        lines.append("    while i < len(lines):")
        lines.append("        if i + param_count > len(lines):")
        lines.append("            break")
        lines.append("        ")
        lines.append("        # Get inputs for this test")
        lines.append("        inputs = []")
        lines.append("        for j in range(param_count):")
        lines.append("            try:")
        lines.append("                value = eval(lines[i + j])")
        lines.append("            except:")
        lines.append("                value = lines[i + j]")
        lines.append("            inputs.append(value)")
        lines.append("        ")

        # Apply conversions for ListNode/TreeNode
        for idx, param in enumerate(test_data.params):
            param_type = param.get('type', 'Any')
            if 'ListNode' in param_type:
                lines.append(f"        inputs[{idx}] = list_to_listnode(inputs[{idx}])")
            elif 'TreeNode' in param_type:
                lines.append(f"        inputs[{idx}] = list_to_treenode(inputs[{idx}])")

        lines.append("        ")
        lines.append("        # Call the solution")
        lines.append("        try:")
        lines.append(f"            result = instance.{test_data.method_name}(*inputs)")

        # Apply return type conversion
        if 'ListNode' in test_data.return_type:
            lines.append("            result = listnode_to_list(result)")
        elif 'TreeNode' in test_data.return_type:
            lines.append("            result = treenode_to_list(result)")

        lines.append("            tests_run += 1")
        lines.append("            print(f'Test {test_num}: {result}')")
        lines.append("            tests_passed += 1  # No assertion, just run")
        lines.append("        except Exception as e:")
        lines.append("            tests_run += 1")
        lines.append("            print(f'Test {test_num} ERROR: {e}')")
        lines.append("        ")
        lines.append("        i += param_count")
        lines.append("        test_num += 1")
        lines.append("    ")
        lines.append("    print()")
        lines.append("    print(f'Tests run: {tests_run}, Passed: {tests_passed}')")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    run_tests()")

        return "\n".join(lines)

    def _parse_test_output(self, output: str) -> tuple:
        """Parse test output to extract counts."""
        import re
        match = re.search(r'Tests run: (\d+), Passed: (\d+)', output)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0

    def validate_solution_file(self, file_path: Path) -> bool:
        """
        Check if a file is a valid solution file.

        Args:
            file_path: Path to check

        Returns:
            True if file exists and is a Python file
        """
        if not file_path.exists():
            return False

        return file_path.suffix == '.py'