"""
Fetch command - Fetch problems from local data and create workspace files.
"""

import click

from bytedojo.core.logger import get_logger
from bytedojo.core import problem_service
from bytedojo.core.models import Language
from bytedojo.commands.subcommands.utils import get_initialized_repo, get_default_language


@click.command()
@click.argument('arguments', nargs=-1, required=True)
@click.option('--force', is_flag=True, help='Overwrite existing problems')
@click.option('--python', '-py', 'language', flag_value='python3', help='Fetch as Python')
@click.option('--java', 'language', flag_value='java', help='Fetch as Java')
@click.option('--cpp', 'language', flag_value='cpp', help='Fetch as C++')
@click.pass_obj
def fetch(ctx, arguments: tuple, force: bool, language: str | None):
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

    # Parse language enum
    lang = Language.from_string(language)
    if lang == Language.UNKNOWN:
        raise click.ClickException(f"Unknown language: {language}")

    # Parse problem IDs
    problem_ids = problem_service.parse_problem_ids(arguments)
    if not problem_ids:
        raise click.ClickException("No problem IDs provided")

    logger.info(f"Fetching {len(problem_ids)} problem(s) as {language.upper()}")

    # Track results
    success_count = 0
    skip_count = 0
    error_count = 0

    # Fetch each problem
    for pid in problem_ids:
        result = problem_service.place_problem(
            problem_id=pid,
            language=lang,
            repo=repo,
            force=force
        )

        if result.error:
            logger.error(f"Problem #{pid}: {result.error}")
            error_count += 1
        elif result.skipped:
            logger.info(f"Problem #{pid} ({language}) already registered (use --force to overwrite)")
            skip_count += 1
        else:
            logger.info(f"Problem #{pid}: {result.title} ({language})")
            logger.info(f"  Saved to: {result.file_path}")
            success_count += 1

    # Summary
    logger.info("")
    logger.info(f"Fetch complete: {success_count} fetched, {skip_count} skipped, {error_count} errors")
