"""
Fetch command - Fetch problems from LeetCode.
"""

import click

from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.fetching import ProblemFetcher, FetchedProblem
from bytedojo.commands.subcommands.utils import get_initialized_repo, get_default_language


def _on_progress(problem: FetchedProblem):
    """Display progress for a fetched problem."""
    logger = get_logger()

    if problem.error:
        logger.error(problem.error)
    elif problem.skipped:
        logger.info(f"Problem #{problem.problem_id} ({problem.language}) already registered (use --force to overwrite)")
    else:
        logger.info(f"Problem #{problem.problem_id}: {problem.title} ({problem.language})")
        logger.info(f"  Saved to: {problem.file_path}")


@click.command()
@click.argument('arguments', nargs=-1, required=True)
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
    repo = get_initialized_repo()

    # Use configured default if no language flag specified
    if language is None:
        language = get_default_language()

    # Parse problem IDs
    try:
        problem_ids = ProblemFetcher.parse_problem_ids(arguments)
    except ValueError as e:
        raise click.ClickException(str(e))

    logger.info(f"Fetching problems as {language.upper()}")

    # Use fetching service
    fetcher = ProblemFetcher(repo)
    result = fetcher.fetch(
        problem_ids=problem_ids,
        language=language,
        output_dir=output_dir,
        force=force,
        on_progress=_on_progress
    )

    # Summary
    logger.info("")
    logger.info(f"Fetch complete: {result.success_count} fetched, {result.skip_count} skipped ({language})")
