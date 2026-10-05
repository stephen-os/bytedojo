"""
Problem - the full problem record.

Composes a ProblemDetail (id/title/slug/difficulty/tags/description)
with worked examples, constraints, and hints. This is the object the
corpus gateway returns and the one formatters consume for the prose
sections of a solution file; the typed method signature used for stub
synthesis comes from the TestBundle (§11).
"""

from dataclasses import dataclass, field
from typing import List, Optional

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.example import Example
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.test_bundle import TestSignature


@dataclass
class Problem:
    """Full problem record: detail + examples + constraints + hints."""

    problem_detail: ProblemDetail
    examples: List[Example] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    signature: Optional[TestSignature] = None

    def get_folder_name(self) -> str:
        """Return the on-disk folder name: zero-padded id + slug (e.g. `0001-two-sum`)."""
        return f"{self.problem_detail.id:04d}-{self.problem_detail.slug}"

    def get_solution_filename(self, language: CodeLanguage) -> str:
        """Return the solution filename for a language (e.g. `solution.py`)."""
        return f"solution{language.extension}"
