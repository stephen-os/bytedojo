"""
Test command - Run tests for problems in the repository.
"""

import click
from pathlib import Path
from typing import Optional, List

from bytedojo.core.logger import get_logger, Theme
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager
from bytedojo.core.executor import Executor, ExecutionResult, TestResult
from bytedojo.core.test_data import TestDataLoader


def format_value(value, max_len=50):
    """Format a value for display, truncating if too long."""
    s = repr(value)
    if len(s) > max_len:
        return s[:max_len-3] + "..."
    return s


def run_problem_tests(
    problem: dict,
    executor: Executor,
    db: DatabaseManager,
    verbose: bool,
    logger
) -> ExecutionResult:
    """
    Run tests for a single problem using internal test data.

    Args:
        problem: Problem dict from database
        executor: Test executor
        db: Database manager
        verbose: Whether to show detailed output
        logger: Logger instance

    Returns:
        ExecutionResult with test details
    """
    problem_id = problem['problem_id']
    source = problem['source']
    title = problem['title']
    file_path = problem.get('file_path', '')

    logger.info(f"Testing #{problem_id}: {title}")

    # Check if solution file exists
    if not file_path or not Path(file_path).exists():
        logger.error(f"  {Theme.ORANGE}ERROR{Theme.RESET} - Solution file not found: {file_path}")
        logger.info("")
        return ExecutionResult(
            passed=False,
            output="",
            error=f"Solution file not found: {file_path}",
            status='error'
        )

    # Determine method name and helpers needed based on problem
    # For now, we'll need to extract this from the solution file or use defaults
    method_name = _get_method_name_for_problem(problem_id)
    needs_listnode = _needs_listnode(problem_id)
    needs_treenode = _needs_treenode(problem_id)

    # Run tests
    result = executor.run_tests_for_problem(
        source=source,
        problem_id=int(problem_id),
        solution_path=Path(file_path),
        class_name="Solution",
        method_name=method_name,
        needs_listnode=needs_listnode,
        needs_treenode=needs_treenode
    )

    # Update database
    output_to_store = result.error if result.error else result.output[:500]
    db.update_test_status(problem['id'], result.status, output_to_store)

    # Schedule review if passed
    if result.status == 'passed':
        db.schedule_review(problem['id'])
        review_freq = db.get_config('review_frequency_days', '7')
        logger.debug(f"Scheduled review in {review_freq} days")

    # Display result
    if result.status == 'passed':
        logger.info(f"  {Theme.GREEN}PASSED{Theme.RESET} ({result.tests_passed}/{result.tests_run} tests)")
    elif result.status == 'failed':
        logger.error(f"  {Theme.RED}FAILED{Theme.RESET} ({result.tests_passed}/{result.tests_run} tests)")
    else:  # error
        logger.error(f"  {Theme.ORANGE}ERROR{Theme.RESET}")
        if result.error:
            logger.error(f"  {result.error}")
        logger.info("")
        return result

    # Show individual test results
    if verbose or result.status == 'failed':
        for tr in result.test_results:
            if tr.passed:
                if verbose:
                    logger.info(f"    {Theme.GREEN}✓{Theme.RESET} Test {tr.test_num}")
            else:
                logger.error(f"    {Theme.RED}✗{Theme.RESET} Test {tr.test_num}")
                logger.error(f"      Input:    {format_value(tr.input)}")
                logger.error(f"      Expected: {format_value(tr.expected)}")
                logger.error(f"      Actual:   {format_value(tr.actual)}")
                if tr.error:
                    logger.error(f"      Error:    {tr.error}")

    logger.info("")
    return result


def _get_method_name_for_problem(problem_id: int) -> str:
    """Get the method name for a specific problem ID."""
    # Map of problem IDs to method names
    method_names = {
        1: "twoSum", 2: "addTwoNumbers", 3: "lengthOfLongestSubstring",
        4: "findMedianSortedArrays", 5: "longestPalindrome", 6: "convert",
        7: "reverse", 8: "myAtoi", 9: "isPalindrome", 10: "isMatch",
        11: "maxArea", 12: "intToRoman", 13: "romanToInt", 14: "longestCommonPrefix",
        15: "threeSum", 16: "threeSumClosest", 17: "letterCombinations", 18: "fourSum",
        19: "removeNthFromEnd", 20: "isValid", 21: "mergeTwoLists", 22: "generateParenthesis",
        23: "mergeKLists", 24: "swapPairs", 25: "reverseKGroup", 26: "removeDuplicates",
        27: "removeElement", 28: "strStr", 29: "divide", 30: "findSubstring",
        31: "nextPermutation", 32: "longestValidParentheses", 33: "search", 34: "searchRange",
        35: "searchInsert", 36: "isValidSudoku", 37: "solveSudoku", 38: "countAndSay",
        39: "combinationSum", 40: "combinationSum2", 41: "firstMissingPositive", 42: "trap",
        43: "multiply", 44: "isMatch", 45: "jump", 46: "permute",
        47: "permuteUnique", 48: "rotate", 49: "groupAnagrams", 50: "myPow",
        51: "solveNQueens", 52: "totalNQueens", 53: "maxSubArray", 54: "spiralOrder",
        55: "canJump", 56: "merge", 57: "insert", 58: "lengthOfLastWord",
        59: "generateMatrix", 60: "getPermutation", 61: "rotateRight", 62: "uniquePaths",
        63: "uniquePathsWithObstacles", 64: "minPathSum", 65: "isNumber", 66: "plusOne",
        67: "addBinary", 68: "fullJustify", 69: "mySqrt", 70: "climbStairs",
        71: "simplifyPath", 72: "minDistance", 73: "setZeroes", 74: "searchMatrix",
        75: "sortColors", 76: "minWindow", 77: "combine", 78: "subsets",
        79: "exist", 80: "removeDuplicates", 81: "search", 82: "deleteDuplicates",
        83: "deleteDuplicates", 84: "largestRectangleArea", 85: "maximalRectangle", 86: "partition",
        87: "isScramble", 88: "merge", 89: "grayCode", 90: "subsetsWithDup",
        91: "numDecodings", 92: "reverseBetween", 93: "restoreIpAddresses", 94: "inorderTraversal",
        95: "generateTrees", 96: "numTrees", 97: "isInterleave", 98: "isValidBST",
        99: "recoverTree", 100: "isSameTree"
    }
    return method_names.get(problem_id, "solution")


