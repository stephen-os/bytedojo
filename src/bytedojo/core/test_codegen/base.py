"""
Base classes for per-language test runner codegen.

A `TypeHandler` knows how to render one canonical type in one specific
language — declaration syntax, value literal, equality, display. Each
language has a registry mapping CanonicalType to its handler; codegen
walks a problem's input/output types and asks the handler for each
piece of generated source.
"""

from abc import ABC, abstractmethod
from typing import Any, List

from bytedojo.core.models.canonical_type import CanonicalType


class CodegenError(Exception):
    """Raised when codegen can't render some piece of the test runner."""


class TypeHandler(ABC):
    """One canonical type, one language. Stateless."""

    #: The canonical type this handler renders.
    canonical: CanonicalType

    @abstractmethod
    def declaration(self, var_name: str) -> str:
        """Variable declaration line, e.g. ``"int[] nums"`` / ``"vector<int> nums"``."""

    @abstractmethod
    def literal(self, value: Any) -> str:
        """
        Render a Python value as a language-native literal.

        E.g. for INT_ARRAY in Java: [2, 7, 11, 15] → ``"new int[]{2, 7, 11, 15}"``.
        For INT in any language: 9 → ``"9"``.
        """

    @abstractmethod
    def equals(self, lhs: str, rhs: str) -> str:
        """
        Boolean expression comparing two expressions of this type.

        E.g. for INT_ARRAY in Java: ``"Arrays.equals(actual, expected)"``.
        For INT in any language: ``"actual == expected"``.
        """

    @abstractmethod
    def to_string(self, expr: str) -> str:
        """
        Expression that converts an expression of this type to a String
        suitable for embedding in the JSON output.

        For arrays this typically pretty-prints (Arrays.toString in Java,
        a small helper in C++); for primitives it's a stringification cast.
        """

    @property
    def imports(self) -> List[str]:
        """Imports/includes this handler depends on (e.g. ``"java.util.Arrays"``)."""
        return []

    @property
    def helpers(self) -> str:
        """Optional helper code (free functions / utilities) to embed in the runner."""
        return ""


def resolve_handler(
    registry: dict,
    canonical: CanonicalType,
    *,
    language: str,
) -> TypeHandler:
    """Look up a handler from a registry, or raise a clear CodegenError."""
    handler = registry.get(canonical)
    if handler is None:
        raise CodegenError(
            f"No {language} TypeHandler registered for {canonical.value}. "
            f"Add one to test_codegen/{language}.py to support this type."
        )
    return handler


# Bounds for 32-bit int — used by Java/C++ when filtering test cases that
# would overflow the canonical INT / INT_ARRAY types.
INT32_MIN = -(2 ** 31)
INT32_MAX = (2 ** 31) - 1


def value_fits_int32(value) -> bool:
    """
    Whether a Python value (or every element if it's a list) fits in int32.

    Used to skip test cases whose data conflicts with the problem's
    declared INT / INT_ARRAY types. LeetCode's published test set
    occasionally includes values outside the stated constraints (e.g.
    Two Sum has cases with 10**10), which would overflow int in Java/C++
    even though Python's arbitrary-precision int swallows them silently.
    """
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, int):
        return INT32_MIN <= value <= INT32_MAX
    if isinstance(value, (list, tuple)):
        return all(value_fits_int32(v) for v in value)
    return True  # other types aren't our concern here


def case_fits_int32(
    case: dict,
    input_handlers: list,
    output_handler: TypeHandler,
) -> bool:
    """
    Whether every INT / INT_ARRAY value in `case` fits in int32.

    `input_handlers` is a list of (name, handler) tuples matching the
    layout in the codegen. Cases that fail this check should be skipped
    by the codegen — including them would just produce uncompilable
    `int` literals.
    """
    int_types = (CanonicalType.INT, CanonicalType.INT_ARRAY)

    for name, handler in input_handlers:
        if handler.canonical not in int_types:
            continue
        if not value_fits_int32(case["args"].get(name)):
            return False

    if output_handler.canonical in int_types:
        if not value_fits_int32(case.get("expected")):
            return False

    return True
