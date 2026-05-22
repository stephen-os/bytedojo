"""
C++ toolchain — compile with g++, run the produced binary.

Build artifacts are placed under the per-run `build_dir` supplied by the
caller (typically `.dojo/build/{problem_id}_cpp/`). The binary is named
`solution` (or `solution.exe` on Windows) so it's easy to spot.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

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


#: Standard install location for vswhere.exe (ships with the Visual Studio Installer).
_VSWHERE_PATH = Path(
    r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
)


def _vswhere_install_version() -> Optional[str]:
    """Return the installed VS version (e.g. '17.8.0'), or None."""
    if not _VSWHERE_PATH.exists():
        return None
    try:
        proc = subprocess.run(
            [str(_VSWHERE_PATH), "-latest", "-property", "installationVersion"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    raw = proc.stdout.strip()
    return f"MSVC (Visual Studio {raw})" if raw else None


def find_msvc_vcvars() -> Optional[Path]:
    """
    Locate a Visual Studio install via vswhere and return the path to its
    `vcvars64.bat`, or None if none of: vswhere isn't installed, no VS
    with the VC++ workload is present, or the bat file is missing.

    This is how we make MSVC work from a *plain* shell — running cl.exe
    directly requires INCLUDE/LIB env vars that only vcvars64.bat sets.
    """
    if not _VSWHERE_PATH.exists():
        return None
    try:
        proc = subprocess.run(
            [
                str(_VSWHERE_PATH),
                "-latest", "-products", "*",
                "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property", "installationPath",
            ],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    install_path = proc.stdout.strip()
    if not install_path:
        return None
    vcvars = Path(install_path) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    return vcvars if vcvars.exists() else None


def find_cpp_compiler() -> Optional[Tuple[str, str]]:
    """
    Return (compiler kind, full path / vcvars path) for the first
    available C++ compiler.

    Probe order:
      1. g++         on PATH
      2. clang++     on PATH
      3. cl          on PATH (already in a Developer Command Prompt)
      4. MSVC        via vswhere — returned as ("msvc", <vcvars64.bat>)

    The "msvc" kind tells callers to wrap the compile in a vcvars
    activation; the others are invoked directly.
    """
    for name in _COMPILER_CANDIDATES:
        path = shutil.which(name)
        if path:
            return name, path
    vcvars = find_msvc_vcvars()
    if vcvars is not None:
        return "msvc", str(vcvars)
    return None


def compile_cpp_source(
    source: Path,
    output: Path,
    *,
    build_dir: Path,
) -> "subprocess.CompletedProcess[str]":
    """
    Compile a single .cpp file to an executable. Returns the subprocess
    result so callers can read returncode / stderr.

    Handles all three compiler shapes: GCC-style flags for g++ / clang++,
    MSVC syntax for `cl`, and shell-wrapped vcvars-activation for MSVC
    discovered via vswhere. `build_dir` becomes the cwd so MSVC's .obj /
    .pdb spillover stays contained.
    """
    found = find_cpp_compiler()
    if not found:
        raise FileNotFoundError(
            "No C++ compiler available (looked for g++, clang++, cl, then vswhere)."
        )
    name, location = found

    if name == "msvc":
        # vcvars64.bat sets INCLUDE / LIB / PATH for the cl.exe in that VS
        # install. Chain it with cl via cmd's `&&`.
        cmd_str = (
            f'call "{location}" >NUL 2>&1 && '
            f'cl /nologo /std:c++17 /O2 /EHsc /Fe:"{output}" "{source}"'
        )
        return subprocess.run(
            cmd_str, cwd=build_dir,
            capture_output=True, text=True, shell=True,
        )

    if name == "cl":
        cmd = [
            "cl", "/nologo", "/std:c++17", "/O2", "/EHsc",
            f"/Fe:{output}", str(source),
        ]
    else:  # g++ / clang++
        cmd = [name, "-std=c++17", "-O2", "-o", str(output), str(source)]

    return subprocess.run(
        cmd, cwd=build_dir, capture_output=True, text=True,
    )


#: Minimum major versions that reliably support -std=c++17.
_MIN_MAJOR = {"g++": 7, "clang++": 5}


def _check_min_version(name: str, version_str: str) -> Optional[str]:
    """Return a warning string if the compiler is too old for C++17, else None."""
    required = _MIN_MAJOR.get(name)
    if required is None:
        return None
    m = re.search(r"(\d+)\.\d+", version_str)
    if m is None:
        return None
    major = int(m.group(1))
    if major < required:
        return (
            f"{name} {major}.x is too old for C++17 — "
            f"upgrade to {name} {required}+ "
            f"(bytedojo uses -std=c++17)"
        )
    return None


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

        warning: Optional[str] = None

        if name == "msvc":
            # `path` here is vcvars64.bat, which doesn't accept --version.
            # Ask vswhere for the install version instead.
            version = _vswhere_install_version() or "MSVC (via vswhere)"
        else:
            try:
                proc = subprocess.run(
                    [path, "--version"],
                    capture_output=True, text=True, timeout=10,
                )
                raw = (proc.stdout or proc.stderr or "").splitlines()
                if raw:
                    version = raw[0].strip()
                    warning = _check_min_version(name, version)
            except (OSError, subprocess.TimeoutExpired):
                pass

        return ToolchainStatus(
            language=self.language,
            found=True,
            paths={name: path},
            version=version,
            install_hint=_INSTALL_HINTS.get(sys.platform),
            warning=warning,
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

        # Compile (handles g++ / clang++ / cl on PATH / MSVC via vswhere).
        try:
            compile_proc = compile_cpp_source(
                source_path, output_path, build_dir=build_dir,
            )
        except FileNotFoundError as e:
            return self._error(source_path, str(e))
        except OSError as e:
            return self._error(source_path, f"C++ compile failed to launch: {e}")

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
