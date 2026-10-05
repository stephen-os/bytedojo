"""
run - Run a problem solution.
"""

import click
from typing import Optional

from bytedojo.commands._options import selectors
from bytedojo.commands._resolve import require_repo, resolve_problem
from bytedojo.commands.ui import accent, bold
from bytedojo.commands.ui.renderers import render_execution, render_run_header
from bytedojo.services import RunService


@click.command()
@click.argument("identifier", required=False)
@click.option(
    "--version",
    "version",
    type=int,
    default=None,
    help="Run a specific version (default: latest)",
)
@selectors
def run(
    identifier: Optional[str],
    name_search: Optional[str],
    desc_search: Optional[str],
    version: int | None,
    language: str | None,
    last: bool,
):
    """
    Run a problem solution.

    Executes the solution's __main__ block and prints its output.
    Each run increments the attempt's run counter.

    Examples:
      dojo run 1                    # Run problem #1
      dojo run --name "Two Sum"     # Search by name
      dojo run --last               # Run last fetched problem
    """
    repo = require_repo()

    problem = resolve_problem(
        repo,
        identifier=identifier,
        name=name_search,
        desc=desc_search,
        last=last,
        command_name="run",
        language=language,
    )

    # Quick pre-message — header comes after the service runs so it can show
    # the version-aware path.
    click.echo()
    click.echo(
        f"  Running {accent('#' + str(problem.problem_id))} {bold(problem.title)}..."
    )

    result = RunService().run_problem(repo, problem, version=version)

    render_run_header(result)
    render_execution(result.execution)
