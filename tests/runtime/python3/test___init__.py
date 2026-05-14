"""Tests for the runtime.python3 package marker."""

from pathlib import Path

from bytedojo.runtime import python3


def test_runtime_dir_points_at_this_package():
    """RUNTIME_DIR resolves to the on-disk runtime/python3/ directory."""
    assert python3.RUNTIME_DIR.is_dir()
    assert python3.RUNTIME_DIR.name == "python3"
    assert isinstance(python3.RUNTIME_DIR, Path)


def test_runtime_dir_holds_runner_and_converters():
    """The two source files TestService stages must exist under RUNTIME_DIR."""
    assert (python3.RUNTIME_DIR / "runner.py").exists()
    assert (python3.RUNTIME_DIR / "converters.py").exists()
