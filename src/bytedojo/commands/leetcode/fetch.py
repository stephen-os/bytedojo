"""
LeetCode fetch command.
"""

import click

from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.leetcode import LeetCodeClient
from bytedojo.core.leetcode.formatters import PythonFormatter, JavaFormatter, CppFormatter
from bytedojo.core.file_writer import FileWriter
from bytedojo.core.database import DatabaseManager
from bytedojo.core.settings import SettingsManager
from bytedojo.commands.utils import get_initialized_repo, get_default_language


# Language to formatter mapping
FORMATTERS = {
    'python': PythonFormatter,
    'java': JavaFormatter,
    'cpp': CppFormatter,
}

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
@click.option('--output-dir', type=click.Path(path_type=Path), default='problems', help='Output directory for problem files')
@click.option('--force', is_flag=True, help='Overwrite existing problems')
@click.option('--python', '-py', 'language', flag_value='python', help='Fetch as Python')
@click.option('--java', 'language', flag_value='java', help='Fetch as Java')
@click.option('--cpp', 'language', flag_value='cpp', help='Fetch as C++')

@click.pass_obj
def fetch(ctx, arguments: tuple, output_dir: Path, force: bool, language: str | None):
    """
    Fetch LeetCode problems.

    Uses configured default language (see: dojo settings default-language).

    Examples:
      dojo fetch 1              # Single problem (uses default language)
      dojo fetch 1 --python     # Fetch as Python
      dojo fetch 1 --java       # Fetch as Java
      dojo fetch 1 --cpp        # Fetch as C++
      dojo fetch 1,2,3          # Multiple problems
      dojo fetch 1..10          # Range
      dojo fetch 1 --force      # Overwrite existing
    """
    logger = get_logger()
    problem_ids = parse_arguments(arguments)
    repo = get_initialized_repo()

    # Use configured default if no language flag specified
    if language is None:
        language = get_default_language()

    # Load settings for organization mode
    settings_manager = SettingsManager(repo.get_dojo_path())
    settings = settings_manager.load()
    organization = settings.leetcode.organization  # "flat" or "difficulty"

    # Initialize components
    client = LeetCodeClient()
    formatter_class = FORMATTERS.get(language, PythonFormatter)
    formatter = formatter_class()
    writer = FileWriter()

    success_count = 0
    skip_count = 0

    logger.info(f"Fetching problems as {language.upper()}")

    # Use database with context manager
    with DatabaseManager(repo.get_db_path()) as db:
        for problem_id in problem_ids:
            # Fetch problem
            problem = client.get_problem_by_id(problem_id)
            if not problem:
                logger.error(f"Problem {problem_id} not found")
                continue

            # Check if already registered for this language (unless force)
            if not force and db.is_problem_registered('leetcode', problem.id, language):
                logger.info(f"Problem #{problem.id} ({language}) already registered (use --force to overwrite)")
                skip_count += 1
                continue

            # Format to string
            content = formatter.format(problem)

            # Get folder name and solution filename
            folder_name = problem.get_folder_name()
            solution_filename = problem.get_solution_filename(language)

            # Build file path: problems/0001-two-sum/solution.py
            # Organization setting affects whether difficulty subfolders are used
            if organization == "difficulty":
                filepath = output_dir / problem.difficulty.lower() / folder_name / solution_filename
            else:  # flat (default)
                filepath = output_dir / folder_name / solution_filename

            # Write to file
            writer.write(content, filepath)

            # Register in database with language
            db.register_problem(
                problem,
                source='leetcode',
                language=language,
                file_path=filepath,
                force=force
            )

            logger.info(f"Problem #{problem.id}: {problem.title} ({language})")
            logger.info(f"  Saved to: {filepath}")
            success_count += 1

    # Summary
    logger.info("")
    logger.info(f"Fetch complete: {success_count} fetched, {skip_count} skipped ({language})")
