"""Tests for the JavaToolchain.

Pure-Python parsing (`_find_main_class`) runs unconditionally.
Subprocess tests for compile/run skip when javac/java aren't on PATH so
the suite stays portable.
"""

import shutil

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.java import JavaToolchain, _find_main_class


# --------------------------------------------------------------------------- #
# _find_main_class — pure regex, no compiler needed                           #
# --------------------------------------------------------------------------- #

def test_find_main_class_solution_only_with_main():
    """Solution class containing main returns 'Solution'."""
    src = (
        "class Solution {\n"
        "    public static void main(String[] args) { System.out.println(1); }\n"
        "}\n"
    )
    assert _find_main_class(src) == "Solution"


def test_find_main_class_solution_plus_main_class():
    """Solution + Main returns 'Main' (the one containing main)."""
    src = (
        "class Solution {\n"
        "    public int solve() { return 0; }\n"
        "}\n"
        "class Main {\n"
        "    public static void main(String[] args) {}\n"
        "}\n"
    )
    assert _find_main_class(src) == "Main"


def test_find_main_class_user_renamed_class():
    """A user-renamed top-level class is detected correctly."""
    src = (
        "public class MyRunner {\n"
        "    public static void main(String[] args) {}\n"
        "}\n"
    )
    assert _find_main_class(src) == "MyRunner"


def test_find_main_class_returns_none_when_no_main():
    """No main method anywhere -> None (test-only files don't need one)."""
    src = "class Solution {\n    public int solve() { return 0; }\n}\n"
    assert _find_main_class(src) is None


def test_find_main_class_returns_none_when_no_class():
    src = "// just a comment, no code\n"
    assert _find_main_class(src) is None


def test_find_main_class_skips_classes_after_main():
    """A class declared after main is not the enclosing class."""
    src = (
        "class Wrapper {\n"
        "    public static void main(String[] args) {}\n"
        "}\n"
        "class Helper { }\n"
    )
    assert _find_main_class(src) == "Wrapper"


# --------------------------------------------------------------------------- #
# detect                                                                      #
# --------------------------------------------------------------------------- #

@pytest.fixture
def toolchain() -> JavaToolchain:
    return JavaToolchain()


def test_detect_when_binaries_missing(toolchain, monkeypatch):
    """All of javac/java missing -> found=False with both listed."""
    monkeypatch.setattr("bytedojo.core.toolchains.java.shutil.which",
                        lambda name: None)
    status = toolchain.detect()
    assert status.found is False
    assert set(status.missing) == {"javac", "java"}
    assert status.paths == {}


def test_detect_partial_install_reports_missing(toolchain, monkeypatch):
    """Only javac on PATH (no java) -> missing=['java']."""
    def fake_which(name):
        return "/fake/javac" if name == "javac" else None
    monkeypatch.setattr("bytedojo.core.toolchains.java.shutil.which", fake_which)

    status = toolchain.detect()
    assert status.found is False
    assert status.missing == ["java"]
    assert status.paths == {"javac": "/fake/javac"}


def test_detect_includes_install_hint_for_current_platform(toolchain, monkeypatch):
    """install_hint is always populated from the platform table."""
    monkeypatch.setattr("bytedojo.core.toolchains.java.shutil.which",
                        lambda name: None)
    status = toolchain.detect()
    assert status.install_hint is not None
    assert len(status.install_hint) > 0


# --------------------------------------------------------------------------- #
# execute — real subprocess, skipped without a JDK                            #
# --------------------------------------------------------------------------- #

#: Cheap PATH probe, evaluated at module import so the @skipif decorator
#: doesn't need to instantiate JavaToolchain (which requires the logger).
_JDK_ON_PATH = bool(shutil.which("javac")) and bool(shutil.which("java"))

jdk_required = pytest.mark.skipif(
    not _JDK_ON_PATH,
    reason="javac/java not on PATH",
)


@jdk_required
def test_execute_compiles_and_runs_hello_world(toolchain, tmp_path):
    src = tmp_path / "Main.java"
    src.write_text(
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        '        System.out.println("hello");\n'
        "    }\n"
        "}\n",
        encoding="utf-8",
    )

    result = toolchain.execute(src, build_dir=tmp_path / "build", timeout=30)
    assert result.exit_code == 0, result.stderr
    assert result.compiled is True
    assert result.stdout.strip() == "hello"
    assert result.language == CodeLanguage.JAVA.value


@jdk_required
def test_execute_reports_compile_error(toolchain, tmp_path):
    src = tmp_path / "Broken.java"
    src.write_text("class Broken { public static void main(String[] a) { not java; } }\n",
                   encoding="utf-8")

    result = toolchain.execute(src, build_dir=tmp_path / "build", timeout=30)
    assert result.exit_code != 0
    assert result.compiled is False
    assert result.compile_error != ""


@jdk_required
def test_execute_reports_no_main_method(toolchain, tmp_path):
    src = tmp_path / "Solution.java"
    src.write_text("class Solution { public int solve() { return 0; } }\n",
                   encoding="utf-8")

    result = toolchain.execute(src, build_dir=tmp_path / "build", timeout=30)
    assert result.exit_code == 1
    assert result.compiled is True
    assert "main" in result.stderr.lower()


def test_execute_requires_build_dir(toolchain, tmp_path):
    """No build_dir -> compile_error rather than crashing on None."""
    src = tmp_path / "Main.java"
    src.write_text("class Main { public static void main(String[] a) {} }\n",
                   encoding="utf-8")

    result = toolchain.execute(src, build_dir=None, timeout=10)
    assert result.exit_code == 1
    assert "build_dir" in result.stderr
