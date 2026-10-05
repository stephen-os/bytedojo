"""
review - Spaced repetition review system for problems.
"""

import click
from typing import Optional

from bytedojo.commands._options import selectors
from bytedojo.commands._resolve import require_repo, resolve_problem
from bytedojo.commands.ui import dim, success
from bytedojo.commands.ui.renderers import (
    render_review_action,
    render_review_completion,
    render_review_list,
    render_review_pick,
    render_review_stats,
)
from bytedojo.services import ReviewQuality, ReviewService


@click.group(invoke_without_command=True)
@click.option(
    "--all",
    "-a",
    "show_all",
    is_flag=True,
    help="Show all scheduled reviews, not just due",
)
@click.pass_context
def review(ctx, show_all: bool):
    """
    Spaced repetition review system.

    Problems enter the schedule when they first pass `dojo test` (or
    `dojo grade --pass`). Testing a due problem again IS completing
    its review; `review complete` exists to signal --easy or --hard
    recall explicitly.

    Examples:
      dojo review                              # Show problems due for review
      dojo review --all                        # Show all scheduled reviews
      dojo review pick                         # Pick a random problem to review
      dojo review complete 1 --good            # Mark a review as completed
      dojo review stats                        # Show review statistics
    """
    if ctx.invoked_subcommand is None:
        _show_due_reviews(show_all)


def _show_due_reviews(show_all: bool = False):
    """Show problems due for review."""
    repo = require_repo()
    service = ReviewService()
    reviews = service.get_due_reviews(repo, include_future=show_all)
    review_freq = service.get_review_frequency(repo)
    render_review_list(
        reviews,
        show_all=show_all,
        review_freq=review_freq,
        format_due_date=ReviewService.format_due_date,
    )


# ============================================================================
# pick - pick a random due review
# ============================================================================


@review.command()
def pick():
    """
    Pick a random problem due for review.

    Examples:
      dojo review pick
    """
    repo = require_repo()
    service = ReviewService()
    problem = service.pick_random_due(repo)

    if not problem:
        click.echo()
        click.echo(f"  {success('No problems due for review!')}")
        click.echo(f"  {dim('You are all caught up. Check back later.')}")
        return

    render_review_pick(
        problem,
        service.get_due_count(repo),
        ReviewService.format_due_date,
    )


# ============================================================================
# complete - apply SM-2 update after reviewing a problem
# ============================================================================


@review.command()
@click.argument("identifier", required=False)
@click.option(
    "--easy", "quality", flag_value="easy", help="Recalled effortlessly — ease grows"
)
@click.option(
    "--good",
    "quality",
    flag_value="good",
    help="Recalled with effort — standard SM-2 step",
)
@click.option(
    "--hard",
    "quality",
    flag_value="hard",
    help="Struggled — interval resets, ease decreases",
)
@selectors
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

    Use this after reviewing a problem via `dojo review pick`. A plain
    `dojo test` pass on a due problem records a --good review
    automatically; this command is for signalling --easy or --hard.

    Examples:
      dojo review complete 1 --good
      dojo review complete --last --easy
    """
    if quality is None:
        raise click.UsageError("Specify a quality rating: --easy, --good, or --hard")

    repo = require_repo()
    problem = resolve_problem(
        repo,
        identifier=identifier,
        name=name_search,
        desc=desc_search,
        last=last,
        command_name="review complete",
        language=language,
    )

    result = ReviewService().complete_review(repo, problem.id, ReviewQuality(quality))
    if result.failed:
        raise click.ClickException(result.error)

    render_review_completion(problem.title, result)


# ============================================================================
# add / snooze / remove
# ============================================================================


@review.command()
@click.argument("identifier", required=False)
@click.option(
    "--days",
    type=int,
    default=None,
    help="Initial interval in days (default: review-frequency setting)",
)
@selectors
def add(
    identifier: Optional[str],
    days: Optional[int],
    name_search: Optional[str],
    desc_search: Optional[str],
    last: bool,
    language: Optional[str],
):
    """
    Manually queue a problem for review without grading it as passed.

    Errors if the problem is already in the review queue — use
    `dojo review snooze` to delay an existing review or
    `dojo review remove` then `dojo review add` to reset.

    Examples:
      dojo review add 1
      dojo review add 1 --days 3
    """
    repo, problem = _resolve(language, identifier, name_search, desc_search, last)
    result = ReviewService().add_review(repo, problem.id, days=days)
    if result.failed:
        raise click.ClickException(result.error)
    render_review_action(problem.title, result)


@review.command()
@click.argument("identifier", required=False)
@click.option(
    "--days",
    type=int,
    default=1,
    help="Snooze duration in days from today (default: 1)",
)
@selectors
def snooze(
    identifier: Optional[str],
    days: int,
    name_search: Optional[str],
    desc_search: Optional[str],
    last: bool,
    language: Optional[str],
):
    """
    Push a scheduled review out to N days from today.

    Doesn't touch the SRS state (interval / ease / repetitions) — only
    the next review date moves. Useful when you know you can't get to a
    review today.

    Examples:
      dojo review snooze 1              # push to tomorrow
      dojo review snooze 1 --days 3     # push 3 days out
    """
    repo, problem = _resolve(language, identifier, name_search, desc_search, last)
    result = ReviewService().snooze_review(repo, problem.id, days=days)
    if result.failed:
        raise click.ClickException(result.error)
    render_review_action(problem.title, result)


@review.command()
@click.argument("identifier", required=False)
@selectors
def remove(
    identifier: Optional[str],
    name_search: Optional[str],
    desc_search: Optional[str],
    last: bool,
    language: Optional[str],
):
    """
    Drop a problem from the review queue entirely.

    Examples:
      dojo review remove 1
    """
    repo, problem = _resolve(language, identifier, name_search, desc_search, last)
    result = ReviewService().remove_review(repo, problem.id)
    if result.failed:
        raise click.ClickException(result.error)
    render_review_action(problem.title, result)


def _resolve(
    language: Optional[str],
    identifier: Optional[str],
    name_search: Optional[str],
    desc_search: Optional[str],
    last: bool,
):
    """Repo + problem lookup shared by add / snooze / remove."""
    repo = require_repo()
    problem = resolve_problem(
        repo,
        identifier=identifier,
        name=name_search,
        desc=desc_search,
        last=last,
        command_name="review",
        language=language,
    )
    return repo, problem


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
    repo = require_repo()
    service = ReviewService()
    render_review_stats(service.get_stats(repo), service.get_review_frequency(repo))
