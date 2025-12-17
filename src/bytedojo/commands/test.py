"""
Test command - Run tests for problems in the repository.
"""

import click
from pathlib import Path

from bytedojo.core.logger import get_logger, Theme
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager
from bytedojo.core.executor import Executor


@click.command()
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
    Run tests for all problems in the repository.
    
    Examples:
      dojo test                    # Run all tests
      dojo test --verbose          # Show detailed output
      dojo test --stop-on-fail     # Stop at first failure
    """
    logger = get_logger()
    
    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")
    
    # Initialize test executor
    executor = Executor(timeout=30)  # Updated class name
    
    # Track results
    total = 0
    passed = 0
    failed = 0
    errors = 0
    skipped = 0
    
    logger.info("Running tests for all problems...")
    logger.info("")
    
    with DatabaseManager(repo.get_db_path()) as db:
        # Get all problems
        problems = db.list_problems()
        
        if not problems:
            logger.info("No problems found in repository")
            return
        
        total = len(problems)
        logger.info(f"Found {total} problem(s)")
        logger.info("")
        
        for problem in problems:
            file_path = problem.get('file_path')

            logger.debug(f"File: {file_path}")
            
            if not file_path:
                logger.warning(f"Problem #{problem['problem_id']}: No file path")
                skipped += 1
                continue
            
            file_path = Path(file_path)
            
            # Validate test file
            if not executor.validate_test_file(file_path):
                logger.warning(f"Problem #{problem['problem_id']}: Invalid test file")
                db.update_test_status(problem['id'], 'error', 'Invalid test file')
                errors += 1
                continue
            
            # Run test
            logger.info(f"Testing #{problem['problem_id']}: {problem['title']}")
            result = executor.run_test(file_path)
            
            # Update database
            output_to_store = result.error if result.error else result.output[:500]  # Limit stored output
            db.update_test_status(problem['id'], result.status, output_to_store)
            
            # Display result
            if result.status == 'passed':
                logger.info(f"{Theme.GREEN} PASSED{Theme.RESET}")
                passed += 1
                
                if verbose and result.output:
                    logger.info("  Output:")
                    for line in result.output.split('\n')[:10]:  # First 10 lines
                        logger.info(f"    {line}")
            
            elif result.status == 'failed':
                logger.error(f"{Theme.RED} FAILED{Theme.RESET}")
                failed += 1
                
                if result.error:
                    logger.error("  Error:")
                    for line in result.error.split('\n')[:5]:  # First 5 lines
                        if line.strip():
                            logger.error(f"    {line}")
                
                if stop_on_fail:
                    logger.info("")
                    logger.info("Stopping due to --stop-on-fail")
                    break
            
            else:  # error
                logger.error(f"{Theme.ORANGE} ERROR{Theme.RESET}")
                errors += 1
                
                if result.error:
                    logger.error(f"  {result.error}")
                
                if stop_on_fail:
                    logger.info("")
                    logger.info("Stopping due to --stop-on-fail")
                    break
            
            logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    logger.info(f"Total:   {total}")
    logger.info(f"{Theme.GREEN}Passed:  {passed}{Theme.RESET}")
    logger.info(f"{Theme.RED}Failed:  {failed}{Theme.RESET}")
    logger.info(f"{Theme.ORANGE}Errors:  {errors}{Theme.RESET}")
    
    if skipped > 0:
        logger.info(f"Skipped: {skipped}")
    
    # Exit code
    if failed > 0 or errors > 0:
        raise click.ClickException("Some tests failed")