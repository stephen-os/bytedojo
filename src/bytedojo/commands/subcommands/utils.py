"""
Shared utilities for bytedojo commands.

Common functionality used across multiple command modules.
"""

import click
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar, Any

from bytedojo.core.logger import get_logger
from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager


# ============================================================================
# CONSTANTS
# ============================================================================

SUPPORTED_LANGUAGES = ['python', 'java', 'cpp']

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
        Default language ('python', 'java', or 'cpp'). Falls back to 'python'
        if repository is not initialized or config is missing.
    """
    repo = Repository(Path.cwd())
    if not repo.is_initialized:
        return 'python'  # Fallback before repo init

    with DatabaseManager(repo.db_path) as db:
        return db.get_config('default_language', 'python')


F = TypeVar('F', bound=Callable[..., Any])


def require_initialized_repo(f: F) -> F:
    """
    Decorator that ensures repository is initialized before running command.

    Injects 'repo' as the first argument to the decorated function.

    Usage:
        @click.command()
        @require_initialized_repo
        def my_command(repo, ...):
            # repo is guaranteed to be initialized
            pass
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        repo = get_initialized_repo()
        return f(repo, *args, **kwargs)
    return wrapper


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


# ============================================================================
# ERROR MESSAGE HELPERS
# ============================================================================

def fetch_hint(problem_id: str = "<id>", language: str = "python") -> str:
    """Generate a hint message for fetching a problem."""
    if language == "python":
        return f"Fetch it first with: dojo fetch {problem_id}"
    return f"Fetch it first with: dojo fetch {problem_id} --{language}"


def no_problems_found_message(language: str, criteria: str = "") -> str:
    """Generate a 'no problems found' error message."""
    if criteria:
        return f"No {language} problems found matching {criteria}. {fetch_hint(language=language)}"
    return f"No {language} problems found. {fetch_hint(language=language)}"
