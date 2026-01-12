"""
Codeforces fetch command.
"""

import re
import click

from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.codeforces import CodeforcesClient, PythonFormatter
from bytedojo.core.file_writer import FileWriter
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager


def parse_problem_id(problem_id: str) -> tuple:
    """
    Parse a problem ID into contest_id and index.

    Args:
        problem_id: Problem ID like '1A', '4B', '1850A'

    Returns:
        Tuple of (contest_id, index) or (None, None) if invalid
    """
    match = re.match(r'^(\d+)([A-Za-z]\d?)$', problem_id.strip())
    if match:
        return int(match.group(1)), match.group(2).upper()
    return None, None


@click.command()
@click.argument('problem_ids', nargs=-1, required=True)
@click.option('--output-dir', type=click.Path(path_type=Path), default='problems/codeforces', help='Output directory for problem files')
@click.option('--force', is_flag=True, help='Overwrite existing problems')
@click.pass_obj
def fetch(ctx, problem_ids: tuple, output_dir: Path, force: bool):
    """
    Fetch Codeforces problems.

    PROBLEM_IDS are in format: contestId + index (e.g., 1A, 4B, 1850A)

    Examples:
      dojo codeforces fetch 1A              # Single problem
      dojo codeforces fetch 1A 4A 71A       # Multiple problems
      dojo codeforces fetch 1A --force      # Overwrite existing
    """
    logger = get_logger()

    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    # Initialize components
    client = CodeforcesClient()
    formatter = PythonFormatter()
    writer = FileWriter()

    success_count = 0
    skip_count = 0

    # Use database with context manager
    with DatabaseManager(repo.get_db_path()) as db:
        for problem_id in problem_ids:
            contest_id, index = parse_problem_id(problem_id)

            if contest_id is None:
                logger.error(f"Invalid problem ID format: {problem_id}")
                logger.info("Expected format: contestId + index (e.g., 1A, 4B, 1850A)")
                continue

            # Fetch problem
            problem = client.get_problem(contest_id, index)
            if not problem:
                logger.error(f"Problem {problem_id} not found")
                continue

            # Check if already registered (unless force)
            if not force and db.is_problem_registered('codeforces', problem.problem_id):
                logger.info(f"Problem {problem.problem_id} already registered (use --force to overwrite)")
                skip_count += 1
                continue

            # Format to string
            content = formatter.format(problem)

            # Determine output path based on difficulty
            difficulty_dir = problem.difficulty.lower()
            filepath = output_dir / difficulty_dir / problem.filename
            writer.write(content, filepath)

            # Register in database
            # Create a simple object to pass to register_problem
            class ProblemData:
                def __init__(self, p):
                    self.id = p.problem_id
                    self.title = p.name
                    self.difficulty = p.difficulty

            db.register_problem(
                ProblemData(problem),
                source='codeforces',
                file_path=filepath,
                force=force
            )

            logger.info(f"Problem {problem.problem_id}: {problem.name}")
            logger.info(f"  Saved to: {filepath}")
            success_count += 1

    # Summary
    logger.info("")
    logger.info(f"Fetch complete: {success_count} fetched, {skip_count} skipped")
