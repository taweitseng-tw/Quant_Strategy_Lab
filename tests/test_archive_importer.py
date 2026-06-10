"""Tests for ArchiveImporter verification skeleton — Task 059M-Impl."""

from __future__ import annotations

import tempfile
import json
import pytest
from pathlib import Path
from typing import Any

from archive.builder import ArchiveBuilder
from archive.exporter import ArchiveExporter
from archive.verifier import ArchiveIntegrityError
from archive.importer import (
    ArchiveImporter,
    ArchiveImporterError,
    IncompatibleSchemaError,
    ArchiveImportPlan,
    IImportCollisionDetector,
    ArchiveImportPreview,
)


class FakeDataSource:
    """In-memory fake implementing ``ArchiveBuilder.ArchiveDataSource``."""

    def __init__(self) -> None:
        self.strategies: dict[str, dict] = {}
        self.datasets: dict[int, dict] = {}
        self.validations: dict[str, dict] = {}

    def get_strategy(self, uid: str) -> dict[str, Any] | None:
        return self.strategies.get(uid)

    def get_dataset(self, did: int) -> dict[str, Any] | None:
        return self.datasets.get(did)

    def get_validation_result(self, uid: str) -> dict[str, Any] | None:
        return self.validations.get(uid)


@pytest.fixture
def fake_source() -> FakeDataSource:
    src = FakeDataSource()
    src.strategies["strat-001"] = {
        "strategy_uid": "strat-001",
        "name": "test_strat",
        "strategy_json": '{"strategy_uid": "strat-001", "name": "test_strat", "conditions":[]}',
        "dataset_id": 42,
        "generator_version": "0.2.0",
        "build_task_id": 1,
    }
    src.datasets[42] = {
        "id": 42,
        "symbol": "ES",
        "timeframe": "1min",
        "row_count": 1000,
    }
    src.validations["strat-001"] = {
        "passed": True,
        "elimination_result": {"passed": True},
    }
    return src


@pytest.fixture
def snapshot_file() -> str:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        f.write("col1,col2\n1,2\n")
        path = f.name
    yield path
    try:
        Path(path).unlink()
    except OSError:
        pass


