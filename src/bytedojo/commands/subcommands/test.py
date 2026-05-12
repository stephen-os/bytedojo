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
from bytedojo.services.test_service import TestRunResult, TestServiceResult
from bytedojo.services import TestService


def _display_test_header(result: TestServiceResult):
    """
    Display problem details after the service ran.

    Pulls file path and version from the service result so the header shows
    what was *actually* tested (i.e. respects --version N) instead of the
    latest path baked into the RegisteredProblem from the lookup.
    """
    problem = result.problem
    file_path = str(result.file_path) if result.file_path else (problem.file_path or "")
    version_label = f"v{result.version}" if result.version is not None else "?"

    click.echo("")
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo(click.style("  TEST PROBLEM", fg='cyan', bold=True))
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo("")
    click.echo(f"  {problem.problem_id}: {click.style(problem.title, bold=True)}")
    click.echo(f"  Language: {problem.language.value.upper()}")
    click.echo(f"  Difficulty: {problem.difficulty.value if problem.difficulty else 'Unknown'}")
    click.echo(f"  Version:  {version_label}")
    click.echo(f"  File:     {file_path}")
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
        click.echo(click.style(
            f"  ALL TESTS PASSED ({result.passed_count}/{result.runnable_count})",
            fg='green', bold=True,
        ))
    else:
        passed_str = click.style(str(result.passed_count), fg='green')
        failed_str = click.style(str(result.failed_count), fg='red')
        error_str = click.style(str(result.error_count), fg='yellow')
        skipped_part = ""
        if result.skipped_count:
            skipped_str = click.style(str(result.skipped_count), fg='bright_black')
            skipped_part = f"  Skipped: {skipped_str}"
        click.echo(
            f"  Passed: {passed_str}  Failed: {failed_str}  Error: {error_str}"
            f"{skipped_part}  (Total: {result.total_cases})"
        )
    if result.skipped_count:
        click.echo(click.style(
            f"  ({result.skipped_count} case(s) skipped — values outside int32 range)",
            fg='bright_black',
        ))

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

    # Quick pre-message — header comes after the service runs so it can show
    # the version-aware path. Without it the user would wait silently.
    click.echo("")
    click.echo(f"  Testing #{problem.problem_id} {problem.title}...")

    service = TestService()
    result = service.test_problem(repo, problem, version=version, timeout=timeout)

    # Header (now with the resolved version + file path from the service)
    _display_test_header(result)

    # Hard failure (missing file, missing toolchain, language not supported)
    if result.failed:
        raise click.ClickException(result.error)

    # Soft skip (no test cases for this problem)
    if result.skipped:
        click.echo(click.style(f"  {result.skip_reason}", fg='yellow'))
        click.echo("")
        return

    # Tests ran — display results and final recorded status
    _display_test_results(result.run_result, verbose)

    status = result.run_result.status
    if status == 'passed':
        click.echo(click.style("  Solution recorded as PASSED", fg='green'))
    elif status == 'error':
        click.echo(click.style("  Solution recorded as ERROR", fg='yellow'))
    elif status == 'failed':
        click.echo(click.style("  Solution recorded as FAILED", fg='red'))
    else:  # untested — ran a subset, all passed, but some were skipped
        click.echo(click.style("  Solution recorded as UNTESTED", fg='yellow'))
    click.echo("")
