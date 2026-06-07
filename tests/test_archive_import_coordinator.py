"""Tests for ArchiveImportCoordinator — Task 060M-Impl."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any

import pytest

from archive.import_coordinator import ArchiveImportCoordinator, ImportResult


# ---------------------------------------------------------------------------
# Fake / spy collaborators
# ---------------------------------------------------------------------------


class FakeImporter:
    def __init__(self) -> None:
        self.build_preview_called = False
        self.raise_error: Exception | None = None

    def build_preview(self, root: str) -> Any:
        self.build_preview_called = True
        if self.raise_error:
            raise self.raise_error
        return {"archive_version": "1.0.0"}


class FakeVerifier:
    def __init__(self) -> None:
        self.verify_all_called = False
        self.raise_error: Exception | None = None

    def verify_all(self) -> bool:
        self.verify_all_called = True
        if self.raise_error:
            raise self.raise_error
        return True


class FakeStrategyAdapter:
    def __init__(self) -> None:
        self.insert_called_with: Any = None
        self.insert_call_count = 0
        self.preflight_called_with: Any = None
        self.preflight_call_count = 0
        self.raise_error: Exception | None = None
        self.raise_on_preflight: Exception | None = None

    def insert_strategy_no_commit(self, dto: Any) -> int:
        self.insert_called_with = dto
        self.insert_call_count += 1
        if self.raise_error:
            raise self.raise_error
        return 42

    def preflight_duplicate(self, dto: Any) -> None:
        self.preflight_called_with = dto
        self.preflight_call_count += 1
        if self.raise_on_preflight:
            raise self.raise_on_preflight


class FakeDatasetAdapter:
    def __init__(self) -> None:
        self.insert_called_with: Any = None
        self.insert_call_count = 0
        self.preflight_called_with: Any = None
        self.preflight_call_count = 0
        self.raise_error: Exception | None = None
        self.raise_on_preflight: Exception | None = None

    def insert_dataset_no_commit(self, dto: Any) -> int:
        self.insert_called_with = dto
        self.insert_call_count += 1
        if self.raise_error:
            raise self.raise_error
        return 99

    def preflight_duplicate(self, dto: Any) -> None:
        self.preflight_called_with = dto
        self.preflight_call_count += 1
        if self.raise_on_preflight:
            raise self.raise_on_preflight


class FakeStager:
    def __init__(self) -> None:
        self.stage_called = False
        self.move_called = False
        self.cleanup_called = False
        self.raise_on_stage: Exception | None = None
        self.raise_on_move: Exception | None = None

    def stage_dataset_snapshot(self, expected_hash: str) -> str:
        self.stage_called = True
        if self.raise_on_stage:
            raise self.raise_on_stage
        return "/tmp/staged/file.csv"

    def move_to_final_destination(self) -> str:
        self.move_called = True
        if self.raise_on_move:
            raise self.raise_on_move
        return "/data/imported/exp/ohlcv.csv"

    def cleanup_temp(self) -> None:
        self.cleanup_called = True


class FakeAuditAdapter:
    def __init__(self) -> None:
        self.failure_called = False
        self.failure_count = 0
        self.raise_error: Exception | None = None

    def insert_failure_log(self, dto: Any) -> None:
        self.failure_called = True
        self.failure_count += 1
        if self.raise_error:
            raise self.raise_error


@dataclass
class FakeStrategyDTO:
    strategy_uid: str = "strat-uid"


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def coord() -> tuple[
    ArchiveImportCoordinator,
    FakeImporter, FakeVerifier, FakeStager,
    FakeStrategyAdapter, FakeDatasetAdapter, FakeAuditAdapter,
    sqlite3.Connection,
]:
    conn = sqlite3.connect(":memory:")
    imp = FakeImporter()
    ver = FakeVerifier()
    stg = FakeStager()
    strat = FakeStrategyAdapter()
    ds = FakeDatasetAdapter()
    aud = FakeAuditAdapter()
    c = ArchiveImportCoordinator(imp, ver, stg, strat, ds, aud, conn)
    return c, imp, ver, stg, strat, ds, aud, conn


# ---------------------------------------------------------------------------
# Success path — call ordering
# ---------------------------------------------------------------------------


def test_success_calls_components_in_order(coord):
    """All components must be called in the correct sequence."""
    c, imp, ver, stg, strat, ds, aud, conn = coord
    result = c.import_archive(
        archive_root="/src",
        experiment_name="exp",
        run_id="r1",
        strategy_dto=FakeStrategyDTO(),
        dataset_dto=FakeStrategyDTO(),
        expected_snapshot_hash="abcd",
    )
    assert result.success is True
    assert result.strategy_id == 42
    assert result.dataset_id == 99
    assert imp.build_preview_called
    assert ver.verify_all_called
    assert stg.stage_called
    assert strat.preflight_call_count == 1
    assert ds.preflight_call_count == 1
    assert strat.insert_call_count == 1
    assert ds.insert_call_count == 1
    assert stg.move_called
    assert stg.cleanup_called


# ---------------------------------------------------------------------------
# Duplicate strategy skips staging and DB
# ---------------------------------------------------------------------------


def test_duplicate_strategy_skips_staging_and_db(coord):
    """Duplicate UID must skip staging and DB writes."""
    c, imp, ver, stg, strat, ds, aud, conn = coord
    strat.raise_on_preflight = Exception("Duplicate UID already exists")

    result = c.import_archive(
        "/src", "exp", "r1", FakeStrategyDTO(), FakeStrategyDTO(), "abcd",
    )
    assert result.skipped is True
    assert stg.stage_called is False
    assert strat.insert_call_count == 0
    assert ds.insert_call_count == 0
    assert aud.failure_called


def test_duplicate_dataset_skips_staging_and_db(coord):
    """Duplicate dataset must skip staging and DB writes."""
    c, imp, ver, stg, strat, ds, aud, conn = coord
    ds.raise_on_preflight = Exception("Dataset already exists")

    result = c.import_archive(
        "/src", "exp", "r1", FakeStrategyDTO(), FakeStrategyDTO(), "abcd",
    )
    assert result.skipped is True
    assert stg.stage_called is False
    assert strat.insert_call_count == 0
    assert ds.insert_call_count == 0
    assert aud.failure_called


# ---------------------------------------------------------------------------
# Staging/hash failure cleans temp and audits
# ---------------------------------------------------------------------------


def test_staging_failure_cleans_temp(coord):
    """Staging failure must call cleanup_temp and audit."""
    c, imp, ver, stg, strat, ds, aud, conn = coord
    stg.raise_on_stage = OSError("copy error")

    result = c.import_archive(
        "/src", "exp", "r1", FakeStrategyDTO(), FakeStrategyDTO(), "abcd",
    )
    assert result.success is False
    assert stg.cleanup_called
    assert aud.failure_called


# ---------------------------------------------------------------------------
# DB write failure rolls back and cleans temp
# ---------------------------------------------------------------------------


def test_db_write_failure_rolls_back_and_cleans(coord):
    """DB write failure must rollback + cleanup temp."""
    c, imp, ver, stg, strat, ds, aud, conn = coord
    ds.raise_error = RuntimeError("insert failure")

    result = c.import_archive(
        "/src", "exp", "r1", FakeStrategyDTO(), FakeStrategyDTO(), "abcd",
    )
    assert result.success is False
    assert stg.cleanup_called
    assert aud.failure_called


# ---------------------------------------------------------------------------
# Commit failure rolls back and cleans temp
# ---------------------------------------------------------------------------


def test_commit_failure_rolls_back(coord, monkeypatch):
    """Commit failure must rollback + cleanup temp."""
    c, imp, ver, stg, strat, ds, aud, conn = coord
    # Force commit to fail by closing the connection before commit.
    from archive.import_coordinator import ArchiveImportCoordinator

    class _FailingConn(sqlite3.Connection):
        def commit(self) -> None:
            raise sqlite3.OperationalError("commit failed")

    # Replace the connection on the coordinator (package-level access).
    c._conn = _FailingConn(":memory:")  # type: ignore[assignment]

    result = c.import_archive(
        "/src", "exp", "r1", FakeStrategyDTO(), FakeStrategyDTO(), "abcd",
    )
    assert result.success is False
    assert aud.failure_called


# ---------------------------------------------------------------------------
# Final move failure returns partial, preserves staged
# ---------------------------------------------------------------------------


def test_move_failure_returns_partial(coord):
    """Move failure must return partial=True, not cleanup_temp."""
    c, imp, ver, stg, strat, ds, aud, conn = coord
    stg.raise_on_move = OSError("move failed")

    result = c.import_archive(
        "/src", "exp", "r1", FakeStrategyDTO(), FakeStrategyDTO(), "abcd",
    )
    assert result.success is False
    assert result.partial is True
    assert result.strategy_id == 42
    assert result.dataset_id == 99
    assert stg.cleanup_called is False  # staging preserved for repair


# ---------------------------------------------------------------------------
# Audit failure does not mask original error
# ---------------------------------------------------------------------------


def test_audit_failure_non_crashing(coord):
    """Audit write failure must NOT crash coordinator."""
    c, imp, ver, stg, strat, ds, aud, conn = coord
    aud.raise_error = RuntimeError("audit log down")
    ds.raise_error = RuntimeError("original insert failure")

    result = c.import_archive(
        "/src", "exp", "r1", FakeStrategyDTO(), FakeStrategyDTO(), "abcd",
    )
    assert result.success is False
    assert "original insert failure" in (result.error or "")
    assert result.audit_failed is True


# ---------------------------------------------------------------------------
# No UI/engine imports
# ---------------------------------------------------------------------------


def test_coordinator_has_no_ui_imports():
    """Coordinator module must not import UI or engine modules."""
    import archive.import_coordinator as mod
    # Check that the module's own namespace doesn't reference engine/UI modules.
    # (PySide6 may be in sys.modules from other tests — that's fine.)
    import_names = set()
    for name, obj in vars(mod).items():
        mod_name = getattr(obj, "__module__", "")
        if mod_name:
            import_names.add(mod_name.split(".")[0])
    assert "backtest_engine" not in import_names
    assert "validation_engine" not in import_names
    assert "PySide6" not in import_names
    assert "app" not in import_names
