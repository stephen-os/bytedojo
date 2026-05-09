"""
Test command - Run solutions against test cases and record results.
"""

import click
from pathlib import Path
from typing import Optional

from bytedojo.core.database import DatabaseManager
from bytedojo.core.search import find_problems, select_problem
from bytedojo.core.test_runner import run_tests, TestRunResult
from bytedojo.commands.subcommands.utils import (
    get_initialized_repo,
    get_default_language,
    LANGUAGE_COLORS,
    DIFFICULTY_COLORS,
    STATUS_COLORS,
)


def _display_test_header(problem: dict, total_cases: int):
    """Display problem details before running tests."""
    problem_id = problem['problem_id']
    title = problem['title']
    language = problem.get('language', 'python')
    difficulty = problem.get('difficulty') or 'Unknown'
    file_path = problem.get('file_path', '')

    click.echo("")
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo(click.style("  TEST PROBLEM", fg='cyan', bold=True))
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo("")
    click.echo(f"  {problem_id}: {click.style(title, bold=True)}")
    click.echo(f"  Language: {click.style(language.upper(), fg=LANGUAGE_COLORS.get(language, 'white'))}")
    click.echo(f"  Difficulty: {click.style(difficulty, fg=DIFFICULTY_COLORS.get(difficulty, 'white'))}")
    click.echo(f"  File: {file_path}")
    click.echo(f"  Test Cases: {total_cases}")
    click.echo("")


def _display_test_results(result: TestRunResult, verbose: bool = False):
    """Display test execution results."""
    click.echo(click.style("-" * 70, fg='bright_black'))
    click.echo(click.style("  RESULTS", fg='cyan'))
    click.echo(click.style("-" * 70, fg='bright_black'))
    click.echo("")

    # Check for compile/runtime errors first
    if result.compile_error:
        click.echo(click.style("  COMPILE ERROR", fg='red', bold=True))
        click.echo("")
        click.echo(result.compile_error)
        click.echo("")
        return

    if result.runtime_error and not result.case_results:
        click.echo(click.style("  ERROR", fg='red', bold=True))
        click.echo(f"  {result.runtime_error}")
        click.echo("")
        return

    # Display summary
    if result.all_passed:
        click.echo(click.style(f"  ALL TESTS PASSED ({result.passed_count}/{result.total_cases})", fg='green', bold=True))
    else:
        passed_str = click.style(str(result.passed_count), fg='green')
        failed_str = click.style(str(result.failed_count), fg='red')
        error_str = click.style(str(result.error_count), fg='yellow')
        click.echo(f"  Passed: {passed_str}  Failed: {failed_str}  Error: {error_str}  (Total: {result.total_cases})")

    click.echo("")

    # Show failed/error cases (or all if verbose)
    failed_cases = [c for c in result.case_results if not c.passed]

    if failed_cases:
        click.echo(click.style("  Failed Test Cases:", fg='red'))
        click.echo(click.style("-" * 70, fg='bright_black'))

        # Limit displayed failures unless verbose
        display_cases = failed_cases if verbose else failed_cases[:5]

        for case in display_cases:
            click.echo("")
            click.echo(f"  Case #{case.case_number}:")
            click.echo(f"    Input:    {_truncate(case.input_str, 60)}")
            click.echo(f"    Expected: {click.style(_truncate(case.expected, 50), fg='green')}")
            if case.error:
                click.echo(f"    Error:    {click.style(_truncate(case.error, 50), fg='yellow')}")
            elif case.timed_out:
                click.echo(f"    Actual:   {click.style('TIMEOUT', fg='red')}")
            else:
                click.echo(f"    Actual:   {click.style(_truncate(case.actual, 50), fg='red')}")

        if len(failed_cases) > 5 and not verbose:
            click.echo("")
            click.echo(f"  ... and {len(failed_cases) - 5} more failures")
            click.echo("  Use --verbose to see all failures")

    click.echo("")

    # Show passed cases if verbose
    if verbose:
        passed_cases = [c for c in result.case_results if c.passed]
        if passed_cases:
            click.echo(click.style("  Passed Test Cases:", fg='green'))
            click.echo(click.style("-" * 70, fg='bright_black'))
            for case in passed_cases:
                click.echo(f"  Case #{case.case_number}: {_truncate(case.input_str, 50)}")
            click.echo("")


