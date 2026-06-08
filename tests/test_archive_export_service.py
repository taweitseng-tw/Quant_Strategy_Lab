"""Tests for ArchiveExportService — Task 060Q-Impl."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from app.services.archive_export_service import (
    ArchiveExportService,
    ArchiveExportServiceError,
)
from archive.builder import MissingDatasetError, MissingValidationResultError
from archive.verifier import ArchiveVerifier
from archive.manifest import ArchiveManifest


# ---------------------------------------------------------------------------
# Fake data source
# ---------------------------------------------------------------------------


class FakeDataSource:
    """Provides strategy, dataset, and validation for export service tests."""

    def __init__(self) -> None:
        self._strategies: dict[str, dict] = {}
        self._datasets: dict[int, dict] = {}
        self._validations: dict[str, dict] = {}

    def add_strategy(
        self, uid: str, strategy_json: dict | str = None,
        dataset_id: int = 1, name: str = "test",
    ) -> None:
        sj = strategy_json or {"uid": uid, "name": name}
        if isinstance(sj, dict):
            sj = json.dumps(sj)
        self._strategies[uid] = {
            "strategy_uid": uid,
            "name": name,
            "strategy_json": sj,
            "dataset_id": dataset_id,
        }

    def add_dataset(self, did: int = 1) -> None:
        self._datasets[did] = {
            "id": did, "symbol": "ES", "timeframe": "1min",
            "row_count": 100, "source_type": "csv",
        }

    def add_validation(self, uid: str, passed: bool = True) -> None:
        self._validations[uid] = {"passed": passed, "elimination": True}

    def get_strategy(self, uid: str) -> dict[str, Any] | None:
        return self._strategies.get(uid)

    def get_dataset(self, did: int) -> dict[str, Any] | None:
        return self._datasets.get(did)

    def get_validation_result(self, uid: str) -> dict[str, Any] | None:
        return self._validations.get(uid)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ds() -> FakeDataSource:
    src = FakeDataSource()
    src.add_strategy("strat-ok", name="Test Strategy")
    src.add_dataset(1)
    src.add_validation("strat-ok")
    return src


@pytest.fixture
def snapshot_file() -> str:
    f = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    f.write("col1,col2\n1,2\n3,4\n")
    f.close()
    path = f.name
    yield path
    try:
        Path(path).unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Success — export + verify
# ---------------------------------------------------------------------------


def test_export_success_and_verify(ds, snapshot_file, tmp_path):
    """Successful export must produce a verifiable archive folder."""
    svc = ArchiveExportService(ds)
    out = tmp_path / "archives" / "test-exp"
    result = svc.export_strategy_archive(
        strategy_uid="strat-ok",
        dataset_snapshot_path=snapshot_file,
        output_dir=out,
    )
    assert result.is_dir()
    assert (result / "manifest.json").is_file()

    # Verify with ArchiveVerifier.
    manifest = ArchiveManifest.read_from_folder(result)
    verifier = ArchiveVerifier(manifest, result)
    assert verifier.verify_all() is True


# ---------------------------------------------------------------------------
# Failure — missing strategy
# ---------------------------------------------------------------------------


def test_export_missing_strategy_raises(ds, snapshot_file, tmp_path):
    """Missing strategy must raise ArchiveExportServiceError."""
    svc = ArchiveExportService(ds)
    with pytest.raises(ArchiveExportServiceError, match="strat-none"):
        svc.export_strategy_archive(
            strategy_uid="strat-none",
            dataset_snapshot_path=snapshot_file,
            output_dir=tmp_path / "out",
        )


# ---------------------------------------------------------------------------
# Failure — missing validation
# ---------------------------------------------------------------------------


def test_export_missing_validation_raises(ds, snapshot_file, tmp_path):
    """Missing validation must raise ArchiveExportServiceError."""
    ds.add_strategy("strat-no-val", name="No Validation", dataset_id=1)
    # No call to add_validation.
    svc = ArchiveExportService(ds)
    output_dir = tmp_path / "out"
    with pytest.raises(ArchiveExportServiceError, match="strat-no-val") as exc_info:
        svc.export_strategy_archive(
            strategy_uid="strat-no-val",
            dataset_snapshot_path=snapshot_file,
            output_dir=output_dir,
        )
    assert isinstance(exc_info.value.__cause__, MissingValidationResultError)
    assert not (output_dir / "manifest.json").exists()


# ---------------------------------------------------------------------------
# Failure — missing dataset
# ---------------------------------------------------------------------------


def test_export_missing_dataset_raises(ds, snapshot_file, tmp_path):
    """Missing dataset must raise ArchiveExportServiceError."""
    ds.add_strategy("strat-no-ds", name="No Dataset", dataset_id=999)
    ds.add_validation("strat-no-ds")
    svc = ArchiveExportService(ds)
    output_dir = tmp_path / "out"
    with pytest.raises(ArchiveExportServiceError, match="strat-no-ds") as exc_info:
        svc.export_strategy_archive(
            strategy_uid="strat-no-ds",
            dataset_snapshot_path=snapshot_file,
            output_dir=output_dir,
        )
    assert isinstance(exc_info.value.__cause__, MissingDatasetError)
    assert not (output_dir / "manifest.json").exists()


def test_service_package_exports_archive_export_service():
    """The service package should expose the archive export service."""
    from app.services import ArchiveExportService as ExportedService

    assert ExportedService is ArchiveExportService


def test_archive_export_service_has_no_ui_imports():
    """ArchiveExportService must stay free of UI dependencies."""
    import app.services.archive_export_service as mod

    module_names = set()
    for _name, obj in vars(mod).items():
        module_name = getattr(obj, "__module__", "")
        if module_name:
            module_names.add(module_name)

    assert not any(name == "PySide6" or name.startswith("PySide6.") for name in module_names)
    assert not any(name == "app.ui" or name.startswith("app.ui.") for name in module_names)
