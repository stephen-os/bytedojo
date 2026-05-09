"""
Pick command - Randomly select an unsolved problem.
"""

import click
from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.picker import ProblemPicker
from bytedojo.core.repository import Repository
from bytedojo.commands.subcommands.utils import DIFFICULTY_COLORS


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
@click.pass_obj
def pick(ctx, difficulty: str, tag: tuple):
    """
    Pick a random problem you haven't solved yet.

    Selects from problems not yet in your .dojo database.

    Examples:
      dojo pick                    # Random unsolved problem
      dojo pick -d easy            # Random easy problem
      dojo pick -t array           # Random array problem
      dojo pick -d medium -t tree  # Random medium tree problem
    """
    logger = get_logger()
    repo = Repository(Path.cwd())
    picker = ProblemPicker(repo)

    # Convert tag tuple to list
    tags_list = list(tag) if tag else None

    # Pick a problem using service
    logger.info("Searching for problems...")
    result = picker.pick(
        difficulty=difficulty,
        tags=tags_list
    )

    if result.total_count == 0:
        logger.warning("No problems found matching your criteria")
        return

    if result.problem is None:
        click.echo(click.style("You've solved all problems matching your criteria!", fg='green'))
        click.echo(f"Total matching: {result.total_count}, All fetched: {result.solved_count}")
        return

    # Display the picked problem
    problem = result.problem
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

    click.echo(f"  URL: https://leetcode.com/problems/{problem.slug}/")
    click.echo("")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo(f"  Unsolved: {result.unsolved_count} | Solved: {result.solved_count} | Total: {result.total_count}")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo("")

    # Offer to fetch
    click.echo(f"  Fetch with: dojo fetch {problem.id}")
    click.echo("")
