"""
Pytest configuration and shared fixtures for ByteDojo tests.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def runner():
    """Fixture providing a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Fixture providing a temporary directory that gets cleaned up."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def isolated_filesystem():
    """
    Fixture providing an isolated filesystem for testing.
    Changes to the filesystem in tests won't affect the real system.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield Path.cwd()


@pytest.fixture(autouse=True)
def setup_logger():
    """
    Fixture that automatically sets up the logger before each test.
    This ensures get_logger() doesn't fail in tests.
    """
    from bytedojo.core.logger import setup_logger as _setup_logger
    _setup_logger(debug=False)
    yield
    # Cleanup happens automatically