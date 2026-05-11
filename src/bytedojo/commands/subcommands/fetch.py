"""
fetch - Fetch LeetCode problems.
"""

import click
from pathlib import Path

from bytedojo.core import problem_service
from bytedojo.core.repository import Repository
from bytedojo.core.logger import get_logger
from bytedojo.core.models.code_language import CodeLanguage, resolve as resolve_language
from bytedojo.services import FetchService

# Define fetch command
@click.command()

# Arguments

# Problem IDs
@click.argument('arguments', nargs=-1, required=True)

# Options

# Force new attempt
@click.option('--force', is_flag=True,
              help='Create a new attempt even if the problem is already registered')

# Refetch tracked version
@click.option('--version', 'version', type=int, default=None,
              help='Refetch an existing tracked version (rewrites that version in place)')

# Custom path (scratch)
@click.option('--path', 'custom_path', type=click.Path(path_type=Path), default=None,
              help='Place into a custom directory (untracked, no DB entry)')

# Language flags (mutually exclusive)
@click.option('--python', '-py', 'language', flag_value='python3', help='Fetch as Python')
@click.option('--java', 'language', flag_value='java', help='Fetch as Java')
@click.option('--cpp', 'language', flag_value='cpp', help='Fetch as C++')

@click.pass_obj
def fetch(ctx, arguments: tuple, force: bool, version: int | None,
          custom_path: Path | None, language: str | None):
    """
    Fetch LeetCode problems.

    Modes:
      default            Register a new attempt and place under problems/.../v{N}/
      --version N        Rewrite an existing tracked version in place
      --path DIR         Place into a custom dir, no DB registration (scratch mode)

    Examples:
      dojo fetch 1                       # New attempt (next version)
      dojo fetch 1 --force               # Force a new attempt even if registered
      dojo fetch 1 --version 3           # Rewrite v3 of #1 in place
      dojo fetch 1 --path ./scratch      # Untracked, drop in ./scratch
      dojo fetch 1,2,5..10 --java        # Multiple, Java
    """
    logger = get_logger()
    logger.debug(f"fetch: args={arguments} force={force} version={version} "
                 f"path={custom_path} language={language}")

    # Validate mutually exclusive modes
    if version is not None and custom_path is not None:
        raise click.ClickException("--version and --path are mutually exclusive")
    if force and version is not None:
        raise click.ClickException("--force has no effect with --version (use --version to overwrite)")
    if force and custom_path is not None:
        raise click.ClickException("--force has no effect with --path (scratch mode never registers)")

    # Resolve language
    lang = resolve_language(language)
    if lang == CodeLanguage.UNKNOWN:
        raise click.ClickException(f"Unknown language: {language}")

    # Resolve repo
    repo = Repository.open(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    # Parse problem IDs
    problem_ids = problem_service.parse_problem_ids(arguments)
    if not problem_ids:
        raise click.ClickException("No problem IDs provided")

    # Mode banner
    if custom_path is not None:
        click.echo(f"Fetching {len(problem_ids)} problem(s) in {lang} into {custom_path} (untracked)")
    elif version is not None:
        click.echo(f"Refetching {len(problem_ids)} problem(s) in {lang} at v{version}")
    else:
        click.echo(f"Fetching {len(problem_ids)} problem(s) in {lang}")

    # Fetch problems
    service = FetchService()
    batch = service.fetch_and_place_batch(
        repo,
        problem_ids,
        lang,
        force=force,
        version=version,
        custom_path=custom_path,
    )

    # Display results
    for result in batch.results:
        if result.success:
            if custom_path is not None:
                click.echo(f"  #{result.problem_id} {result.title}: placed at {result.target_path} (untracked)")
            elif version is not None:
                click.echo(f"  #{result.problem_id} {result.title}: refetched v{version} at {result.target_path}")
            else:
                click.echo(f"  #{result.problem_id} {result.title}: placed v{result.version} at {result.target_path}")
        elif result.skipped:
            if result.skip_reason == "already registered":
                click.echo(f"  #{result.problem_id}: already registered (use --force for new attempt, "
                           f"--version N to rewrite)")
            else:
                click.echo(f"  #{result.problem_id}: {result.skip_reason}", err=True)
        elif result.failed:
            click.echo(f"  #{result.problem_id}: {result.error}", err=True)

    # Summary
    click.echo("")
    click.echo(f"Done: {batch.placed_count} placed, {batch.skipped_count} skipped, {batch.failed_count} failed")
    logger.info(f"fetch: complete — placed={batch.placed_count} skipped={batch.skipped_count} failed={batch.failed_count}")