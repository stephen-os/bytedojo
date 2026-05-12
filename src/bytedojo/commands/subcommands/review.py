"""
review - Spaced repetition review system for problems.
"""

import click
from pathlib import Path
from typing import Optional

from bytedojo.commands._resolve import resolve_problem
from bytedojo.core.logger import Theme
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.repository import Repository
from bytedojo.services import ReviewService, ReviewQuality, ReviewCompletionResult


@click.group(invoke_without_command=True)
@click.option('--all', '-a', 'show_all', is_flag=True, help='Show all scheduled reviews, not just due')
@click.pass_context
def review(ctx, show_all: bool):
    """
    Spaced repetition review system.

    Shows problems that are due for review. When you grade a problem as
    passed, it gets scheduled at the base interval (`review-frequency`).
    Reviewing it again with `dojo review complete --easy/--good/--hard`
    applies an SM-2-style update that grows the interval as the problem
    becomes more familiar.

    Examples:
      dojo review                              # Show problems due for review
      dojo review --all                        # Show all scheduled reviews
      dojo review pick                         # Pick a random problem to review
      dojo review complete 1 --python --good   # Mark a review as completed
      dojo review stats                        # Show review statistics
    """
    ctx.ensure_object(dict)
    ctx.obj['show_all'] = show_all

    if ctx.invoked_subcommand is None:
        _show_due_reviews(show_all)


# ============================================================================
# DEFAULT: show due reviews
# ============================================================================

