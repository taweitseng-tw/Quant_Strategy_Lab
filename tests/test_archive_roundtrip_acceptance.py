"""Export-to-import round-trip acceptance test — Task 060S-Impl.

Exports a strategy archive via ArchiveExportService, verifies the folder,
then imports it into a fresh in-memory SQLite DB via ArchiveImportCoordinator
with real repository adapters.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.archive_export_service import ArchiveExportService
from archive.manifest import ArchiveManifest
from archive.verifier import ArchiveVerifier
from archive.stager import ArchiveStager
from archive.import_coordinator import ArchiveImportCoordinator, ImportResult
from repository.db import DatabaseManager
from repository.strategy_import_adapter import (
    StrategyRepoAdapter,
    ImportStrategyDTO,
)
from repository.dataset_import_adapter import (
    DatasetRepoAdapter,
    ImportDatasetDTO,
)
from repository.import_audit_repo import AuditLogRepositoryAdapter


# ---------------------------------------------------------------------------
# Fake data source for export
# ---------------------------------------------------------------------------


class FakeExportDataSource:
    """In-memory data for ArchiveExportService."""

    def __init__(self) -> None:
        self._strategies: dict[str, dict] = {}
        self._datasets: dict[int, dict] = {}
        self._validations: dict[str, dict] = {}

    def add_strategy(
        self, uid: str, strategy_json: dict, name: str = "test",
        dataset_id: int = 1,
    ) -> None:
        payload = {"strategy_uid": uid, "name": name, "conditions": []} | strategy_json
        self._strategies[uid] = {
            "strategy_uid": uid,
            "name": name,
            "strategy_json": json.dumps(payload),
            "dataset_id": dataset_id,
        }

    def add_dataset(self, did: int = 1, symbol: str = "ES", timeframe: str = "1min") -> None:
        self._datasets[did] = {
            "id": did, "symbol": symbol, "timeframe": timeframe,
            "row_count": 100, "source_type": "csv",
            "source_path": "/src/csv", "normalized_path": "/data/csv",
        }

    def add_validation(self, uid: str, passed: bool = True) -> None:
        self._validations[uid] = {"passed": passed, "elimination": {"passed": True}}

    def get_strategy(self, uid: str) -> dict[str, Any] | None:
        return self._strategies.get(uid)

    def get_dataset(self, did: int) -> dict[str, Any] | None:
        return self._datasets.get(did)

    def get_validation_result(self, uid: str) -> dict[str, Any] | None:
        return self._validations.get(uid)


# ---------------------------------------------------------------------------
# Importer fake (just returns a minimal manifest dict)
# ---------------------------------------------------------------------------


class FakeImporter:
    def build_preview(self, root: str) -> dict:
        return {"archive_version": "1.0.0"}


# ---------------------------------------------------------------------------
# Verifier wrapper (uses real ArchiveVerifier)
# ---------------------------------------------------------------------------


def _make_verifier(manifest: ArchiveManifest, root: Path):
    return ArchiveVerifier(manifest, root)


# ---------------------------------------------------------------------------
# Round-trip test
# ---------------------------------------------------------------------------


def test_export_verify_import_roundtrip(tmp_path):
    """Export → verify → import → assert repository state."""
    # -- 1. EXPORT -----------------------------------------------------------
    src = FakeExportDataSource()
    src.add_strategy("strat-rt", strategy_json={}, name="Round Trip Strategy", dataset_id=1)
    src.add_dataset(1, symbol="ES", timeframe="1min")
    src.add_validation("strat-rt")

    svc = ArchiveExportService(src)

    csv_path = tmp_path / "snapshot.csv"
    csv_path.write_text("o,h,l,c,v\n100,102,99,101,1000\n", encoding="utf-8")

    out_dir = tmp_path / "archives" / "strat-rt"
    export_result = svc.export_strategy_archive(
        strategy_uid="strat-rt",
        dataset_snapshot_path=str(csv_path),
        output_dir=out_dir,
        experiment_name="strat-rt-roundtrip",
    )
    assert export_result.is_dir()

    # -- 2. VERIFY -----------------------------------------------------------
    manifest = ArchiveManifest.read_from_folder(export_result)
    ArchiveVerifier(manifest, export_result).verify_all()
    snapshot_hash = manifest.content_hashes.get("ohlcv_snapshot.csv", "")
    assert snapshot_hash, "Manifest must contain ohlcv_snapshot.csv hash"

    # -- 3. IMPORT -----------------------------------------------------------
    import_db = DatabaseManager(":memory:")
    import_db.initialize()

    importer = FakeImporter()
    verifier = ArchiveVerifier(manifest, export_result)
    project_root = tmp_path / "import-project"
    project_root.mkdir(parents=True)

    run_id = "rt-001"
    stager = ArchiveStager(export_result, project_root, "strat-rt-roundtrip", run_id)

    strategy_adapter = StrategyRepoAdapter(import_db.connection)
    dataset_adapter = DatasetRepoAdapter(import_db.connection)
    audit_adapter = AuditLogRepositoryAdapter(import_db.connection)

    coordinator = ArchiveImportCoordinator(
        importer, verifier, stager,
        strategy_adapter, dataset_adapter, audit_adapter,
        import_db.connection,
    )

    # Build import DTOs from exported files.
    strategy_data = json.loads(
        (export_result / "strategy.json").read_text(encoding="utf-8")
    )
    uid = strategy_data.get("strategy_uid", "strat-rt")
    strategy_dto = ImportStrategyDTO(
        name=f"Imported {uid}",
        strategy_json=(export_result / "strategy.json").read_text(encoding="utf-8"),
        strategy_uid=uid,
    )

    ds_meta = json.loads(
        (export_result / "dataset_meta.json").read_text(encoding="utf-8")
    )
    dataset_dto = ImportDatasetDTO(
        name=f"ds-{uid}",
        symbol=ds_meta.get("symbol", "ES"),
        timeframe=ds_meta.get("timeframe", "1min"),
        source_type=ds_meta.get("source_type", "csv"),
        source_path=str(export_result),
        normalized_path=str(project_root / "data" / "imported" / "strat-rt-roundtrip" / "ohlcv.csv"),
        snapshot_hash=snapshot_hash,
    )

    result: ImportResult = coordinator.import_archive(
        archive_root=str(export_result),
        experiment_name="strat-rt-roundtrip",
        run_id=run_id,
        strategy_dto=strategy_dto,
        dataset_dto=dataset_dto,
        expected_snapshot_hash=snapshot_hash,
    )

    # -- 4. ASSERT -----------------------------------------------------------
    assert result.success is True, f"Import failed: {result.error}"
    assert result.strategy_id is not None
    assert result.dataset_id is not None

    # Imported strategy row exists.
    strat_row = import_db.connection.execute(
        "SELECT * FROM strategies WHERE name='Imported strat-rt'"
    ).fetchone()
    assert strat_row is not None
    loaded = json.loads(strat_row["strategy_json"])
    assert loaded.get("strategy_uid") == "strat-rt"

    # Imported dataset row exists.
    ds_row = import_db.connection.execute(
        "SELECT * FROM datasets WHERE name='ds-strat-rt'"
    ).fetchone()
    assert ds_row is not None
    assert ds_row["symbol"] == "ES"
    assert ds_row["timeframe"] == "1min"
    if "snapshot_hash" in ds_row.keys():
        assert ds_row["snapshot_hash"] == snapshot_hash

    final_snapshot_path = (
        project_root / "data" / "imported" / "strat-rt-roundtrip" / "ohlcv.csv"
    )
    assert final_snapshot_path.is_file()
    assert final_snapshot_path.read_text(encoding="utf-8") == csv_path.read_text(
        encoding="utf-8"
    )

    # No failure audit rows.
    fail_cnt = import_db.connection.execute(
        "SELECT COUNT(*) AS c FROM ImportAuditLog WHERE status='FAILED'"
    ).fetchone()["c"]
    assert fail_cnt == 0

    # Coordinator has no UI/engine imports.
    import archive.import_coordinator as mod
    import_names = set()
    for _name, obj in vars(mod).items():
        mn = getattr(obj, "__module__", "")
        if mn:
            import_names.add(mn.split(".")[0])
    assert "PySide6" not in import_names
    assert "backtest_engine" not in import_names
    assert "validation_engine" not in import_names

    import_db.close()


def test_roundtrip_export_includes_config_snapshot(tmp_path):
    """Archive config snapshots must not break export, verify, or import roundtrip."""
    src = FakeExportDataSource()
    src.add_strategy("cfg-rt", strategy_json={}, name="Config RT Strategy", dataset_id=1)
    src.add_dataset(1, symbol="ES", timeframe="1min")
    src.add_validation("cfg-rt")

    svc = ArchiveExportService(src)

    csv_path = tmp_path / "snapshot.csv"
    csv_path.write_text("o,h,l,c,v\n100,102,99,101,1000\n", encoding="utf-8")

    # Create source config files.
    config_dir = tmp_path / "config_src"
    config_dir.mkdir()
    (config_dir / "instruments.json").write_text('{"symbol": "ES"}', encoding="utf-8")
    (config_dir / "sessions.json").write_text('{"session": "day"}', encoding="utf-8")
    (config_dir / "app_settings.json").write_text(
        '{"execution_model": "next_bar_open"}', encoding="utf-8",
    )

    out_dir = tmp_path / "archives" / "cfg-rt"
    export_result = svc.export_strategy_archive(
        strategy_uid="cfg-rt",
        dataset_snapshot_path=str(csv_path),
        output_dir=out_dir,
        experiment_name="cfg-rt-roundtrip",
        config_sources={
            "instruments.json": str(config_dir / "instruments.json"),
            "sessions.json": str(config_dir / "sessions.json"),
            "app_settings.json": str(config_dir / "app_settings.json"),
        },
    )

    # Config files exist in archive folder.
    assert (export_result / "instruments.json").is_file()
    assert (export_result / "sessions.json").is_file()
    assert (export_result / "app_settings.json").is_file()

    # Content is preserved.
    assert json.loads((export_result / "instruments.json").read_text(encoding="utf-8")) == {
        "symbol": "ES",
    }
    assert json.loads((export_result / "app_settings.json").read_text(encoding="utf-8")) == {
        "execution_model": "next_bar_open",
    }

    # Verifier passes.
    manifest = ArchiveManifest.read_from_folder(export_result)
    verifier = ArchiveVerifier(manifest, export_result)
    assert verifier.verify_all() is True
    snapshot_hash = manifest.content_hashes.get("ohlcv_snapshot.csv", "")
    assert snapshot_hash, "Manifest must contain ohlcv_snapshot.csv hash"

    # Import still succeeds with extra config files listed in the manifest.
    import_db = DatabaseManager(":memory:")
    import_db.initialize()

    importer = FakeImporter()
    project_root = tmp_path / "import-project"
    project_root.mkdir(parents=True)

    run_id = "cfg-rt-001"
    stager = ArchiveStager(export_result, project_root, "cfg-rt-roundtrip", run_id)

    strategy_adapter = StrategyRepoAdapter(import_db.connection)
    dataset_adapter = DatasetRepoAdapter(import_db.connection)
    audit_adapter = AuditLogRepositoryAdapter(import_db.connection)

    coordinator = ArchiveImportCoordinator(
        importer,
        ArchiveVerifier(manifest, export_result),
        stager,
        strategy_adapter,
        dataset_adapter,
        audit_adapter,
        import_db.connection,
    )

    strategy_data = json.loads(
        (export_result / "strategy.json").read_text(encoding="utf-8")
    )
    uid = strategy_data.get("strategy_uid", "cfg-rt")
    strategy_dto = ImportStrategyDTO(
        name=f"Imported {uid}",
        strategy_json=(export_result / "strategy.json").read_text(encoding="utf-8"),
        strategy_uid=uid,
    )

    ds_meta = json.loads(
        (export_result / "dataset_meta.json").read_text(encoding="utf-8")
    )
    dataset_dto = ImportDatasetDTO(
        name=f"ds-{uid}",
        symbol=ds_meta.get("symbol", "ES"),
        timeframe=ds_meta.get("timeframe", "1min"),
        source_type=ds_meta.get("source_type", "csv"),
        source_path=str(export_result),
        normalized_path=str(
            project_root / "data" / "imported" / "cfg-rt-roundtrip" / "ohlcv.csv"
        ),
        snapshot_hash=snapshot_hash,
    )

    result: ImportResult = coordinator.import_archive(
        archive_root=str(export_result),
        experiment_name="cfg-rt-roundtrip",
        run_id=run_id,
        strategy_dto=strategy_dto,
        dataset_dto=dataset_dto,
        expected_snapshot_hash=snapshot_hash,
    )

    assert result.success is True, f"Import failed: {result.error}"
    assert result.strategy_id is not None
    assert result.dataset_id is not None

    final_snapshot_path = (
        project_root / "data" / "imported" / "cfg-rt-roundtrip" / "ohlcv.csv"
    )
    assert final_snapshot_path.is_file()
    assert final_snapshot_path.read_text(encoding="utf-8") == csv_path.read_text(
        encoding="utf-8"
    )

    # This slice proves import tolerance only; config restore remains out of scope.
    assert not (project_root / "config" / "instruments.json").exists()
    import_db.close()
