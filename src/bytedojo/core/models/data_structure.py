"""
DataStructure - data structure types used in method signatures
"""

from enum import Enum


class DataStructure(str, Enum):
    """Structural and reference types used in method signatures."""

    # Sequential 
    ARRAY = "ARRAY"
    MATRIX = "MATRIX"

    # Linked
    LINKED_LIST = "LINKED_LIST"
    DOUBLY_LINKED_LIST = "DOUBLY_LINKED_LIST"

    # Trees
    BINARY_TREE = "BINARY_TREE"
    BINARY_SEARCH_TREE = "BINARY_SEARCH_TREE"
    N_ARY_TREE = "N_ARY_TREE"
    TRIE = "TRIE"
    SEGMENT_TREE = "SEGMENT_TREE"

    # Graph
    GRAPH = "GRAPH"

    # Hash-based
    HASH_MAP = "HASH_MAP"
    HASH_SET = "HASH_SET"

    # Abstract
    STACK = "STACK"
    QUEUE = "QUEUE"
    DEQUE = "DEQUE"
    HEAP = "HEAP"

    @classmethod
    def _missing_(cls, value):
        """Return None for unrecognized type strings."""
        return None

    @classmethod
    def from_string(cls, value: str) -> "DataStructure | None":
        """Parse from string; None if not a recognized data structure."""
        if not value:
            return None
        return cls._value2member_map_.get(value.upper())

    def __str__(self):
        """Return canonical name."""
        return self.value

    def __repr__(self):
        """Return canonical name."""
        return f"DataStructure.{self.name}"
