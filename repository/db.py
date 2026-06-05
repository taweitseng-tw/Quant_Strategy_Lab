"""SQLite database connection manager for Quant Strategy Lab projects."""

from __future__ import annotations

import sqlite3
from pathlib import Path


DB_FILENAME = "project.sqlite"

# Minimal MVP schema — projects + datasets tables (PRD §15.1–15.2).
# root_path is UNIQUE to prevent duplicate project rows for the same folder.
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    root_path   TEXT    NOT NULL UNIQUE,
    description TEXT    NOT NULL DEFAULT '',
    version     TEXT    NOT NULL DEFAULT '0.0.1',
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS datasets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER DEFAULT NULL,
    name            TEXT    NOT NULL,
    symbol          TEXT    NOT NULL DEFAULT '',
    timeframe       TEXT    NOT NULL DEFAULT '',
    source_type     TEXT    NOT NULL DEFAULT 'csv',
    source_path     TEXT    NOT NULL DEFAULT '',
    normalized_path TEXT    NOT NULL DEFAULT '',
    row_count       INTEGER NOT NULL DEFAULT 0,
    start_datetime  TEXT    NOT NULL DEFAULT '',
    end_datetime    TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS strategies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER DEFAULT NULL,
    name            TEXT    NOT NULL,
    strategy_json   TEXT    NOT NULL,
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL
);
"""


class DatabaseManager:
    """Manages a single project SQLite database connection.

    Uses WAL journal mode.  On close, runs a TRUNCATE checkpoint so that
    WAL/SHM sidecar files are cleaned up — this is especially important on
    Windows where open file handles can block directory deletion.
    """

    def __init__(self, project_dir: Path | str) -> None:
        self._db_path: Path | str
        if str(project_dir) == ":memory:":
            self._db_path = ":memory:"
        else:
            self._db_path = Path(project_dir) / DB_FILENAME
        self._conn: sqlite3.Connection | None = None

    @property
    def db_path(self) -> Path | str:
        return self._db_path

    def initialize(self) -> None:
        """Create (or open) the database and ensure the schema exists."""
        self._conn = sqlite3.connect(self._db_path if self._db_path == ":memory:" else str(self._db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not initialized — call initialize() first.")
        return self._conn

    def close(self) -> None:
        """Close the connection after running a TRUNCATE checkpoint.

        The TRUNCATE checkpoint flushes the WAL into the main database file
        and removes the -wal and -shm sidecar files, allowing the parent
        directory to be deleted cleanly on Windows.
        """
        if self._conn is not None:
            try:
                self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception:
                pass  # Best-effort — connection may already be unusable.
            self._conn.close()
            self._conn = None
