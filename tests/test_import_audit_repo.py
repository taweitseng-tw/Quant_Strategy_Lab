"""Tests for AuditLogRepositoryAdapter — Task 059W-Impl."""

from __future__ import annotations

import sqlite3
import pytest

from repository.db import DatabaseManager
from repository.import_audit_repo import (
    AuditLogRepositoryAdapter,
    ImportAuditLogDTO,
    AuditLogWriteError,
    AuditLogStatusError,
)


@pytest.fixture
def adapter() -> tuple[AuditLogRepositoryAdapter, DatabaseManager]:
    db = DatabaseManager(":memory:")
    db.initialize()
    conn = db.connection
    return AuditLogRepositoryAdapter(conn), db


# ---------------------------------------------------------------------------
# Successful failed-audit insert
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# DTO immutability
# ---------------------------------------------------------------------------


def test_dto_is_frozen():
    """ImportAuditLogDTO must be frozen and immutable."""
    dto = ImportAuditLogDTO(
        imported_at="2026-06-07T14:00:00Z",
        archive_version="1.0.0",
        experiment_name="Test",
        strategy_uid="strat-dto",
        archive_source="/src",
        manifest_hash="h",
        original_filename="s.json",
        conflict_policy_applied="REJECT",
        status="FAILED",
    )
    with pytest.raises(AttributeError):
        dto.status = "SUCCESS"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Successful failed-audit insert
# ---------------------------------------------------------------------------


def test_insert_failure_log_succeeds(adapter):
    """A valid failed-audit DTO must insert without error."""
    aud, db = adapter
    dto = ImportAuditLogDTO(
        imported_at="2026-06-07T14:00:00Z",
        archive_version="1.0.0",
        experiment_name="Exp Fail",
        strategy_uid="strat-999",
        archive_source="/src/archive",
        manifest_hash="abc123def456",
        original_filename="strat.json",
        conflict_policy_applied="REJECT",
        status="FAILED",
        error_message="Strategy 'strat-999' already exists.",
    )
    aud.insert_failure_log(dto)  # must not raise


# ---------------------------------------------------------------------------
# All DTO fields persisted exactly
# ---------------------------------------------------------------------------


def test_insert_failure_log_persists_all_fields(adapter):
    """All DTO fields (including archive_source and manifest_hash) must be persisted."""
    aud, db = adapter
    dto = ImportAuditLogDTO(
        imported_at="2026-06-07T14:01:00Z",
        archive_version="1.0.0",
        experiment_name="Exp Full",
        strategy_uid="strat-001",
        archive_source="/data/archives/test",
        manifest_hash="deadbeefcafe",
        original_filename="strategy.json",
        conflict_policy_applied="OVERWRITE",
        status="FAILED",
        error_message="Duplicate UID across archives.",
    )
    aud.insert_failure_log(dto)

    row = db.connection.execute(
        "SELECT * FROM ImportAuditLog WHERE strategy_uid='strat-001'"
    ).fetchone()
    assert row is not None
    assert row["imported_at"] == "2026-06-07T14:01:00Z"
    assert row["archive_version"] == "1.0.0"
    assert row["experiment_name"] == "Exp Full"
    assert row["strategy_uid"] == "strat-001"
    assert row["archive_source"] == "/data/archives/test"
    assert row["manifest_hash"] == "deadbeefcafe"
    assert row["original_filename"] == "strategy.json"
    assert row["conflict_policy_applied"] == "OVERWRITE"
    assert row["status"] == "FAILED"
    assert row["error_message"] == "Duplicate UID across archives."
    assert row["id"] is not None  # auto-generated PK


# ---------------------------------------------------------------------------
# Status guard — insert_failure_log rejects non-FAILED (domain guard)
# ---------------------------------------------------------------------------


def test_insert_success_status_rejected(adapter):
    """status='SUCCESS' must be rejected by domain guard before any DB insert."""
    aud, db = adapter
    dto = ImportAuditLogDTO(
        imported_at="2026-06-07T14:00:00Z",
        archive_version="1.0.0",
        experiment_name="Should Fail",
        strategy_uid="strat-good",
        archive_source="/src",
        manifest_hash="h0",
        original_filename="s.json",
        conflict_policy_applied="REJECT",
        status="SUCCESS",  # not allowed for this adapter
    )
    with pytest.raises(AuditLogStatusError, match="FAILED"):
        aud.insert_failure_log(dto)

    # Verify no row was inserted.
    cnt = db.connection.execute("SELECT COUNT(*) AS c FROM ImportAuditLog").fetchone()["c"]
    assert cnt == 0


# ---------------------------------------------------------------------------
# Schema constraints (policy) still enforced
# ---------------------------------------------------------------------------


def test_insert_invalid_policy_raises(adapter):
    """Invalid conflict_policy_applied must be rejected by CHECK constraint."""
    aud, db = adapter
    dto = ImportAuditLogDTO(
        imported_at="2026-06-07T14:00:00Z",
        archive_version="1.0.0",
        experiment_name="Bad Policy",
        strategy_uid="strat-pol",
        archive_source="/src",
        manifest_hash="h2",
        original_filename="s.json",
        conflict_policy_applied="MERGE",  # invalid
        status="FAILED",
    )
    with pytest.raises(AuditLogWriteError, match="CHECK constraint|IntegrityError"):
        aud.insert_failure_log(dto)


# ---------------------------------------------------------------------------
# Adapter wraps SQLite failures in AuditLogWriteError
# ---------------------------------------------------------------------------


def test_adapter_wraps_sqlite_error(adapter):
    """SQLite write failures must surface as AuditLogWriteError."""
    aud, db = adapter
    # Close the connection to force a write failure.
    db.connection.close()
    dto = ImportAuditLogDTO(
        imported_at="2026-06-07T14:00:00Z",
        archive_version="1.0.0",
        experiment_name="Closed DB",
        strategy_uid="strat-closed",
        archive_source="/src",
        manifest_hash="h3",
        original_filename="s.json",
        conflict_policy_applied="REJECT",
        status="FAILED",
    )
    with pytest.raises(AuditLogWriteError):
        aud.insert_failure_log(dto)


# ---------------------------------------------------------------------------
# No strategy/dataset/validation tables are modified
# ---------------------------------------------------------------------------


def test_adapter_does_not_touch_other_tables(adapter):
    """insert_failure_log must not create rows in strategy/dataset tables."""
    aud, db = adapter
    dto = ImportAuditLogDTO(
        imported_at="2026-06-07T14:00:00Z",
        archive_version="1.0.0",
        experiment_name="Isolated",
        strategy_uid="strat-iso",
        archive_source="/src",
        manifest_hash="h4",
        original_filename="s.json",
        conflict_policy_applied="REJECT",
        status="FAILED",
        error_message="Isolation test.",
    )
    aud.insert_failure_log(dto)

    # Query all other known tables — should be empty.
    for tbl in ("strategies", "datasets", "backtest_results", "build_tasks"):
        cursor = db.connection.execute(
            "SELECT COUNT(*) AS cnt FROM sqlite_master WHERE type='table' AND name=?",
            (tbl,),
        )
        if cursor.fetchone()["cnt"] > 0:
            cnt = db.connection.execute(f"SELECT COUNT(*) AS c FROM [{tbl}]").fetchone()["c"]
            assert cnt == 0, f"Table '{tbl}' has {cnt} rows — should be 0"
