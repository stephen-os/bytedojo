"""
Settings command - View and modify bytedojo settings.
"""

import click

from bytedojo.core.logger import get_logger
from bytedojo.core.settings import SettingsManager
from bytedojo.core.database import DatabaseManager
from bytedojo.commands.utils import get_initialized_repo, SUPPORTED_LANGUAGES


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
    logger = get_logger()
    repo = get_initialized_repo()

    # Load and display settings
    settings_manager = SettingsManager(repo.get_dojo_path())
    current_settings = settings_manager.load()

    # Get database config
    with DatabaseManager(repo.get_db_path()) as db:
        review_freq = db.get_config('review_frequency_days', '7')
        default_lang = db.get_config('default_language', 'python')
        default_source = db.get_config('default_source', 'leetcode')

    click.echo("")
    click.echo(click.style("=" * 50, fg='bright_black'))
    click.echo(click.style("  BYTEDOJO SETTINGS", fg='cyan', bold=True))
    click.echo(click.style("=" * 50, fg='bright_black'))
    click.echo("")
    click.echo("  defaults:")
    click.echo(f"    language:     {click.style(default_lang, fg='blue', bold=True)}")
    click.echo(f"    source:       {default_source}")
    click.echo("")
    click.echo("  review:")
    click.echo(f"    frequency:    {review_freq} days")
    click.echo("")
    click.echo("  leetcode:")
    click.echo(f"    organization: {current_settings.leetcode.organization}")
    click.echo("")
    click.echo(click.style("-" * 50, fg='bright_black'))
    click.echo("  Change with:")
    click.echo("    dojo settings default-language <python|java|cpp>")
    click.echo("    dojo settings review-frequency <days>")
    click.echo(click.style("-" * 50, fg='bright_black'))
    click.echo("")


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
    repo = get_initialized_repo()

    with DatabaseManager(repo.get_db_path()) as db:
        old_value = db.get_config('default_language', 'python')
        new_value = language.lower()
        db.set_config('default_language', new_value)

        logger.info(f"Default language updated: {old_value} -> {new_value}")
        logger.info(f"Commands like 'dojo fetch 1' will now use {new_value.upper()}.")


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
    logger = get_logger()
    repo = get_initialized_repo()

    # Validate known settings
    valid_settings = {
        "leetcode.organization": ["flat", "difficulty"]
    }

    if key not in valid_settings:
        logger.error(f"Unknown setting: {key}")
        logger.info("")
        logger.info("Available settings:")
        for setting_key, valid_values in valid_settings.items():
            logger.info(f"  {setting_key}: {', '.join(valid_values)}")
        raise click.ClickException(f"Unknown setting: {key}")

    if value not in valid_settings[key]:
        logger.error(f"Invalid value '{value}' for {key}")
        logger.info(f"Valid values: {', '.join(valid_settings[key])}")
        raise click.ClickException(f"Invalid value: {value}")

    # Set the value
    settings_manager = SettingsManager(repo.get_dojo_path())
    if settings_manager.set(key, value):
        logger.info(f"Set {key} = {value}")
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
    logger = get_logger()
    repo = get_initialized_repo()

    # Get the value
    settings_manager = SettingsManager(repo.get_dojo_path())
    value = settings_manager.get(key)

    if value is None:
        logger.error(f"Unknown setting: {key}")
        raise click.ClickException(f"Unknown setting: {key}")

    logger.info(f"{key} = {value}")


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
    logger = get_logger()

    if days < 1:
        raise click.ClickException("Review frequency must be at least 1 day")

    if days > 365:
        raise click.ClickException("Review frequency cannot exceed 365 days")

    repo = get_initialized_repo()

    with DatabaseManager(repo.get_db_path()) as db:
        old_value = db.get_config('review_frequency_days', '7')
        db.set_config('review_frequency_days', str(days))

        logger.info(f"Review frequency updated: {old_value} days -> {days} days")
        logger.info("New problems will be scheduled for review after this interval.")
