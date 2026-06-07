"""Tests for dataset snapshot_hash schema migration — Task 060G-Impl."""

from __future__ import annotations

import pytest

from repository.db import (
    DatabaseManager,
    ensure_dataset_snapshot_hash_column,
)


# ---------------------------------------------------------------------------
# New in-memory DB includes snapshot_hash column
# ---------------------------------------------------------------------------


def test_new_db_has_snapshot_hash_column():
    """A new in-memory DB must have the snapshot_hash column after initialize()."""
    db = DatabaseManager(":memory:")
    db.initialize()
    conn = db.connection

    cursor = conn.execute("PRAGMA table_info(datasets)")
    columns = {row["name"] for row in cursor.fetchall()}
    assert "snapshot_hash" in columns, (
        "snapshot_hash column missing from new database"
    )
    db.close()


# ---------------------------------------------------------------------------
# Migration helper is idempotent
# ---------------------------------------------------------------------------


def test_migration_helper_is_idempotent():
    """Calling ensure_dataset_snapshot_hash_column twice must not error."""
    db = DatabaseManager(":memory:")
    db.initialize()
    conn = db.connection

    # First call — column should exist from initialize()
    ensure_dataset_snapshot_hash_column(conn)
    # Second call — idempotent, must not raise
    ensure_dataset_snapshot_hash_column(conn)

    db.close()


# ---------------------------------------------------------------------------
# Old-style DB without the column is migrated
# ---------------------------------------------------------------------------


def test_old_db_without_column_is_migrated():
    """A DB created without the column must be migrated on initialize()."""
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    # Column must be absent before migration.
    cursor = conn.execute("PRAGMA table_info(datasets)")
    columns_before = {row[1] for row in cursor.fetchall()}
    assert "snapshot_hash" not in columns_before

    # Migrate.
    ensure_dataset_snapshot_hash_column(conn)

    cursor = conn.execute("PRAGMA table_info(datasets)")
    columns_after = {row[1] for row in cursor.fetchall()}
    assert "snapshot_hash" in columns_after, (
        "snapshot_hash column was not added by migration"
    )
    conn.close()


# ---------------------------------------------------------------------------
# Existing rows survive migration with snapshot_hash = ''
# ---------------------------------------------------------------------------


def test_existing_rows_survive_migration_with_default():
    """After migration, existing rows must have snapshot_hash = ''."""
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("INSERT INTO datasets (name, created_at) VALUES ('old-ds', '2024-01-01')")
    conn.commit()

    # Migrate.
    ensure_dataset_snapshot_hash_column(conn)

    row = conn.execute("SELECT * FROM datasets WHERE name='old-ds'").fetchone()
    assert row is not None
    assert row["snapshot_hash"] == "", (
        f"Existing row has snapshot_hash = {row['snapshot_hash']!r}, expected ''"
    )
    conn.close()


# ---------------------------------------------------------------------------
# DatabaseManager.initialize() migrates an on-disk old-style project.sqlite
# ---------------------------------------------------------------------------


def test_initialize_migrates_old_disk_project_db(tmp_path):
    """DatabaseManager.initialize() must migrate an existing project.sqlite on disk."""
    import sqlite3 as _s

    db_path = tmp_path / "project.sqlite"
    # Create an old-style database without snapshot_hash column.
    old = _s.connect(str(db_path))
    old.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    old.execute("INSERT INTO datasets (name, created_at) VALUES ('old-disk-row', '2024-01-01')")
    old.commit()
    old.close()

    # Now open with DatabaseManager.initialize().
    db = DatabaseManager(tmp_path)
    db.initialize()
    conn = db.connection

    cursor = conn.execute("PRAGMA table_info(datasets)")
    columns = {row["name"] for row in cursor.fetchall()}
    assert "snapshot_hash" in columns, (
        "snapshot_hash column missing after DatabaseManager.initialize()"
    )

    row = conn.execute(
        "SELECT * FROM datasets WHERE name='old-disk-row'"
    ).fetchone()
    assert row is not None, "Old row missing after migration"
    assert row["snapshot_hash"] == "", (
        f"Old row snapshot_hash = {row['snapshot_hash']!r}, expected ''"
    )
    db.close()


# ---------------------------------------------------------------------------
# Existing DatasetRepository.insert() works with new schema (column added)
# ---------------------------------------------------------------------------


def test_dataset_repo_insert_works_with_snapshot_hash_column():
    """DatasetRepository.insert() must work unchanged with the new column."""
    from repository.dataset_repo import DatasetRepository
    from core.models.dataset import DatasetMeta

    db = DatabaseManager(":memory:")
    db.initialize()

    repo = DatasetRepository(db)
    meta = DatasetMeta(
        name="test-ds", symbol="ES", timeframe="1min",
        source_type="csv", source_path="/src", normalized_path="/norm",
        row_count=100, start_datetime="2024-01-01", end_datetime="2024-01-02",
    )
    row_id = repo.insert(meta)
    assert row_id > 0

    row = db.connection.execute(
        "SELECT * FROM datasets WHERE name='test-ds'"
    ).fetchone()
    assert row is not None
    assert row["snapshot_hash"] == "", "New row must have default snapshot_hash=''"
    db.close()
