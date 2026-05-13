"""
ProblemDetail - core problem metadata used for listings and queries.

The light-weight projection of a problem: just enough to identify it,
filter it by difficulty / tags, and render it in a list. The heavy
parts (description body, code snippets, examples) live on `Problem`,
which composes a ProblemDetail with the rest.

`__post_init__` coerces raw strings into the typed enum fields so the
class can be constructed straight from a dict (JSON / DB row) without
the caller pre-converting.
"""

from dataclasses import dataclass, field
from typing import List

from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag


@dataclass
class ProblemDetail:
    """Light-weight problem metadata for listings and queries."""
    id: int
    title: str
    slug: str
    difficulty: ProblemDifficulty
    description: str
    tags: List[ProblemTag] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.difficulty, str):
            self.difficulty = ProblemDifficulty.from_string(self.difficulty)
        self.tags = [
            ProblemTag.from_string(t) if isinstance(t, str) else t
            for t in self.tags
        ]

    def __str__(self):
        return self.title

    def __repr__(self):
        return (f"ProblemDetail(id={self.id}, title={self.title!r}, slug={self.slug!r}, "
                f"difficulty={self.difficulty!r}, tags={self.tags!r})")
