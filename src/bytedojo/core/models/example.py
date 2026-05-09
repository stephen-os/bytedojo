from dataclasses import dataclass, field

from typing import List

@dataclass
class Example:
    """An example demonstrating problem input/output."""
    example_num: int
    example_text: str
    images: List[str] = field(default_factory=list)

    def __str__(self):
        return f"Example {self.example_num}: {self.example_text}"

    def __repr__(self):
        return f"Example(example_num={self.example_num}, example_text={self.example_text!r}, images={self.images!r})"
    