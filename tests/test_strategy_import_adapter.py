"""Tests for StrategyRepoAdapter insert-only slice — Task 059Y-Fix."""

from __future__ import annotations

import json
import pytest

from repository.db import DatabaseManager
from repository.strategy_import_adapter import (
    ImportStrategyDTO,
    StrategyRepoAdapter,
    DuplicateStrategyUIDError,
    StrategyRepoAdapterError,
)


@pytest.fixture
def adapter() -> tuple[StrategyRepoAdapter, DatabaseManager]:
    db = DatabaseManager(":memory:")
    db.initialize()
    conn = db.connection
    return StrategyRepoAdapter(conn), db


def _strategy_json(strategy_uid: str, **extra) -> str:
    """Helper: produce a valid strategy JSON string."""
    data = {"strategy_uid": strategy_uid, "name": "test", **extra}
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Successful strategy insert
# ---------------------------------------------------------------------------


def test_insert_strategy_succeeds(adapter):
    """A valid DTO must insert without error and return a positive row id."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="My Display Name",
        strategy_json=_strategy_json("strat-001", conditions=[]),
        strategy_uid="strat-001",
    )
    row_id = aud.insert_strategy(dto)
    assert row_id > 0

    row = db.connection.execute(
        "SELECT * FROM strategies WHERE name='My Display Name'"
    ).fetchone()
    assert row is not None
    assert row["name"] == "My Display Name"
    assert row["strategy_json"] == _strategy_json("strat-001", conditions=[])


# ---------------------------------------------------------------------------
# Duplicate UID rejected — same UID, different name
# ---------------------------------------------------------------------------


def test_duplicate_uid_rejected_different_name(adapter):
    """Same UID, different display name must be rejected."""
    aud, db = adapter
    dto1 = ImportStrategyDTO(
        name="First Name",
        strategy_json=_strategy_json("strat-dup", version=1),
        strategy_uid="strat-dup",
    )
    aud.insert_strategy(dto1)

    dto2 = ImportStrategyDTO(
        name="Second Name",
        strategy_json=_strategy_json("strat-dup", version=2),
        strategy_uid="strat-dup",
    )
    with pytest.raises(DuplicateStrategyUIDError, match="already exists"):
        aud.insert_strategy(dto2)

    # Original row must be unchanged.
    rows = list(db.connection.execute(
        "SELECT name, strategy_json FROM strategies ORDER BY id"
    ).fetchall())
    assert len(rows) == 1
    assert rows[0]["name"] == "First Name"


# ---------------------------------------------------------------------------
# Persisted fields exactly
# ---------------------------------------------------------------------------


def test_insert_strategy_persists_all_fields(adapter):
    """All DTO fields must be persisted exactly."""
    aud, db = adapter
    payload = _strategy_json("strat-full", params={"a": 1})
    dto = ImportStrategyDTO(
        name="Full Strat",
        strategy_json=payload,
        strategy_uid="strat-full",
        project_id=1,
    )
    row_id = aud.insert_strategy(dto)
    assert row_id > 0

    row = db.connection.execute(
        "SELECT * FROM strategies WHERE name='Full Strat'"
    ).fetchone()
    assert row["name"] == "Full Strat"
    assert row["strategy_json"] == payload
    assert row["project_id"] == 1
    assert row["created_at"] is not None
    assert row["updated_at"] is not None


# ---------------------------------------------------------------------------
# Missing / empty strategy_uid rejected
# ---------------------------------------------------------------------------


def test_empty_strategy_uid_rejected(adapter):
    """Empty strategy_uid must be rejected before any DB insert."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="No UID",
        strategy_json=_strategy_json("real-uid"),
        strategy_uid="   ",
    )
    with pytest.raises(StrategyRepoAdapterError, match="strategy_uid.*required"):
        aud.insert_strategy(dto)

    cnt = db.connection.execute("SELECT COUNT(*) AS c FROM strategies").fetchone()["c"]
    assert cnt == 0


# ---------------------------------------------------------------------------
# strategy_uid mismatch: dto.uid != payload.uid
# ---------------------------------------------------------------------------


