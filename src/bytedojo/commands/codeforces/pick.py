"""
Codeforces pick command - randomly select an unsolved problem.
"""

import random
import click

from bytedojo.core.logger import get_logger
from bytedojo.core.codeforces import CodeforcesClient
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager


# Rating ranges for difficulty levels
DIFFICULTY_RATINGS = {
    'easy': (0, 1199),
    'medium': (1200, 1599),
    'hard': (1600, 2099),
    'expert': (2100, 3500),
}


def _get_rating_color(rating):
    """Get color based on Codeforces rating."""
    if rating is None:
        return 'white'
    elif rating < 1200:
        return 'bright_black'
    elif rating < 1400:
        return 'green'
    elif rating < 1600:
        return 'cyan'
    elif rating < 1900:
        return 'blue'
    elif rating < 2100:
        return 'magenta'
    elif rating < 2400:
        return 'yellow'
    else:
        return 'red'


def _get_fetched_problem_ids(repo):
    """Get set of problem IDs already in the database."""
    fetched_ids = set()
    if repo.is_initialized():
        with DatabaseManager(repo.get_db_path()) as db:
            problems = db.list_problems(source='codeforces')
            fetched_ids = {p['problem_id'] for p in problems}
    return fetched_ids


@click.command()
@click.option(
    '--difficulty', '-d',
    type=click.Choice(['easy', 'medium', 'hard', 'expert'], case_sensitive=False),
    help='Filter by difficulty level'
)
@click.option(
    '--rating-min', '-r',
    type=int,
    help='Minimum rating (e.g., 800)'
)
@click.option(
    '--rating-max', '-R',
    type=int,
    help='Maximum rating (e.g., 1500)'
)
@click.option(
    '--tag', '-t',
    multiple=True,
    help='Filter by tag (can be used multiple times)'
)
@click.pass_obj
def pick(ctx, difficulty: str, rating_min: int, rating_max: int, tag: tuple):
    """
    Pick a random Codeforces problem you haven't solved yet.

    Selects from problems not yet in your .dojo database.

    Examples:
      dojo codeforces pick                      # Random unsolved problem
      dojo codeforces pick -d easy              # Random easy problem
      dojo codeforces pick -r 1200 -R 1600      # Rating range
      dojo codeforces pick -t dp                # Random DP problem
    """
    logger = get_logger()
    client = CodeforcesClient()
    repo = DojoRepository()

    # Convert difficulty to rating range
    if difficulty:
        diff_range = DIFFICULTY_RATINGS.get(difficulty.lower())
        if diff_range:
            rating_min = rating_min or diff_range[0]
            rating_max = rating_max or diff_range[1]

    # Convert tag tuple to list
    tags_list = list(tag) if tag else None

    # Query all matching problems from Codeforces
    logger.info("Fetching problems from Codeforces...")
    all_problems = client.query_problems(
        rating_min=rating_min,
        rating_max=rating_max,
        tags=tags_list
    )

    if not all_problems:
        logger.warning("No problems found matching your criteria")
        return

    # Get problems already in database
    fetched_ids = _get_fetched_problem_ids(repo)

    # Filter to unsolved problems only
    unsolved = [p for p in all_problems if p.problem_id not in fetched_ids]

    if not unsolved:
        click.echo(click.style("You've solved all problems matching your criteria!", fg='green'))
        click.echo(f"Total matching: {len(all_problems)}, All fetched: {len(fetched_ids)}")
        return

    # Pick a random problem
    problem = random.choice(unsolved)

    # Display the picked problem
    rating_str = str(problem.rating) if problem.rating else "Unrated"
    rating_color = _get_rating_color(problem.rating)

    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo(click.style("  PICKED FOR YOU", fg='cyan', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")
    click.echo(f"  {problem.problem_id}: {click.style(problem.name, bold=True)}")
    click.echo(f"  Rating: {click.style(rating_str, fg=rating_color)} ({problem.difficulty})")

    if problem.tags:
        tags_display = ", ".join(problem.tags[:5])
        if len(problem.tags) > 5:
            tags_display += f" (+{len(problem.tags) - 5} more)"
        click.echo(f"  Tags: {tags_display}")

    url = f"https://codeforces.com/problemset/problem/{problem.contest_id}/{problem.index}"
    click.echo(f"  URL: {url}")
    click.echo("")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo(f"  Unsolved: {len(unsolved)} | Solved: {len(fetched_ids)} | Total: {len(all_problems)}")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo("")

    # Offer to fetch
    click.echo(f"  Fetch with: dojo codeforces fetch {problem.problem_id}")
    click.echo("")
