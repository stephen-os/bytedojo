"""
Test runner for executing problem tests.

Runs tests against user solutions using internal test data.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, List, Any
from dataclasses import dataclass, field

from bytedojo.core.logger import get_logger
from bytedojo.core.test_data import TestDataLoader, ProblemTestData, TestCase


@dataclass
class TestResult:
    """Result of a single test case."""
    test_num: int
    input: List[Any]
    expected: Any
    actual: Any
    passed: bool
    error: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result from running all tests for a problem."""
    passed: bool
    output: str
    error: Optional[str] = None
    status: str = 'untested'  # 'passed', 'failed', 'error', 'untested'
    tests_run: int = 0
    tests_passed: int = 0
    test_results: List[TestResult] = field(default_factory=list)


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
        self.test_data_loader = TestDataLoader()

    def run_tests_for_problem(
        self,
        source: str,
        problem_id: int,
        solution_path: Path,
        class_name: str = "Solution",
        method_name: str = None,
        needs_listnode: bool = False,
        needs_treenode: bool = False
    ) -> ExecutionResult:
        """
        Run tests for a problem using internal test data.

        Args:
            source: Problem source (e.g., 'leetcode')
            problem_id: Problem ID
            solution_path: Path to solution file
            class_name: Class name in solution
            method_name: Method to call
            needs_listnode: Whether ListNode helpers are needed
            needs_treenode: Whether TreeNode helpers are needed

        Returns:
            ExecutionResult with execution details
        """
        # Load test data
        test_data = self.test_data_loader.get_test_data(source, problem_id)
        if not test_data:
            return ExecutionResult(
                passed=False,
                output="",
                error=f"No test data found for {source} problem #{problem_id}",
                status='error'
            )

        solution_path = Path(solution_path).resolve()

        if not solution_path.exists():
            return ExecutionResult(
                passed=False,
                output="",
                error=f"Solution file not found: {solution_path}",
                status='error'
            )

        # Generate test runner script
        test_script = self._generate_test_script(
            test_data=test_data,
            solution_path=solution_path,
            class_name=class_name,
            method_name=method_name,
            needs_listnode=needs_listnode,
            needs_treenode=needs_treenode
        )

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

            # Parse the JSON results from output
            test_results, tests_run, tests_passed = self._parse_test_results(output)

            if result.returncode == 0 and tests_run > 0 and tests_passed == tests_run:
                return ExecutionResult(
                    passed=True,
                    output=output,
                    error=None,
                    status='passed',
                    tests_run=tests_run,
                    tests_passed=tests_passed,
                    test_results=test_results
                )
            else:
                return ExecutionResult(
                    passed=False,
                    output=output,
                    error=error,
                    status='failed',
                    tests_run=tests_run,
                    tests_passed=tests_passed,
                    test_results=test_results
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

    def _generate_test_script(
        self,
        test_data: ProblemTestData,
        solution_path: Path,
        class_name: str,
        method_name: str,
        needs_listnode: bool,
        needs_treenode: bool
    ) -> str:
        """Generate a test runner script for the problem."""
        lines = []

        # Add imports
        lines.append("import sys")
        lines.append("import json")
        lines.append("import importlib.util")
        lines.append("")

        # Add helper classes/functions if needed
        if needs_listnode:
            lines.append(self.LISTNODE_HELPERS)
        if needs_treenode:
            lines.append(self.TREENODE_HELPERS)

        # Load the solution module dynamically
        lines.append(f"solution_path = {repr(str(solution_path))}")
        lines.append("spec = importlib.util.spec_from_file_location('solution', solution_path)")
        lines.append("module = importlib.util.module_from_spec(spec)")
        lines.append("spec.loader.exec_module(module)")
        lines.append(f"{class_name} = getattr(module, '{class_name}')")
        lines.append("")

        # Build test cases
        tests_json = json.dumps([
            {"input": t.input, "expected": t.expected}
            for t in test_data.tests
        ])

        lines.append(f"test_cases = {tests_json}")
        lines.append("")

        # Add test runner
        lines.append("def run_tests():")
        lines.append(f"    instance = {class_name}()")
        lines.append("    results = []")
        lines.append("    tests_run = 0")
        lines.append("    tests_passed = 0")
        lines.append("")
        lines.append("    for i, test in enumerate(test_cases, 1):")
        lines.append("        inputs = test['input']")
        lines.append("        expected = test['expected']")
        lines.append("        tests_run += 1")
        lines.append("")
        lines.append("        try:")

        # Call the method
        if method_name:
            lines.append(f"            actual = instance.{method_name}(*inputs)")
        else:
            lines.append("            # Method name not specified")
            lines.append("            actual = None")

        lines.append("")
        lines.append("            # Compare results")
        lines.append("            passed = actual == expected")
        lines.append("            if passed:")
        lines.append("                tests_passed += 1")
        lines.append("")
        lines.append("            results.append({")
        lines.append("                'test_num': i,")
        lines.append("                'input': inputs,")
        lines.append("                'expected': expected,")
        lines.append("                'actual': actual,")
        lines.append("                'passed': passed,")
        lines.append("                'error': None")
        lines.append("            })")
        lines.append("")
        lines.append("        except Exception as e:")
        lines.append("            results.append({")
        lines.append("                'test_num': i,")
        lines.append("                'input': inputs,")
        lines.append("                'expected': expected,")
        lines.append("                'actual': None,")
        lines.append("                'passed': False,")
        lines.append("                'error': str(e)")
        lines.append("            })")
        lines.append("")
        lines.append("    # Output results as JSON")
        lines.append("    print('===RESULTS===')")
        lines.append("    print(json.dumps({")
        lines.append("        'tests_run': tests_run,")
        lines.append("        'tests_passed': tests_passed,")
        lines.append("        'results': results")
        lines.append("    }))")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    run_tests()")

        return "\n".join(lines)

    def _parse_test_results(self, output: str) -> tuple:
        """Parse test output to extract results."""
        import json
        import re

        test_results = []
        tests_run = 0
        tests_passed = 0

        # Find the JSON results section
        match = re.search(r'===RESULTS===\n(.+)', output, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1).strip())
                tests_run = data.get('tests_run', 0)
                tests_passed = data.get('tests_passed', 0)

                for r in data.get('results', []):
                    test_results.append(TestResult(
                        test_num=r.get('test_num', 0),
                        input=r.get('input', []),
                        expected=r.get('expected'),
                        actual=r.get('actual'),
                        passed=r.get('passed', False),
                        error=r.get('error')
                    ))

            except json.JSONDecodeError:
                pass

        return test_results, tests_run, tests_passed

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
