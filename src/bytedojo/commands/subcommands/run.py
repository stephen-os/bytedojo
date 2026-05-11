"""
Run command - Execute problem solutions for testing.
"""

import click
from pathlib import Path
from typing import Optional

from bytedojo.core.database import DatabaseManager
from bytedojo.core.execution import ProblemExecutor, ExecutionResult
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.repository import Repository
from bytedojo.core.search import find_problems, select_problem


def _display_run_header(problem: dict):
    """Display problem details before running."""
    problem_id = problem['problem_id']
    title = problem['title']
    language = problem.get('language', 'python')
    file_path = problem.get('file_path', '')

    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo(click.style("  RUN PROBLEM", fg='cyan', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")
    click.echo(f"  {problem_id}: {click.style(title, bold=True)}")
    click.echo(f"  Language: {language.upper()}")
    click.echo(f"  File: {file_path}")
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

@click.command()
@click.argument('identifier', required=False)
@click.option('--name', '-n', 'name_search', help='Search by problem name')
@click.option('--desc', '-d', 'desc_search', help='Search by description keywords')
@click.option('--python', '-py', 'language', flag_value='python3', help='Run Python version')
@click.option('--java', 'language', flag_value='java', help='Run Java version')
@click.option('--cpp', 'language', flag_value='cpp', help='Run C++ version')
@click.option('--last', is_flag=True, help='Run most recently fetched problem')
def run(identifier: Optional[str], name_search: Optional[str], desc_search: Optional[str], language: str | None, last: bool):
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

    with DatabaseManager(repo.db_path) as db:
        # Handle --last flag
        if last:
            problems = db.list_problems(language=language, limit=1)
            if not problems:
                raise click.ClickException(
                    f"No {language} problems found. "
                    f"Fetch one first with: dojo fetch <id> --{language}"
                )
            problem_data = problems[0]
        else:
            # Require either identifier, name, or desc
            if not identifier and not name_search and not desc_search:
                raise click.ClickException(
                    "Please specify a problem ID, --name, --desc, or --last\n"
                    "Examples:\n"
                    "  dojo run 1\n"
                    "  dojo run --name 'Two Sum'\n"
                    "  dojo run --last"
                )

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

    # Display header and execute
    _display_run_header(problem_data)

    try:
        executor = ProblemExecutor(repo)
        result = executor.execute(problem_data)
        _display_execution_result(result)
    except ValueError as e:
        raise click.ClickException(str(e))