def test_strategy_uid_mismatch_rejected(adapter):
    """dto.strategy_uid != strategy_json['strategy_uid'] must be rejected."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="Mismatch",
        strategy_json=_strategy_json("payload-uid"),
        strategy_uid="dto-uid",
    )
    with pytest.raises(StrategyRepoAdapterError, match="does not match"):
        aud.insert_strategy(dto)

    cnt = db.connection.execute("SELECT COUNT(*) AS c FROM strategies").fetchone()["c"]
    assert cnt == 0


# ---------------------------------------------------------------------------
# Invalid JSON payload rejected
# ---------------------------------------------------------------------------


def test_invalid_json_rejected(adapter):
    """Invalid JSON string as strategy_json must be rejected."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="Bad JSON",
        strategy_json="this is not json",
        strategy_uid="bad-json",
    )
    with pytest.raises(StrategyRepoAdapterError, match="not valid JSON"):
        aud.insert_strategy(dto)

    cnt = db.connection.execute("SELECT COUNT(*) AS c FROM strategies").fetchone()["c"]
    assert cnt == 0


def test_non_dict_json_rejected(adapter):
    """Non-dict JSON (e.g. list) must be rejected."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="Array",
        strategy_json='["a", 1]',
        strategy_uid="array-uid",
    )
    with pytest.raises(StrategyRepoAdapterError, match="must be a JSON object"):
        aud.insert_strategy(dto)

    cnt = db.connection.execute("SELECT COUNT(*) AS c FROM strategies").fetchone()["c"]
    assert cnt == 0


# ---------------------------------------------------------------------------
# Missing strategy_uid in payload
# ---------------------------------------------------------------------------


def test_json_missing_payload_uid_rejected(adapter):
    """strategy_json without 'strategy_uid' key must be rejected."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="No Payload UID",
        strategy_json='{"name":"test"}',
        strategy_uid="no-payload-uid",
    )
    with pytest.raises(StrategyRepoAdapterError, match="missing required field"):
        aud.insert_strategy(dto)

    cnt = db.connection.execute("SELECT COUNT(*) AS c FROM strategies").fetchone()["c"]
    assert cnt == 0


# ---------------------------------------------------------------------------
# No dataset/validation/audit tables modified
# ---------------------------------------------------------------------------


def test_no_other_tables_touched(adapter):
    """insert_strategy must not modify dataset, validation, or audit tables."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="Isolated",
        strategy_json=_strategy_json("strat-iso"),
        strategy_uid="strat-iso",
    )
    aud.insert_strategy(dto)

    for tbl in ("datasets", "backtest_results", "build_tasks", "ImportAuditLog"):
        cursor = db.connection.execute(
            "SELECT COUNT(*) AS cnt FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (tbl,),
        )
        if cursor.fetchone()["cnt"] > 0:
            cnt = db.connection.execute(f"SELECT COUNT(*) AS c FROM [{tbl}]").fetchone()["c"]
            assert cnt == 0, f"Table '{tbl}' has {cnt} rows — should be 0"


# ---------------------------------------------------------------------------
# Legacy tests: empty name, empty JSON, None JSON still rejected
# ---------------------------------------------------------------------------


def test_empty_name_rejected(adapter):
    """Empty name must raise StrategyRepoAdapterError."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="   ",
        strategy_json=_strategy_json("empty-name"),
        strategy_uid="empty-name",
    )
    with pytest.raises(StrategyRepoAdapterError, match="name is required"):
        aud.insert_strategy(dto)


def test_empty_strategy_json_rejected(adapter):
    """Empty strategy_json must raise StrategyRepoAdapterError."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="strat-empty",
        strategy_json="   ",
        strategy_uid="empty-json",
    )
    with pytest.raises(StrategyRepoAdapterError, match="strategy_json.*required"):
        aud.insert_strategy(dto)


def test_none_strategy_json_rejected(adapter):
    """Empty string strategy_json must raise StrategyRepoAdapterError."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="strat-none",
        strategy_json="",
        strategy_uid="none-json",
    )
    with pytest.raises(StrategyRepoAdapterError, match="strategy_json.*required"):
        aud.insert_strategy(dto)


