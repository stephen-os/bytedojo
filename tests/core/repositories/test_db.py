"""Tests for the schema bootstrap (_db)."""

import sqlite3

from bytedojo.core.repositories import _db
from bytedojo.core.repositories.config import ConfigRepository


def test_create_schema_creates_all_tables(tmp_path):
    path = tmp_path / "db.sqlite"
    _db.create_schema(path)
    conn = sqlite3.connect(path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    for expected in {"problems", "attempts", "reviews", "config"}:
        assert expected in tables


def test_create_schema_seeds_default_config(tmp_path):
    path = tmp_path / "db.sqlite"
    _db.create_schema(path)
    conn = _db.connect(path)
    config = ConfigRepository(conn)
    assert config.get("default_source") == "leetcode"
    assert config.get("initialized_at") is not None
    conn.close()


def test_create_schema_is_idempotent(tmp_path):
    """Re-running the bootstrap must not clobber existing data."""
    path = tmp_path / "db.sqlite"
    _db.create_schema(path)
    conn = _db.connect(path)
    ConfigRepository(conn).set("default_source", "other")
    conn.close()

    _db.create_schema(path)

    conn = _db.connect(path)
    assert ConfigRepository(conn).get("default_source") == "other"
    conn.close()


def test_connect_uses_row_factory(tmp_path):
    """Rows are sqlite3.Row instances (so dict(row) works in from_row)."""
    path = tmp_path / "db.sqlite"
    _db.create_schema(path)
    conn = _db.connect(path)
    row = conn.execute("SELECT 1 AS one, 2 AS two").fetchone()
    conn.close()
    assert dict(row) == {"one": 1, "two": 2}


def test_problems_status_defaults_to_ungraded(tmp_path):
    path = tmp_path / "db.sqlite"
    _db.create_schema(path)
    conn = sqlite3.connect(path)
    cols = {row[1]: row for row in conn.execute("PRAGMA table_info(problems)")}
    conn.close()
    assert "ungraded" in str(cols["status"][4])
