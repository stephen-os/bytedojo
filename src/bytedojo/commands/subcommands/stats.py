"""
stats - View statistics about problems in the repository.
"""

import click

from bytedojo.commands._resolve import require_repo
from bytedojo.commands.ui.renderers import render_problem_list, render_stats_summary
from bytedojo.core.logger import get_logger
from bytedojo.services import problem_service


@click.command()
@click.option("--list", "list_problems", is_flag=True, help="List all problems")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed information including attempts"
)
@click.option("--source", type=str, help="Filter by source (e.g., leetcode)")
@click.option(
    "--difficulty",
    "-d",
    type=click.Choice(["easy", "medium", "hard"], case_sensitive=False),
    help="Filter by difficulty",
)
@click.pass_obj
def stats(
    ctx, list_problems: bool, verbose: bool, source: str | None, difficulty: str | None
):
    """
    View statistics about problems in the repository.

    Examples:
      dojo stats                          # Show summary
      dojo stats --list                   # List all problems
      dojo stats --list --verbose         # List with details
      dojo stats --list -d easy           # List easy problems
    """
    logger = get_logger()
    logger.debug(
        f"stats: list_problems={list_problems} verbose={verbose} "
        f"source={source} difficulty={difficulty}"
    )

    repo = require_repo()

    if list_problems:
        # ProblemDifficulty stores the capitalised form; the CLI accepts
        # lowercase. Normalise so the exact-match WHERE clause hits.
        problems = problem_service.list_registered_problems(
            repo,
            source=source,
            difficulty=difficulty.capitalize() if difficulty else None,
        )
        attempt_stats = (
            problem_service.get_attempt_status_map(repo) if verbose else None
        )
        render_problem_list(problems, attempt_stats)
    else:
        render_stats_summary(problem_service.get_summary_stats(repo))

    logger.debug("stats: complete")
