"""
Settings command - View and modify bytedojo settings.

User preferences live in .dojo/settings.json (see core/settings.py for
the key list); this command is a thin CLI over SettingsManager.
"""

import click

from bytedojo.commands._resolve import require_repo
from bytedojo.core.logger import get_logger
from bytedojo.core.settings import SETTING_KEYS, SUPPORTED_LANGUAGES, SettingsManager
from bytedojo.commands.ui import accent, bold, success, dim, blank, hint


@click.group(invoke_without_command=True)
@click.pass_context
def settings(ctx):
    """
    View and modify bytedojo settings.

    Examples:
      dojo settings                              # Show all settings
      dojo settings list                         # Same as above
      dojo settings default-language python      # Set default language
      dojo settings review-frequency 7           # Set review frequency
      dojo settings set organize-by-language true
    """
    # If no subcommand, show all settings
    if ctx.invoked_subcommand is None:
        _show_settings()


def _show_settings():
    """Display all current settings."""
    repo = require_repo()
    current = SettingsManager(repo.dojo_dir).load()

    blank()
    click.echo(dim("  " + "─" * 50))
    click.echo(f"  {accent('ByteDojo Settings')}")
    click.echo(dim("  " + "─" * 50))
    blank()
    click.echo(f"    {dim('default-language')}      {bold(current.default_language)}")
    click.echo(
        f"    {dim('review-frequency')}      {current.review_frequency_days} days"
    )
    click.echo(
        f"    {dim('organize-by-language')}  "
        f"{'true' if current.organize_by_language else 'false'}"
    )
    blank()
    click.echo(dim("  " + "─" * 50))
    hint("dojo settings set <key> <value>")
    hint("keys: " + ", ".join(SETTING_KEYS))
    click.echo(dim("  " + "─" * 50))
    blank()


@settings.command("list")
def list_settings():
    """
    List all current settings.

    Examples:
      dojo settings list
    """
    _show_settings()


@settings.command("default-language")
@click.argument(
    "language", type=click.Choice(SUPPORTED_LANGUAGES, case_sensitive=False)
)
def default_language(language: str):
    """
    Set the default programming language.

    This sets the default language for fetch, run, test, and grade
    commands. Override per-command with the --python flag.

    Examples:
      dojo settings default-language python    # Default (Python)
    """
    _set_and_confirm("default-language", language)


@settings.command("review-frequency")
@click.argument("days")
def review_frequency(days: str):
    """
    Set the review frequency in days.

    This is the base SM-2 interval: the gap scheduled when a problem
    first passes. Default is 7 days.

    Examples:
      dojo settings review-frequency 7     # Review weekly (default)
      dojo settings review-frequency 3     # Review every 3 days
    """
    _set_and_confirm("review-frequency", days)


@settings.command()
@click.argument("key")
@click.argument("value")
def set(key: str, value: str):
    """
    Set a configuration value.

    Examples:
      dojo settings set review-frequency 14
      dojo settings set organize-by-language true
    """
    _set_and_confirm(key, value)


@settings.command()
@click.argument("key")
def get(key: str):
    """
    Get a configuration value.

    Examples:
      dojo settings get review-frequency
    """
    repo = require_repo()
    value = SettingsManager(repo.dojo_dir).get(key)
    if value is None:
        raise click.ClickException(
            f"Unknown setting: {key}. Available: {', '.join(SETTING_KEYS)}"
        )
    click.echo(f"  {dim(key)} = {bold(str(value))}")


def _set_and_confirm(key: str, value: str) -> None:
    """Shared set-validate-confirm flow for all setter subcommands."""
    logger = get_logger()
    repo = require_repo()
    manager = SettingsManager(repo.dojo_dir)
    old_value = manager.get(key)
    try:
        stored = manager.set(key, value)
    except KeyError:
        raise click.ClickException(
            f"Unknown setting: {key}. Available: {', '.join(SETTING_KEYS)}"
        )
    except ValueError as e:
        raise click.ClickException(str(e))

    click.echo(
        f"  {success('✓')}  {bold(key)} set to {bold(str(stored))}"
        f"  {dim(f'(was {old_value})')}"
    )
    logger.debug(f"settings: {key} {old_value} -> {stored}")
