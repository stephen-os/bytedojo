"""
Shared pytest fixtures for the bytedojo test suite.

- `_initialise_logger` (session, autouse): sets up the global logger so
  `get_logger()` works for direct-import tests. Production callers always
  go through main()'s explicit setup_logger; this fills the gap for tests.

- `repo` (function): builds a fresh, fully-initialised Repository at
  tmp_path. Each test gets its own sqlite DB + .dojo / problems / build
  directories, so service tests can exercise real DB writes and file
  placement without mocks.
"""

import pytest

from bytedojo.core.logger import setup_logger
from bytedojo.core.repository import Repository


@pytest.fixture(scope="session", autouse=True)
def _initialise_logger():
    setup_logger(debug=False)


@pytest.fixture
def repo(tmp_path) -> Repository:
    """Fresh Repository at tmp_path — real sqlite, real filesystem layout."""
    return Repository.create(tmp_path)
