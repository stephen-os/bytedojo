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
from typing import List, Optional, Tuple

from bytedojo.core.logger import get_logger
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.base import (
    ExecutionResult,
    Toolchain,
    ToolchainStatus,
)


_INSTALL_HINTS = {
    "win32": (
        "Install any one of:\n"
        "    Visual Studio Build Tools (cl.exe):  "
        "winget install Microsoft.VisualStudio.2022.BuildTools\n"
        "    MSYS2 + GCC:                          "
        "winget install MSYS2.MSYS2  # then: pacman -S mingw-w64-x86_64-gcc\n"
        "    LLVM (clang++):                       "
        "winget install LLVM.LLVM"
    ),
    "darwin": "xcode-select --install  # or: brew install gcc",
    "linux":  "apt install g++  # or: dnf install gcc-c++",
}

#: Compilers tried in order; first one on PATH wins. g++/clang++ use the
#: same flags so we treat them interchangeably; cl.exe has its own syntax.
_COMPILER_CANDIDATES: Tuple[str, ...] = ("g++", "clang++", "cl")


def find_cpp_compiler() -> Optional[Tuple[str, str]]:
    """
    Return (compiler name, full path) of the first available C++ compiler.

    Probes PATH for g++, clang++, then cl (MSVC) — in that order. Returns
    None if none are found.

    Note for MSVC: cl.exe lives in Visual Studio's bin dirs, which are
    only added to PATH inside a "Developer Command Prompt for VS" (or
    after running vcvarsall.bat). If the user runs dojo from a plain
    shell, cl won't be detected here even with VS installed.
    """
    for name in _COMPILER_CANDIDATES:
        path = shutil.which(name)
        if path:
            return name, path
    return None


def build_cpp_compile_command(
    compiler: str,
    source: Path,
    output: Path,
) -> List[str]:
    """Compile command line for the detected compiler."""
    if compiler == "cl":
        # MSVC syntax: /Fe sets exe output, /EHsc enables C++ exceptions,
        # /nologo suppresses the startup banner.
        return [
            "cl", "/nologo", "/std:c++17", "/O2", "/EHsc",
            f"/Fe:{output}", str(source),
        ]
    # GCC-style (g++ / clang++)
    return [compiler, "-std=c++17", "-O2", "-o", str(output), str(source)]


class CppToolchain(Toolchain):
    """C++ toolchain — prefers g++ / clang++ / cl.exe in that order."""

    language = CodeLanguage.CPP

    def __init__(self):
        self.logger = get_logger()

    def detect(self) -> ToolchainStatus:
        found = find_cpp_compiler()
        if not found:
            return ToolchainStatus(
                language=self.language,
                found=False,
                missing=["g++, clang++, or cl.exe"],
                install_hint=_INSTALL_HINTS.get(sys.platform),
            )

        name, path = found
        version: Optional[str] = None
        try:
            version_arg = "/?" if name == "cl" else "--version"
            proc = subprocess.run(
                [path, version_arg],
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
            found=True,
            paths={name: path},
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

        found = find_cpp_compiler()
        if not found:
            return self._error(
                source_path,
                "No C++ compiler found (looked for g++, clang++, cl).",
            )
        compiler_name, _ = found

        # Determine output path (.exe suffix on Windows)
        output_name = "solution.exe" if os.name == "nt" else "solution"
        output_path = build_dir / output_name

        # Compile. cwd=build_dir keeps cl.exe's .obj/.pdb spillover contained.
        try:
            compile_proc = subprocess.run(
                build_cpp_compile_command(compiler_name, source_path, output_path),
                cwd=build_dir,
                capture_output=True,
                text=True,
            )
        except OSError as e:
            return self._error(source_path, f"{compiler_name} not runnable: {e}")

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
