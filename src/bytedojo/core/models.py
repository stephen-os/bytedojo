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


class Topic(str, Enum):
    """Problem topic/tag categories."""
    UNKNOWN = "Unknown"
    ARRAY = "Array"
    BACKTRACKING = "Backtracking"
    BICONNECTED_COMPONENT = "Biconnected Component"
    BINARY_INDEXED_TREE = "Binary Indexed Tree"
    BINARY_SEARCH = "Binary Search"
    BINARY_SEARCH_TREE = "Binary Search Tree"
    BINARY_TREE = "Binary Tree"
    BIT_MANIPULATION = "Bit Manipulation"
    BITMASK = "Bitmask"
    BRAINTEASER = "Brainteaser"
    BREADTH_FIRST_SEARCH = "Breadth-First Search"
    BUCKET_SORT = "Bucket Sort"
    COMBINATORICS = "Combinatorics"
    COUNTING = "Counting"
    COUNTING_SORT = "Counting Sort"
    DEPTH_FIRST_SEARCH = "Depth-First Search"
    DIVIDE_AND_CONQUER = "Divide and Conquer"
    DYNAMIC_PROGRAMMING = "Dynamic Programming"
    ENUMERATION = "Enumeration"
    EULERIAN_CIRCUIT = "Eulerian Circuit"
    GAME_THEORY = "Game Theory"
    GEOMETRY = "Geometry"
    GRAPH = "Graph"
    GREEDY = "Greedy"
    HASH_FUNCTION = "Hash Function"
    HASH_TABLE = "Hash Table"
    HEAP = "Heap (Priority Queue)"
    INTERACTIVE = "Interactive"
    LINE_SWEEP = "Line Sweep"
    LINKED_LIST = "Linked List"
    MATH = "Math"
    MATRIX = "Matrix"
    MEMOIZATION = "Memoization"
    MERGE_SORT = "Merge Sort"
    MINIMUM_SPANNING_TREE = "Minimum Spanning Tree"
    MONOTONIC_QUEUE = "Monotonic Queue"
    MONOTONIC_STACK = "Monotonic Stack"
    NUMBER_THEORY = "Number Theory"
    ORDERED_SET = "Ordered Set"
    PREFIX_SUM = "Prefix Sum"
    PROBABILITY_AND_STATISTICS = "Probability and Statistics"
    QUEUE = "Queue"
    QUICKSELECT = "Quickselect"
    RADIX_SORT = "Radix Sort"
    RANDOMIZED = "Randomized"
    RECURSION = "Recursion"
    ROLLING_HASH = "Rolling Hash"
    SEGMENT_TREE = "Segment Tree"
    SHORTEST_PATH = "Shortest Path"
    SIMULATION = "Simulation"
    SLIDING_WINDOW = "Sliding Window"
    SORT = "Sort"
    SORTING = "Sorting"
    STACK = "Stack"
    STRING = "String"
    STRING_MATCHING = "String Matching"
    STRONGLY_CONNECTED_COMPONENT = "Strongly Connected Component"
    SUFFIX_ARRAY = "Suffix Array"
    TOPOLOGICAL_SORT = "Topological Sort"
    TREE = "Tree"
    TRIE = "Trie"
    TWO_POINTERS = "Two Pointers"
    UNION_FIND = "Union Find"

    @classmethod
    def _missing_(cls, value):
        """Return UNKNOWN for unrecognized topic values."""
        return cls.UNKNOWN

    @classmethod
    def from_string(cls, value: str) -> "Topic":
        """Parse topic from string."""
        if not value:
            return cls.UNKNOWN

        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN


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
class TestCase:
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
    topics: List[Topic]
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
    test_cases: List[TestCase]
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
