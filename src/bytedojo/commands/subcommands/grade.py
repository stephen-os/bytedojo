"""
Grade command - View solution status and manually grade problems.

Grades are applied by hand: pass, fail or skip. Passing a problem schedules
it for spaced-repetition review.
"""

import click
from pathlib import Path
from typing import Optional, List

from bytedojo.commands._resolve import resolve_problem
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.services import GradingService, GradeResult
from bytedojo.commands.ui import accent, bold, success, warn, error, dim


def _display_problem_status(problem: RegisteredProblem, show_test_hint: bool = True):
    """Display problem details and current grade."""
    click.echo()
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent('Problem Status')}")
    click.echo(dim("  " + "─" * 70))
    click.echo()
    click.echo(f"  {accent('#' + str(problem.problem_id))}  {bold(problem.title)}")
    click.echo(f"  {dim('Source')}      {problem.source.capitalize()}")
    click.echo(f"  {dim('Language')}    {problem.language.value.upper()}")
    click.echo(f"  {dim('Difficulty')}  {problem.difficulty.value or 'Unknown'}")

    if problem.file_path:
        click.echo(f"  {dim('File')}        {dim(problem.file_path)}")

    click.echo()
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent('Grade')}")
    click.echo(dim("  " + "─" * 70))
    click.echo()

    status = problem.status or ProblemStatus.UNGRADED

    if status == ProblemStatus.PASSED:
        click.echo(f"  Status: {success('PASSED')}")
    elif status == ProblemStatus.FAILED:
        click.echo(f"  Status: {error('FAILED')}")
    elif status == ProblemStatus.SKIPPED:
        click.echo(f"  Status: {warn('SKIPPED')}")
    elif status == ProblemStatus.UNGRADED:
        click.echo(f"  Status: {dim('UNGRADED')}")
        if show_test_hint:
            click.echo(f"  {dim('Tip:')} Run {accent(f'dojo grade {problem.problem_id} --pass')} once you have solved it")
    else:
        click.echo(f"  Status: {status.value.upper()}")

    if problem.last_graded:
        click.echo(f"  {dim('Last Graded')}  {problem.last_graded}")

    if problem.notes:
        click.echo(f"  {dim('Notes')}        {problem.notes}")

    click.echo()


def _prompt_for_manual_grade() -> tuple[Optional[str], Optional[str]]:
    """
    Prompt user to select a manual grade.

    Returns:
        Tuple of (status, notes) where status is 'passed', 'failed', 'skipped', or None to cancel
    """
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent('Manual Grade')}")
    click.echo(dim("  " + "─" * 70))
    click.echo()
    click.echo("  Override test results with a manual grade:")
    click.echo()
    click.echo(
        f"  {success('[P]')}ass  "
        f"{error('[F]')}ail  "
        f"{warn('[S]')}kip  "
        f"{dim('[Q]')}uit"
    )
    click.echo()

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


def _apply_grade(
    repo: Repository,
    problem: RegisteredProblem,
    status: str,
    notes: Optional[str] = None,
):
    """Apply a grade via the service and display the result."""
    service = GradingService()
    result = service.grade(repo, problem, status=status, notes=notes)

    if result.failed:
        click.echo()
        click.echo(f"  {error(result.error)}")
        click.echo()
        return

    _display_grade_result(result)


def _display_grade_result(result: GradeResult):
    """Display the grading result to the user."""
    click.echo()

    if result.status == 'passed':
        click.echo(f"  {success('MARKED AS PASSED')}")
        if result.scheduled_review:
            click.echo(
                f"  {accent(f'Scheduled for review in {result.review_frequency_days} days')}"
            )
    elif result.status == 'failed':
        click.echo(f"  {error('MARKED AS FAILED')}")
        if result.notes:
            click.echo(f"  {dim('Notes')}  {result.notes}")
    elif result.status == 'skipped':
        click.echo(f"  {warn('MARKED AS SKIPPED')}")
        if result.notes:
            click.echo(f"  {dim('Notes')}  {result.notes}")

    click.echo()


def _view_and_grade_problem(
    repo: Repository,
    problem: RegisteredProblem,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    manual: bool = False,
):
    """
    View problem status and optionally apply a manual grade.

    Returns True if action completed, False if cancelled.
    """
    # Refresh problem data so we display the latest test status
    with repo.open_db() as db:
        refreshed = db.get_problem(problem.source, problem.problem_id, problem.language.value)
    if refreshed:
        problem = refreshed

    _display_problem_status(problem, show_test_hint=(status is None and not manual))

    # If status provided via flags, apply it directly
    if status is not None:
        _apply_grade(repo, problem, status, notes)
        return True

    # If manual flag, prompt for grade
    if manual:
        status, notes = _prompt_for_manual_grade()
        if status is None:
            click.echo(f"  {dim('Cancelled.')}")
            return False
        _apply_grade(repo, problem, status, notes)
        return True

    return True


