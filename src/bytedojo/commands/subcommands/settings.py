"""
Settings command - View and modify bytedojo settings.
"""

import click
from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.settings import SettingsManager
from bytedojo.core.database import Database
from bytedojo.core.repository import Repository
from bytedojo.commands.ui import accent, bold, success, error, dim, blank, kv, hint


# Languages supported by CLI (user-facing names)
SUPPORTED_LANGUAGES = ['python', 'java', 'cpp']


@click.group(invoke_without_command=True)
@click.pass_context
def settings(ctx):
    """
    View and modify bytedojo settings.

    Examples:
      dojo settings                              # Show all settings
      dojo settings list                         # Same as above
      dojo settings default-language cpp         # Set default language
      dojo settings review-frequency 7           # Set review frequency
    """
    # If no subcommand, show all settings
    if ctx.invoked_subcommand is None:
        _show_settings()


def _show_settings():
    """Display all current settings."""
    repo = Repository.find(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    # Load and display settings
    settings_manager = SettingsManager(repo.dojo_dir)
    current_settings = settings_manager.load()

    # Get database config
    with Database(repo.db_path) as db:
        review_freq = db.get_config('review_frequency_days', '7')
        default_lang = db.get_config('default_language', 'python')
        default_source = db.get_config('default_source', 'leetcode')

    blank()
    click.echo(dim("  " + "─" * 50))
    click.echo(f"  {accent('ByteDojo Settings')}")
    click.echo(dim("  " + "─" * 50))
    blank()
    click.echo(f"  {dim('defaults')}")
    click.echo(f"    {dim('language')}     {bold(default_lang)}")
    click.echo(f"    {dim('source')}       {default_source}")
    blank()
    click.echo(f"  {dim('review')}")
    click.echo(f"    {dim('frequency')}    {review_freq} days")
    blank()
    click.echo(f"  {dim('leetcode')}")
    click.echo(f"    {dim('organization')} {current_settings.leetcode.organization}")
    blank()
    click.echo(dim("  " + "─" * 50))
    hint("dojo settings default-language <python|java|cpp>")
    hint("dojo settings review-frequency <days>")
    click.echo(dim("  " + "─" * 50))
    blank()


@settings.command('list')
def list_settings():
    """
    List all current settings.

    Examples:
      dojo settings list
    """
    _show_settings()


@settings.command('default-language')
@click.argument('language', type=click.Choice(SUPPORTED_LANGUAGES, case_sensitive=False))
def default_language(language: str):
    """
    Set the default programming language.

    This sets the default language for fetch, run, and grade commands.
    You can still override with --python, --java, or --cpp flags.

    Examples:
      dojo settings default-language python    # Default (Python)
      dojo settings default-language java      # Use Java by default
      dojo settings default-language cpp       # Use C++ by default
    """
    logger = get_logger()
    repo = Repository.find(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    with Database(repo.db_path) as db:
        old_value = db.get_config('default_language', 'python')
        new_value = language.lower()
        db.set_config('default_language', new_value)

        click.echo(f"  {success('✓')}  Default language set to {bold(new_value)}")
        logger.debug(f"settings: default_language {old_value} -> {new_value}")


@settings.command()
@click.argument('key')
@click.argument('value')
def set(key: str, value: str):
    """
    Set a configuration value.

    Examples:
      dojo settings set leetcode.organization flat
      dojo settings set leetcode.organization difficulty
    """
    repo = Repository.find(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    # Validate known settings
    valid_settings = {
        "leetcode.organization": ["flat", "difficulty"]
    }

    if key not in valid_settings:
        click.echo()
        click.echo(f"  {error('Unknown setting:')} {bold(key)}")
        click.echo(f"  {dim('Available settings:')}")
        for setting_key, valid_values in valid_settings.items():
            click.echo(f"    {dim(setting_key)}  {', '.join(valid_values)}")
        raise click.ClickException(f"Unknown setting: {key}")

    if value not in valid_settings[key]:
        click.echo(f"  {error('Invalid value')} {bold(repr(value))} {dim('for')} {bold(key)}")
        click.echo(f"  {dim('Valid values:')} {', '.join(valid_settings[key])}")
        raise click.ClickException(f"Invalid value: {value}")

    # Set the value
    settings_manager = SettingsManager(repo.dojo_dir)
    if settings_manager.set(key, value):
        click.echo(f"  {success('✓')}  {bold(key)} set to {bold(value)}")
    else:
        raise click.ClickException(f"Failed to set {key}")


@settings.command()
@click.argument('key')
def get(key: str):
    """
    Get a configuration value.

    Examples:
      dojo settings get leetcode.organization
    """
    repo = Repository.find(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    # Get the value
    settings_manager = SettingsManager(repo.dojo_dir)
    value = settings_manager.get(key)

    if value is None:
        raise click.ClickException(f"Unknown setting: {key}")

    click.echo(f"  {dim(key)} = {bold(value)}")


@settings.command('review-frequency')
@click.argument('days', type=int)
def review_frequency(days: int):
    """
    Set the review frequency in days.

    This controls how often problems are scheduled for review after passing tests.
    Default is 7 days.

    Examples:
      dojo settings review-frequency 7     # Review weekly (default)
      dojo settings review-frequency 3     # Review every 3 days
      dojo settings review-frequency 14    # Review bi-weekly
    """
    if days < 1:
        raise click.ClickException("Review frequency must be at least 1 day")

    if days > 365:
        raise click.ClickException("Review frequency cannot exceed 365 days")

    repo = Repository.find(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    with Database(repo.db_path) as db:
        old_value = db.get_config('review_frequency_days', '7')
        db.set_config('review_frequency_days', str(days))

        click.echo(f"  {success('✓')}  Review frequency set to {bold(str(days))} days  {dim(f'(was {old_value})')}")
