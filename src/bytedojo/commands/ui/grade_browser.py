"""
Interactive grade presenter — the single-problem view/grade flow and
the paginated batch browser, extracted from the grade command (§7).

Pure presentation + prompting: all persistence goes through
GradingService; all lookups through the repository session.
"""

import click
from typing import List, Optional, Tuple

from bytedojo.commands.ui.palette import accent, dim, error, success, warn
from bytedojo.commands.ui.renderers import render_grade_result, render_problem_status
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.services import GradingService


def view_and_grade_problem(
    repo: Repository,
    problem: RegisteredProblem,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    manual: bool = False,
) -> bool:
    """
    View problem status and optionally apply a manual grade.

    Returns True if action completed, False if cancelled.
    """
    # Refresh problem data so we display the latest test status
    with repo.session() as s:
        refreshed = s.problems.get(problem.source, problem.problem_id)
    if refreshed:
        problem = refreshed

    render_problem_status(problem, show_test_hint=(status is None and not manual))

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


def browse_problems(
    repo: Repository,
    problems: List[RegisteredProblem],
    per_page: int = 10,
) -> None:
    """Run the interactive problem-status browser (batch mode)."""
    if not problems:
        click.echo()
        click.echo(f"  {warn('No problems found!')}")
        click.echo(f"  {dim('Use dojo fetch <id> to add problems.')}")
        click.echo()
        return

    current_page = 1

    while True:
        current_page, total_pages, page_problems = _render_problems_page(
            problems, current_page, per_page, "Problem Status"
        )

        nav_hints = ["1-{} view".format(len(page_problems))]
        if current_page > 1:
            nav_hints.append("p=prev")
        if current_page < total_pages:
            nav_hints.append("n=next")
        nav_hints.append("q=quit")

        click.echo()
        prompt = f"  [{' | '.join(nav_hints)}]: "

        try:
            user_input = (
                click.prompt("", prompt_suffix=prompt, default="q", show_default=False)
                .strip()
                .lower()
            )
        except click.Abort:
            break

        if user_input in ("q", "quit", ""):
            break
        elif user_input in ("n", "next", ">"):
            if current_page < total_pages:
                current_page += 1
            else:
                click.echo(f"  {dim('Already on last page.')}")
        elif user_input in ("p", "prev", "<"):
            if current_page > 1:
                current_page -= 1
            else:
                click.echo(f"  {dim('Already on first page.')}")
        else:
            try:
                selection = int(user_input)
            except ValueError:
                click.echo(f"  {dim('Invalid input. Use number/n/p/q.')}")
                continue
            if 1 <= selection <= len(page_problems):
                view_and_grade_problem(repo, page_problems[selection - 1], manual=True)

                # Refresh problems list after grading
                problems = repo.get_registered_problems()

                click.prompt(
                    "  Press Enter to continue", default="", show_default=False
                )
            else:
                click.echo(
                    f"  {dim(f'Invalid selection. Enter 1-{len(page_problems)}.')}"
                )


# --------------------------------------------------------------------------- #
# Internals                                                                   #
# --------------------------------------------------------------------------- #


def _apply_grade(
    repo: Repository,
    problem: RegisteredProblem,
    status: str,
    notes: Optional[str] = None,
) -> None:
    """Apply a grade via the service and render the result."""
    result = GradingService().grade(repo, problem, status=status, notes=notes)

    if result.failed:
        click.echo()
        click.echo(f"  {error(result.error)}")
        click.echo()
        return

    render_grade_result(result)


def _prompt_for_manual_grade() -> Tuple[Optional[str], Optional[str]]:
    """
    Prompt user to select a manual grade.

    Returns:
        Tuple of (status, notes) where status is 'passed', 'failed',
        'skipped', or None to cancel.
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
        choice = (
            click.prompt("  Select", default="q", show_default=False).strip().lower()
        )

        if choice in ("p", "pass"):
            status = "passed"
            break
        elif choice in ("f", "fail"):
            status = "failed"
            break
        elif choice in ("s", "skip"):
            status = "skipped"
            break
        elif choice in ("q", "quit", ""):
            return None, None
        else:
            click.echo("  Invalid choice. Use p/f/s/q.")

    notes = click.prompt(
        "  Notes (optional, Enter to skip)", default="", show_default=False
    ).strip()

    return status, notes if notes else None


def _render_problems_page(
    problems: List[RegisteredProblem],
    page: int,
    per_page: int,
    title: str,
) -> Tuple[int, int, List[RegisteredProblem]]:
    """Render a page of problems. Returns (current_page, total_pages, page_problems)."""
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
    click.echo(
        f"  {dim('-' * 3)}  {dim('-' * 8)}  {dim('-' * 8)}"
        f"  {dim('-' * 6)}  {dim('-' * 6)}  {dim('-' * 25)}"
    )

    for i, problem in enumerate(page_problems, start=1):
        status = problem.status or ProblemStatus.UNGRADED
        status_val = status.value[:8]
        lang_val = (problem.language.value if problem.language else "py")[:6]
        diff_val = (problem.difficulty.value if problem.difficulty else "?")[:6]
        title_text = problem.title[:25] + ("..." if len(problem.title) > 25 else "")

        click.echo(
            f"  {i:>3}  {problem.problem_id:>8}  {status_val:8}"
            f"  {lang_val:6}  {diff_val:6}  {title_text}"
        )

    click.echo()
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {dim(f'Showing {start_idx + 1}-{end_idx} of {total}')}")
    click.echo(dim("  " + "─" * 70))

    return page, total_pages, page_problems
