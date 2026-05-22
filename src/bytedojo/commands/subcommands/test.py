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
from bytedojo.commands.ui import accent, bold, success, warn, error, dim, problem_line


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

    click.echo()
    click.echo(dim("  " + "─" * 70))
    click.echo(
        f"  {problem_line(problem.problem_id, problem.title, problem.difficulty.value, problem.language.value)}"
        f"  {dim(version_label)}"
    )
    click.echo(f"  {dim(file_path)}")
    click.echo()


def _display_test_results(result: TestRunResult, verbose: bool = False):
    """Display test execution results."""
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent('Results')}")
    click.echo(dim("  " + "─" * 70))
    click.echo()

    # Check for compile/runtime errors first
    if result.compile_error:
        click.echo(f"  {error('COMPILE ERROR')}")
        click.echo()
        click.echo(result.compile_error)
        click.echo()
        return

    if result.runtime_error and not result.case_results:
        click.echo(f"  {error('ERROR')}")
        click.echo(f"  {result.runtime_error}")
        click.echo()
        return

    # Display summary
    if result.all_passed:
        click.echo(success(
            f"  ALL TESTS PASSED ({result.passed_count}/{result.runnable_count})"
        ))
    else:
        passed_str = success(str(result.passed_count))
        failed_str = error(str(result.failed_count))
        error_str = warn(str(result.error_count))
        skipped_part = ""
        if result.skipped_count:
            skipped_str = dim(str(result.skipped_count))
            skipped_part = f"  Skipped: {skipped_str}"
        click.echo(
            f"  Passed: {passed_str}  Failed: {failed_str}  Error: {error_str}"
            f"{skipped_part}  {dim(f'(Total: {result.total_cases})')}"
        )
    if result.skipped_count:
        click.echo(dim(
            f"  ({result.skipped_count} case(s) skipped — values outside int32 range)"
        ))

    click.echo()

    # Show failed/error cases (or all if verbose)
    failed_cases = [c for c in result.case_results if not c.passed]

    if failed_cases:
        click.echo(f"  {error('Failed Test Cases:')}")
        click.echo(dim("  " + "─" * 70))

        # Limit displayed failures unless verbose
        display_cases = failed_cases if verbose else failed_cases[:5]

        for case in display_cases:
            click.echo()
            click.echo(f"  {accent('Case #' + str(case.case_number))}")
            click.echo(f"    {dim('Input')}     {_truncate(case.input_str, 60)}")
            click.echo(f"    {dim('Expected')}  {success(_truncate(case.expected, 50))}")
            if case.error:
                click.echo(f"    {dim('Error')}     {warn(_truncate(case.error, 50))}")
            elif case.timed_out:
                click.echo(f"    {dim('Actual')}    {error('TIMEOUT')}")
            else:
                click.echo(f"    {dim('Actual')}    {error(_truncate(case.actual, 50))}")

        if len(failed_cases) > 5 and not verbose:
            click.echo()
            click.echo(f"  {dim(f'... and {len(failed_cases) - 5} more failures')}")
            click.echo(f"  {dim('Use --verbose to see all failures')}")

    click.echo()

    # Show passed cases if verbose
    if verbose:
        passed_cases = [c for c in result.case_results if c.passed]
        if passed_cases:
            click.echo(f"  {success('Passed Test Cases:')}")
            click.echo(dim("  " + "─" * 70))
            for case in passed_cases:
                click.echo(f"  Case #{case.case_number}: {_truncate(case.input_str, 50)}")
            click.echo()


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
    repo = Repository.find(Path.cwd())
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
    click.echo()
    click.echo(f"  Testing {accent('#' + str(problem.problem_id))} {bold(problem.title)}...")

    service = TestService()
    result = service.test_problem(repo, problem, version=version, timeout=timeout)

    # Header (now with the resolved version + file path from the service)
    _display_test_header(result)

    # Hard failure (missing file, missing toolchain, language not supported)
    if result.failed:
        raise click.ClickException(result.error)

    # Soft skip (no test cases for this problem)
    if result.skipped:
        click.echo(warn(f"  {result.skip_reason}"))
        click.echo()
        return

    # Tests ran — display results and final recorded status
    _display_test_results(result.run_result, verbose)

    status = result.run_result.status
    if status == 'passed':
        click.echo(success("  ✓ Solution recorded as PASSED"))
    elif status == 'error':
        click.echo(warn("  Solution recorded as ERROR"))
    elif status == 'failed':
        click.echo(error("  ✗ Solution recorded as FAILED"))
    else:  # ungraded — ran a subset, all passed, but some were skipped
        click.echo(warn("  Solution recorded as UNGRADED"))
    click.echo()
