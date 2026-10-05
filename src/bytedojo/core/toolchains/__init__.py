"""
Toolchain registry — maps a CodeLanguage to its Toolchain implementation.

Use get_toolchain(language) to look up a single toolchain, or
all_toolchains() to iterate (e.g. for `dojo doctor`).

Adding a new language: implement a Toolchain in this package and register
it in _REGISTRY below.
"""

from typing import List, Optional

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.base import (
    DEFAULT_TIMEOUT_SECONDS,
    ExecutionResult,
    Toolchain,
    ToolchainStatus,
)
from bytedojo.core.toolchains.python import PythonToolchain


_REGISTRY: dict[CodeLanguage, type[Toolchain]] = {
    CodeLanguage.PYTHON: PythonToolchain,
}


def get_toolchain(language: CodeLanguage) -> Optional[Toolchain]:
    """Return a Toolchain instance for `language`, or None if unsupported."""
    cls = _REGISTRY.get(language)
    return cls() if cls else None


def all_toolchains() -> List[Toolchain]:
    """Return one instance of every registered toolchain (used by doctor)."""
    return [cls() for cls in _REGISTRY.values()]


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "ExecutionResult",
    "Toolchain",
    "ToolchainStatus",
    "PythonToolchain",
    "get_toolchain",
    "all_toolchains",
]