def _truncate(s: str, max_len: int) -> str:
    """Truncate string with ellipsis if too long."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


# ============================================================================
# CLI COMMANDS
# ============================================================================

@click.command()
@click.argument('identifier', required=False)
@click.option('--name', '-n', 'name_search', help='Search by problem name')
@click.option('--desc', '-d', 'desc_search', help='Search by description keywords')
@click.option('--python', '-py', 'language', flag_value='python3', help='Test Python version')
@click.option('--java', 'language', flag_value='java', help='Test Java version')
@click.option('--cpp', 'language', flag_value='cpp', help='Test C++ version')
@click.option('--last', is_flag=True, help='Test most recently fetched problem')
@click.option('--verbose', '-v', is_flag=True, help='Show all test case results')
@click.option('--timeout', '-t', type=int, default=60, help='Timeout in seconds (default: 60)')
def test(
    identifier: Optional[str],
    name_search: Optional[str],
    desc_search: Optional[str],
    language: str | None,
    last: bool,
    verbose: bool,
    timeout: int
):
    """
    Run tests against a problem solution.

    Executes the solution against all available test cases and shows results.
    Results are recorded in the database.

    Uses configured default language (see: dojo settings default-language).

    Examples:
      dojo test 1                    # Test problem #1
      dojo test 1 --verbose          # Show all test case results
      dojo test --name "Two Sum"     # Search by name
      dojo test --last               # Test last fetched problem
    """
    repo = get_initialized_repo()

    # Use configured default if no language flag specified
    if language is None:
        language = get_default_language()

    with DatabaseManager(repo.db_path) as db:
        # Handle --last flag
        if last:
            problems = db.list_problems(language=language, limit=1)
            if not problems:
                raise click.ClickException(
                    f"No {language} problems found. "
                    f"Fetch one first with: dojo fetch <id> --{language if language != 'python3' else 'python'}"
                )
            problem_data = problems[0]
        else:
            # Require either identifier, name, or desc
            if not identifier and not name_search and not desc_search:
                raise click.ClickException(
                    "Please specify a problem ID, --name, --desc, or --last\n"
                    "Examples:\n"
                    "  dojo test 1\n"
                    "  dojo test --name 'Two Sum'\n"
                    "  dojo test --last"
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
                    f"Fetch one first with: dojo fetch <id>"
                )

            # Select problem (interactive if multiple)
            problem_data = select_problem(matches)
            if not problem_data:
                raise click.Abort()

        # Get file path
        file_path_str = problem_data.get('file_path')
        if not file_path_str:
            raise click.ClickException("Problem has no associated file path")

        file_path = Path(file_path_str)
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path

        if not file_path.exists():
            raise click.ClickException(f"Solution file not found: {file_path}")

        # Get problem ID as int
        problem_id_str = problem_data['problem_id']
        try:
            problem_id = int(problem_id_str)
        except ValueError:
            raise click.ClickException(f"Invalid problem ID: {problem_id_str}")

        # Import here to avoid circular imports
        from bytedojo.core.test_fetcher import fetch_test_cases
        test_cases = fetch_test_cases(problem_id)

        # Display header
        _display_test_header(problem_data, len(test_cases))

        if not test_cases:
            click.echo(click.style("  No test cases available for this problem.", fg='yellow'))
            click.echo("")
            return

        # Run tests
        click.echo("  Running tests...")
        click.echo("")

        result = run_tests(
            solution_path=file_path,
            problem_id=problem_id,
            language=language,
            timeout=timeout
        )

        # Display results
        _display_test_results(result, verbose)

        # Update database with test status
        problem_db_id = problem_data['id']
        db.update_test_status(
            problem_db_id=problem_db_id,
            status=result.status,
            output=f"Passed: {result.passed_count}/{result.total_cases}"
        )

        # Show final status
        if result.all_passed:
            click.echo(click.style("  Solution recorded as PASSED", fg='green'))
        elif result.status == 'error':
            click.echo(click.style("  Solution recorded as ERROR", fg='yellow'))
        else:
            click.echo(click.style("  Solution recorded as FAILED", fg='red'))
        click.echo("")
