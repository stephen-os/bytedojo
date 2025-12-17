"""
LeetCode fetch command.
"""

import click

from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.leetcode import LeetCodeClient
from bytedojo.core.leetcode.formatters import PythonFormatter
from bytedojo.core.file_writer import FileWriter
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager

def parse_arguments(arguments: tuple[str, ...]) -> list[int]:
    problem_ids: list[int] = []

    for token in arguments:
        parts = token.split(',')

        for part in parts:
            if '..' in part: # Range
                try:
                    start, end = part.split('..', 1)
                    start, end = int(start), int(end)
                except (ValueError, TypeError):
                    raise click.ClickException(f"Invalid range '{part}'. Expected format: start..end")
                
                step = 1 if start <= end else -1
                problem_ids.extend(range(start, end + step, step))
            else: # Single
                try:
                    problem_ids.append(int(part))
                except (ValueError, TypeError):
                    raise click.ClickException(f"Invalid number '{part}'. Expected an integer.")

    return sorted(problem_ids)

@click.command()

# Define arguments
@click.argument('arguments', nargs=-1, required=True)

# Define options
@click.option('--output-dir', type=click.Path(path_type=Path), default='problems/leetcode', help='Output directory for problem files')
@click.option('--force', is_flag=True, help='Overwrite existing problems')

@click.pass_obj
def fetch(ctx, arguments: tuple, output_dir: Path, force: bool):
    """
    Fetch LeetCode problems.
    
    Examples:
      dojo leetcode fetch 1              # Single problem
      dojo leetcode fetch 1,2,3          # Multiple problems
      dojo leetcode fetch 1..10          # Range
      dojo leetcode fetch 1 --force      # Overwrite existing
    """
    logger = get_logger()
    problem_ids = parse_arguments(arguments)
    
    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")
    
    # Initialize components
    client = LeetCodeClient()
    formatter = PythonFormatter()
    writer = FileWriter()
    
    success_count = 0
    skip_count = 0
    
    # Use database with context manager
    with DatabaseManager(repo.get_db_path()) as db:
        for problem_id in problem_ids:
            # Fetch problem
            problem = client.get_problem_by_id(problem_id)
            if not problem:
                logger.error(f"Problem {problem_id} not found")
                continue
            
            # Check if already registered (unless force)
            if not force and db.is_problem_registered('leetcode', problem.id):
                logger.info(f"Problem #{problem.id} already registered (use --force to overwrite)")
                skip_count += 1
                continue
            
            # Format to string
            content = formatter.format(problem)
            
            # Write to file
            filepath = output_dir / problem.difficulty.lower() / problem.filename
            writer.write(content, filepath)
            
            # Register in database
            db.register_problem(
                problem,
                source='leetcode',
                file_path=filepath,
                force=force
            )
            
            logger.info(f"Problem #{problem.id}: {problem.title}")
            logger.info(f"  Saved to: {filepath}")
            success_count += 1
    
    # Summary
    logger.info("")
    logger.info(f"Fetch complete: {success_count} fetched, {skip_count} skipped")