"""
Grade command - View solution status and manually grade problems.

`dojo test` is the primary grading loop; this command is the manual
override: pass, fail or skip by hand, with the same §9 schedule
effects a test outcome would have.
"""

import click
from typing import Optional

from bytedojo.commands._options import selectors
from bytedojo.commands._resolve import require_repo, resolve_problem
from bytedojo.commands.ui.grade_browser import browse_problems, view_and_grade_problem


@click.command()
@click.argument("identifier", required=False)
@click.option(
    "--manual",
    "-m",
    is_flag=True,
    help="Manually override grade (without running tests)",
)
@click.option("--pass", "-p", "status_pass", is_flag=True, help="Mark as passed")
@click.option("--fail", "-f", "status_fail", is_flag=True, help="Mark as failed")
@click.option("--skip", "-s", "status_skip", is_flag=True, help="Mark as skipped")
@click.option("--notes", type=str, default=None, help="Add notes")
@click.option("--per-page", type=int, default=10, help="Problems per page in list mode")
@selectors
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
    per_page: int,
):
    """
    View solution status and manually grade problems.

    Marking a problem as passed schedules (or advances) its
    spaced-repetition review; failing lapses it; skipping sets it
    aside and drops the schedule.

    Examples:
      dojo grade                       # Browse all problems and their status
      dojo grade 1                     # View status of problem #1
      dojo grade 1 --manual            # Manually grade problem #1
      dojo grade 1 --pass              # Quick pass problem #1
      dojo grade --name "Two Sum"      # Search by name
      dojo grade --last                # View/grade last fetched problem
      dojo grade 1 -f --notes "TLE"    # Fail with notes
    """
    repo = require_repo()

    # Determine status from flags (mutually exclusive)
    status = None
    flag_count = sum([status_pass, status_fail, status_skip])

    if flag_count > 1:
        raise click.UsageError(
            "Cannot specify multiple status flags. Use one of --pass, --fail, or --skip."
        )

    if status_pass:
        status = "passed"
    elif status_fail:
        status = "failed"
    elif status_skip:
        status = "skipped"

    # Batch mode: no identifier, name, desc, or last → browse all problems
    if not identifier and not name_search and not desc_search and not last:
        if status is not None or manual or notes is not None:
            raise click.UsageError(
                "--pass/--fail/--skip/--manual/--notes need a problem "
                "selector (id, --name, --desc or --last)."
            )
        browse_problems(repo, repo.get_registered_problems(), per_page)
        return

    # Single-problem mode: resolve, then view / grade
    problem = resolve_problem(
        repo,
        identifier=identifier,
        name=name_search,
        desc=desc_search,
        last=last,
        command_name="grade",
        language=language,
    )
    view_and_grade_problem(
        repo,
        problem,
        status,
        notes,
        manual=manual or status is not None,
    )