def test_successful_importer_verification(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """An importer must successfully read, verify, and return an ArchiveImportPlan for a valid export folder."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_test"
    disclaimer = "This is a non-financial-advice disclaimer.\nResearch only."

    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text=disclaimer,
        output_dir=output_dir,
        experiment_name="My Experiment",
    )

    importer = ArchiveImporter(output_dir)
    plan = importer.verify()

    assert isinstance(plan, ArchiveImportPlan)
    assert plan.archive_root == output_dir
    assert plan.archive_version == "1.0.0"
    assert plan.experiment_name == "My Experiment"
    assert plan.verified is True
    assert set(plan.files) == {
        "disclaimer.txt",
        "strategy.json",
        "dataset_meta.json",
        "validation_result.json",
        "ohlcv_snapshot.csv",
    }


def test_importer_missing_manifest(tmp_path: Path):
    """Importer must raise ArchiveImporterError when manifest.json is missing."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()

    importer = ArchiveImporter(empty_dir)
    with pytest.raises(ArchiveImporterError, match="manifest.json' not found"):
        importer.verify()


def test_importer_malformed_manifest_json(tmp_path: Path):
    """Importer must raise ArchiveImporterError when manifest.json is malformed JSON."""
    bad_dir = tmp_path / "bad_json"
    bad_dir.mkdir()
    (bad_dir / "manifest.json").write_text("invalid json {", encoding="utf-8")

    importer = ArchiveImporter(bad_dir)
    with pytest.raises(ArchiveImporterError, match="Failed to read or parse manifest"):
        importer.verify()


@pytest.mark.parametrize(
    "invalid_version",
    [
        "",
        "abc",
        "2.0.0",
        "0.9.0",
        "1a.0.0",
    ]
)
def test_importer_incompatible_schema_version(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path, invalid_version: str):
    """Importer must raise IncompatibleSchemaError for unsupported or malformed versions."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / f"export_{invalid_version.replace('.', '_')}"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Disclaimer",
        output_dir=output_dir,
    )

    # Modify version in manifest
    manifest_path = output_dir / "manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_data["archive_version"] = invalid_version
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    importer = ArchiveImporter(output_dir)
    with pytest.raises(IncompatibleSchemaError) as exc_info:
        importer.verify()
    
    assert "Incompatible" in str(exc_info.value) or "version" in str(exc_info.value)


def test_importer_verifier_integrity_failure(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Importer must raise ArchiveIntegrityError if verifier checks fail."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_integrity_fail"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    # Corrupt a file to trigger hash mismatch
    strategy_file = output_dir / "strategy.json"
    strategy_file.write_text('{"corrupted": true}', encoding="utf-8")

    importer = ArchiveImporter(output_dir)
    with pytest.raises(ArchiveIntegrityError, match="Hash mismatch"):
        importer.verify()


def test_plan_files_immutability(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Import plan files field must be a tuple and raise AttributeError or TypeError when mutated."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_immutability"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    importer = ArchiveImporter(output_dir)
    plan = importer.verify()

    assert isinstance(plan.files, tuple)
    with pytest.raises(AttributeError):
        plan.files.append("new_file.txt")  # type: ignore
    with pytest.raises(TypeError):
        plan.files[0] = "new_file.txt"  # type: ignore


def test_importer_missing_archive_version(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Importer must raise IncompatibleSchemaError when archive_version is missing from the manifest."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_missing_version"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    # Delete archive_version from manifest.json
    manifest_path = output_dir / "manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest_data["archive_version"]
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    importer = ArchiveImporter(output_dir)
    with pytest.raises(IncompatibleSchemaError, match="Archive version is missing"):
        importer.verify()


def test_importer_build_preview_success(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """build_preview must verify the folder and return an ArchiveImportPreview with DTO data."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_preview_success"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )


    importer = ArchiveImporter(output_dir)
    preview = importer.build_preview()

    assert isinstance(preview, ArchiveImportPreview)
    assert isinstance(preview.plan, ArchiveImportPlan)
    assert preview.strategy_name == "test_strat"
    assert preview.dataset_id == 42
    assert preview.dataset_symbol == "ES"
    assert preview.dataset_timeframe == "1min"
    assert preview.validation_passed is True
    assert preview.strategy_collision is False
    assert preview.dataset_collision is False