# ---------------------------------------------------------------------------
# insert_strategy_no_commit — caller-committed transaction
# ---------------------------------------------------------------------------


def test_no_commit_caller_can_rollback(adapter):
    """insert_strategy_no_commit must not commit — caller can rollback."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="Rollback Me",
        strategy_json=_strategy_json("strat-rollback"),
        strategy_uid="strat-rollback",
    )
    aud.insert_strategy_no_commit(dto)
    db.connection.rollback()

    # Verify nothing was committed.
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies WHERE name='Rollback Me'"
    ).fetchone()["c"]
    assert cnt == 0


def test_no_commit_caller_can_commit(adapter):
    """insert_strategy_no_commit must let caller commit successfully."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="Commit Me",
        strategy_json=_strategy_json("strat-commit"),
        strategy_uid="strat-commit",
    )
    aud.insert_strategy_no_commit(dto)
    db.connection.commit()

    row = db.connection.execute(
        "SELECT * FROM strategies WHERE name='Commit Me'"
    ).fetchone()
    assert row is not None
    assert row["name"] == "Commit Me"


def test_no_commit_duplicate_uid_raises_without_commit(adapter):
    """Duplicate UID via insert_strategy_no_commit must raise and not commit."""
    aud, db = adapter
    dto1 = ImportStrategyDTO(
        name="First",
        strategy_json=_strategy_json("strat-nc-dup"),
        strategy_uid="strat-nc-dup",
    )
    aud.insert_strategy_no_commit(dto1)
    db.connection.commit()

    dto2 = ImportStrategyDTO(
        name="Second",
        strategy_json=_strategy_json("strat-nc-dup"),
        strategy_uid="strat-nc-dup",
    )
    with pytest.raises(DuplicateStrategyUIDError, match="already exists"):
        aud.insert_strategy_no_commit(dto2)
    db.connection.rollback()  # clean up the failed transaction state

    # Only the first row exists.
    rows = list(db.connection.execute(
        "SELECT name FROM strategies ORDER BY id"
    ).fetchall())
    assert len(rows) == 1
    assert rows[0]["name"] == "First"


def test_insert_strategy_rollback_on_sqlite_failure(adapter):
    """insert_strategy must rollback on SQLite INSERT execute failure.

    Strategy: stage an uncommitted row via no_commit, then break the
    INSERT SQL so the execute() fails inside _insert_strategy_core.
    The rollback must clean up the prior uncommitted row.
    """
    aud, db = adapter
    # Stage a prior uncommitted row via no_commit.
    dto_prior = ImportStrategyDTO(
        name="Prior Row",
        strategy_json=_strategy_json("strat-rollback-prior"),
        strategy_uid="strat-rollback-prior",
    )
    aud.insert_strategy_no_commit(dto_prior)

    # Break the INSERT SQL to force execute() failure.
    original_sql = aud._INSERT_SQL
    aud._INSERT_SQL = (
        "INSERT INTO no_such_table "
        "(project_id, name, strategy_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)"
    )
    try:
        dto_bad = ImportStrategyDTO(
            name="Will Fail",
            strategy_json=_strategy_json("strat-fail"),
            strategy_uid="strat-fail",
        )
        with pytest.raises(StrategyRepoAdapterError, match="Failed to insert"):
            aud.insert_strategy(dto_bad)
    finally:
        aud._INSERT_SQL = original_sql

    # Prior uncommitted row must have been rolled back by the adapter.
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies WHERE name='Prior Row'"
    ).fetchone()["c"]
    assert cnt == 0, (
        "Prior uncommitted row was NOT rolled back after SQLite INSERT failure "
        "— the rollback branch inside insert_strategy() did not execute."
    )


