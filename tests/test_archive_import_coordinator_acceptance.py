"""Coordinator acceptance tests — Task 060O-Impl.

Integration-style tests using real temp archive folders and SQLite-backed
repository adapters where practical.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from repository.db import DatabaseManager
from repository.strategy_import_adapter import (
    StrategyRepoAdapter,
    ImportStrategyDTO as StrategyImportDTO,
    DuplicateStrategyUIDError,
)
from repository.dataset_import_adapter import (
    DatasetRepoAdapter,
    ImportDatasetDTO as DatasetImportDTO,
)
from repository.import_audit_repo import AuditLogRepositoryAdapter
from archive.stager import ArchiveStager
from archive.import_coordinator import ArchiveImportCoordinator, ImportResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_archive_with_files(tmp: Path, snapshot_content: str = "a,b\n1,2\n") -> Path:
    """Create a minimal archive with manifest.json and ohlcv_snapshot.csv."""
    root = tmp / "archive"
    root.mkdir(parents=True)
    manifest = {
        "archive_version": "1.0.0",
        "experiment_name": "exp-test",
        "generated_at": "2026-01-01T00:00:00Z",
        "generator_version": "0.2.0",
        "files": ["ohlcv_snapshot.csv", "disclaimer.txt"],
        "content_hashes": {},
        "disclaimer_path": "disclaimer.txt",
    }
    (root / "manifest.json").write_text(json.dumps(manifest))
    (root / "ohlcv_snapshot.csv").write_bytes(snapshot_content.encode("utf-8"))
    (root / "disclaimer.txt").write_text("Research only.")
    return root


def _sha256_of_bytes(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def _snapshot_hash_of_archive(archive_root: Path) -> str:
    return _sha256_of_bytes((archive_root / "ohlcv_snapshot.csv").read_bytes())


class FakeImporter:
    def build_preview(self, root: str) -> dict:
        return {"archive_version": "1.0.0"}


class FakeVerifier:
    def __init__(self) -> None:
        self.raise_error: Exception | None = None
        self.verify_all_called = False

    def verify_all(self) -> bool:
        self.verify_all_called = True
        if self.raise_error:
            raise self.raise_error
        return True


class DatasetAdapterWithNoOpPreflight:
    """Test wrapper: keep real insert behavior while bypassing preflight."""

    def __init__(self, inner: DatasetRepoAdapter) -> None:
        self._inner = inner
        self.preflight_call_count = 0

    def preflight_duplicate(self, dto: DatasetImportDTO) -> None:
        self.preflight_call_count += 1

    def insert_dataset_no_commit(self, dto: DatasetImportDTO) -> int:
        return self._inner.insert_dataset_no_commit(dto)


# ---------------------------------------------------------------------------
# Fixture: real coordinator with in-memory DB + real adapters + real stager
# ---------------------------------------------------------------------------


@pytest.fixture
def real_components(tmp_path):
    """Return coordinator + project_root + archive_root + DB."""
    db = DatabaseManager(":memory:")
    db.initialize()

    project_root = tmp_path / "project"
    project_root.mkdir(parents=True)

    archive_root = _make_archive_with_files(tmp_path)

    importer = FakeImporter()
    verifier = FakeVerifier()
    stager = ArchiveStager(archive_root, project_root, "exp-test", "r1")
    strategy_adapter = StrategyRepoAdapter(db.connection)
    dataset_adapter = DatasetRepoAdapter(db.connection)
    audit_adapter = AuditLogRepositoryAdapter(db.connection)

    coordinator = ArchiveImportCoordinator(
        importer, verifier, stager,
        strategy_adapter, dataset_adapter, audit_adapter,
        db.connection,
    )

    yield coordinator, project_root, archive_root, db, verifier, audit_adapter
    db.close()


def _make_strategy_dto(uid: str = "strat-acc") -> StrategyImportDTO:
    payload = {"strategy_uid": uid, "name": "Test Strategy", "conditions": []}
    return StrategyImportDTO(
        name=f"Strategy {uid}",
        strategy_json=json.dumps(payload),
        strategy_uid=uid,
    )


def _make_dataset_dto(name: str = "ds-acc") -> DatasetImportDTO:
    return DatasetImportDTO(
        name=name, symbol="ES", timeframe="1min",
        snapshot_hash="", source_path="/src",
    )


# ---------------------------------------------------------------------------
# 1. Manifest/hash verification failure
# ---------------------------------------------------------------------------


def test_manifest_verification_failure_no_staging_no_db(real_components):
    """Verifier failure must produce success=False, no staging, no DB writes."""
    c, proj, arch, db, verifier, audit = real_components
    verifier.raise_error = RuntimeError("manifest checksum mismatch")

    result = c.import_archive(
        str(arch), "exp-test", "r1",
        _make_strategy_dto(), _make_dataset_dto(),
        _snapshot_hash_of_archive(arch),
    )
    assert result.success is False
    assert "manifest checksum" in (result.error or "")

    # No rows in strategies table.
    cnt = db.connection.execute("SELECT COUNT(*) AS c FROM strategies").fetchone()["c"]
    assert cnt == 0
    assert not (proj / ".staging").exists()


# ---------------------------------------------------------------------------
# 2. Duplicate strategy UID returns skipped, preserves existing row
# ---------------------------------------------------------------------------


def test_duplicate_strategy_uid_skipped_no_staging(real_components):
    """Duplicate UID must return skipped=True, no staging, no DB insert."""
    c, proj, arch, db, verifier, audit = real_components
    uid = "strat-dup-acc"

    # Pre-populate DB with strategy having this UID.
    existing = _make_strategy_dto(uid)
    aud_adapter = StrategyRepoAdapter(db.connection)
    aud_adapter.insert_strategy(existing)

    # Now attempt import with same UID.
    new_dto = StrategyImportDTO(
        name=f"Strategy {uid} v2",
        strategy_json=json.dumps({"strategy_uid": uid, "name": "v2"}),
        strategy_uid=uid,
    )
    result = c.import_archive(
        str(arch), "exp-test", "r1",
        new_dto, _make_dataset_dto(),
        _snapshot_hash_of_archive(arch),
    )
    assert result.skipped is True
    assert result.success is False

    # Original row still exists — only one row.
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies WHERE name='Strategy strat-dup-acc'"
    ).fetchone()["c"]
    assert cnt == 1

    # No dataset rows inserted.
    cnt_ds = db.connection.execute(
        "SELECT COUNT(*) AS c FROM datasets"
    ).fetchone()["c"]
    assert cnt_ds == 0
    assert not (proj / ".staging").exists()


# ---------------------------------------------------------------------------
# 3. Duplicate dataset snapshot hash during DB write rolls back strategy
# ---------------------------------------------------------------------------


def test_duplicate_dataset_hash_rolls_back_strategy(real_components):
    """Dataset duplicate during insert must roll back strategy from same txn."""
    _c, proj, arch, db, verifier, audit = real_components

    # Pre-populate DB with a dataset that has a matching fallback key.
    dto_pre = DatasetImportDTO(
        name="existing-ds", symbol="ES", timeframe="1min",
        snapshot_hash="", source_path="/src",
    )
    ds_adapter = DatasetRepoAdapter(db.connection)
    ds_adapter.insert_dataset(dto_pre)
    dataset_adapter = DatasetAdapterWithNoOpPreflight(ds_adapter)

    # This coordinator keeps real SQLite adapters but bypasses dataset
    # preflight, simulating a duplicate/race discovered at DB write time.
    c = ArchiveImportCoordinator(
        FakeImporter(), verifier,
        ArchiveStager(arch, proj, "exp-test", "r-db-write-duplicate"),
        StrategyRepoAdapter(db.connection),
        dataset_adapter,
        audit,
        db.connection,
    )

    # Import with a dataset that will duplicate on the fallback key.
    result = c.import_archive(
        str(arch), "exp-test", "r1",
        _make_strategy_dto("strat-ds-dup"),
        dto_pre,  # same DTO as pre-populated
        _snapshot_hash_of_archive(arch),
    )
    assert result.success is False
    assert result.skipped is False
    assert dataset_adapter.preflight_call_count == 1

    # Strategy must NOT have been inserted.
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies"
    ).fetchone()["c"]
    assert cnt == 0

    # Audit log has a failure row.
    audit_rows = db.connection.execute(
        "SELECT COUNT(*) AS c FROM ImportAuditLog"
    ).fetchone()["c"]
    assert audit_rows >= 1


# ---------------------------------------------------------------------------
# 4. Final move failure returns partial, keeps DB rows
# ---------------------------------------------------------------------------


def test_move_failure_returns_partial_keeps_db_rows(real_components, monkeypatch):
    """Move failure must return partial=True, keep DB rows, preserve staging."""
    c, proj, arch, db, verifier, audit = real_components

    import archive.stager as stager_mod
    original_move = stager_mod.ArchiveStager.move_to_final_destination

    def _fail_move(self_ignored):
        raise OSError("simulated move failure")

    monkeypatch.setattr(stager_mod.ArchiveStager, "move_to_final_destination", _fail_move)

    result = c.import_archive(
        str(arch), "exp-test", "r1",
        _make_strategy_dto("strat-partial"),
        _make_dataset_dto("ds-partial"),
        _snapshot_hash_of_archive(arch),
    )
    assert result.partial is True
    assert result.success is False
    assert result.strategy_id is not None
    assert result.dataset_id is not None

    # DB rows exist.
    cnt = db.connection.execute(
        "SELECT COUNT(*) AS c FROM strategies"
    ).fetchone()["c"]
    assert cnt == 1


# ---------------------------------------------------------------------------
# 5. Audit adapter failure preserves original error and sets audit_failed=True
# ---------------------------------------------------------------------------


def test_audit_failure_sets_audit_failed(real_components):
    """Audit failure must set audit_failed=True and preserve original error.

    Uses duplicate strategy path which explicitly triggers audit.
    """
    c, proj, arch, db, verifier, audit = real_components

    # Pre-populate with a strategy that will be duplicated.
    uid = "strat-audit-fail-test"
    aud_adapter = StrategyRepoAdapter(db.connection)
    existing = _make_strategy_dto(uid)
    aud_adapter.insert_strategy(existing)

    # Monkeypatch audit adapter to fail.
    original = audit.insert_failure_log
    def _fail(*a, **kw):
        raise RuntimeError("audit log unreachable")
    audit.insert_failure_log = _fail

    # Import with duplicate UID — triggers audit via preflight path.
    new_dto = StrategyImportDTO(
        name=f"Strategy {uid} v2",
        strategy_json=json.dumps({"strategy_uid": uid, "name": "v2"}),
        strategy_uid=uid,
    )
    result = c.import_archive(
        str(arch), "exp-test", "r1",
        new_dto, _make_dataset_dto(),
        _snapshot_hash_of_archive(arch),
    )
    assert result.skipped is True
    assert result.audit_failed is True
    assert "already exists" in (result.error or "").lower()

    audit.insert_failure_log = original


# ---------------------------------------------------------------------------
# 6. Coordinator has no UI/engine dependency
# ---------------------------------------------------------------------------


def test_coordinator_no_ui_engine_boundary():
    """Coordinator module must not import UI or engine modules."""
    import archive.import_coordinator as mod
    import_names = set()
    for _name, obj in vars(mod).items():
        mn = getattr(obj, "__module__", "")
        if mn:
            import_names.add(mn.split(".")[0])
    assert "PySide6" not in import_names
    assert "app" not in import_names
    assert "backtest_engine" not in import_names
    assert "validation_engine" not in import_names
