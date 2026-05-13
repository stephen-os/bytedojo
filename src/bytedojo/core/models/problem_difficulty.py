"""
ProblemDifficulty - LeetCode difficulty levels.

Values match LeetCode's display strings (`"Easy"`, `"Medium"`, `"Hard"`)
so a raw API payload parses through `ProblemDifficulty(value)` directly.
`NONE` is the sentinel for "no difficulty filter / unrecognized input".
"""

from enum import Enum


class ProblemDifficulty(str, Enum):
    """LeetCode difficulty levels. NONE is the sentinel / unrecognized fallback."""
    NONE = "None"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

    @classmethod
    def _missing_(cls, value):
        """Return NONE for unrecognized difficulty values."""
        return cls.NONE

    @classmethod
    def from_string(cls, value: str) -> "ProblemDifficulty":
        """Parse difficulty from string; NONE on empty / unrecognized."""
        if not value:
            return cls.NONE
        return cls(value.capitalize())

    @classmethod
    def all(cls) -> list["ProblemDifficulty"]:
        """Return all real difficulties (EASY, MEDIUM, HARD), excluding NONE."""
        return [d for d in cls if d != cls.NONE]

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"ProblemDifficulty.{self.name}"
