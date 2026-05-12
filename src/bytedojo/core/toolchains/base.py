"""
Toolchain base — the contract every language implementation satisfies.

A Toolchain knows how to:
  - detect()  — whether the required executables exist on this machine
  - execute() — compile (if needed) and run a single source file

Services compose toolchains via the registry in core/toolchains/__init__.py;
they never call into per-language modules directly.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from bytedojo.core.models.code_language import CodeLanguage


# Default execution timeout (5 minutes)
DEFAULT_TIMEOUT_SECONDS = 300


@dataclass
class ToolchainStatus:
    """Result of probing the local environment for a toolchain."""
    language: CodeLanguage
    found: bool
    missing: List[str] = field(default_factory=list)
    paths: Dict[str, str] = field(default_factory=dict)
    version: Optional[str] = None
    install_hint: Optional[str] = None


@dataclass
class ExecutionResult:
    """Outcome of compiling + running a single source file."""
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    language: str
    file_path: str
    compiled: bool = False
    compile_error: str = ""


class Toolchain(ABC):
    """
    Per-language toolchain.

    Subclasses are stateless — constructed on demand by the registry. They
    own the platform-specific knowledge of what binaries are needed and how
    to invoke them; the service layer treats every language uniformly.
    """

    #: The language this toolchain implements.
    language: CodeLanguage

    @abstractmethod
    def detect(self) -> ToolchainStatus:
        """Probe the local environment. Cheap to call (used by doctor + pre-flight)."""

    @abstractmethod
    def execute(self, source_path: Path, *, timeout: int) -> ExecutionResult:
        """
        Compile (if needed) and run `source_path`, capturing stdout/stderr.

        Implementations should never raise on missing binaries — they should
        either be guarded by a `detect()` pre-flight at the call site, or
        catch OSError and return an ExecutionResult with `compile_error`
        populated.
        """
