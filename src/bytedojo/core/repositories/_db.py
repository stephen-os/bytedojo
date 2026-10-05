"""
Connection + schema bootstrap for the .dojo sqlite database.

The schema is created once by `dojo init`; the per-aggregate
repositories in this package assume it exists. Raw sqlite3, no ORM.

Versioning is flat (§7.1): an attempt's version is a monotonic ordinal
per (source, problem_id) — language is attempt metadata, not part of
the key. Problems are likewise unique per (source, problem_id); their
`language` / `file_path` columns describe the latest attempt.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    problem_id INTEGER NOT NULL,
    language TEXT NOT NULL DEFAULT 'python3',
    title TEXT NOT NULL,
    difficulty TEXT,
    description TEXT,
    file_path TEXT,
    status TEXT DEFAULT 'ungraded',
    last_graded TIMESTAMP,
    notes TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, problem_id)
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL DEFAULT 'leetcode',
    problem_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ungraded',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_count INTEGER DEFAULT 0,
    notes TEXT,
    UNIQUE(source, problem_id, version)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id INTEGER NOT NULL UNIQUE,
    next_review_date DATE NOT NULL,
    interval_days INTEGER DEFAULT 1,
    ease_factor REAL DEFAULT 2.5,
    repetitions INTEGER DEFAULT 0,
    FOREIGN KEY (problem_id) REFERENCES problems(id)
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a connection with dict-style row access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(db_path: Path) -> None:
    """Create all tables and seed default config values."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_SCHEMA)
        conn.execute(
            """
            INSERT OR IGNORE INTO config (key, value) VALUES
            ('initialized_at', ?),
            ('default_source', 'leetcode')
            """,
            (datetime.now().isoformat(),),
        )
        conn.commit()
    finally:
        conn.close()
