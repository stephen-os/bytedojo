"""Tests for the Toolchain base contract and result dataclasses."""

from pathlib import Path

import pytest

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.base import (
    DEFAULT_TIMEOUT_SECONDS,
    ExecutionResult,
    Toolchain,
    ToolchainStatus,
)


# --------------------------------------------------------------------------- #
# ToolchainStatus                                                             #
# --------------------------------------------------------------------------- #

def test_toolchain_status_minimal_defaults():
    s = ToolchainStatus(language=CodeLanguage.PYTHON, found=True)
    assert s.language is CodeLanguage.PYTHON
    assert s.found is True
    assert s.missing == []
    assert s.paths == {}
    assert s.version is None
    assert s.install_hint is None


def test_toolchain_status_records_missing_and_install_hint():
    s = ToolchainStatus(
        language=CodeLanguage.JAVA,
        found=False,
        missing=["javac", "java"],
        install_hint="winget install Microsoft.OpenJDK.21",
    )
    assert s.missing == ["javac", "java"]
    assert s.install_hint.startswith("winget install")


def test_toolchain_status_default_factories_are_independent_per_instance():
    """Regression: list/dict defaults must not share state across instances."""
    a = ToolchainStatus(language=CodeLanguage.PYTHON, found=True)
    b = ToolchainStatus(language=CodeLanguage.JAVA, found=True)
    a.missing.append("javac")
    a.paths["javac"] = "/usr/bin/javac"
    assert b.missing == []
    assert b.paths == {}


# --------------------------------------------------------------------------- #
# ExecutionResult                                                             #
# --------------------------------------------------------------------------- #

def test_execution_result_minimal_defaults():
    r = ExecutionResult(
        exit_code=0, stdout="hello\n", stderr="", timed_out=False,
        language="python3", file_path="/tmp/x.py",
    )
    assert r.exit_code == 0
    assert r.stdout == "hello\n"
    assert r.timed_out is False
    assert r.compiled is False         # default
    assert r.compile_error == ""       # default


def test_execution_result_records_compile_error():
    r = ExecutionResult(
        exit_code=1, stdout="", stderr="error: expected ';'", timed_out=False,
        language="cpp", file_path="/tmp/x.cpp",
        compiled=False, compile_error="error: expected ';'",
    )
    assert r.compiled is False
    assert "expected" in r.compile_error


# --------------------------------------------------------------------------- #
# Toolchain ABC                                                               #
# --------------------------------------------------------------------------- #

def test_toolchain_cannot_be_instantiated_directly():
    """Toolchain.detect and .execute are abstract; ABC blocks instantiation."""
    with pytest.raises(TypeError):
        Toolchain()


def test_toolchain_subclass_missing_methods_cannot_be_instantiated():
    class Partial(Toolchain):
        language = CodeLanguage.UNKNOWN
        # detect/execute not implemented

    with pytest.raises(TypeError):
        Partial()


def test_toolchain_complete_subclass_can_be_instantiated():
    class Complete(Toolchain):
        language = CodeLanguage.UNKNOWN

        def detect(self) -> ToolchainStatus:
            return ToolchainStatus(language=self.language, found=True)

        def execute(self, source_path: Path, *, build_dir=None, timeout: int = 1):
            return ExecutionResult(
                exit_code=0, stdout="", stderr="", timed_out=False,
                language=self.language.value, file_path=str(source_path),
            )

    instance = Complete()
    assert instance.detect().found is True


# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #

def test_default_timeout_is_five_minutes():
    assert DEFAULT_TIMEOUT_SECONDS == 300
