"""
LeetCode pick command - randomly select an unsolved problem.
"""

import random
import click

from bytedojo.core.logger import get_logger
from bytedojo.core.leetcode import LeetCodeClient
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager


DIFFICULTY_MAP = {
    'easy': 1,
    'medium': 2,
    'hard': 3,
    '1': 1,
    '2': 2,
    '3': 3,
}

DIFFICULTY_COLORS = {
    'Easy': 'green',
    'Medium': 'yellow',
    'Hard': 'red',
}


def _get_fetched_problem_ids(repo):
    """Get set of problem IDs already in the database."""
    fetched_ids = set()
    if repo.is_initialized():
        with DatabaseManager(repo.get_db_path()) as db:
            problems = db.list_problems(source='leetcode')
            fetched_ids = {int(p['problem_id']) for p in problems}
    return fetched_ids


@click.command()
@click.option(
    '--difficulty', '-d',
    type=click.Choice(['easy', 'medium', 'hard', '1', '2', '3'], case_sensitive=False),
    help='Filter by difficulty (easy/1, medium/2, hard/3)'
)
@click.option(
    '--tag', '-t',
    multiple=True,
    help='Filter by algorithm tag (can be used multiple times)'
)
@click.option(
    '--include-premium',
    is_flag=True,
    help='Include premium (paid) problems'
)
@click.pass_obj
def pick(ctx, difficulty: str, tag: tuple, include_premium: bool):
    """
    Pick a random problem you haven't solved yet.

    Selects from problems not yet in your .dojo database.

    Examples:
      dojo leetcode pick                    # Random unsolved problem
      dojo leetcode pick -d easy            # Random easy problem
      dojo leetcode pick -t array           # Random array problem
      dojo leetcode pick -d medium -t tree  # Random medium tree problem
    """
    logger = get_logger()
    client = LeetCodeClient()
    repo = DojoRepository()

    # Convert difficulty to int
    difficulty_int = None
    if difficulty:
        difficulty_int = DIFFICULTY_MAP.get(difficulty.lower())

    # Convert tag tuple to list
    tags_list = list(tag) if tag else None

    # Query all matching problems from LeetCode
    logger.info("Fetching problems from LeetCode...")
    all_problems = client.query_problems(
        difficulty=difficulty_int,
        tags=tags_list
    )

    if not all_problems:
        logger.warning("No problems found matching your criteria")
        return

    # Filter out premium problems unless requested
    if not include_premium:
        all_problems = [p for p in all_problems if not p.paid_only]

    if not all_problems:
        logger.warning("No free problems found matching your criteria")
        return

    # Get problems already in database
    fetched_ids = _get_fetched_problem_ids(repo)

    # Filter to unsolved problems only
    unsolved = [p for p in all_problems if p.id not in fetched_ids]

    if not unsolved:
        click.echo(click.style("You've solved all problems matching your criteria!", fg='green'))
        click.echo(f"Total matching: {len(all_problems)}, All fetched: {len(fetched_ids)}")
        return

    # Pick a random problem
    problem = random.choice(unsolved)

    # Display the picked problem
    diff_color = DIFFICULTY_COLORS.get(problem.difficulty, 'white')

    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo(click.style("  PICKED FOR YOU", fg='cyan', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")
    click.echo(f"  #{problem.id}: {click.style(problem.title, bold=True)}")
    click.echo(f"  Difficulty: {click.style(problem.difficulty, fg=diff_color)}")

    if problem.tags:
        tags_display = ", ".join(problem.tags[:5])
        if len(problem.tags) > 5:
            tags_display += f" (+{len(problem.tags) - 5} more)"
        click.echo(f"  Tags: {tags_display}")

    click.echo(f"  URL: https://leetcode.com/problems/{problem.title_slug}/")
    click.echo("")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo(f"  Unsolved: {len(unsolved)} | Solved: {len(fetched_ids)} | Total: {len(all_problems)}")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo("")

    # Offer to fetch
    click.echo(f"  Fetch with: dojo leetcode fetch {problem.id}")
    click.echo("")
