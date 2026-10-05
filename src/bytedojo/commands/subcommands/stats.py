"""
stats - View statistics about problems in the repository.
"""

import click

from bytedojo.commands._resolve import require_repo
from bytedojo.commands.ui.renderers import render_problem_list, render_stats_summary
from bytedojo.core.logger import get_logger


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

    with repo.session() as s:
        if list_problems:
            # ProblemDifficulty stores the capitalised form; the CLI accepts
            # lowercase. Normalise so the exact-match WHERE clause hits.
            problems = s.problems.list(
                source=source,
                difficulty=difficulty.capitalize() if difficulty else None,
            )
            attempt_stats = (
                {
                    p.problem_id: s.attempts.stats(p.source, p.problem_id)
                    for p in problems
                }
                if verbose
                else None
            )
        else:
            summary = s.problems.summary_stats()

    if list_problems:
        render_problem_list(problems, attempt_stats)
    else:
        render_stats_summary(summary)

    logger.debug("stats: complete")
