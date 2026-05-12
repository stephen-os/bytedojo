"""
Test command - Run solutions against test cases and record results.
"""

import click
from pathlib import Path
from typing import Optional

from bytedojo.commands._resolve import resolve_problem
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.services.test_service import TestRunResult
from bytedojo.services import TestService


def _display_test_header(problem: RegisteredProblem):
    """Display problem details before running tests."""
    click.echo("")
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo(click.style("  TEST PROBLEM", fg='cyan', bold=True))
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo("")
    click.echo(f"  {problem.problem_id}: {click.style(problem.title, bold=True)}")
    click.echo(f"  Language: {problem.language.value.upper()}")
    click.echo(f"  Difficulty: {problem.difficulty.value if problem.difficulty else 'Unknown'}")
    click.echo(f"  File: {problem.file_path or ''}")
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
@click.option('--version', 'version', type=int, default=None,
              help='Test a specific version (default: latest)')
@click.option('--verbose', '-v', is_flag=True, help='Show all test case results')
@click.option('--timeout', '-t', type=int, default=60, help='Timeout in seconds (default: 60)')
def test(
    identifier: Optional[str],
    name_search: Optional[str],
    desc_search: Optional[str],
    language: str | None,
    last: bool,
    version: int | None,
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
        command_name="test",
    )

    # Display problem details, then run tests via the service
    _display_test_header(problem)
    click.echo("  Running tests...")
    click.echo("")

    service = TestService()
    result = service.test_problem(repo, problem, version=version, timeout=timeout)

    # Hard failure (missing file etc.)
    if result.failed:
        raise click.ClickException(result.error)

    # Soft skip (no test cases for this problem)
    if result.skipped:
        click.echo(click.style(f"  {result.skip_reason}", fg='yellow'))
        click.echo("")
        return

    # Tests ran — display results and final recorded status
    _display_test_results(result.run_result, verbose)

    if result.run_result.all_passed:
        click.echo(click.style("  Solution recorded as PASSED", fg='green'))
    elif result.run_result.status == 'error':
        click.echo(click.style("  Solution recorded as ERROR", fg='yellow'))
    else:
        click.echo(click.style("  Solution recorded as FAILED", fg='red'))
    click.echo("")
