"""
fetch - Place bundled problems into the working tree.

Fully offline: draws from the corpus shipped inside the package and is
restricted to it — unsupported ids fail cleanly before anything is
placed.
"""

import click
from pathlib import Path

from bytedojo.commands._resolve import require_repo
from bytedojo.services import problem_service
from bytedojo.commands.ui import bold, dim
from bytedojo.commands.ui.renderers import render_fetch_results
from bytedojo.core.repository import Repository
from bytedojo.core.logger import get_logger
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.settings import SettingsManager
from bytedojo.services import FetchService


@click.command()
@click.argument("arguments", nargs=-1, required=True)
@click.option(
    "--new-attempt",
    "-na",
    is_flag=True,
    help="Add the next attempt version even if the problem is already registered",
)
@click.option(
    "--version",
    "version",
    type=int,
    default=None,
    help="Rewrite an existing tracked version in place",
)
@click.option(
    "--path",
    "custom_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Place into a custom directory (untracked, no DB entry)",
)
@click.option(
    "--python", "-py", "language", flag_value="python3", help="Fetch as Python"
)
@click.pass_obj
def fetch(
    ctx,
    arguments: tuple,
    new_attempt: bool,
    version: int | None,
    custom_path: Path | None,
    language: str | None,
):
    """
    Fetch problems from the bundled catalog.

    Modes:
      default            Register v1; refuses if already registered
      --new-attempt/-na  Add the next attempt version (v2, v3, ...)
      --version N        Rewrite an existing tracked version in place
      --path DIR         Place into a custom dir, no DB registration (scratch)

    Examples:
      dojo fetch 1                       # Register and place v1
      dojo fetch 1 --new-attempt         # Add the next attempt version
      dojo fetch 1 --version 3           # Rewrite v3 of #1 in place
      dojo fetch 1 --path ./scratch      # Untracked, drop in ./scratch
      dojo fetch 1,2,5..10               # Multiple / ranges
    """
    logger = get_logger()
    logger.debug(
        f"fetch: args={arguments} new_attempt={new_attempt} "
        f"version={version} path={custom_path} language={language}"
    )

    # Validate mutually exclusive modes
    if version is not None and custom_path is not None:
        raise click.UsageError("--version and --path are mutually exclusive")
    if new_attempt and version is not None:
        raise click.UsageError(
            "--new-attempt has no effect with --version (use --version to overwrite)"
        )
    if new_attempt and custom_path is not None:
        raise click.UsageError(
            "--new-attempt has no effect with --path (scratch mode never registers)"
        )

    # Resolve repo
    repo = require_repo()

    lang = _resolve_language(repo, language)

    # Parse problem IDs
    problem_ids = problem_service.parse_problem_ids(arguments)
    if not problem_ids:
        raise click.UsageError("No problem IDs provided")

    # Mode banner
    if custom_path is not None:
        click.echo(
            f"  Fetching {bold(str(len(problem_ids)))} problem(s) in {bold(str(lang))} "
            f"into {dim(str(custom_path))} {dim('(untracked)')}"
        )
    elif version is not None:
        click.echo(
            f"  Fetching {bold(str(len(problem_ids)))} problem(s) in {bold(str(lang))} "
            f"at {dim('v' + str(version))}"
        )
    else:
        click.echo(
            f"  Fetching {bold(str(len(problem_ids)))} problem(s) in {bold(str(lang))}"
        )

    # Fetch problems (raises UnsupportedProblemError for ids ∉ catalog)
    service = FetchService()
    batch = service.fetch_and_place_batch(
        repo,
        problem_ids,
        lang,
        new_attempt=new_attempt,
        version=version,
        custom_path=custom_path,
    )

    render_fetch_results(batch, version=version, custom_path=custom_path)
    logger.debug(
        f"fetch: complete — placed={batch.placed_count} "
        f"skipped={batch.skipped_count} failed={batch.failed_count}"
    )


def _resolve_language(repo: Repository, flag_value: str | None) -> CodeLanguage:
    """The language flag if given, else the configured default."""
    raw = flag_value or SettingsManager(repo.dojo_dir).load().default_language
    lang = CodeLanguage.from_string(raw)
    if lang is CodeLanguage.UNKNOWN:
        raise click.ClickException(f"Unknown language: {raw}")
    return lang
