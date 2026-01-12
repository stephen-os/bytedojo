"""
Test command - Run tests for problems in the repository.
"""

import click
from pathlib import Path
from typing import Optional, List

from bytedojo.core.logger import get_logger, Theme
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager
from bytedojo.core.executor import Executor
from bytedojo.core.test_store import TestStore, TestData


def run_single_test(
    test_data: TestData,
    executor: Executor,
    db: DatabaseManager,
    verbose: bool,
    logger
) -> str:
    """
    Run a single test and return status.

    Returns:
        Status string: 'passed', 'failed', or 'error'
    """
    logger.info(f"Testing #{test_data.problem_id}: {test_data.title}")

    result = executor.run_test(test_data)

    # Update database
    output_to_store = result.error if result.error else result.output[:500]

    # Find the problem in database to update
    problem = db.get_problem('leetcode', test_data.problem_id)
    if problem:
        db.update_test_status(problem['id'], result.status, output_to_store)

    # Display result
    if result.status == 'passed':
        logger.info(f"  {Theme.GREEN}PASSED{Theme.RESET} ({result.tests_run} tests)")

        if verbose and result.output:
            logger.info("  Output:")
            for line in result.output.split('\n')[:10]:
                if line.strip():
                    logger.info(f"    {line}")

    elif result.status == 'failed':
        if result.tests_run > 0:
            logger.error(f"  {Theme.RED}FAILED{Theme.RESET} ({result.tests_passed}/{result.tests_run} passed)")
        else:
            logger.error(f"  {Theme.RED}FAILED{Theme.RESET}")

        if result.error:
            logger.error("  Error:")
            for line in result.error.split('\n')[:5]:
                if line.strip():
                    logger.error(f"    {line}")
        elif verbose and result.output:
            logger.info("  Output:")
            for line in result.output.split('\n')[:10]:
                if line.strip():
                    logger.info(f"    {line}")

    else:  # error
        logger.error(f"  {Theme.ORANGE}ERROR{Theme.RESET}")

        if result.error:
            logger.error(f"  {result.error}")

    logger.info("")
    return result.status


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
    """Run tests for all problems."""
    logger = get_logger()

    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    # Initialize components
    executor = Executor(timeout=30)
    test_store = TestStore(repo.get_dojo_path())

    # Get all test data
    tests = test_store.list_tests()

    if not tests:
        logger.info("No tests found. Fetch some problems first with 'dojo leetcode fetch'")
        return

    # Track results
    total = len(tests)
    passed = 0
    failed = 0
    errors = 0

    logger.info(f"Running tests for {total} problem(s)...")
    logger.info("")

    with DatabaseManager(repo.get_db_path()) as db:
        for test_data in tests:
            status = run_single_test(test_data, executor, db, verbose, logger)

            if status == 'passed':
                passed += 1
            elif status == 'failed':
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
    test_store = TestStore(repo.get_dojo_path())

    # Get last test data
    test_data = test_store.get_last()

    if not test_data:
        logger.info("No tests found. Fetch some problems first with 'dojo leetcode fetch'")
        return

    logger.info("Running test for last fetched problem...")
    logger.info("")

    with DatabaseManager(repo.get_db_path()) as db:
        status = run_single_test(test_data, executor, db, verbose, logger)

    if status == 'failed' or status == 'error':
        raise click.ClickException("Test failed")