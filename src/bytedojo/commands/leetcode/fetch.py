"""
LeetCode fetch command.
"""

import click

from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.leetcode import LeetCodeClient
from bytedojo.core.leetcode.formatters import PythonFormatter
from bytedojo.core.file_writer import FileWriter

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

@click.pass_obj
def fetch(ctx, arguments: tuple, output_dir: Path):
    """Fetch LeetCode problems."""
    logger = get_logger()
    problem_ids = parse_arguments(arguments)
    
    # Initialize components
    client = LeetCodeClient()
    formatter = PythonFormatter()
    writer = FileWriter()
    
    for problem_id in problem_ids:
        # Fetch problem
        problem = client.get_problem_by_id(problem_id)
        if not problem:
            logger.error(f"Problem {problem_id} not found")
            continue
        
        # Format to string
        content = formatter.format(problem)
        
        # Write to file
        filepath = output_dir / problem.difficulty.lower() / problem.filename
        writer.write(content, filepath)
        
        logger.info(f"Problem #{problem.id}: {problem.title}")
        logger.info(f"  Saved to: {filepath}")