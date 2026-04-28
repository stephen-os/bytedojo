"""
Grade command - Mark problems as passed, failed, or skipped.
"""

import click
from datetime import datetime
from typing import Optional, List

from bytedojo.core.logger import get_logger, Theme
from bytedojo.core.database import DatabaseManager
from bytedojo.core.search import find_problems, select_problem
from bytedojo.commands.utils import (
    get_initialized_repo,
    STATUS_COLORS,
    DIFFICULTY_COLORS,
    SOURCE_COLORS,
    LANGUAGE_COLORS,
)


def _display_problem_header(problem: dict):
    """Display problem details header."""
    problem_id = problem['problem_id']
    source = problem['source']
    title = problem['title']
    difficulty = problem.get('difficulty') or 'Unknown'
    language = problem.get('language', 'python')
    file_path = problem.get('file_path', '')
    current_status = problem.get('test_status', 'ungraded')

    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo(click.style("  GRADE PROBLEM", fg='cyan', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")
    click.echo(f"  {problem_id}: {click.style(title, bold=True)}")
    click.echo(f"  Source: {click.style(source.capitalize(), fg=SOURCE_COLORS.get(source, 'white'))}")
    click.echo(f"  Language: {click.style(language.upper(), fg=LANGUAGE_COLORS.get(language, 'white'))}")
    click.echo(f"  Difficulty: {click.style(difficulty, fg=DIFFICULTY_COLORS.get(difficulty, 'white'))}")
    click.echo(f"  Current Status: {click.style(current_status, fg=STATUS_COLORS.get(current_status, 'white'))}")

    if file_path:
        click.echo(f"  File: {file_path}")

    click.echo("")


def _prompt_for_grade() -> tuple[Optional[str], Optional[str]]:
    """
    Prompt user to select a grade interactively.

    Returns:
        Tuple of (status, notes) where status is 'passed', 'failed', 'skipped', or None to cancel
    """
    click.echo("  Grade: ", nl=False)
    click.echo(
        f"{click.style('[P]', fg='green')}ass  "
        f"{click.style('[F]', fg='red')}ail  "
        f"{click.style('[S]', fg='yellow')}kip  "
        f"{click.style('[Q]', fg='bright_black')}uit"
    )
    click.echo("")

    while True:
        choice = click.prompt("  Select", default="q", show_default=False).strip().lower()

        if choice in ('p', 'pass'):
            status = 'passed'
            break
        elif choice in ('f', 'fail'):
            status = 'failed'
            break
        elif choice in ('s', 'skip'):
            status = 'skipped'
            break
        elif choice in ('q', 'quit', ''):
            return None, None
        else:
            click.echo("  Invalid choice. Use p/f/s/q.")

    # Prompt for optional notes
    notes = click.prompt("  Notes (optional, Enter to skip)", default="", show_default=False).strip()

    return status, notes if notes else None


def _apply_grade(db: DatabaseManager, problem: dict, status: str, notes: str = None):
    """
    Apply a grade to a problem and handle review scheduling.

    Args:
        db: Database manager
        problem: Problem dict
        status: Grade status ('passed', 'failed', 'skipped')
        notes: Optional notes
    """
    logger = get_logger()
    problem_db_id = problem['id']

    # Update the status
    db.update_test_status(problem_db_id, status, notes)

    # Schedule review if passed
    if status == 'passed':
        db.schedule_review(problem_db_id)
        review_freq = db.get_config('review_frequency_days', '7')

        click.echo("")
        click.echo(f"  {click.style('PASSED', fg='green', bold=True)}")
        click.echo(f"  {Theme.AQUA}Scheduled for review in {review_freq} days{Theme.RESET}")
    elif status == 'failed':
        click.echo("")
        click.echo(f"  {click.style('FAILED', fg='red', bold=True)}")
        if notes:
            click.echo(f"  Notes: {notes}")
    elif status == 'skipped':
        click.echo("")
        click.echo(f"  {click.style('SKIPPED', fg='yellow', bold=True)}")
        if notes:
            click.echo(f"  Notes: {notes}")

    click.echo("")


def _grade_single_problem(problem: dict, status: str = None, notes: str = None):
    """
    Grade a single problem, either with provided status or interactively.

    Args:
        problem: Problem dict from database
        status: Optional status ('passed', 'failed', 'skipped')
        notes: Optional notes

    Returns:
        True if graded, False if cancelled
    """
    repo = get_initialized_repo()

    with DatabaseManager(repo.get_db_path()) as db:
        _display_problem_header(problem)

        # If no status provided, prompt interactively
        if status is None:
            status, notes = _prompt_for_grade()
            if status is None:
                click.echo("  Cancelled.")
                return False

        _apply_grade(db, problem, status, notes)
        return True


def _display_ungraded_page(problems: list, page: int, per_page: int) -> tuple[int, int, List[dict]]:
    """
    Display a page of ungraded problems.

    Returns:
        Tuple of (current_page, total_pages, page_problems)
    """
    total = len(problems)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    page_problems = problems[start_idx:end_idx]

    click.echo("")
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo(click.style(f"  UNGRADED PROBLEMS (Page {page}/{total_pages})", fg='cyan', bold=True))
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo("")
    click.echo(f"  {'#':>3}  {'ID':>8}  {'Lang':6}  {'Diff':6}  Title")
    click.echo(f"  {'-' * 3}  {'-' * 8}  {'-' * 6}  {'-' * 6}  {'-' * 30}")

    for i, problem in enumerate(page_problems, start=1):
        problem_id = problem['problem_id']
        language = (problem.get('language') or 'py')[:6]
        difficulty = (problem.get('difficulty') or '?')[:6]
        title = problem['title'][:30] + ('...' if len(problem['title']) > 30 else '')

        lang_styled = click.style(f"{language:6}", fg=LANGUAGE_COLORS.get(problem.get('language'), 'white'))
        diff_styled = click.style(f"{difficulty:6}", fg=DIFFICULTY_COLORS.get(problem.get('difficulty'), 'white'))

        click.echo(f"  {i:>3}  {problem_id:>8}  {lang_styled}  {diff_styled}  {title}")

    click.echo("")
    click.echo(click.style("-" * 70, fg='bright_black'))
    click.echo(f"  Showing {start_idx + 1}-{end_idx} of {total}")
    click.echo(click.style("-" * 70, fg='bright_black'))

    return page, total_pages, page_problems


def _batch_grading_loop(problems: list, per_page: int = 10):
    """Run interactive batch grading loop."""
    if not problems:
        click.echo("")
        click.echo(click.style("  No ungraded problems found!", fg='green'))
        click.echo("  All your problems have been graded.")
        click.echo("")
        return

    current_page = 1

    while problems:  # Re-fetch to account for graded problems
        repo = get_initialized_repo()
        with DatabaseManager(repo.get_db_path()) as db:
            # Refresh ungraded list
            problems = db.get_problems_by_status('ungraded')

        if not problems:
            click.echo("")
            click.echo(click.style("  All problems graded!", fg='green'))
            click.echo("")
            break

        current_page, total_pages, page_problems = _display_ungraded_page(problems, current_page, per_page)

        # Navigation prompt
        nav_hints = []
        nav_hints.append("1-{} select".format(len(page_problems)))
        if current_page > 1:
            nav_hints.append("p=prev")
        if current_page < total_pages:
            nav_hints.append("n=next")
        nav_hints.append("q=quit")

        click.echo("")
        prompt = f"  [{' | '.join(nav_hints)}]: "

        try:
            user_input = click.prompt("", prompt_suffix=prompt, default="q", show_default=False).strip().lower()
        except click.Abort:
            break

        if user_input in ('q', 'quit', ''):
            break
        elif user_input in ('n', 'next', '>'):
            if current_page < total_pages:
                current_page += 1
            else:
                click.echo("  Already on last page.")
        elif user_input in ('p', 'prev', '<'):
            if current_page > 1:
                current_page -= 1
            else:
                click.echo("  Already on first page.")
        else:
            # Try to parse as selection number
            try:
                selection = int(user_input)
                if 1 <= selection <= len(page_problems):
                    selected_problem = page_problems[selection - 1]
                    _grade_single_problem(selected_problem)

                    # Pause before returning to list
                    click.prompt("  Press Enter to continue", default="", show_default=False)
                else:
                    click.echo(f"  Invalid selection. Enter 1-{len(page_problems)}.")
            except ValueError:
                click.echo("  Invalid input. Use number/n/p/q.")


# ============================================================================
# CLI COMMANDS
# ============================================================================

@click.command()
@click.argument('identifier', required=False)
@click.option('--name', '-n', 'name_search', help='Search by problem name')
@click.option('--desc', '-d', 'desc_search', help='Search by description keywords')
@click.option('--last', is_flag=True, help='Grade most recently fetched problem')
@click.option('--pass', '-p', 'status_pass', is_flag=True, help='Mark as passed')
@click.option('--fail', '-f', 'status_fail', is_flag=True, help='Mark as failed')
@click.option('--skip', '-s', 'status_skip', is_flag=True, help='Mark as skipped')
@click.option('--notes', type=str, default=None, help='Add notes')
@click.option('--python', 'language', flag_value='python', default=True, help='Grade Python version (default)')
@click.option('--java', 'language', flag_value='java', help='Grade Java version')
@click.option('--cpp', 'language', flag_value='cpp', help='Grade C++ version')
@click.option('--per-page', type=int, default=10, help='Problems per page in batch mode')
def grade(
    identifier: Optional[str],
    name_search: Optional[str],
    desc_search: Optional[str],
    last: bool,
    status_pass: bool,
    status_fail: bool,
    status_skip: bool,
    notes: Optional[str],
    language: str,
    per_page: int
):
    """
    Grade problems as passed, failed, or skipped.

    When a problem is marked as passed, it gets scheduled for spaced repetition review.

    Examples:
      dojo grade                       # Interactive batch grading
      dojo grade 1                     # Grade problem #1 (Python)
      dojo grade 1 --java              # Grade Java version
      dojo grade --name "Two Sum"      # Search by name
      dojo grade --last                # Grade last fetched problem
      dojo grade 1 --pass              # Quick pass problem #1
      dojo grade 1 -f --notes "TLE"    # Fail with notes
    """
    repo = get_initialized_repo()

    # Determine status from flags
    status = None
    flag_count = sum([status_pass, status_fail, status_skip])

    if flag_count > 1:
        raise click.ClickException("Cannot specify multiple status flags. Use one of --pass, --fail, or --skip.")

    if status_pass:
        status = 'passed'
    elif status_fail:
        status = 'failed'
    elif status_skip:
        status = 'skipped'

    with DatabaseManager(repo.get_db_path()) as db:
        # Batch mode: no identifier, name, desc, or last
        if not identifier and not name_search and not desc_search and not last:
            ungraded = db.get_problems_by_status('ungraded')
            _batch_grading_loop(ungraded, per_page)
            return

        # Handle --last flag
        if last:
            problems = db.list_problems(language=language, limit=1)
            if not problems:
                raise click.ClickException(
                    f"No {language} problems found. "
                    f"Fetch one first with: dojo fetch <id> --{language}"
                )
            # Get most recent by fetched_at
            problem_data = max(problems, key=lambda p: p.get('fetched_at', ''))
        else:
            # Find matching problems
            matches = find_problems(
                db,
                identifier=identifier,
                name=name_search,
                desc=desc_search,
                language=language
            )

            if not matches:
                criteria = []
                if identifier:
                    criteria.append(f"ID '{identifier}'")
                if name_search:
                    criteria.append(f"name '{name_search}'")
                if desc_search:
                    criteria.append(f"description '{desc_search}'")

                criteria_str = ", ".join(criteria) if criteria else "given criteria"
                raise click.ClickException(
                    f"No {language} problems found matching {criteria_str}. "
                    f"Fetch one first with: dojo fetch <id> --{language}"
                )

            # Select problem (interactive if multiple)
            problem_data = select_problem(matches)
            if not problem_data:
                raise click.Abort()

    _grade_single_problem(problem_data, status, notes)
