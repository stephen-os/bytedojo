"""
fetch - Fetch LeetCode problems.
"""

import click
from pathlib import Path

from bytedojo.core import problem_service
from bytedojo.core.repository import Repository
from bytedojo.core.logger import get_logger

from bytedojo.core.models.code_language import CodeLanguage

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
    if language is None:
        lang = CodeLanguage.default()
    else:
        lang = CodeLanguage.from_string(language)
        if lang == CodeLanguage.UNKNOWN:
            logger.error(f"Unknown language: {language}")
            raise click.ClickException(f"Unknown language: {language}")
    logger.debug(f"fetch: resolved language={lang}")

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

    # Per-problem loop
    placed = skipped = failed = 0

    for pid in problem_ids:
        problem = problem_service.get_problem(pid)
        if problem is None:
            click.echo(f"  #{pid}: not found", err=True)
            logger.warning(f"fetch: problem #{pid} not found")
            failed += 1
            continue

        # Mode 1: scratch (no DB, custom path)
        if custom_path is not None:
            target = custom_path / problem.get_folder_name()
            repo.place_problem(problem, lang, target)
            click.echo(f"  #{pid} {problem.problem_detail.title}: placed at {target} (untracked)")
            logger.info(f"fetch: placed #{pid} ({lang}) at {target}, untracked")
            placed += 1

        # Mode 2: refetch existing tracked version
        elif version is not None:
            target = repo.attempt_path(problem, lang, version)
            if not target.exists():
                click.echo(f"  #{pid}: v{version} not found at {target}", err=True)
                logger.warning(f"fetch: #{pid} v{version} not found at {target}")
                failed += 1
                continue
            repo.place_problem(problem, lang, target)
            click.echo(f"  #{pid} {problem.problem_detail.title}: refetched v{version} at {target}")
            logger.info(f"fetch: refetched #{pid} ({lang}) v{version} at {target}")
            placed += 1

        # Mode 3: default (register new attempt, place under problems/)
        else:
            if not force and repo.is_problem_registered("leetcode", pid, lang):
                click.echo(f"  #{pid}: already registered (use --force for new attempt, "
                           f"--version N to rewrite)")
                logger.info(f"fetch: skipped #{pid} ({lang}), already registered")
                skipped += 1
                continue

            attempt = repo.register_attempt(problem, lang)
            target = repo.attempt_path(problem, lang, attempt.version)
            repo.place_problem(problem, lang, target)
            click.echo(f"  #{pid} {problem.problem_detail.title}: placed v{attempt.version} at {target}")
            logger.info(f"fetch: placed #{pid} ({lang}) v{attempt.version} at {target}")
            placed += 1

    # Summary
    click.echo("")
    click.echo(f"Done: {placed} placed, {skipped} skipped, {failed} failed")
    logger.info(f"fetch: complete — placed={placed} skipped={skipped} failed={failed}")