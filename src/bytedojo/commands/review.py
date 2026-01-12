"""
Review command - Spaced repetition review system for problems.
"""

import random
import click
from datetime import date, datetime

from bytedojo.core.logger import get_logger
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager


def _format_date(date_str: str) -> str:
    """Format a date string for display."""
    if not date_str:
        return "N/A"
    try:
        d = datetime.fromisoformat(date_str).date()
        today = date.today()
        delta = (d - today).days

        if delta < 0:
            return f"{abs(delta)} days overdue"
        elif delta == 0:
            return "Today"
        elif delta == 1:
            return "Tomorrow"
        elif delta < 7:
            return f"In {delta} days"
        else:
            return d.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str


def _get_source_color(source: str) -> str:
    """Get color for source platform."""
    if source == 'leetcode':
        return 'yellow'
    elif source == 'codeforces':
        return 'cyan'
    return 'white'


@click.group(invoke_without_command=True)
@click.option('--all', '-a', 'show_all', is_flag=True, help='Show all scheduled reviews, not just due')
@click.pass_context
def review(ctx, show_all: bool):
    """
    Spaced repetition review system.

    Shows problems that are due for review based on your review frequency setting.
    When you grade a problem as passed, it gets scheduled for review.

    Examples:
      dojo review                  # Show problems due for review
      dojo review --all            # Show all scheduled reviews
      dojo review pick             # Pick a random problem to review
      dojo review stats            # Show review statistics
    """
    ctx.ensure_object(dict)
    ctx.obj['show_all'] = show_all

    if ctx.invoked_subcommand is None:
        _show_due_reviews(show_all)


def _show_due_reviews(show_all: bool = False):
    """Show problems due for review."""
    logger = get_logger()

    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    with DatabaseManager(repo.get_db_path()) as db:
        reviews = db.get_due_reviews(include_future=show_all)
        review_freq = db.get_config('review_frequency_days', '7')

        if not reviews:
            if show_all:
                click.echo("\nNo problems scheduled for review yet.")
                click.echo("Problems are added to review when you grade them as passed.")
            else:
                click.echo(click.style("\nNo problems due for review!", fg='green'))
                click.echo("Great job staying on top of your reviews.")

            click.echo(f"\nCurrent review frequency: {review_freq} days")
            click.echo("Change with: dojo settings review-frequency <days>")
            return

        # Count due vs upcoming
        today = date.today()
        due_count = sum(1 for r in reviews
                       if datetime.fromisoformat(r['next_review_date']).date() <= today)

        # Header
        click.echo("")
        if show_all:
            click.echo(click.style("=" * 60, fg='bright_black'))
            click.echo(click.style("  ALL SCHEDULED REVIEWS", fg='cyan', bold=True))
            click.echo(click.style("=" * 60, fg='bright_black'))
        else:
            click.echo(click.style("=" * 60, fg='bright_black'))
            click.echo(click.style(f"  PROBLEMS DUE FOR REVIEW ({due_count})", fg='yellow', bold=True))
            click.echo(click.style("=" * 60, fg='bright_black'))

        click.echo("")
        click.echo(f"  {'ID':>8}  {'Source':10}  {'Due':15}  {'Reviews':>7}  Title")
        click.echo(f"  {'-' * 8}  {'-' * 10}  {'-' * 15}  {'-' * 7}  {'-' * 20}")

        for r in reviews:
            problem_id = r['problem_id']
            source = r['source']
            title = r['title'][:30] + '...' if len(r['title']) > 30 else r['title']
            due_date = _format_date(r['next_review_date'])
            reps = r['repetitions']

            # Color based on due status
            review_date = datetime.fromisoformat(r['next_review_date']).date()
            if review_date < today:
                due_styled = click.style(f"{due_date:15}", fg='red')
            elif review_date == today:
                due_styled = click.style(f"{due_date:15}", fg='yellow')
            else:
                due_styled = click.style(f"{due_date:15}", fg='green')

            source_styled = click.style(f"{source:10}", fg=_get_source_color(source))

            click.echo(f"  {problem_id:>8}  {source_styled}  {due_styled}  {reps:>7}  {title}")

        click.echo("")
        click.echo(click.style("-" * 60, fg='bright_black'))
        click.echo(f"  Review frequency: {review_freq} days")
        click.echo(click.style("-" * 60, fg='bright_black'))
        click.echo("")

        if due_count > 0:
            click.echo("  Start reviewing with: dojo review pick")
            click.echo("")


