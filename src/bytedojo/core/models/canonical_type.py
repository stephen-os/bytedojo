"""
CanonicalType — the language-agnostic type universe for problem signatures.

LeetCode encodes the same logical type as different strings per language
(`int[]` in Java, `vector<int>&` in C++, `List[int]` in Python). For
codegen we collapse all of those down to a single canonical name and let
per-language TypeHandlers render the right declaration / literal / etc.

The data migration in scripts/migrate_problem_types.py infers these from
the existing per-language strings; this module is the central registry.

Reference-type semantics:
    TreeNode and ListNode are *always nullable* — Python uses
    Optional[...], C++ uses pointers (which are nullable), Java/JS
    can hold null, Rust uses Option<...>. We don't model an explicit
    optional variant; nullability is implicit in the type.
"""

from enum import Enum


class CanonicalType(str, Enum):
    """Language-agnostic type identifiers used by problem signatures."""

    # Primitives
    INT = "INT"
    LONG = "LONG"
    DOUBLE = "DOUBLE"
    BOOL = "BOOL"
    CHAR = "CHAR"
    STRING = "STRING"
    VOID = "VOID"

    # 1-D arrays
    INT_ARRAY = "INT_ARRAY"
    LONG_ARRAY = "LONG_ARRAY"
    DOUBLE_ARRAY = "DOUBLE_ARRAY"
    BOOL_ARRAY = "BOOL_ARRAY"
    CHAR_ARRAY = "CHAR_ARRAY"
    STRING_ARRAY = "STRING_ARRAY"

    # 2-D arrays (matrices / grids)
    INT_MATRIX = "INT_MATRIX"
    LONG_MATRIX = "LONG_MATRIX"
    CHAR_MATRIX = "CHAR_MATRIX"
    STRING_MATRIX = "STRING_MATRIX"

    # LeetCode reference types — always nullable in semantics
    TREE_NODE = "TREE_NODE"
    LIST_NODE = "LIST_NODE"
    LIST_NODE_ARRAY = "LIST_NODE_ARRAY"

    # Fallback when the mapping is missing
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN

    @classmethod
    def from_string(cls, value: str) -> "CanonicalType":
        """Parse a canonical name from string; UNKNOWN on unrecognized input."""
        if not value:
            return cls.UNKNOWN
        return cls(value.upper())

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"CanonicalType.{self.name}"
