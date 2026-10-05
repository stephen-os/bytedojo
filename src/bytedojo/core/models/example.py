"""
Example - a worked example shown in a problem description.
"""

from dataclasses import dataclass


@dataclass
class Example:
    """A worked example from the problem statement."""

    example_num: int
    example_text: str

    def __str__(self):
        return f"Example {self.example_num}: {self.example_text}"
