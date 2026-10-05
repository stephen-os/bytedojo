"""
Test command - Run solutions against test cases and record results.
"""

import click
from typing import Optional

from bytedojo.commands._options import selectors
from bytedojo.commands._resolve import require_repo, resolve_problem
from bytedojo.commands.ui import accent, bold, warn
from bytedojo.commands.ui.renderers import (
    render_test_header,
    render_test_outcome,
    render_test_results,
)
from bytedojo.services import TestService


@click.command()
@click.argument("identifier", required=False)
@click.option(
    "--version",
    "version",
    type=int,
    default=None,
    help="Test a specific version (default: latest)",
)
@click.option("--verbose", "-v", is_flag=True, help="Show all test case results")
@click.option(
    "--timeout", "-t", type=int, default=60, help="Timeout in seconds (default: 60)"
)
@selectors
def test(
    identifier: Optional[str],
    name_search: Optional[str],
    desc_search: Optional[str],
    language: str | None,
    last: bool,
    version: int | None,
    verbose: bool,
    timeout: int,
):
    """
    Run tests against a problem solution.

    Executes the solution against the bundled test cases and records
    the outcome. Testing is the primary loop: a pass schedules (or
    advances) the problem's spaced-repetition review, a fail lapses it.

    Examples:
      dojo test 1                    # Test problem #1
      dojo test 1 --verbose          # Show all test case results
      dojo test --name "Two Sum"     # Search by name
      dojo test --last               # Test last fetched problem
    """
    repo = require_repo()

    problem = resolve_problem(
        repo,
        identifier=identifier,
        name=name_search,
        desc=desc_search,
        last=last,
        command_name="test",
        language=language,
    )

    # Quick pre-message — header comes after the service runs so it can show
    # the version-aware path. Without it the user would wait silently.
    click.echo()
    click.echo(
        f"  Testing {accent('#' + str(problem.problem_id))} {bold(problem.title)}..."
    )

    result = TestService().test_problem(repo, problem, version=version, timeout=timeout)

    render_test_header(result)

    # Soft skip (no test cases for this problem)
    if result.skipped:
        click.echo(warn(f"  {result.skip_reason}"))
        click.echo()
        return

    render_test_results(result.run_result, verbose)
    render_test_outcome(result)
