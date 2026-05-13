"""Tests for the CppToolchain.

Pure-Python compiler-discovery (`find_cpp_compiler`) is tested with
monkeypatched `shutil.which`. Subprocess tests for compile/run skip
when no C++ compiler is on PATH so the suite stays portable.
"""

import shutil

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.cpp import (
    CppToolchain,
    find_cpp_compiler,
    find_msvc_vcvars,
)


# --------------------------------------------------------------------------- #
# find_cpp_compiler — pure dispatch, mocked via shutil.which                  #
# --------------------------------------------------------------------------- #

def test_find_cpp_compiler_prefers_gpp(monkeypatch):
    """When all three are on PATH, g++ wins."""
    def fake_which(name):
        return f"/fake/{name}" if name in {"g++", "clang++", "cl"} else None
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.shutil.which", fake_which)

    assert find_cpp_compiler() == ("g++", "/fake/g++")


def test_find_cpp_compiler_falls_through_to_clangpp(monkeypatch):
    """No g++, but clang++ is on PATH."""
    def fake_which(name):
        return "/fake/clang++" if name == "clang++" else None
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.shutil.which", fake_which)

    assert find_cpp_compiler() == ("clang++", "/fake/clang++")


def test_find_cpp_compiler_falls_through_to_cl(monkeypatch):
    """Only cl on PATH (already inside a Developer Command Prompt)."""
    def fake_which(name):
        return "/fake/cl" if name == "cl" else None
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.shutil.which", fake_which)
    # Don't fall through to vswhere lookup.
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.find_msvc_vcvars",
                        lambda: None)

    assert find_cpp_compiler() == ("cl", "/fake/cl")


def test_find_cpp_compiler_falls_through_to_vswhere(monkeypatch, tmp_path):
    """No compiler on PATH, but vswhere locates an MSVC install."""
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.shutil.which",
                        lambda name: None)
    fake_vcvars = tmp_path / "vcvars64.bat"
    fake_vcvars.write_text("@echo off\n")
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.find_msvc_vcvars",
                        lambda: fake_vcvars)

    assert find_cpp_compiler() == ("msvc", str(fake_vcvars))


def test_find_cpp_compiler_returns_none_when_nothing_available(monkeypatch):
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.shutil.which",
                        lambda name: None)
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.find_msvc_vcvars",
                        lambda: None)

    assert find_cpp_compiler() is None


# --------------------------------------------------------------------------- #
# find_msvc_vcvars — returns None when vswhere isn't installed                #
# --------------------------------------------------------------------------- #

def test_find_msvc_vcvars_returns_none_when_vswhere_missing(monkeypatch):
    """Standard install path doesn't exist -> return None, don't raise."""
    from pathlib import Path

    monkeypatch.setattr(
        "bytedojo.core.toolchains.cpp._VSWHERE_PATH",
        Path(r"C:\does\not\exist\vswhere.exe"),
    )
    assert find_msvc_vcvars() is None


# --------------------------------------------------------------------------- #
# CppToolchain.detect                                                         #
# --------------------------------------------------------------------------- #

@pytest.fixture
def toolchain() -> CppToolchain:
    return CppToolchain()


def test_detect_reports_missing_compiler(toolchain, monkeypatch):
    """No compiler available -> found=False with a single 'missing' entry."""
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.shutil.which",
                        lambda name: None)
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.find_msvc_vcvars",
                        lambda: None)

    status = toolchain.detect()
    assert status.found is False
    assert len(status.missing) == 1     # the union "g++, clang++, or cl.exe"
    assert status.install_hint is not None


def test_detect_records_compiler_path_when_found(toolchain, monkeypatch):
    """A discovered compiler is recorded by its kind in `paths`."""
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.find_cpp_compiler",
                        lambda: ("g++", "/fake/g++"))
    # Skip the subprocess `--version` call by returning a benign exception.
    import subprocess
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("no g++ at fake path")))

    status = toolchain.detect()
    assert status.found is True
    assert status.paths == {"g++": "/fake/g++"}
    assert status.language is CodeLanguage.CPP


# --------------------------------------------------------------------------- #
# execute — real subprocess, skipped without a compiler                       #
# --------------------------------------------------------------------------- #

#: Cheap probe evaluated at module import — checks PATH for the direct
#: compilers and falls back to the vswhere-discovered MSVC path. Avoids
#: instantiating CppToolchain so the @skipif decorator doesn't need the
#: logger initialised yet (that happens later, in the autouse fixture).
_CPP_AVAILABLE = (
    any(shutil.which(c) for c in ("g++", "clang++", "cl"))
    or find_msvc_vcvars() is not None
)

cpp_required = pytest.mark.skipif(
    not _CPP_AVAILABLE,
    reason="no C++ compiler available (g++ / clang++ / cl / vswhere-MSVC)",
)


@cpp_required
def test_execute_compiles_and_runs_hello_world(toolchain, tmp_path):
    src = tmp_path / "hello.cpp"
    src.write_text(
        "#include <iostream>\n"
        "int main() { std::cout << \"hello\" << std::endl; return 0; }\n",
        encoding="utf-8",
    )

    result = toolchain.execute(src, build_dir=tmp_path / "build", timeout=60)
    assert result.exit_code == 0, result.stderr
    assert result.compiled is True
    assert result.stdout.strip() == "hello"
    assert result.language == CodeLanguage.CPP.value


@cpp_required
def test_execute_reports_compile_error(toolchain, tmp_path):
    """A broken source returns non-zero with compiled=False."""
    src = tmp_path / "broken.cpp"
    src.write_text("int main() { not valid c++ }\n", encoding="utf-8")

    result = toolchain.execute(src, build_dir=tmp_path / "build", timeout=60)
    assert result.exit_code != 0
    assert result.compiled is False
    # Note: on MSVC the diagnostic does not currently land in stderr /
    # compile_error — see the open follow-up to surface cl.exe output to
    # the user. So this assertion intentionally only checks the contract
    # bits the toolchain promises today: failed exit + compiled=False.


def test_execute_requires_build_dir(toolchain, tmp_path):
    """No build_dir -> compile_error rather than crashing on None."""
    src = tmp_path / "x.cpp"
    src.write_text("int main() { return 0; }\n", encoding="utf-8")

    result = toolchain.execute(src, build_dir=None, timeout=10)
    assert result.exit_code == 1
    assert "build_dir" in result.stderr


def test_execute_reports_missing_compiler(toolchain, tmp_path, monkeypatch):
    """No compiler available -> a clean error string, not an unhandled raise."""
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.shutil.which",
                        lambda name: None)
    monkeypatch.setattr("bytedojo.core.toolchains.cpp.find_msvc_vcvars",
                        lambda: None)

    src = tmp_path / "x.cpp"
    src.write_text("int main() { return 0; }\n", encoding="utf-8")

    result = toolchain.execute(src, build_dir=tmp_path / "build", timeout=10)
    assert result.exit_code == 1
    assert "No C++ compiler" in result.stderr
