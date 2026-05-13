"""Tests for the PythonToolchain.

Python is always available (it's the interpreter running these tests), so
these are real-subprocess tests against `tmp_path` files. No mocking.
"""

import sys

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.python import PythonToolchain


# --------------------------------------------------------------------------- #
# detect                                                                      #
# --------------------------------------------------------------------------- #

@pytest.fixture
def toolchain() -> PythonToolchain:
    return PythonToolchain()


def test_detect_always_finds_python(toolchain):
    """Python toolchain uses sys.executable — detection is trivially true."""
    status = toolchain.detect()
    assert status.found is True
    assert status.language is CodeLanguage.PYTHON
    assert status.missing == []


def test_detect_records_interpreter_path(toolchain):
    """The resolved path matches the interpreter we're running on."""
    status = toolchain.detect()
    assert status.paths["python"] == sys.executable


def test_detect_records_version_string(toolchain):
    """Version is a dotted X.Y.Z string matching sys.version_info."""
    status = toolchain.detect()
    info = sys.version_info
    assert status.version == f"{info.major}.{info.minor}.{info.micro}"


# --------------------------------------------------------------------------- #
# execute                                                                     #
# --------------------------------------------------------------------------- #

def test_execute_captures_stdout(toolchain, tmp_path):
    script = tmp_path / "hello.py"
    script.write_text('print("hello")\n', encoding="utf-8")

    result = toolchain.execute(script, timeout=10)
    assert result.exit_code == 0
    assert result.stdout.strip() == "hello"
    assert result.stderr == ""
    assert result.timed_out is False
    assert result.language == "python3"
    assert result.file_path == str(script)


def test_execute_captures_nonzero_exit_and_stderr(toolchain, tmp_path):
    script = tmp_path / "boom.py"
    script.write_text("import sys; sys.stderr.write('nope'); sys.exit(3)\n",
                      encoding="utf-8")

    result = toolchain.execute(script, timeout=10)
    assert result.exit_code == 3
    assert result.stdout == ""
    assert "nope" in result.stderr


def test_execute_times_out(toolchain, tmp_path):
    """A script that sleeps longer than the timeout returns timed_out=True."""
    script = tmp_path / "slow.py"
    script.write_text("import time; time.sleep(5)\n", encoding="utf-8")

    result = toolchain.execute(script, timeout=1)
    assert result.timed_out is True
    assert result.exit_code == 1
    assert "timed out" in result.stderr.lower()


def test_execute_runs_in_source_parent_dir(toolchain, tmp_path):
    """cwd is the source file's parent so sibling imports resolve."""
    sibling = tmp_path / "sibling.py"
    sibling.write_text("VALUE = 42\n", encoding="utf-8")
    script = tmp_path / "main.py"
    script.write_text("import sibling; print(sibling.VALUE)\n", encoding="utf-8")

    result = toolchain.execute(script, timeout=10)
    assert result.exit_code == 0
    assert result.stdout.strip() == "42"


def test_execute_ignores_build_dir(toolchain, tmp_path):
    """Python doesn't compile; passing build_dir is accepted but inert."""
    script = tmp_path / "x.py"
    script.write_text('print("ok")\n', encoding="utf-8")
    build = tmp_path / "build"

    result = toolchain.execute(script, build_dir=build, timeout=10)
    assert result.exit_code == 0
    assert result.compiled is False
    # Python toolchain should not have created build/ as a side effect.
    assert not build.exists()
