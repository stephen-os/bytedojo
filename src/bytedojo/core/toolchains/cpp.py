"""
C++ toolchain — compile with g++, run the produced binary.

Build artifacts are placed under the per-run `build_dir` supplied by the
caller (typically `.dojo/build/{problem_id}_cpp/`). The binary is named
`solution` (or `solution.exe` on Windows) so it's easy to spot.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from bytedojo.core.logger import get_logger
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.base import (
    ExecutionResult,
    Toolchain,
    ToolchainStatus,
)


_INSTALL_HINTS = {
    "win32":  "winget install MSYS2.MSYS2  # then: pacman -S mingw-w64-x86_64-gcc",
    "darwin": "xcode-select --install  # or: brew install gcc",
    "linux":  "apt install g++  # or: dnf install gcc-c++",
}


class CppToolchain(Toolchain):
    """C++ toolchain — g++ to compile, then run the binary."""

    language = CodeLanguage.CPP

    #: Only one binary needed.
    _REQUIRED = ("g++",)

    def __init__(self):
        self.logger = get_logger()

    def detect(self) -> ToolchainStatus:
        paths: dict[str, str] = {}
        missing: list[str] = []
        for binary in self._REQUIRED:
            resolved = shutil.which(binary)
            if resolved:
                paths[binary] = resolved
            else:
                missing.append(binary)

        version: Optional[str] = None
        if not missing:
            try:
                proc = subprocess.run(
                    [paths["g++"], "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                raw = (proc.stdout or proc.stderr or "").splitlines()
                if raw:
                    version = raw[0].strip()
            except (OSError, subprocess.TimeoutExpired):
                pass

        return ToolchainStatus(
            language=self.language,
            found=not missing,
            missing=missing,
            paths=paths,
            version=version,
            install_hint=_INSTALL_HINTS.get(sys.platform),
        )

    def execute(
        self,
        source_path: Path,
        *,
        build_dir: Optional[Path] = None,
        timeout: int,
    ) -> ExecutionResult:
        self.logger.debug(
            f"cpp_toolchain: executing {source_path} "
            f"build_dir={build_dir} timeout={timeout}s"
        )

        if build_dir is None:
            return self._error(
                source_path,
                "Internal: CppToolchain requires build_dir",
            )
        build_dir.mkdir(parents=True, exist_ok=True)

        # Determine output path (.exe suffix on Windows)
        output_name = "solution.exe" if os.name == "nt" else "solution"
        output_path = build_dir / output_name

        # Compile
        try:
            compile_proc = subprocess.run(
                ["g++", "-std=c++17", "-O2", "-o", str(output_path), str(source_path)],
                capture_output=True,
                text=True,
            )
        except OSError as e:
            return self._error(source_path, f"g++ not runnable: {e}")

        if compile_proc.returncode != 0:
            return ExecutionResult(
                exit_code=compile_proc.returncode,
                stdout="",
                stderr=compile_proc.stderr,
                timed_out=False,
                language=self.language.value,
                file_path=str(source_path),
                compiled=False,
                compile_error=compile_proc.stderr.strip(),
            )

        # Run
        try:
            run_proc = subprocess.run(
                [str(output_path)],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return ExecutionResult(
                exit_code=run_proc.returncode,
                stdout=run_proc.stdout,
                stderr=run_proc.stderr,
                timed_out=False,
                language=self.language.value,
                file_path=str(source_path),
                compiled=True,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                timed_out=True,
                language=self.language.value,
                file_path=str(source_path),
                compiled=True,
            )

    def _error(self, source_path: Path, message: str) -> ExecutionResult:
        return ExecutionResult(
            exit_code=1,
            stdout="",
            stderr=message,
            timed_out=False,
            language=self.language.value,
            file_path=str(source_path),
        )