def _needs_listnode(problem_id: int) -> bool:
    """Check if problem needs ListNode helpers."""
    listnode_problems = {2, 19, 21, 23, 24, 25, 61, 82, 83, 86, 92}
    return problem_id in listnode_problems


def _needs_treenode(problem_id: int) -> bool:
    """Check if problem needs TreeNode helpers."""
    treenode_problems = {94, 95, 98, 99, 100}
    return problem_id in treenode_problems


@click.group(invoke_without_command=True)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    help='Show detailed output for each test'
)
@click.option(
    '--stop-on-fail',
    is_flag=True,
    help='Stop testing after first failure'
)
@click.pass_context
def test(ctx, verbose: bool, stop_on_fail: bool):
    """
    Run tests for problems in the repository.

    Examples:
      dojo test                    # Run all tests
      dojo test last               # Run test for last fetched problem
      dojo test --verbose          # Show detailed output
      dojo test --stop-on-fail     # Stop at first failure
    """
    # Store options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['stop_on_fail'] = stop_on_fail

    # If no subcommand, run all tests
    if ctx.invoked_subcommand is None:
        run_all_tests(verbose, stop_on_fail)


def run_all_tests(verbose: bool, stop_on_fail: bool):
    """Run tests for all problems in the database."""
    logger = get_logger()

    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    # Initialize components
    executor = Executor(timeout=30)
    test_loader = TestDataLoader()

    with DatabaseManager(repo.get_db_path()) as db:
        # Get all problems from database
        problems = db.list_problems()

        if not problems:
            logger.info("No problems found. Fetch some problems first with 'dojo leetcode fetch'")
            return

        # Filter to problems with test data
        testable_problems = []
        for p in problems:
            if test_loader.has_test_data(p['source'], int(p['problem_id'])):
                testable_problems.append(p)

        if not testable_problems:
            logger.info("No testable problems found. Internal test data is available for LeetCode problems 1-100.")
            return

        # Track results
        total = len(testable_problems)
        passed = 0
        failed = 0
        errors = 0

        logger.info(f"Running tests for {total} problem(s)...")
        logger.info("")

        for problem in testable_problems:
            result = run_problem_tests(problem, executor, db, verbose, logger)

            if result.status == 'passed':
                passed += 1
            elif result.status == 'failed':
                failed += 1
                if stop_on_fail:
                    logger.info("Stopping due to --stop-on-fail")
                    break
            else:
                errors += 1
                if stop_on_fail:
                    logger.info("Stopping due to --stop-on-fail")
                    break

    # Summary
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    logger.info(f"Total:   {total}")
    logger.info(f"{Theme.GREEN}Passed:  {passed}{Theme.RESET}")
    logger.info(f"{Theme.RED}Failed:  {failed}{Theme.RESET}")
    logger.info(f"{Theme.ORANGE}Errors:  {errors}{Theme.RESET}")

    # Exit code
    if failed > 0 or errors > 0:
        raise click.ClickException("Some tests failed")


@test.command()
@click.pass_context
def last(ctx):
    """
    Run test for the last fetched problem.

    Examples:
      dojo test last               # Test the most recently fetched problem
      dojo test last --verbose     # With detailed output
    """
    logger = get_logger()
    verbose = ctx.obj.get('verbose', False)

    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    # Initialize components
    executor = Executor(timeout=30)

    with DatabaseManager(repo.get_db_path()) as db:
        # Get the most recently fetched problem
        problems = db.list_problems()

        if not problems:
            logger.info("No problems found. Fetch some problems first with 'dojo leetcode fetch'")
            return

        # Get last problem (most recent)
        problem = problems[-1]

        logger.info("Running test for last fetched problem...")
        logger.info("")

        result = run_problem_tests(problem, executor, db, verbose, logger)

    if result.status == 'failed' or result.status == 'error':
        raise click.ClickException("Test failed")


@test.command()
@click.argument('problem_id', type=int)
@click.pass_context
def problem(ctx, problem_id: int):
    """
    Run test for a specific problem by ID.

    Examples:
      dojo test problem 1          # Test problem #1 (Two Sum)
      dojo test problem 42         # Test problem #42 (Trapping Rain Water)
    """
    logger = get_logger()
    verbose = ctx.obj.get('verbose', False)

    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    # Initialize components
    executor = Executor(timeout=30)

    with DatabaseManager(repo.get_db_path()) as db:
        # Find the specific problem
        problem = db.get_problem('leetcode', str(problem_id))

        if not problem:
            logger.error(f"Problem #{problem_id} not found in database.")
            logger.info("Fetch it first with: dojo leetcode fetch {problem_id}")
            raise click.ClickException("Problem not found")

        logger.info(f"Running test for problem #{problem_id}...")
        logger.info("")

        result = run_problem_tests(problem, executor, db, verbose, logger)

    if result.status == 'failed' or result.status == 'error':
        raise click.ClickException("Test failed")