def test_validation_error_does_not_rollback_caller_uncommitted(adapter):
    """Validation error must NOT rollback the caller's own uncommitted data.

    Flow: stage prior → validation error → check prior is STILL visible
    → caller rollback → check prior is gone.  This proves the adapter
    did not rollback (if it had, prior would already be invisible).
    """
    aud, db = adapter
    # Stage an uncommitted row.
    dto_prior = ImportStrategyDTO(
        name="Prior Uncommitted",
        strategy_json=_strategy_json("strat-prior"),
        strategy_uid="strat-prior",
    )
    aud.insert_strategy_no_commit(dto_prior)

    # Call insert_strategy with a validation error.
    dto_bad = ImportStrategyDTO(
        name="Bad UID",
        strategy_json=_strategy_json("real-uid"),
        strategy_uid="   ",  # empty → validation error before any SQL
    )
    with pytest.raises(StrategyRepoAdapterError, match="strategy_uid.*required"):
        aud.insert_strategy(dto_bad)

    # The prior uncommitted row must still be visible — adapter did NOT
    # rollback.  If the adapter had rolled back, the row would be gone now.
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies WHERE name='Prior Uncommitted'"
    ).fetchone()["c"]
    assert cnt == 1, (
        "Prior uncommitted row disappeared before caller rollback — "
        "the adapter incorrectly rolled back on a validation error."
    )

    # Caller rollback must clean it up.
    db.connection.rollback()
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies WHERE name='Prior Uncommitted'"
    ).fetchone()["c"]
    assert cnt == 0


def test_duplicate_uid_does_not_rollback_caller_uncommitted(adapter):
    """DuplicateUIDError must NOT rollback the caller's own uncommitted data.

    Flow: commit a source row → stage an uncommitted prior row →
    duplicate UID error → check prior is STILL visible →
    caller rollback → check prior is gone, source row still exists.
    This proves the adapter did not rollback on duplicate UID.
    """
    aud, db = adapter
    # First, commit a source row that will cause the duplicate.
    dto_source = ImportStrategyDTO(
        name="Source Row",
        strategy_json=_strategy_json("strat-dup-source"),
        strategy_uid="strat-dup-source",
    )
    aud.insert_strategy(dto_source)

    # Stage an uncommitted prior row via no_commit.
    dto_prior = ImportStrategyDTO(
        name="Prior Duplicate",
        strategy_json=_strategy_json("strat-dup-prior"),
        strategy_uid="strat-dup-prior",
    )
    aud.insert_strategy_no_commit(dto_prior)

    # Attempt duplicate via insert_strategy — must NOT rollback prior.
    dto_dup = ImportStrategyDTO(
        name="Second",
        strategy_json=_strategy_json("strat-dup-source"),
        strategy_uid="strat-dup-source",
    )
    with pytest.raises(DuplicateStrategyUIDError):
        aud.insert_strategy(dto_dup)

    # The prior uncommitted row must still be visible — adapter did NOT
    # rollback.  If the adapter had rolled back, prior would be gone now.
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies WHERE name='Prior Duplicate'"
    ).fetchone()["c"]
    assert cnt == 1, (
        "Prior uncommitted row disappeared before caller rollback — "
        "the adapter incorrectly rolled back on a DuplicateUIDError."
    )

    # Caller rollback must clean up the prior row only.
    db.connection.rollback()
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies WHERE name='Prior Duplicate'"
    ).fetchone()["c"]
    assert cnt == 0

    # The committed source row must still exist.
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies WHERE name='Source Row'"
    ).fetchone()["c"]
    assert cnt == 1, (
        "Committed source row disappeared — the duplicate error or rollback "
        "should not have affected it."
    )


def test_no_commit_does_not_touch_other_tables(adapter):
    """insert_strategy_no_commit must not modify other tables."""
    aud, db = adapter
    dto = ImportStrategyDTO(
        name="NoCommit Iso",
        strategy_json=_strategy_json("strat-nc-iso"),
        strategy_uid="strat-nc-iso",
    )
    aud.insert_strategy_no_commit(dto)
    db.connection.rollback()  # never committed

    for tbl in ("datasets", "backtest_results", "build_tasks", "ImportAuditLog"):
        cursor = db.connection.execute(
            "SELECT COUNT(*) AS cnt FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (tbl,),
        )
        if cursor.fetchone()["cnt"] > 0:
            cnt = db.connection.execute(f"SELECT COUNT(*) AS c FROM [{tbl}]").fetchone()["c"]
            assert cnt == 0, f"Table '{tbl}' has {cnt} rows — should be 0"
