"""
Signature - a single type in a method signature.

Combines a base type (Primitive or DataStructure) with an optional element
type for parameterized containers like arrays and matrices.

Examples:
    INT32                  -> Signature(base=Primitive.INT32)
    ARRAY of INT32         -> Signature(base=DataStructure.ARRAY, element=Primitive.INT32)
    MATRIX of CHAR         -> Signature(base=DataStructure.MATRIX, element=Primitive.CHAR)
    LINKED_LIST            -> Signature(base=DataStructure.LINKED_LIST)
    ARRAY of LINKED_LIST   -> Signature(base=DataStructure.ARRAY, element=DataStructure.LINKED_LIST)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from bytedojo.core.models.data_structure import DataStructure
from bytedojo.core.models.primitive import Primitive

BaseType = Union[Primitive, DataStructure]


def _parse_base(value: str) -> BaseType:
    """Resolve a string to a DataStructure or Primitive, preferring DataStructure."""
    ds = DataStructure.from_string(value)
    if ds is not None:
        return ds
    return Primitive.from_string(value)


@dataclass
class Signature:
    """A single type in a method signature — primitive or data structure, optionally parameterized."""

    base: BaseType
    element: Optional[BaseType] = None

    def __post_init__(self):
        if isinstance(self.base, str):
            self.base = _parse_base(self.base)
        if isinstance(self.element, str):
            self.element = _parse_base(self.element)

    @classmethod
    def from_dict(cls, data: dict) -> Signature:
        """Build from a dict with 'base' and optional 'element' keys."""
        return cls(base=data["base"], element=data.get("element"))

    def __str__(self):
        if self.element is not None:
            return f"{self.base}<{self.element}>"
        return str(self.base)

    def __repr__(self):
        if self.element is not None:
            return f"Signature(base={self.base!r}, element={self.element!r})"
        return f"Signature(base={self.base!r})"
