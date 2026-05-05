from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class Language(str, Enum):
    """Programming languages available for problems."""
    BASH = "bash"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    DART = "dart"
    ELIXIR = "elixir"
    ERLANG = "erlang"
    GO = "golang"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    KOTLIN = "kotlin"
    MSSQL = "mssql"
    MYSQL = "mysql"
    ORACLESQL = "oraclesql"
    PHP = "php"
    POSTGRESQL = "postgresql"
    PYTHON = "python"
    PYTHON3 = "python3"
    PYTHONDATA = "pythondata"
    RACKET = "racket"
    RUBY = "ruby"
    RUST = "rust"
    SCALA = "scala"
    SWIFT = "swift"
    TYPESCRIPT = "typescript"

    @classmethod
    def from_string(cls, value: str) -> Optional["Language"]:
        """Parse language from string, returns None if unknown."""
        try:
            return cls(value.lower())
        except ValueError:
            return None

    @property
    def extension(self) -> str:
        """Get file extension for this language."""
        extensions = {
            Language.PYTHON: ".py",
            Language.PYTHON3: ".py",
            Language.JAVA: ".java",
            Language.CPP: ".cpp",
            Language.C: ".c",
            Language.JAVASCRIPT: ".js",
            Language.TYPESCRIPT: ".ts",
            Language.GO: ".go",
            Language.RUST: ".rs",
            Language.RUBY: ".rb",
            Language.SWIFT: ".swift",
            Language.KOTLIN: ".kt",
            Language.SCALA: ".scala",
            Language.CSHARP: ".cs",
            Language.PHP: ".php",
            Language.DART: ".dart",
        }
        return extensions.get(self, ".txt")


class Difficulty(str, Enum):
    """Problem difficulty levels."""
    NONE = "None"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

    @classmethod
    def from_string(cls, value: str) -> "Difficulty":
        """Parse difficulty from string (case-insensitive)."""
        if not value:
            return cls.NONE
        try:
            return cls(value.capitalize())
        except ValueError:
            return cls.NONE


class Status(str, Enum):
    """Problem completion status."""
    NONE = "none"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNGRADED = "ungraded"

    @classmethod
    def from_string(cls, value: str) -> "Status":
        """Parse status from string (case-insensitive)."""
        if not value:
            return cls.NONE
        try:
            return cls(value.lower())
        except ValueError:
            return cls.NONE


@dataclass
class CodeSnippet:
    """Code snippet in a specific language."""
    lang: Language
    code: str


@dataclass
class ProblemSummary:
    """Summary of a LeetCode problem from query results."""
    id: int
    title: str
    title_slug: str
    difficulty: Difficulty
    tags: List[str]


@dataclass
class Case:
    """A test case with input and expected output."""
    input: str
    output: str  


@dataclass
class Problem:
    """LeetCode problem data."""
    id: int
    title: str
    title_slug: str
    difficulty: Difficulty
    description: str
    code_snippets: List[CodeSnippet]
    test_cases: List[Case]

    def get_snippet(self, language: Language) -> Optional[str]:
        """Get code snippet for a specific language."""
        for snippet in self.code_snippets:
            if snippet.lang == language:
                return snippet.code
        return None

    def get_folder_name(self) -> str:
        """Get problem folder name."""
        return f"{self.id:04d}-{self.title_slug}"

    def get_solution_filename(self, language: Optional[Language] = Language.PYTHON3) -> Optional[str]:
        """Get solution filename for problem-first organization."""
        if language is None:
            return None
        return f"solution{language.extension}"


@dataclass
class Attempt:
    """A single versioned attempt at solving a problem in a language."""
    problem_id: int
    language: Language
    version: int
    status: Status
    created_at: datetime
    run_count: int = 0
    notes: str = ""

    def get_version_string(self) -> str:
        """Get version as v001, v002, etc."""
        return f"v{self.version:03d}"


@dataclass
class AttemptStats:
    """Aggregated stats for a problem/language combination."""
    problem_id: int
    language: Language
    total_attempts: int
    latest_version: int
    latest_status: Status
    pass_count: int
    fail_count: int
    skip_count: int
    total_runs: int
