"""
Settings command - View and modify bytedojo settings.
"""

import click

from bytedojo.core.logger import get_logger
from bytedojo.core.repository import DojoRepository
from bytedojo.core.settings import SettingsManager
from bytedojo.core.database import DatabaseManager


@click.group(invoke_without_command=True)
@click.pass_context
def settings(ctx):
    """
    View and modify bytedojo settings.

    Examples:
      dojo settings                              # Show all settings
      dojo settings set leetcode.organization flat
      dojo settings set leetcode.organization difficulty
    """
    # If no subcommand, show all settings
    if ctx.invoked_subcommand is None:
        show_settings()


def show_settings():
    """Display all current settings."""
    logger = get_logger()

    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    # Load and display settings
    settings_manager = SettingsManager(repo.get_dojo_path())
    current_settings = settings_manager.load()

    # Get database config
    with DatabaseManager(repo.get_db_path()) as db:
        review_freq = db.get_config('review_frequency_days', '7')
        default_lang = db.get_config('default_language', 'python')
        default_source = db.get_config('default_source', 'leetcode')

    logger.info("Current settings:")
    logger.info("")
    logger.info("  leetcode:")
    logger.info(f"    organization: {current_settings.leetcode.organization}")
    logger.info("")
    logger.info("  review:")
    logger.info(f"    frequency: {review_freq} days")
    logger.info("")
    logger.info("  defaults:")
    logger.info(f"    language: {default_lang}")
    logger.info(f"    source: {default_source}")
    logger.info("")
    logger.info("Use 'dojo settings set <key> <value>' to change settings.")
    logger.info("Use 'dojo settings review-frequency <days>' to change review frequency.")


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

    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

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

    # Check if repository is initialized
    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

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

    repo = DojoRepository()
    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    with DatabaseManager(repo.get_db_path()) as db:
        old_value = db.get_config('review_frequency_days', '7')
        db.set_config('review_frequency_days', str(days))

        logger.info(f"Review frequency updated: {old_value} days -> {days} days")
        logger.info("New problems will be scheduled for review after this interval.")