def _display_problems_page(
    problems: List[RegisteredProblem],
    page: int,
    per_page: int,
    title: str,
) -> tuple[int, int, List[RegisteredProblem]]:
    """Display a page of problems. Returns (current_page, total_pages, page_problems)."""
    total = len(problems)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    page_problems = problems[start_idx:end_idx]

    click.echo()
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent(title)}  {dim(f'(page {page}/{total_pages})')}")
    click.echo(dim("  " + "─" * 70))
    click.echo()
    click.echo(f"  {'#':>3}  {'ID':>8}  {'Status':8}  {'Lang':6}  {'Diff':6}  Title")
    click.echo(f"  {dim('-' * 3)}  {dim('-' * 8)}  {dim('-' * 8)}  {dim('-' * 6)}  {dim('-' * 6)}  {dim('-' * 25)}")

    for i, problem in enumerate(page_problems, start=1):
        status = problem.status or ProblemStatus.UNGRADED
        status_val = status.value[:8]
        lang_val = (problem.language.value if problem.language else 'py')[:6]
        diff_val = (problem.difficulty.value if problem.difficulty else '?')[:6]
        title_text = problem.title[:25] + ('...' if len(problem.title) > 25 else '')

        click.echo(
            f"  {i:>3}  {problem.problem_id:>8}  {status_val:8}  {lang_val:6}  {diff_val:6}  {title_text}"
        )

    click.echo()
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {dim(f'Showing {start_idx + 1}-{end_idx} of {total}')}")
    click.echo(dim("  " + "─" * 70))

    return page, total_pages, page_problems


def _batch_view_loop(repo: Repository, problems: List[RegisteredProblem], per_page: int = 10):
    """Run interactive problem status viewing loop."""
    if not problems:
        click.echo()
        click.echo(f"  {warn('No problems found!')}")
        click.echo(f"  {dim('Use dojo fetch <id> to add problems.')}")
        click.echo()
        return

    current_page = 1

    while True:
        current_page, total_pages, page_problems = _display_problems_page(
            problems, current_page, per_page, "Problem Status"
        )

        # Navigation prompt
        nav_hints = []
        nav_hints.append("1-{} view".format(len(page_problems)))
        if current_page > 1:
            nav_hints.append("p=prev")
        if current_page < total_pages:
            nav_hints.append("n=next")
        nav_hints.append("q=quit")

        click.echo()
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
                click.echo(f"  {dim('Already on last page.')}")
        elif user_input in ('p', 'prev', '<'):
            if current_page > 1:
                current_page -= 1
            else:
                click.echo(f"  {dim('Already on first page.')}")
        else:
            # Try to parse as selection number
            try:
                selection = int(user_input)
                if 1 <= selection <= len(page_problems):
                    selected_problem = page_problems[selection - 1]
                    _view_and_grade_problem(repo, selected_problem, manual=True)

                    # Refresh problems list after grading
                    with repo.open_db() as db:
                        problems = db.list_problems()

                    # Pause before returning to list
                    click.prompt("  Press Enter to continue", default="", show_default=False)
                else:
                    click.echo(f"  {dim(f'Invalid selection. Enter 1-{len(page_problems)}.')}")
            except ValueError:
                click.echo(f"  {dim('Invalid input. Use number/n/p/q.')}")


@click.command()
@click.argument('identifier', required=False)
@click.option('--name', '-n', 'name_search', help='Search by problem name')
@click.option('--desc', '-d', 'desc_search', help='Search by description keywords')
@click.option('--last', is_flag=True, help='View/grade most recently fetched problem')
@click.option('--manual', '-m', is_flag=True, help='Manually override grade (without running tests)')
@click.option('--pass', '-p', 'status_pass', is_flag=True, help='Mark as passed')
@click.option('--fail', '-f', 'status_fail', is_flag=True, help='Mark as failed')
@click.option('--skip', '-s', 'status_skip', is_flag=True, help='Mark as skipped')
@click.option('--notes', type=str, default=None, help='Add notes')
@click.option('--python', '-py', 'language', flag_value='python3', help='Select Python version')
@click.option('--java', 'language', flag_value='java', help='Select Java version')
@click.option('--cpp', 'language', flag_value='cpp', help='Select C++ version')
@click.option('--per-page', type=int, default=10, help='Problems per page in list mode')
def grade(
    identifier: Optional[str],
    name_search: Optional[str],
    desc_search: Optional[str],
    last: bool,
    manual: bool,
    status_pass: bool,
    status_fail: bool,
    status_skip: bool,
    notes: Optional[str],
    language: str | None,
    per_page: int
):
    """
    View solution status and manually grade problems.

    This command shows the current status of problems. Grade them with
    --manual or the status flags.

    When a problem is marked as passed, it gets scheduled for spaced repetition review.
    Uses configured default language (see: dojo settings default-language).

    Examples:
      dojo grade                       # Browse all problems and their status
      dojo grade 1                     # View status of problem #1
      dojo grade 1 --manual            # Manually grade problem #1
      dojo grade 1 --pass              # Quick pass problem #1
      dojo grade --name "Two Sum"      # Search by name
      dojo grade --last                # View/grade last fetched problem
      dojo grade 1 -f --notes "TLE"    # Fail with notes
    """
    repo = Repository.find(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    # Use configured default if no language flag specified
    if language is None:
        language = CodeLanguage.default().value

    # Determine status from flags (mutually exclusive)
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

    # Batch mode: no identifier, name, desc, or last → browse all problems
    if not identifier and not name_search and not desc_search and not last:
        with repo.open_db() as db:
            problems = db.list_problems()
        _batch_view_loop(repo, problems, per_page)
        return

    # Single-problem mode: resolve, then view / grade
    problem = resolve_problem(
        repo, language,
        identifier=identifier, name=name_search, desc=desc_search, last=last,
        command_name="grade",
    )
    _view_and_grade_problem(
        repo, problem, status, notes, manual=manual or status is not None,
    )
