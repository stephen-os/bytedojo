"""
Shared pytest fixtures for the bytedojo test suite.

`get_logger()` raises if the global logger hasn't been initialised yet.
That contract is right for the CLI (main() always calls setup_logger first)
but inconvenient for unit tests, which import bytedojo modules directly.
The autouse fixture below initialises the logger once per session so any
test that ends up calling get_logger() works without ceremony.
"""

import pytest

from bytedojo.core.logger import setup_logger


@pytest.fixture(scope="session", autouse=True)
def _initialise_logger():
    setup_logger(debug=False)
