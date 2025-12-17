"""
Stats command - View statistics about problems in the repository.
"""

import click
from bytedojo.core.logger import get_logger
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager


@click.command()

@click.option('--list', 'list_problems', is_flag=True, help='List all problems')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information including attempts')
@click.option('--source', type=str, help='Filter by source (e.g., leetcode)')
@click.option('--difficulty', type=click.Choice(['Easy', 'Medium', 'Hard'], case_sensitive=False), help='Filter by difficulty' )

@click.pass_context
def stats(ctx, list_problems: bool, verbose: bool, source: str, difficulty: str):
    """
    View statistics about problems in the repository.
    
    Examples:
      dojo stats                          # Show summary
      dojo stats --list                   # List all problems
      dojo stats --list --verbose         # List with details
      dojo stats --list --difficulty Easy # List easy problems
    """
    logger = get_logger()
    
    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")
    
    with DatabaseManager(repo.get_db_path()) as db:
        if list_problems:
            _list_problems(db, verbose, source, difficulty, logger)
        else:
            _show_summary(db, logger)


def _show_summary(db: DatabaseManager, logger):
    """Show summary statistics."""
    stats = db.get_summary_stats()
    
    logger.info("=" * 60)
    logger.info("ByteDojo Repository Statistics")
    logger.info("=" * 60)
    logger.info("")
    
    logger.info(f"Total Problems: {stats['total_problems']}")
    logger.info("")
    
    if stats['by_difficulty']:
        logger.info("By Difficulty:")
        for difficulty, count in sorted(stats['by_difficulty'].items()):
            logger.info(f"  {difficulty:10s}: {count}")
        logger.info("")
    
    if stats['by_source']:
        logger.info("By Source:")
        for source, count in sorted(stats['by_source'].items()):
            logger.info(f"  {source:10s}: {count}")


def _list_problems(db: DatabaseManager, verbose: bool, source: str, difficulty: str, logger):
    """List problems with optional verbosity."""
    problems = db.list_problems(source=source, difficulty=difficulty)
    
    if not problems:
        logger.info("No problems found matching criteria")
        return
    
    logger.info(f"Found {len(problems)} problem(s)")
    logger.info("")
    
    for problem in problems:
        _print_problem(db, problem, verbose, logger)
        logger.info("")


def _print_problem(db: DatabaseManager, problem: dict, verbose: bool, logger):
    """Print a single problem."""
    # Basic info
    logger.info(f"#{problem['problem_id']:4s} - {problem['title']}")
    logger.info(f"  Source: {problem['source']}")
    logger.info(f"  Difficulty: {problem['difficulty']}")
    logger.info(f"  Fetched: {problem['fetched_at']}")
    
    if problem['file_path']:
        logger.info(f"  File: {problem['file_path']}")
    
    # Verbose info - show attempt statistics
    if verbose:
        attempt_stats = db.get_problem_stats(problem['id'])
        
        if attempt_stats['total_attempts'] > 0:
            logger.info(f"  Attempts: {attempt_stats['total_attempts']}")
            logger.info(f"    Passed: {attempt_stats['passed_attempts']}")
            logger.info(f"    Failed: {attempt_stats['failed_attempts']}")
            logger.info(f"    Last: {attempt_stats['last_attempt']}")
        else:
            logger.info("  Attempts: None")