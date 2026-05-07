"""
Subcommands for the ByteDojo CLI.
"""

from bytedojo.commands.subcommands.init import init
from bytedojo.commands.subcommands.stats import stats
from bytedojo.commands.subcommands.grade import grade
from bytedojo.commands.subcommands.fetch import fetch
from bytedojo.commands.subcommands.query import query
from bytedojo.commands.subcommands.pick import pick
from bytedojo.commands.subcommands.run import run
from bytedojo.commands.subcommands.review import review
from bytedojo.commands.subcommands.settings import settings
from bytedojo.commands.subcommands.enter import enter
from bytedojo.commands.subcommands.test import test

__all__ = [
    'init',
    'stats',
    'grade',
    'fetch',
    'query',
    'pick',
    'run',
    'review',
    'settings',
    'enter',
    'test',
]