@review.command()
@click.pass_context
def pick(ctx):
    """
    Pick a random problem due for review.

    Selects a random problem from those due for review and shows its details.

    Examples:
      dojo review pick             # Pick a random due problem
    """
    logger = get_logger()

    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    with DatabaseManager(repo.get_db_path()) as db:
        due_reviews = db.get_due_reviews(include_future=False)

        if not due_reviews:
            click.echo(click.style("\nNo problems due for review!", fg='green'))
            click.echo("You're all caught up. Check back later.")
            return

        # Pick a random problem
        problem = random.choice(due_reviews)

        problem_id = problem['problem_id']
        source = problem['source']
        title = problem['title']
        difficulty = problem['difficulty'] or 'Unknown'
        file_path = problem.get('file_path', '')
        reps = problem['repetitions']
        due_date = _format_date(problem['next_review_date'])

        # Display the picked problem
        click.echo("")
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo(click.style("  REVIEW THIS PROBLEM", fg='yellow', bold=True))
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo("")
        click.echo(f"  {problem_id}: {click.style(title, bold=True)}")
        click.echo(f"  Source: {click.style(source.capitalize(), fg=_get_source_color(source))}")
        click.echo(f"  Difficulty: {difficulty}")
        click.echo(f"  Times Reviewed: {reps}")
        click.echo(f"  Due: {due_date}")

        if file_path:
            click.echo(f"  File: {file_path}")

        # Generate URL
        if source == 'leetcode':
            # Get title slug from file path or use problem_id
            url = f"https://leetcode.com/problems/"
            click.echo(f"  URL: {url}")
        elif source == 'codeforces':
            # Parse contest_id and index from problem_id
            import re
            match = re.match(r'^(\d+)([A-Za-z]\d?)$', problem_id)
            if match:
                contest_id, index = match.groups()
                url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
                click.echo(f"  URL: {url}")

        click.echo("")
        click.echo(click.style("-" * 60, fg='bright_black'))

        # Show stats
        due_count = len(due_reviews)
        click.echo(f"  Due for review: {due_count} problem(s)")
        click.echo(click.style("-" * 60, fg='bright_black'))
        click.echo("")

        # Instructions
        if file_path:
            click.echo(f"  1. Open the file and solve it again")
            click.echo(f"  2. Submit to {source.capitalize()} to verify your solution")
            click.echo(f"  3. Run: dojo grade problem {problem_id} --pass")
            click.echo(f"  4. Grading as passed will schedule the next review")
        click.echo("")


@review.command()
def stats():
    """
    Show review statistics.

    Displays statistics about your review schedule and progress.

    Examples:
      dojo review stats
    """
    logger = get_logger()

    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    with DatabaseManager(repo.get_db_path()) as db:
        review_stats = db.get_review_stats()
        review_freq = db.get_config('review_frequency_days', '7')

        click.echo("")
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo(click.style("  REVIEW STATISTICS", fg='cyan', bold=True))
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo("")

        click.echo(f"  Review Frequency: {review_freq} days")
        click.echo("")
        click.echo(f"  Due Today:        {click.style(str(review_stats['due_today']), fg='yellow' if review_stats['due_today'] > 0 else 'green')}")
        click.echo(f"  Due This Week:    {review_stats['due_this_week']}")
        click.echo(f"  Total in Review:  {review_stats['total_in_review']}")

        if review_stats['most_reviewed']:
            click.echo("")
            click.echo("  Most Reviewed Problems:")
            for p in review_stats['most_reviewed']:
                click.echo(f"    {p['problem_id']:>8} ({p['source']}) - {p['repetitions']} reviews")

        click.echo("")
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo("")
