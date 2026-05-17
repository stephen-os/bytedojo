"""
Primitive - primitive value types used in method signatures.
"""

from enum import Enum

class Primitive(str, Enum):
    """Primitive value types."""

    UNKNOWN = "UNKNOWN"
    INT32 = "INT32"
    INT64 = "INT64"
    FLOAT64 = "FLOAT64"
    BOOL = "BOOL"
    CHAR = "CHAR"
    STRING = "STRING"
    VOID = "VOID"

    @classmethod
    def _missing_(cls, value):
        """Return UNKNOWN for unrecognized type strings."""
        return cls.UNKNOWN

    @classmethod
    def from_string(cls, value: str) -> "Primitive":
        """Parse from string; UNKNOWN on unrecognized input."""
        if not value:
            return cls.UNKNOWN
        return cls(value.upper())

    def __str__(self):
        """Return canonical name."""
        return self.value

    def __repr__(self):
        """Return canonical name."""
        return f"Primitive.{self.name}"
