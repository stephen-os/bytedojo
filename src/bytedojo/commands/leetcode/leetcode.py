"""
LeetCode command group.
"""

import click
from bytedojo.commands.leetcode.fetch import fetch


@click.group()
def leetcode():
    """LeetCode problem management commands."""
    pass


# Register subcommands
leetcode.add_command(fetch)