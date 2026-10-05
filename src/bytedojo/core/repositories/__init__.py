"""
Per-aggregate persistence repositories for the .dojo database.

Each repository owns one aggregate's SQL and is constructed over an
open sqlite3 connection. Repository.session() (core/repository.py)
wires all four over a single connection per unit of work.
"""

from bytedojo.core.repositories.attempts import AttemptsRepository
from bytedojo.core.repositories.config import ConfigRepository
from bytedojo.core.repositories.problems import ProblemsRepository
from bytedojo.core.repositories.reviews import ReviewsRepository

__all__ = [
    "AttemptsRepository",
    "ConfigRepository",
    "ProblemsRepository",
    "ReviewsRepository",
]
