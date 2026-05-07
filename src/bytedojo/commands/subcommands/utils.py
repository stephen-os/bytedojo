"""
Shared utilities for bytedojo commands.

Common functionality used across multiple command modules.
"""

import click
from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager


# ============================================================================
# CONSTANTS
# ============================================================================

# Languages supported by CLI (user-facing names)
SUPPORTED_LANGUAGES = ['python', 'java', 'cpp']

# Map user-facing language names to internal Language enum values
LANGUAGE_TO_INTERNAL = {
    'python': 'python3',  # Modern Python 3
    'java': 'java',
    'cpp': 'cpp',
}

DEFAULT_REVIEW_FREQUENCY_DAYS = 7

# Language display colors
LANGUAGE_COLORS = {
    'python': 'blue',
    'java': 'red',
    'cpp': 'cyan',
}

# Difficulty display colors
DIFFICULTY_COLORS = {
    'Easy': 'green',
    'Medium': 'yellow',
    'Hard': 'red',
}

# Problem source colors
SOURCE_COLORS = {
    'leetcode': 'yellow',
}

# Grade/test status colors
STATUS_COLORS = {
    'passed': 'green',
    'failed': 'red',
    'skipped': 'yellow',
    'ungraded': 'bright_black',
    'untested': 'bright_black',  # Legacy
}


# ============================================================================
# REPOSITORY HELPERS
# ============================================================================

def get_initialized_repo() -> Repository:
    """
    Get repository or raise error if not initialized.

    Returns:
        Initialized Repository instance

    Raises:
        click.ClickException: If repository is not initialized
    """
    logger = get_logger()
    repo = Repository(Path.cwd())

    if not repo.is_initialized:
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    return repo


def get_default_language() -> str:
    """
    Get the configured default language from database.

    Returns:
        Internal language value ('python3', 'java', or 'cpp') for use with
        Language enum. Falls back to 'python3' if repository is not initialized
        or config is missing.
    """
    repo = Repository(Path.cwd())
    if not repo.is_initialized:
        return 'python3'  # Fallback before repo init

    with DatabaseManager(repo.db_path) as db:
        user_lang = db.get_config('default_language', 'python')
        # Map user-facing name to internal value
        return LANGUAGE_TO_INTERNAL.get(user_lang, 'python3')


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def style_language(language: str) -> str:
    """Return styled language string."""
    color = LANGUAGE_COLORS.get(language, 'white')
    return click.style(language.upper(), fg=color)


def style_difficulty(difficulty: str) -> str:
    """Return styled difficulty string."""
    color = DIFFICULTY_COLORS.get(difficulty, 'white')
    return click.style(difficulty, fg=color)


def style_status(status: str) -> str:
    """Return styled status string."""
    color = STATUS_COLORS.get(status, 'white')
    return click.style(status, fg=color)


def style_source(source: str) -> str:
    """Return styled source string."""
    color = SOURCE_COLORS.get(source, 'white')
    return click.style(source.capitalize(), fg=color)
