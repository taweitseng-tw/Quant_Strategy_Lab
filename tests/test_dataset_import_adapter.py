"""Tests for DatasetRepoAdapter — Task 060I-Impl."""

from __future__ import annotations

import sqlite3
import pytest

from repository.db import DatabaseManager
from repository.dataset_import_adapter import (
    ImportDatasetDTO,
    DatasetRepoAdapter,
    DatasetRepoAdapterError,
    DuplicateDatasetError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def adapter_post_migration() -> tuple[DatasetRepoAdapter, DatabaseManager]:
    """Post-migration adapter with snapshot_hash column present."""
    db = DatabaseManager(":memory:")
    db.initialize()
    conn = db.connection
    return DatasetRepoAdapter(conn), db


@pytest.fixture
def adapter_old_db() -> tuple[DatasetRepoAdapter, DatabaseManager]:
    """Old-DB adapter without snapshot_hash column."""
    db = DatabaseManager(":memory:")
    # initialize() adds snapshot_hash — we bypass and create our own schema.
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER DEFAULT NULL,
            name TEXT NOT NULL,
            symbol TEXT NOT NULL DEFAULT '',
            timeframe TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT 'csv',
            source_path TEXT NOT NULL DEFAULT '',
            normalized_path TEXT NOT NULL DEFAULT '',
            row_count INTEGER NOT NULL DEFAULT 0,
            start_datetime TEXT NOT NULL DEFAULT '',
            end_datetime TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    # Wrap in a fake DatabaseManager so caller can close() later.
    class _FakeDB(DatabaseManager):
        def __init__(self, conn) -> None:
            self._conn = conn

        def close(self) -> None:
            conn.close()

    return DatasetRepoAdapter(conn), _FakeDB(conn)


# ---------------------------------------------------------------------------
# Success
# ---------------------------------------------------------------------------


def test_insert_succeeds_post_migration(adapter_post_migration):
    """Insert must succeed on post-migration schema."""
    aud, db = adapter_post_migration
    dto = ImportDatasetDTO(
        name="ds-1", symbol="ES", timeframe="1min",
        snapshot_hash="abc", source_path="/src",
    )
    row_id = aud.insert_dataset(dto)
    assert row_id > 0


def test_insert_succeeds_old_db(adapter_old_db):
    """Insert must succeed on old-DB schema without snapshot_hash column."""
    aud, db = adapter_old_db
    dto = ImportDatasetDTO(
        name="ds-old", symbol="CL", timeframe="5min", source_path="/src",
    )
    row_id = aud.insert_dataset(dto)
    assert row_id > 0

    # Verify snapshot_hash column was not created.
    row = db.connection.execute("SELECT * FROM datasets WHERE name='ds-old'").fetchone()
    assert row is not None
    # Row keys on old DB should not include snapshot_hash.
    assert "snapshot_hash" not in dict(row).keys()


# ---------------------------------------------------------------------------
# Duplicate reject — post-migration
# ---------------------------------------------------------------------------


def test_duplicate_by_hash_rejected(adapter_post_migration):
    """Duplicate non-empty snapshot_hash must be rejected."""
    aud, db = adapter_post_migration
    dto1 = ImportDatasetDTO(
        name="ds-dup", symbol="ES", timeframe="1min",
        snapshot_hash="deadbeef", source_path="/src1",
    )
    aud.insert_dataset(dto1)

    dto2 = ImportDatasetDTO(
        name="ds-dup-2", symbol="NQ", timeframe="5min",
        snapshot_hash="deadbeef", source_path="/src2",
    )
    with pytest.raises(DuplicateDatasetError, match="already exists"):
        aud.insert_dataset(dto2)


def test_empty_hash_falls_back_to_fallback(adapter_post_migration):
    """Empty snapshot_hash on post-migration schema must use fallback dedup."""
    aud, db = adapter_post_migration
    dto1 = ImportDatasetDTO(
        name="ds-fb", symbol="ES", timeframe="1min",
        snapshot_hash="", source_path="/src",
    )
    aud.insert_dataset(dto1)

    dto2 = ImportDatasetDTO(
        name="ds-fb-2", symbol="ES", timeframe="1min",
        snapshot_hash="", source_path="/src",
    )
    with pytest.raises(DuplicateDatasetError, match="already exists"):
        aud.insert_dataset(dto2)


# ---------------------------------------------------------------------------
# Duplicate reject — old-DB
# ---------------------------------------------------------------------------


def test_duplicate_by_fallback_rejected_old_db(adapter_old_db):
    """Duplicate by fallback key must be rejected on old-DB schema."""
    aud, db = adapter_old_db
    dto1 = ImportDatasetDTO(
        name="ds-fb-old", symbol="ES", timeframe="1min", source_path="/src",
    )
    aud.insert_dataset(dto1)

    dto2 = ImportDatasetDTO(
        name="ds-fb-old-2", symbol="ES", timeframe="1min", source_path="/src",
    )
    with pytest.raises(DuplicateDatasetError, match="already exists"):
        aud.insert_dataset(dto2)


# ---------------------------------------------------------------------------
# No-commit
# ---------------------------------------------------------------------------


def test_no_commit_caller_can_commit(adapter_post_migration):
    """insert_dataset_no_commit must let caller commit."""
    aud, db = adapter_post_migration
    dto = ImportDatasetDTO(
        name="ds-nc-commit", symbol="ES", timeframe="1min",
    )
    aud.insert_dataset_no_commit(dto)
    db.connection.commit()

    row = db.connection.execute(
        "SELECT * FROM datasets WHERE name='ds-nc-commit'"
    ).fetchone()
    assert row is not None


def test_no_commit_caller_can_rollback(adapter_post_migration):
    """insert_dataset_no_commit must not commit — caller can rollback."""
    aud, db = adapter_post_migration
    dto = ImportDatasetDTO(
        name="ds-nc-rollback", symbol="ES", timeframe="1min",
    )
    aud.insert_dataset_no_commit(dto)
    db.connection.rollback()

    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM datasets WHERE name='ds-nc-rollback'"
    ).fetchone()["c"]
    assert cnt == 0


