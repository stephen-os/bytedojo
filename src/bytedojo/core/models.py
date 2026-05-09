from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class Language(str, Enum):
    """Programming languages available for problems."""
    UNKNOWN = "unknown"
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
    def _missing_(cls, value):
        """Return UNKNOWN for unrecognized language values."""
        return cls.UNKNOWN

    @classmethod
    def from_string(cls, value: str) -> "Language":
        """Parse language from string, returns UNKNOWN if unknown."""
        if not value:
            return cls.UNKNOWN
        return cls(value.lower())

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
    def _missing_(cls, value):
        """Return NONE for unrecognized difficulty values."""
        return cls.NONE

    @classmethod
    def from_string(cls, value: str) -> "Difficulty":
        """Parse difficulty from string (case-insensitive)."""
        if not value:
            return cls.NONE
        return cls(value.capitalize())


class Status(str, Enum):
    """Problem completion status."""
    NONE = "none"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNGRADED = "ungraded"

    @classmethod
    def _missing_(cls, value):
        """Return NONE for unrecognized status values."""
        return cls.NONE

    @classmethod
    def from_string(cls, value: str) -> "Status":
        """Parse status from string (case-insensitive)."""
        if not value:
            return cls.NONE
        return cls(value.lower())


class Tag(str, Enum):
    """Problem tag categories."""
    UNKNOWN = "unknown"
    ARRAY = "array"
    BACKTRACKING = "backtracking"
    BICONNECTED_COMPONENT = "biconnected-component"
    BINARY_INDEXED_TREE = "binary-indexed-tree"
    BINARY_SEARCH = "binary-search"
    BINARY_SEARCH_TREE = "binary-search-tree"
    BINARY_TREE = "binary-tree"
    BIT_MANIPULATION = "bit-manipulation"
    BITMASK = "bitmask"
    BRAINTEASER = "brainteaser"
    BREADTH_FIRST_SEARCH = "breadth-first-search"
    BUCKET_SORT = "bucket-sort"
    COMBINATORICS = "combinatorics"
    COUNTING = "counting"
    COUNTING_SORT = "counting-sort"
    DEPTH_FIRST_SEARCH = "depth-first-search"
    DIVIDE_AND_CONQUER = "divide-and-conquer"
    DYNAMIC_PROGRAMMING = "dynamic-programming"
    ENUMERATION = "enumeration"
    EULERIAN_CIRCUIT = "eulerian-circuit"
    GAME_THEORY = "game-theory"
    GEOMETRY = "geometry"
    GRAPH = "graph"
    GREEDY = "greedy"
    HASH_FUNCTION = "hash-function"
    HASH_TABLE = "hash-table"
    HEAP = "heap"
    INTERACTIVE = "interactive"
    LINE_SWEEP = "line-sweep"
    LINKED_LIST = "linked-list"
    MATH = "math"
    MATRIX = "matrix"
    MEMOIZATION = "memoization"
    MERGE_SORT = "merge-sort"
    MINIMUM_SPANNING_TREE = "minimum-spanning-tree"
    MONOTONIC_QUEUE = "monotonic-queue"
    MONOTONIC_STACK = "monotonic-stack"
    NUMBER_THEORY = "number-theory"
    ORDERED_SET = "ordered-set"
    PREFIX_SUM = "prefix-sum"
    PROBABILITY_AND_STATISTICS = "probability-and-statistics"
    QUEUE = "queue"
    QUICKSELECT = "quickselect"
    RADIX_SORT = "radix-sort"
    RANDOMIZED = "randomized"
    RECURSION = "recursion"
    ROLLING_HASH = "rolling-hash"
    SEGMENT_TREE = "segment-tree"
    SHORTEST_PATH = "shortest-path"
    SIMULATION = "simulation"
    SLIDING_WINDOW = "sliding-window"
    SORT = "sort"
    SORTING = "sorting"
    STACK = "stack"
    STRING = "string"
    STRING_MATCHING = "string-matching"
    STRONGLY_CONNECTED_COMPONENT = "strongly-connected-component"
    SUFFIX_ARRAY = "suffix-array"
    TOPOLOGICAL_SORT = "topological-sort"
    TREE = "tree"
    TRIE = "trie"
    TWO_POINTERS = "two-pointers"
    UNION_FIND = "union-find"

    @classmethod
    def _missing_(cls, value):
        """Return UNKNOWN for unrecognized tag values."""
        return cls.UNKNOWN

    @classmethod
    def from_string(cls, value: str) -> "Tag":
        """Parse tag from string."""
        if not value:
            return cls.UNKNOWN

        try:
            return cls(value.lower())
        except ValueError:
            return cls.UNKNOWN

    @classmethod
    def all(cls) -> list["Tag"]:
        """Return all tags except UNKNOWN."""
        return [t for t in cls if t != cls.UNKNOWN]


@dataclass
class CodeSnippet:
    """Code snippet in a specific language."""
    lang: Language
    code: str


@dataclass
class Example:
    """An example demonstrating problem input/output."""
    example_num: int
    example_text: str
    images: List[str] = field(default_factory=list)


@dataclass
class TypeParam:
    """A typed parameter with name and type string."""
    name: str
    type_str: str


@dataclass
class TypeInfo:
    """Type information for a language's function signature."""
    lang: Language
    input: List[TypeParam]
    output: str


@dataclass
class EntryPoint:
    """Entry point expression for invoking solution in a language."""
    lang: Language
    expression: str


@dataclass
class TestSnippet:
    """Test code snippet for a specific language."""
    lang: Language
    code: str


@dataclass
class Case:
    """A test case with input and expected output as strings."""
    input: str
    output: str


@dataclass
class ProblemDetail:
    """Core problem metadata used for listings and queries."""
    id: int
    title: str
    slug: str
    difficulty: Difficulty
    tags: List[Tag]
    description: str


@dataclass
class Problem(ProblemDetail):
    """Full LeetCode problem data with tests and metadata."""
    examples: List[Example]
    constraints: List[str]
    hints: List[str]
    code_snippets: List[CodeSnippet]
    entry_points: List[EntryPoint]
    types: List[TypeInfo]
    test_cases: List[Case]
    test_snippets: List[TestSnippet]

    def get_snippet(self, language: Language) -> Optional[str]:
        """Get code snippet for a specific language."""
        for snippet in self.code_snippets:
            if snippet.lang == language:
                return snippet.code
        return None

    def get_entry_point(self, language: Language) -> Optional[str]:
        """Get entry point expression for a specific language."""
        for entry in self.entry_points:
            if entry.lang == language:
                return entry.expression
        return None

    def get_type_info(self, language: Language) -> Optional[TypeInfo]:
        """Get type information for a specific language."""
        for type_info in self.types:
            if type_info.lang == language:
                return type_info
        return None

    def get_test_snippet(self, language: Language) -> Optional[str]:
        """Get test snippet for a specific language."""
        for snippet in self.test_snippets:
            if snippet.lang == language:
                return snippet.code
        return None

    def get_folder_name(self) -> str:
        """Get problem folder name."""
        return f"{self.id:04d}-{self.slug}"

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
