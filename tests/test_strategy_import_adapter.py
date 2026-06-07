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
