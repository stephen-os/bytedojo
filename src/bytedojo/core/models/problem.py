"""
Problem - the full problem record.

Composes a ProblemDetail (id/title/slug/difficulty/tags/description)
with per-language starter snippets, worked examples, constraints, and
hints. This is the object returned by problem_service when fetching
either fresh from LeetCode or from a cached local payload, and the one
formatters consume when placing files on disk.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.example import Example
from bytedojo.core.models.problem_detail import ProblemDetail


@dataclass
class Problem:
    """Full problem record: detail + per-language snippets + examples + constraints + hints."""
    problem_detail: ProblemDetail
    code_snippets: List[CodeSnippet] = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)

    def get_code_snippet(self, language: CodeLanguage) -> Optional[CodeSnippet]:
        """Return the CodeSnippet for a language, or None if missing."""
        for cs in self.code_snippets:
            if cs.lang == language:
                return cs
        return None

    def get_snippet(self, language: CodeLanguage) -> Optional[str]:
        """Return the starter code text for a language, or None if missing."""
        cs = self.get_code_snippet(language)
        return cs.code if cs else None

    def get_folder_name(self) -> str:
        """Return the on-disk folder name: zero-padded id + slug (e.g. `0001-two-sum`)."""
        return f"{self.problem_detail.id:04d}-{self.problem_detail.slug}"

    def get_solution_filename(self, language: CodeLanguage) -> str:
        """Return the solution filename for a language (e.g. `solution.py`)."""
        return f"solution{language.extension}"
