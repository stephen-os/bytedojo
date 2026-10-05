"""
dojo - main bytedojo command and entrypoint for all other commands.
"""

import click

from bytedojo import __author__, __version__
from bytedojo.core.logger import setup_logger

from bytedojo.commands.subcommands import init
from bytedojo.commands.subcommands import grade
from bytedojo.commands.subcommands import settings
from bytedojo.commands.subcommands import fetch
from bytedojo.commands.subcommands import query
from bytedojo.commands.subcommands import pick
from bytedojo.commands.subcommands import review
from bytedojo.commands.subcommands import run
from bytedojo.commands.subcommands import test
from bytedojo.commands.subcommands import stats
from bytedojo.commands.subcommands import support


def print_version(ctx, _, value):
    """Print version information and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Version: {__version__}")
    ctx.exit()


def print_author(ctx, _, value):
    """Print author information and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Author: {__author__}")
    ctx.exit()


def print_description(ctx, _, value):
    """Print full description and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(
        "ByteDojo is a fully offline CLI for practicing LeetCode problems\n"
        "with spaced repetition. The loop: fetch a problem, solve it, run\n"
        "it, test it against the bundled cases, grade it, and review it\n"
        "when it comes due."
    )
    ctx.exit()


@click.group()
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Enable debug mode with verbose logging",
)
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show version info",
)
@click.option(
    "--author",
    is_flag=True,
    callback=print_author,
    expose_value=False,
    is_eager=True,
    help="Show author info",
)
@click.option(
    "--desc",
    is_flag=True,
    callback=print_description,
    expose_value=False,
    is_eager=True,
    help="Show full description",
)
@click.pass_context
def bytedojo(ctx, debug: bool):
    """
    ByteDojo — practice LeetCode problems offline, on a schedule.

    The loop: fetch → run → test → grade → review.
    """
    setup_logger(debug=debug)
    ctx.ensure_object(dict)


bytedojo.add_command(fetch)
bytedojo.add_command(grade)
bytedojo.add_command(init)
bytedojo.add_command(pick)
bytedojo.add_command(query)
bytedojo.add_command(review)
bytedojo.add_command(run)
bytedojo.add_command(test)
bytedojo.add_command(settings)
bytedojo.add_command(stats)
bytedojo.add_command(support)
