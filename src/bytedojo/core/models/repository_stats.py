"""
RepositoryStats - Summary statistics for the repository.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class RepositoryStats:
    """Summary statistics for a .dojo repository."""
    total_problems: int
    by_difficulty: Dict[str, int] = field(default_factory=dict)
    by_source: Dict[str, int] = field(default_factory=dict)
    by_language: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "RepositoryStats":
        """Return empty stats."""
        return cls(total_problems=0)
