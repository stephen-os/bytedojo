from enum import Enum

class ProblemTag(str, Enum):
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
    def from_string(cls, value: str) -> "ProblemTag":
        """Parse tag from string."""
        if not value:
            return cls.UNKNOWN
        return cls(value.lower())

    @classmethod
    def all(cls) -> list["ProblemTag"]:
        """Return all tags except UNKNOWN."""
        return [t for t in cls if t != cls.UNKNOWN]
    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return f"ProblemTag.{self.name}"
