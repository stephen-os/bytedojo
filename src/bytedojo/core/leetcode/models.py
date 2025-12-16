from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class CodeSnippet:
    """Code snippet in a specific language."""
    lang: str
    code: str


@dataclass
class Problem:
    """LeetCode problem data."""
    id: int
    title: str
    title_slug: str
    difficulty: str  # "Easy", "Medium", "Hard"
    description: str  # HTML content
    test_cases: str
    code_snippets: List[CodeSnippet]
    
    def get_snippet(self, language: str) -> Optional[str]:
        """Get code snippet for a specific language."""
        for snippet in self.code_snippets:
            if snippet.lang.lower() == language.lower():
                return snippet.code
        return None
    
    @property
    def filename(self) -> str:
        """Generate filename for this problem."""
        return f"{self.id:04d}-{self.title_slug}.py"