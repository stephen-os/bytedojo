"""
dojo - main bytedojo command and entrypoint for all other commands.
"""

import click

from pathlib import Path
from typing import Optional

from bytedojo.core.context import Context

from bytedojo.core.logger import setup_logger, get_logger

from bytedojo.__init__ import __version__, __author__

from bytedojo.commands.subcommands import (
    init,
    stats,
    grade,
    settings,
    fetch,
    query,
    pick,
    review,
    run,
    enter,
)

# Helper functions for printing the version of bytedojo. 
def print_version(ctx, _, value):
    """Print version information and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Version: {__version__}")
    ctx.exit()

# Helper function for printing the author of bytedojo.
def print_author(ctx, _, value):
    """Print author information and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Author: {__author__}")
    ctx.exit()

# Helper function for printing the full description of bytedojo.
def print_description(ctx, _, value):
    """Print full description and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(
        "ByteDojo is a CLI tool for practicing LeetCode problems.\n"
        "Fetch, run, and grade problems, review solutions, and track\n"
        "progress—all from the command line."
    )
    ctx.exit()

# Define root command
@click.group()

# Options

# Debug mode
@click.option('--debug', is_flag=True, default=False, help='Enable debug mode with verbose logging')

# Version
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help='Show version info')

# Author
@click.option('--author', is_flag=True, callback=print_author, expose_value=False, is_eager=True, help='Show author info')

# Description
@click.option('--desc', is_flag=True, callback=print_description, expose_value=False, is_eager=True, help='Show full description')

# Config file
@click.option('--config', type=click.Path(exists=True, path_type=Path), help='Path to custom config file')

# Define main command
@click.pass_context
def bytedojo(ctx, debug: bool, config: Optional[Path]):
    """
    ByteDojo is a CLI tool for practicing LeetCode problems.
    Fetch, run, and grade problems, review solutions, and track
    progress—all from the command line.
    """
    # Initialize logger
    setup_logger(debug=debug)
    logger = get_logger() 
    
    # Create and store application context
    ctx.ensure_object(dict)
    ctx.obj = Context(debug=debug, config_path=config)

bytedojo.add_command(enter)
bytedojo.add_command(fetch)
bytedojo.add_command(grade)
bytedojo.add_command(init)
bytedojo.add_command(pick)
bytedojo.add_command(query)
bytedojo.add_command(review)
bytedojo.add_command(run)
bytedojo.add_command(settings)
bytedojo.add_command(stats)