"""
Java toolchain — compile with javac, run with java.

Build artifacts (.class files) are placed under the per-run `build_dir`
supplied by the caller (typically `.dojo/build/{problem_id}_java/`).

The entry class is detected from the source by finding which class contains
`public static void main`. This keeps `dojo run` honest about what the user
wrote — no hardcoded class name.
"""

import re
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
    "win32":  "winget install Microsoft.OpenJDK.21",
    "darwin": "brew install openjdk@21",
    "linux":  "apt install default-jdk  # or: dnf install java-latest-openjdk-devel",
}


class JavaToolchain(Toolchain):
    """Java toolchain — javac to compile, java to run."""

    language = CodeLanguage.JAVA

    #: Both binaries are required.
    _REQUIRED = ("javac", "java")

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
            # `java --version` writes to stdout on modern JDKs (>= 9);
            # capture both streams just in case we hit an older one.
            try:
                proc = subprocess.run(
                    [paths["java"], "--version"],
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
            f"java_toolchain: executing {source_path} "
            f"build_dir={build_dir} timeout={timeout}s"
        )

        if build_dir is None:
            return self._error(
                source_path,
                "Internal: JavaToolchain requires build_dir",
            )
        build_dir.mkdir(parents=True, exist_ok=True)

        # Compile
        try:
            compile_proc = subprocess.run(
                ["javac", "-d", str(build_dir), str(source_path)],
                capture_output=True,
                text=True,
            )
        except OSError as e:
            return self._error(source_path, f"javac not runnable: {e}")

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

        # Identify the entry class (the one with public static void main)
        source = source_path.read_text(encoding="utf-8")
        main_class = _find_main_class(source)
        if main_class is None:
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=(
                    "No `public static void main` method found. "
                    "Add a main method to one of the classes in this file to "
                    "use `dojo run`. (Test runs do not need a main method.)"
                ),
                timed_out=False,
                language=self.language.value,
                file_path=str(source_path),
                compiled=True,
            )

        # Run
        try:
            run_proc = subprocess.run(
                ["java", "-cp", str(build_dir), main_class],
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


def _find_main_class(source: str) -> Optional[str]:
    """
    Return the name of the Java class containing `public static void main`.

    Uses the most recent class declaration before the first main method.
    Works for the common shapes (Solution-only with main, Solution + Main,
    user-renamed top-level class).
    """
    classes = list(re.finditer(r"(?:public\s+)?class\s+(\w+)", source))
    mains = list(re.finditer(r"public\s+static\s+void\s+main\s*\(", source))
    if not mains or not classes:
        return None

    main_offset = mains[0].start()
    enclosing: Optional[str] = None
    for m in classes:
        if m.start() < main_offset:
            enclosing = m.group(1)
        else:
            break
    return enclosing
