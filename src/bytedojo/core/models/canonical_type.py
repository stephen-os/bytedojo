"""
CanonicalType - the language-agnostic type universe for test signatures.

Each test bundle in data/tests/{id}.json carries a signature whose
parameter and return types are drawn from this enum. Per-language
converter libraries (Python/Java/C++ runtimes) map each canonical type
into the native representation for that language.

Bit-width is encoded explicitly in the integer/float types (INT32 vs
INT64, FLOAT64). Python ints are arbitrary precision so both INT32 and
INT64 round-trip through the same native `int`; the distinction only
matters in compiled languages where the converter picks `int`/`long` or
`int32_t`/`int64_t`.

TREE_NODE / LIST_NODE / LIST_NODE_ARRAY are always nullable in
semantics — Python uses Optional[...], C++ uses pointers, Java/JS can
hold null. We don't model an explicit optional variant; nullability is
implicit in the type.
"""

from enum import Enum


class CanonicalType(str, Enum):
    """Language-agnostic type identifiers used by test bundle signatures."""

    # Primitives
    INT32 = "INT32"
    INT64 = "INT64"
    FLOAT64 = "FLOAT64"
    BOOL = "BOOL"
    CHAR = "CHAR"
    STRING = "STRING"
    VOID = "VOID"

    # 1-D arrays
    INT32_ARRAY = "INT32_ARRAY"
    INT64_ARRAY = "INT64_ARRAY"
    FLOAT64_ARRAY = "FLOAT64_ARRAY"
    BOOL_ARRAY = "BOOL_ARRAY"
    CHAR_ARRAY = "CHAR_ARRAY"
    STRING_ARRAY = "STRING_ARRAY"

    # 2-D arrays (matrices / grids)
    INT32_MATRIX = "INT32_MATRIX"
    INT64_MATRIX = "INT64_MATRIX"
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
        """Return UNKNOWN for unrecognized type strings."""
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
