"""Tests for the ImportAuditLog schema helper and constraints — Task 059U-Impl."""

from __future__ import annotations

import sqlite3
import pytest
from repository.db import DatabaseManager, ensure_import_audit_log_schema


def test_schema_creation_and_idempotency():
    """Verify table and indexes exist after helper execution, and it runs idempotently."""
    db = DatabaseManager(":memory:")
    db.initialize()
    conn = db.connection

    # 1. Verify table exists in sqlite_master
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ImportAuditLog'"
    )
    assert cursor.fetchone() is not None

    # 2. Verify indexes exist in sqlite_master
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ImportAuditLog'"
    )
    indexes = {row["name"] for row in cursor.fetchall()}
    assert "idx_import_audit_log_strategy_uid" in indexes
    assert "idx_import_audit_log_imported_at" in indexes

    # 3. Verify idempotency — calling the helper again must not raise any exceptions
    ensure_import_audit_log_schema(conn)

    # Clean up
    db.close()


def test_status_constraint():
    """Verify that only 'SUCCESS' and 'FAILED' statuses are allowed by the CHECK constraint."""
    db = DatabaseManager(":memory:")
    db.initialize()
    conn = db.connection

    # Valid status 'SUCCESS'
    conn.execute(
        "INSERT INTO ImportAuditLog ("
        "  imported_at, archive_version, experiment_name, strategy_uid, "
        "  archive_source, manifest_hash, original_filename, conflict_policy_applied, status"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "2026-06-07T12:00:00Z",
            "1.0.0",
            "Test Exp",
            "strat-001",
            "/src/archive",
            "hash123",
            "strat.json",
            "REJECT",
            "SUCCESS",
        ),
    )
    conn.commit()

    # Invalid status 'PENDING' must fail the CHECK constraint
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO ImportAuditLog ("
            "  imported_at, archive_version, experiment_name, strategy_uid, "
            "  archive_source, manifest_hash, original_filename, conflict_policy_applied, status"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-06-07T12:00:00Z",
                "1.0.0",
                "Test Exp",
                "strat-001",
                "/src/archive",
                "hash123",
                "strat.json",
                "REJECT",
                "PENDING",
            ),
        )

    db.close()


def test_conflict_policy_constraint():
    """Verify that only allowed policies are accepted by the CHECK constraint."""
    db = DatabaseManager(":memory:")
    db.initialize()
    conn = db.connection

    # Valid conflict policy 'OVERWRITE'
    conn.execute(
        "INSERT INTO ImportAuditLog ("
        "  imported_at, archive_version, experiment_name, strategy_uid, "
        "  archive_source, manifest_hash, original_filename, conflict_policy_applied, status"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "2026-06-07T12:00:00Z",
            "1.0.0",
            "Test Exp",
            "strat-001",
            "/src/archive",
            "hash123",
            "strat.json",
            "OVERWRITE",
            "SUCCESS",
        ),
    )
    conn.commit()

    # Invalid conflict policy 'MERGE' must fail the CHECK constraint
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO ImportAuditLog ("
            "  imported_at, archive_version, experiment_name, strategy_uid, "
            "  archive_source, manifest_hash, original_filename, conflict_policy_applied, status"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-06-07T12:00:00Z",
                "1.0.0",
                "Test Exp",
                "strat-001",
                "/src/archive",
                "hash123",
                "strat.json",
                "MERGE",
                "SUCCESS",
            ),
        )

    db.close()


def test_insert_failed_audit_row():
    """Verify that a minimal failed audit log row can be inserted and queried successfully."""
    db = DatabaseManager(":memory:")
    db.initialize()
    conn = db.connection

    # Insert a failed log with error message
    conn.execute(
        "INSERT INTO ImportAuditLog ("
        "  imported_at, archive_version, experiment_name, strategy_uid, "
        "  archive_source, manifest_hash, original_filename, conflict_policy_applied, status, error_message"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "2026-06-07T13:40:00Z",
            "1.0.0",
            "Exp Fail",
            "strat-001",
            "/src/archive",
            "hash123",
            "strat.json",
            "REJECT",
            "FAILED",
            "DuplicateStrategyImportError: Strategy 'strat-001' already exists.",
        ),
    )
    conn.commit()

    # Query and assert details
    row = conn.execute("SELECT * FROM ImportAuditLog WHERE status='FAILED'").fetchone()
    assert row is not None
    assert row["strategy_uid"] == "strat-001"
    assert row["archive_source"] == "/src/archive"
    assert row["manifest_hash"] == "hash123"
    assert row["conflict_policy_applied"] == "REJECT"
    assert row["status"] == "FAILED"
    assert "already exists" in row["error_message"]

    db.close()
