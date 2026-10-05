"""
ConfigRepository — key/value bookkeeping in the .dojo database.

Holds internal repository state (e.g. initialized_at). User-facing
preferences live in .dojo/settings.json via SettingsManager.
"""

import sqlite3
from typing import Optional


class ConfigRepository:
    """Raw-sqlite persistence for config key/value pairs."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """The value for `key`, or `default` when unset."""
        row = self._conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default

    def set(self, key: str, value: str) -> None:
        """Set (or overwrite) a config value."""
        self._conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
        self._conn.commit()

    def all(self) -> dict[str, str]:
        """Every config key/value pair."""
        rows = self._conn.execute("SELECT key, value FROM config").fetchall()
        return {row[0]: row[1] for row in rows}
