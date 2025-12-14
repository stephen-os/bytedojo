"""
ByteDojo CLI - Command-line interface logic.
"""

import click

from pathlib import Path
from typing import Optional

from bytedojo.core.context import Context

from bytedojo.core.logger import setup_logger, get_logger

from bytedojo.__init__ import __version__, __author__

from bytedojo.commands import init

def print_version(ctx, param, value):
    """Print version information and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Version: {__version__}")
    ctx.exit()

def print_author(ctx, param, value):
    """Print author information and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Author: {__author__}")
    ctx.exit()

def print_description(ctx, param, value):
    """Print full description and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo("A CLI tool for fetching, solving, and tracking programming problems")
    click.echo("from platforms like LeetCode. Master coding through structured")
    click.echo("repetition and spaced review.")
    ctx.exit()

# Define root command
@click.group()

# Define options
@click.option('--debug', is_flag=True, default=False, help='Enable debug mode with verbose logging')
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help='Show version info')
@click.option('--author', is_flag=True, callback=print_author, expose_value=False, is_eager=True, help='Show author info')
@click.option('--desc', is_flag=True, callback=print_description, expose_value=False, is_eager=True, help='Show full description')
@click.option('--config', type=click.Path(exists=True, path_type=Path), help='Path to custom config file')

# Define main command
@click.pass_context
def dojo(ctx, debug: bool, config: Optional[Path]):
    """
    ByteDojo - A CLI tool for practicing programming problems through spaced repetition.

    Fetch problems from LeetCode and other platforms, track your progress, 
    and revisit challenges systematically to build mastery through practice.
    """
    # Initialize logger first
    setup_logger(debug=debug)
    logger = get_logger() 
    
    # Create and store context
    ctx.ensure_object(dict)
    ctx.obj = Context(debug=debug, config_path=config)

dojo.add_command(init)