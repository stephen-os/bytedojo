"""
LeetCode command group.
"""

import click
from bytedojo.commands.leetcode.fetch import fetch
from bytedojo.commands.leetcode.query import query
from bytedojo.commands.leetcode.pick import pick


@click.group()
def leetcode():
    """LeetCode problem management commands."""
    pass


# Register subcommands
leetcode.add_command(fetch)
leetcode.add_command(query)
leetcode.add_command(pick)