def test_importer_build_preview_missing_payload_file(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """build_preview must raise ArchiveIntegrityError if a required payload file is missing."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_preview_missing_file"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    # Delete strategy.json to cause verification integrity failure
    (output_dir / "strategy.json").unlink()

    importer = ArchiveImporter(output_dir)
    with pytest.raises(ArchiveIntegrityError, match="Missing files in archive"):
        importer.build_preview()


def test_importer_build_preview_corrupt_payload_file(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """build_preview must raise ArchiveImporterError if a payload file contains invalid JSON."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_preview_corrupt"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    # Write corrupt JSON to strategy.json
    strategy_file = output_dir / "strategy.json"
    strategy_file.write_text("{corrupt: json}", encoding="utf-8")

    # Update manifest hash so verify() integrity check passes
    manifest_path = output_dir / "manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    import hashlib
    new_hash = hashlib.sha256(b"{corrupt: json}").hexdigest()
    manifest_data["content_hashes"]["strategy.json"] = new_hash
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    importer = ArchiveImporter(output_dir)
    with pytest.raises(ArchiveImporterError, match="Failed to read or parse strategy payload"):
        importer.build_preview()


class FakeCollisionDetector:
    """Read-only test double for collision detection."""

    def __init__(self, strategy_exists_val: bool, dataset_exists_val: bool) -> None:
        self._strat_exists = strategy_exists_val
        self._ds_exists = dataset_exists_val
        self.strategy_exists_called_with = None

    def strategy_exists(self, strategy_uid: str) -> bool:
        self.strategy_exists_called_with = strategy_uid
        return self._strat_exists

    def dataset_exists(self, dataset_id: int, symbol: str, timeframe: str) -> bool:
        return self._ds_exists


def test_importer_build_preview_strategy_collision(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """build_preview must report strategy collision correctly using the detector double."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_preview_strat_collision"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    detector = FakeCollisionDetector(strategy_exists_val=True, dataset_exists_val=False)
    importer = ArchiveImporter(output_dir)
    preview = importer.build_preview(detector)

    assert preview.strategy_collision is True
    assert preview.dataset_collision is False
    assert preview.strategy_uid == "strat-001"
    assert detector.strategy_exists_called_with == "strat-001"


def test_importer_build_preview_dataset_collision(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """build_preview must report dataset collision correctly using the detector double."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_preview_ds_collision"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    detector = FakeCollisionDetector(strategy_exists_val=False, dataset_exists_val=True)
    importer = ArchiveImporter(output_dir)
    preview = importer.build_preview(detector)

    assert preview.strategy_collision is False
    assert preview.dataset_collision is True


def test_importer_build_preview_read_only_boundary(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """build_preview must only call read-only collision methods and never call mutation/write methods."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_preview_boundary"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    class SpyDetector:
        def __init__(self) -> None:
            self.calls = []

        def strategy_exists(self, strategy_uid: str) -> bool:
            self.calls.append("strategy_exists")
            return False

        def dataset_exists(self, dataset_id: int, symbol: str, timeframe: str) -> bool:
            self.calls.append("dataset_exists")
            return False

        def commit(self, *args, **kwargs):
            raise AssertionError("commit() called on read-only detector")

        def rollback(self, *args, **kwargs):
            raise AssertionError("rollback() called on read-only detector")

        def write(self, *args, **kwargs):
            raise AssertionError("write() called on read-only detector")

        def copy(self, *args, **kwargs):
            raise AssertionError("copy() called on read-only detector")

    detector = SpyDetector()
    importer = ArchiveImporter(output_dir)
    importer.build_preview(detector)

    assert set(detector.calls) == {"strategy_exists", "dataset_exists"}


# ---------------------------------------------------------------------------
# Config snapshot files in import plan (Tasks 145-150)
# ---------------------------------------------------------------------------


def test_plan_config_snapshot_files_with_config(tmp_path, fake_source, snapshot_file):
    """Import preview plan must list config snapshot files when present in archive."""
    config_dir = tmp_path / "config_src"
    config_dir.mkdir()
    (config_dir / "instruments.json").write_text('{"symbol":"ES"}', encoding="utf-8")
    (config_dir / "sessions.json").write_text('[{"name":"day"}]', encoding="utf-8")
    (config_dir / "app_settings.json").write_text(
        '{"execution_model":"next_bar_open"}', encoding="utf-8"
    )

    output_dir = tmp_path / "export"
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
        config_sources={
            "instruments.json": str(config_dir / "instruments.json"),
            "sessions.json": str(config_dir / "sessions.json"),
            "app_settings.json": str(config_dir / "app_settings.json"),
        },
    )

    importer = ArchiveImporter(output_dir)
    plan = importer.verify()
    preview = importer.build_preview()

    assert set(plan.config_snapshot_files) == {
        "instruments.json",
        "sessions.json",
        "app_settings.json",
    }
    assert preview.plan.config_snapshot_files == plan.config_snapshot_files


def test_plan_config_snapshot_files_without_config(fake_source, snapshot_file, tmp_path):
    """Import plan must return empty config_snapshot_files when no config files present."""
    output_dir = tmp_path / "export_no_cfg"
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    importer = ArchiveImporter(output_dir)
    plan = importer.verify()
    preview = importer.build_preview()

    assert plan.config_snapshot_files == ()
    assert preview.plan.config_snapshot_files == ()


def test_plan_config_snapshot_files_partial(tmp_path, fake_source, snapshot_file):
    """Partial config files (only instruments.json) must be listed without the missing ones."""
    config_dir = tmp_path / "config_src"
    config_dir.mkdir()
    (config_dir / "instruments.json").write_text('{"symbol":"ES"}', encoding="utf-8")

    output_dir = tmp_path / "export_partial"
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
        config_sources={"instruments.json": str(config_dir / "instruments.json")},
    )

    importer = ArchiveImporter(output_dir)
    plan = importer.verify()

    assert plan.config_snapshot_files == ("instruments.json",)
