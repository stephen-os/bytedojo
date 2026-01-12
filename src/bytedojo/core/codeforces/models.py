"""Codeforces data models."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProblemSummary:
    """Summary of a Codeforces problem from query results."""
    contest_id: int
    index: str  # A, B, C, etc.
    name: str
    rating: Optional[int]  # Difficulty rating (800-3500)
    tags: List[str]

    @property
    def problem_id(self) -> str:
        """Get unique problem identifier (e.g., '1A', '4B')."""
        return f"{self.contest_id}{self.index}"

    @property
    def difficulty(self) -> str:
        """Convert rating to difficulty category."""
        if self.rating is None:
            return "Unrated"
        elif self.rating < 1200:
            return "Easy"
        elif self.rating < 1600:
            return "Medium"
        elif self.rating < 2100:
            return "Hard"
        else:
            return "Expert"


@dataclass
class Problem:
    """Full Codeforces problem data."""
    contest_id: int
    index: str
    name: str
    rating: Optional[int]
    tags: List[str]
    time_limit: str  # e.g., "1 second"
    memory_limit: str  # e.g., "256 megabytes"
    description: str  # HTML content
    input_spec: str  # Input specification
    output_spec: str  # Output specification
    sample_tests: List[dict]  # List of {"input": ..., "output": ...}
    note: str  # Additional notes

    @property
    def problem_id(self) -> str:
        """Get unique problem identifier."""
        return f"{self.contest_id}{self.index}"

    @property
    def difficulty(self) -> str:
        """Convert rating to difficulty category."""
        if self.rating is None:
            return "Unrated"
        elif self.rating < 1200:
            return "Easy"
        elif self.rating < 1600:
            return "Medium"
        elif self.rating < 2100:
            return "Hard"
        else:
            return "Expert"

    @property
    def filename(self) -> str:
        """Generate filename for this problem."""
        # Sanitize name for filename
        safe_name = self.name.lower()
        safe_name = safe_name.replace(' ', '-')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
        return f"{self.contest_id}{self.index}-{safe_name}.py"

    @property
    def url(self) -> str:
        """Get problem URL."""
        return f"https://codeforces.com/problemset/problem/{self.contest_id}/{self.index}"
