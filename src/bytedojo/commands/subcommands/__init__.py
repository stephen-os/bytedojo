"""
Subcommands for the ByteDojo CLI.
"""

from bytedojo.commands.subcommands.init import init
from bytedojo.commands.subcommands.grade import grade
from bytedojo.commands.subcommands.fetch import fetch
from bytedojo.commands.subcommands.query import query
from bytedojo.commands.subcommands.pick import pick
from bytedojo.commands.subcommands.review import review
from bytedojo.commands.subcommands.settings import settings

__all__ = [
    'init',
    'grade',
    'fetch',
    'query',
    'pick',
    'review',
    'settings',
]
