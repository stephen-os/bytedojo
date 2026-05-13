"""
Example - one worked input/output example from a problem statement.

LeetCode problem pages typically include 2-3 numbered examples with
optional image illustrations. We strip them out of the raw HTML and
attach them to `Problem.examples` so the fetched solution file can
surface them as comments.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Example:
    """A single worked example from a problem statement."""
    example_num: int
    example_text: str
    images: List[str] = field(default_factory=list)

    def __str__(self):
        return f"Example {self.example_num}: {self.example_text}"
