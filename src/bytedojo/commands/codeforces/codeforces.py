"""
Codeforces command group.
"""

import click
from bytedojo.commands.codeforces.fetch import fetch
from bytedojo.commands.codeforces.query import query
from bytedojo.commands.codeforces.pick import pick


@click.group()
def codeforces():
    """Codeforces problem management commands."""
    pass


# Register subcommands
codeforces.add_command(fetch)
codeforces.add_command(query)
codeforces.add_command(pick)
