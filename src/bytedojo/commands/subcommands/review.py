"""
Review command - Spaced repetition review system for problems.
"""

import click

from bytedojo.core.database import DatabaseManager
from bytedojo.core.review_service import ReviewService, ReviewProblem
from bytedojo.commands.subcommands.utils import get_initialized_repo, SOURCE_COLORS


def _get_source_color(source: str) -> str:
    """Get color for source platform."""
    return SOURCE_COLORS.get(source, 'white')


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
    repo = get_initialized_repo()

    with DatabaseManager(repo.get_db_path()) as db:
        service = ReviewService(db)
        reviews = service.get_due_reviews(include_future=show_all)
        review_freq = service.get_review_frequency()

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
        due_count = sum(1 for r in reviews if r.days_until_due <= 0)

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
            title = r.title[:30] + '...' if len(r.title) > 30 else r.title
            due_date = ReviewService.format_due_date(r.next_review_date)

            # Color based on due status
            if r.is_overdue:
                due_styled = click.style(f"{due_date:15}", fg='red')
            elif r.is_due_today:
                due_styled = click.style(f"{due_date:15}", fg='yellow')
            else:
                due_styled = click.style(f"{due_date:15}", fg='green')

            source_styled = click.style(f"{r.source:10}", fg=_get_source_color(r.source))

            click.echo(f"  {r.problem_id:>8}  {source_styled}  {due_styled}  {r.repetitions:>7}  {title}")

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
    repo = get_initialized_repo()

    with DatabaseManager(repo.get_db_path()) as db:
        service = ReviewService(db)
        problem = service.pick_random_due()

        if not problem:
            click.echo(click.style("\nNo problems due for review!", fg='green'))
            click.echo("You're all caught up. Check back later.")
            return

        due_date = ReviewService.format_due_date(problem.next_review_date)

        # Display the picked problem
        click.echo("")
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo(click.style("  REVIEW THIS PROBLEM", fg='yellow', bold=True))
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo("")
        click.echo(f"  {problem.problem_id}: {click.style(problem.title, bold=True)}")
        click.echo(f"  Source: {click.style(problem.source.capitalize(), fg=_get_source_color(problem.source))}")
        click.echo(f"  Difficulty: {problem.difficulty}")
        click.echo(f"  Times Reviewed: {problem.repetitions}")
        click.echo(f"  Due: {due_date}")

        if problem.file_path:
            click.echo(f"  File: {problem.file_path}")

        if problem.url:
            click.echo(f"  URL: {problem.url}")

        click.echo("")
        click.echo(click.style("-" * 60, fg='bright_black'))

        # Show stats
        due_count = service.get_due_count()
        click.echo(f"  Due for review: {due_count} problem(s)")
        click.echo(click.style("-" * 60, fg='bright_black'))
        click.echo("")

        # Instructions
        if problem.file_path:
            click.echo(f"  1. Open the file and solve it again")
            click.echo(f"  2. Submit to {problem.source.capitalize()} to verify your solution")
            click.echo(f"  3. Run: dojo grade {problem.problem_id} --pass")
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
    repo = get_initialized_repo()

    with DatabaseManager(repo.get_db_path()) as db:
        service = ReviewService(db)
        review_stats = service.get_stats()

        click.echo("")
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo(click.style("  REVIEW STATISTICS", fg='cyan', bold=True))
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo("")

        click.echo(f"  Review Frequency: {review_stats.review_frequency_days} days")
        click.echo("")
        click.echo(f"  Due Today:        {click.style(str(review_stats.due_today), fg='yellow' if review_stats.due_today > 0 else 'green')}")
        click.echo(f"  Due This Week:    {review_stats.due_this_week}")
        click.echo(f"  Total in Review:  {review_stats.total_in_review}")

        if review_stats.most_reviewed:
            click.echo("")
            click.echo("  Most Reviewed Problems:")
            for p in review_stats.most_reviewed:
                click.echo(f"    {p['problem_id']:>8} ({p['source']}) - {p['repetitions']} reviews")

        click.echo("")
        click.echo(click.style("=" * 60, fg='bright_black'))
        click.echo("")
