"""
Python toolchain — runs solutions with the same interpreter that runs dojo.

Using sys.executable (rather than searching PATH for `python` / `python3`)
means dojo always runs your code with the interpreter it's already running
on. Same Python, same packages, same surprises — no PATH drift.
"""

import subprocess
import sys
from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.base import (
    ExecutionResult,
    Toolchain,
    ToolchainStatus,
)


class PythonToolchain(Toolchain):
    """Python toolchain — uses sys.executable directly."""

    language = CodeLanguage.PYTHON

    def __init__(self):
        self.logger = get_logger()

    def detect(self) -> ToolchainStatus:
        # We use the same interpreter that runs dojo, so detection is trivial:
        # if dojo is running, Python is "found".
        info = sys.version_info
        return ToolchainStatus(
            language=self.language,
            found=True,
            paths={"python": sys.executable},
            version=f"{info.major}.{info.minor}.{info.micro}",
        )

    def execute(self, source_path: Path, *, timeout: int) -> ExecutionResult:
        self.logger.debug(
            f"python_toolchain: executing {source_path} (timeout={timeout}s)"
        )

        try:
            result = subprocess.run(
                [sys.executable, str(source_path)],
                cwd=source_path.parent,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                timed_out=False,
                language=self.language.value,
                file_path=str(source_path),
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                timed_out=True,
                language=self.language.value,
                file_path=str(source_path),
            )