def _show_due_reviews(show_all: bool = False):
    """Show problems due for review."""
    repo = Repository.open(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    service = ReviewService()
    reviews = service.get_due_reviews(repo, include_future=show_all)
    review_freq = service.get_review_frequency(repo)

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
    click.echo(click.style("=" * 60, fg='bright_black'))
    if show_all:
        click.echo(click.style("  ALL SCHEDULED REVIEWS", fg='cyan', bold=True))
    else:
        click.echo(click.style(f"  PROBLEMS DUE FOR REVIEW ({due_count})", fg='yellow', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))

    click.echo("")
    click.echo(f"  {'ID':>8}  {'Source':10}  {'Due':15}  {'Reviews':>7}  Title")
    click.echo(f"  {'-' * 8}  {'-' * 10}  {'-' * 15}  {'-' * 7}  {'-' * 20}")

    for r in reviews:
        title = r.title[:30] + '...' if len(r.title) > 30 else r.title
        due_date = ReviewService.format_due_date(r.next_review_date)
        display_id = r.problem_num if r.problem_num else r.problem_id

        # Color based on due status
        if r.is_overdue:
            due_styled = click.style(f"{due_date:15}", fg='red')
        elif r.is_due_today:
            due_styled = click.style(f"{due_date:15}", fg='yellow')
        else:
            due_styled = click.style(f"{due_date:15}", fg='green')

        click.echo(f"  {display_id:>8}  {r.source:10}  {due_styled}  {r.repetitions:>7}  {title}")

    click.echo("")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo(f"  Review frequency: {review_freq} days")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo("")

    if due_count > 0:
        click.echo("  Start reviewing with: dojo review pick")
        click.echo("  Mark complete with:   dojo review complete <id> --[easy|good|hard]")
        click.echo("")


# ============================================================================
# pick - pick a random due review
# ============================================================================

@review.command()
@click.pass_context
def pick(ctx):
    """
    Pick a random problem due for review.

    Examples:
      dojo review pick
    """
    repo = Repository.open(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    service = ReviewService()
    problem = service.pick_random_due(repo)

    if not problem:
        click.echo(click.style("\nNo problems due for review!", fg='green'))
        click.echo("You're all caught up. Check back later.")
        return

    due_date = ReviewService.format_due_date(problem.next_review_date)
    display_id = problem.problem_num if problem.problem_num else problem.problem_id

    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo(click.style("  REVIEW THIS PROBLEM", fg='yellow', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")
    click.echo(f"  {display_id}: {click.style(problem.title, bold=True)}")
    click.echo(f"  Source: {problem.source.capitalize()}")
    click.echo(f"  Language: {problem.language.upper()}")
    click.echo(f"  Difficulty: {problem.difficulty or 'Unknown'}")
    click.echo(f"  Times Reviewed: {problem.repetitions}")
    click.echo(f"  Current interval: {problem.interval_days} days  "
               f"({Theme.AQUA}ease {problem.ease_factor:.2f}{Theme.RESET})")
    click.echo(f"  Due: {due_date}")

    if problem.file_path:
        click.echo(f"  File: {problem.file_path}")

    click.echo("")
    click.echo(click.style("-" * 60, fg='bright_black'))

    due_count = service.get_due_count(repo)
    click.echo(f"  Due for review: {due_count} problem(s)")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo("")

    if problem.file_path:
        lang_flag = "--python" if problem.language == "python3" else f"--{problem.language}"
        click.echo(f"  1. Open the file and solve it again")
        click.echo(f"  2. Verify your solution (e.g. `dojo test {display_id} {lang_flag}`)")
        click.echo(f"  3. Mark complete: `dojo review complete {display_id} {lang_flag} --good`")
        click.echo(f"     (use --easy / --good / --hard to grade how well you recalled)")
    click.echo("")


# ============================================================================
# complete - apply SM-2 update after reviewing a problem
# ============================================================================

@review.command()
@click.argument('identifier', required=False)

# Quality flags (mutually exclusive)
@click.option('--easy', 'quality', flag_value='easy',
              help='Recalled effortlessly — interval grows extra')
@click.option('--good', 'quality', flag_value='good',
              help='Recalled with effort — interval grows by ease factor')
@click.option('--hard', 'quality', flag_value='hard',
              help='Struggled — reset interval, ease decreases')

# Selector flags (same shape as dojo grade / test / run)
@click.option('--name', '-n', 'name_search', help='Search by problem name')
@click.option('--desc', '-d', 'desc_search', help='Search by description keywords')
@click.option('--last', is_flag=True, help='Most recently fetched problem')
@click.option('--python', '-py', 'language', flag_value='python3', help='Python version')
@click.option('--java', 'language', flag_value='java', help='Java version')
@click.option('--cpp', 'language', flag_value='cpp', help='C++ version')
def complete(
    identifier: Optional[str],
    quality: Optional[str],
    name_search: Optional[str],
    desc_search: Optional[str],
    last: bool,
    language: Optional[str],
):
    """
    Mark a review as complete with an SM-2 quality rating.

    Use this after reviewing a problem via `dojo review pick`. The quality
    flag controls how the next interval is computed:

      --easy    interval × ease × 1.3; ease increases (problem feels easy)
      --good    interval × ease;        ease unchanged (standard recall)
      --hard    interval reset to 1;    ease decreases (struggled)

    Examples:
      dojo review complete 1 --python --good
      dojo review complete --last --easy
    """
    if quality is None:
        raise click.ClickException(
            "Specify a quality rating: --easy, --good, or --hard"
        )

    repo = Repository.open(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    if language is None:
        language = CodeLanguage.default().value

    problem = resolve_problem(
        repo, language,
        identifier=identifier, name=name_search, desc=desc_search, last=last,
        command_name="review complete",
    )

    quality_enum = ReviewQuality(quality)
    service = ReviewService()
    result = service.complete_review(repo, problem.id, quality_enum)

    if result.failed:
        raise click.ClickException(result.error)

    _display_completion(problem.title, result)


def _display_completion(title: str, r: ReviewCompletionResult) -> None:
    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo(click.style(f"  REVIEW COMPLETE - {r.quality.value.upper()}", fg='green', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")
    click.echo(f"  {title}")
    click.echo("")
    click.echo(
        f"  Interval:     {r.previous_interval} days  ->  "
        f"{click.style(str(r.next_interval) + ' days', fg='cyan', bold=True)}"
    )
    click.echo(
        f"  Ease factor:  {r.previous_ease:.2f}  ->  "
        f"{click.style(f'{r.next_ease:.2f}', fg='cyan')}"
    )
    click.echo(
        f"  Repetitions:  {r.previous_repetitions}  ->  {r.next_repetitions}"
    )
    if r.next_review_date:
        click.echo(f"  Next review:  {r.next_review_date}")
    click.echo("")


# ============================================================================
# stats - review statistics
# ============================================================================

@review.command()
def stats():
    """
    Show review statistics.

    Examples:
      dojo review stats
    """
    repo = Repository.open(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    service = ReviewService()
    review_stats = service.get_stats(repo)
    review_freq = service.get_review_frequency(repo)

    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo(click.style("  REVIEW STATISTICS", fg='cyan', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")

    click.echo(f"  Review Frequency: {review_freq} days")
    click.echo("")
    click.echo(f"  Due Today:        {click.style(str(review_stats.due_today), fg='yellow' if review_stats.due_today > 0 else 'green')}")
    click.echo(f"  Due This Week:    {review_stats.due_this_week}")
    click.echo(f"  Total in Review:  {review_stats.total_in_review}")

    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")
