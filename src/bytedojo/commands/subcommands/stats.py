"""
stats - View statistics about problems in the repository.
"""

import click
from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.repository import Repository


# Define stats command
@click.command()

# Options
@click.option('--list', 'list_problems', is_flag=True, help='List all problems')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information including attempts')
@click.option('--source', type=str, help='Filter by source (e.g., leetcode)')
@click.option('--difficulty', '-d',
              type=click.Choice(['easy', 'medium', 'hard'], case_sensitive=False),
              help='Filter by difficulty')

@click.pass_obj
def stats(ctx, list_problems: bool, verbose: bool, source: str | None, difficulty: str | None):
    """
    View statistics about problems in the repository.

    Examples:
      dojo stats                          # Show summary
      dojo stats --list                   # List all problems
      dojo stats --list --verbose         # List with details
      dojo stats --list -d easy           # List easy problems
    """
    logger = get_logger()
    logger.debug(f"stats: list_problems={list_problems} verbose={verbose} "
                 f"source={source} difficulty={difficulty}")

    # Resolve repo
    repo = Repository.find(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    with repo.open_db() as db:
        if list_problems:
            _list_problems(db, verbose, source, difficulty)
        else:
            _show_summary(db)

    logger.debug("stats: complete")


def _show_summary(db):
    """Show summary statistics."""
    stats = db.get_summary_stats()

    click.echo("Repository Statistics")
    click.echo("")
    click.echo(f"Total problems: {stats.total_problems}")

    if stats.by_difficulty:
        click.echo("")
        click.echo("By difficulty:")
        for diff, count in sorted(stats.by_difficulty.items()):
            click.echo(f"  {diff:10s}: {count}")

    if stats.by_source:
        click.echo("")
        click.echo("By source:")
        for src, count in sorted(stats.by_source.items()):
            click.echo(f"  {src:10s}: {count}")


def _list_problems(db, verbose: bool, source: str | None, difficulty: str | None):
    """List problems with optional verbosity."""
    problems = db.list_problems(source=source, difficulty=difficulty)

    if not problems:
        click.echo("No problems found matching criteria.")
        return

    click.echo(f"Found {len(problems)} problem(s)")
    click.echo("")

    for problem in problems:
        _print_problem(problem, verbose)
        click.echo("")


def _print_problem(problem, verbose: bool):
    """Print a single problem (RegisteredProblem)."""
    # Basic info
    click.echo(f"#{problem.problem_id} {problem.title}")
    click.echo(f"  source: {problem.source}")
    click.echo(f"  difficulty: {problem.difficulty.value if problem.difficulty else 'Unknown'}")
    click.echo(f"  language: {problem.language.value if problem.language else 'unknown'}")
    click.echo(f"  fetched: {problem.fetched_at}")

    if problem.file_path:
        click.echo(f"  file: {problem.file_path}")

    # Verbose attempt stats are temporarily unavailable — the old
    # db.get_problem_stats() was removed during the dict→model refactor.
    # AttemptService.get_stats() exposes per-language stats and is the
    # right path to rebuild this on.
    if verbose:
        click.echo("  attempts: (verbose stats temporarily unavailable)")