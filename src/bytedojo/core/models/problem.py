from dataclasses import dataclass, field
from typing import List, Optional

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.example import Example
from bytedojo.core.models.problem_detail import ProblemDetail


@dataclass
class Problem:
    """Full problem metadata: description, starter snippets per language, examples."""
    problem_detail: ProblemDetail
    code_snippets: List[CodeSnippet] = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)

    def get_code_snippet(self, language: CodeLanguage) -> Optional[CodeSnippet]:
        """Get the CodeSnippet object for a specific language."""
        for cs in self.code_snippets:
            if cs.lang == language:
                return cs
        return None

    def get_snippet(self, language: CodeLanguage) -> Optional[str]:
        """Get starter code snippet text for a specific language."""
        cs = self.get_code_snippet(language)
        return cs.code if cs else None

    def get_folder_name(self) -> str:
        """Get problem folder name (zero-padded id + slug)."""
        return f"{self.problem_detail.id:04d}-{self.problem_detail.slug}"

    def get_solution_filename(self, language: CodeLanguage = CodeLanguage.PYTHON) -> str:
        """Get solution filename for problem-first organization."""
        return f"solution{language.extension}"
