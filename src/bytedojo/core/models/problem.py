from dataclasses import dataclass, field
from typing import List, Optional

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_parameters import CodeParameters
from bytedojo.core.models.entry_point import EntryPoint
from bytedojo.core.models.example import Example
from bytedojo.core.models.problem_code import ProblemCode
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.test_case import TestCase


@dataclass
class Problem:
    """Full LeetCode problem data with tests and per-language code."""
    problem_detail: ProblemDetail
    problem_codes: List[ProblemCode] = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)

    def get_problem_code(self, language: CodeLanguage) -> Optional[ProblemCode]:
        """Get the per-language code package for a specific language."""
        for pc in self.problem_codes:
            if pc.lang == language:
                return pc
        return None

    def get_snippet(self, language: CodeLanguage) -> Optional[str]:
        """Get starter code snippet for a specific language."""
        pc = self.get_problem_code(language)
        return pc.problem_code.code if pc else None

    def get_entry_point(self, language: CodeLanguage) -> Optional[EntryPoint]:
        """Get entry point for a specific language."""
        pc = self.get_problem_code(language)
        return pc.entry_point if pc else None

    def get_parameters(self, language: CodeLanguage) -> Optional[CodeParameters]:
        """Get parameter information for a specific language."""
        pc = self.get_problem_code(language)
        return pc.problem_parameters if pc else None

    def get_test_snippet(self, language: CodeLanguage) -> Optional[str]:
        """Get test snippet for a specific language."""
        pc = self.get_problem_code(language)
        return pc.test_code.code if pc else None

    def get_folder_name(self) -> str:
        """Get problem folder name."""
        return f"{self.problem_detail.id:04d}-{self.problem_detail.slug}"

    def get_solution_filename(self, language: CodeLanguage = CodeLanguage.PYTHON) -> str:
        """Get solution filename for problem-first organization."""
        return f"solution{language.extension}"
