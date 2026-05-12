"""
run - Run a problem solution.
"""

import click
from pathlib import Path
from typing import Optional

from bytedojo.commands._resolve import resolve_problem
from bytedojo.core.toolchains import ExecutionResult
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.services import RunService
from bytedojo.services.run_service import RunServiceResult


def _display_run_header(result: RunServiceResult):
    """
    Display problem details after the service ran.

    Pulls file path and version from the service result so the header shows
    what was *actually* run (i.e. respects --version N) instead of the
    latest path baked into the RegisteredProblem from the lookup.
    """
    problem = result.problem
    file_path = str(result.file_path) if result.file_path else (problem.file_path or "")
    version_label = f"v{result.version}" if result.version is not None else "?"

    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo(click.style("  RUN PROBLEM", fg='cyan', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")
    click.echo(f"  {problem.problem_id}: {click.style(problem.title, bold=True)}")
    click.echo(f"  Language: {problem.language.value.upper()}")
    click.echo(f"  Version:  {version_label}")
    click.echo(f"  File:     {file_path}")
    click.echo("")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo(click.style("  OUTPUT", fg='cyan'))
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo("")


def _display_execution_result(result: ExecutionResult):
    """Display execution output and result."""
    # Show compilation error if applicable
    if result.compile_error:
        click.echo(click.style("Compilation failed:", fg='red', bold=True))
        click.echo(result.compile_error)
        return

    # Show stdout if any
    if result.stdout:
        click.echo(result.stdout, nl=False)
        if not result.stdout.endswith('\n'):
            click.echo("")

    # Show stderr if any (and not a timeout message already shown)
    if result.stderr and not result.timed_out:
        click.echo(click.style(result.stderr, fg='yellow'), nl=False)
        if not result.stderr.endswith('\n'):
            click.echo("")

    # Show timeout message
    if result.timed_out:
        click.echo(click.style(result.stderr, fg='red'))

    # Show final status
    click.echo("")
    if result.exit_code == 0:
        click.echo(click.style("  Execution completed successfully", fg='green'))
    else:
        click.echo(click.style(f"  Execution failed (exit code: {result.exit_code})", fg='red'))


# ============================================================================
# CLI COMMANDS
# ============================================================================

# Define run command
@click.command()

# Arguments

# Problem identifier (ID or omit when using --name / --desc / --last)
@click.argument('identifier', required=False)

# Options

# Name search
@click.option('--name', '-n', 'name_search', help='Search by problem name')

# Description search
@click.option('--desc', '-d', 'desc_search', help='Search by description keywords')

# Run a specific version (default: latest)
@click.option('--version', 'version', type=int, default=None,
              help='Run a specific version (default: latest)')

# Language flags (mutually exclusive)
@click.option('--python', '-py', 'language', flag_value='python3', help='Run Python version')
@click.option('--java', 'language', flag_value='java', help='Run Java version')
@click.option('--cpp', 'language', flag_value='cpp', help='Run C++ version')

# Run most recently fetched
@click.option('--last', is_flag=True, help='Run most recently fetched problem')

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

    Uses configured default language (see: dojo settings default-language).

    Examples:
      dojo run 1                    # Run problem #1 (uses default language)
      dojo run 1 --java             # Run Java version
      dojo run 1 --cpp              # Run C++ version
      dojo run --name "Two Sum"     # Search by name
      dojo run --last               # Run last fetched problem
    """
    repo = Repository.open(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    # Use configured default if no language flag specified
    if language is None:
        language = CodeLanguage.default().value

    # Resolve the problem (handles --last, lookup, and disambiguation)
    problem = resolve_problem(
        repo, language,
        identifier=identifier, name=name_search, desc=desc_search, last=last,
        command_name="run",
    )

    # Quick pre-message — header comes after the service runs so it can show
    # the version-aware path.
    click.echo("")
    click.echo(f"  Running #{problem.problem_id} {problem.title}...")

    service = RunService()
    result = service.run_problem(repo, problem, version=version)

    # Header (now with the resolved version + file path from the service)
    _display_run_header(result)

    # Hard failure (missing file, missing toolchain, etc.)
    if result.failed:
        raise click.ClickException(result.error)

    # Execution finished — display output and status
    _display_execution_result(result.execution)
