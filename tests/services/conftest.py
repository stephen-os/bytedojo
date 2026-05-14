"""Service-test fixture re-exports.

The Problem-seeding helpers (`make_problem`, `insert_registered_problem`)
and the `registered_problem` fixture were promoted to the top-level
`tests/conftest.py` so commands/ tests can use them too. Service test
files still import the helpers from here for backward compatibility.
"""

from tests.conftest import (    # noqa: F401 — re-exported for service tests
    insert_registered_problem,
    make_problem,
)