# ---------------------------------------------------------------------------
# Rollback scope
# ---------------------------------------------------------------------------


def test_sqlite_insert_failure_triggers_rollback(adapter_post_migration):
    """SQLite INSERT failure must rollback caller's prior uncommitted data."""
    aud, db = adapter_post_migration
    # Stage a prior uncommitted row.
    dto_prior = ImportDatasetDTO(
        name="Prior Row", symbol="ES", timeframe="1min",
    )
    aud.insert_dataset_no_commit(dto_prior)

    # Break INSERT SQL.
    original_sql = aud._INSERT_SQL_POST
    aud._INSERT_SQL_POST = (
        "INSERT INTO no_such_table "
        "(project_id, name, symbol, timeframe, source_type, source_path, "
        "normalized_path, row_count, start_datetime, end_datetime, "
        "snapshot_hash, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    try:
        dto_bad = ImportDatasetDTO(
            name="Will Fail", symbol="ES", timeframe="1min",
            snapshot_hash="h1",
        )
        with pytest.raises(DatasetRepoAdapterError, match="Failed to insert"):
            aud.insert_dataset(dto_bad)
    finally:
        aud._INSERT_SQL_POST = original_sql

    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM datasets WHERE name='Prior Row'"
    ).fetchone()["c"]
    assert cnt == 0, "Prior row was NOT rolled back after INSERT failure"


def test_validation_error_does_not_rollback(adapter_post_migration):
    """Validation error must NOT rollback caller's prior uncommitted data."""
    aud, db = adapter_post_migration
    dto_prior = ImportDatasetDTO(
        name="Prior Valid", symbol="ES", timeframe="1min",
    )
    aud.insert_dataset_no_commit(dto_prior)

    dto_bad = ImportDatasetDTO(
        name="   ", symbol="ES", timeframe="1min",
    )
    with pytest.raises(DatasetRepoAdapterError, match="name is required"):
        aud.insert_dataset(dto_bad)

    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM datasets WHERE name='Prior Valid'"
    ).fetchone()["c"]
    assert cnt == 1, "Prior row was rolled back on validation error"


def test_duplicate_error_does_not_rollback(adapter_post_migration):
    """DuplicateDatasetError must NOT rollback caller's prior uncommitted data."""
    aud, db = adapter_post_migration
    # Commit a source row.
    dto_source = ImportDatasetDTO(
        name="Source", symbol="ES", timeframe="1min",
        snapshot_hash="dup-no-rollback", source_path="/src-src",
    )
    aud.insert_dataset(dto_source)

    # Stage a prior uncommitted row.
    dto_prior = ImportDatasetDTO(
        name="Prior Dup", symbol="CL", timeframe="5min",
    )
    aud.insert_dataset_no_commit(dto_prior)

    # Trigger duplicate error.
    dto_dup = ImportDatasetDTO(
        name="Duplicate", symbol="XX", timeframe="1min",
        snapshot_hash="dup-no-rollback", source_path="/src-dup",
    )
    with pytest.raises(DuplicateDatasetError):
        aud.insert_dataset(dto_dup)

    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM datasets WHERE name='Prior Dup'"
    ).fetchone()["c"]
    assert cnt == 1, "Prior row was rolled back on duplicate error"


# ---------------------------------------------------------------------------
# Boundary
# ---------------------------------------------------------------------------


def test_no_other_tables_modified(adapter_post_migration):
    """insert_dataset must not modify strategy/validation/audit tables."""
    aud, db = adapter_post_migration
    dto = ImportDatasetDTO(
        name="ds-iso", symbol="ES", timeframe="1min",
    )
    aud.insert_dataset(dto)

    for tbl in ("strategies", "backtest_results", "build_tasks", "ImportAuditLog"):
        cursor = db.connection.execute(
            "SELECT COUNT(*) AS cnt FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (tbl,),
        )
        if cursor.fetchone()["cnt"] > 0:
            cnt = db.connection.execute(f"SELECT COUNT(*) AS c FROM [{tbl}]").fetchone()["c"]
            assert cnt == 0, f"Table '{tbl}' has {cnt} rows"
