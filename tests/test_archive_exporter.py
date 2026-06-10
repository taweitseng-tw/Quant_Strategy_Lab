"""Tests for ArchiveExporter folder writer — Task 059K-Impl."""

from __future__ import annotations

import tempfile
import json
import hashlib
from pathlib import Path
from typing import Any
import pytest

from archive.builder import ArchiveBuilder
from archive.exporter import ArchiveExporter, ExportDataUnavailableError
from archive.manifest import ArchiveIntegrityError, ArchiveManifest
from archive.verifier import ArchiveVerifier


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
        "strategy_json": '{"conditions":[]}',
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


def test_successful_folder_export(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Exporter must write strategy artifacts and a manifest to output folder."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_test"
    disclaimer = "This is a non-financial-advice disclaimer.\nResearch only."

    exported_path = exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text=disclaimer,
        output_dir=output_dir,
    )

    assert exported_path == output_dir
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "disclaimer.txt").exists()
    assert (output_dir / "strategy.json").exists()
    assert (output_dir / "dataset_meta.json").exists()
    assert (output_dir / "validation_result.json").exists()
    assert (output_dir / "ohlcv_snapshot.csv").exists()

    # Verify disclaimer contents
    assert (output_dir / "disclaimer.txt").read_text(encoding="utf-8") == disclaimer

    # Verify strategy contents
    strategy_data = json.loads((output_dir / "strategy.json").read_text(encoding="utf-8"))
    assert strategy_data == {"conditions": []}


def test_manifest_includes_all_written_files(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Manifest files list must contain all expected files and their correct hashes."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_test"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    # Read written manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    expected_files = {
        "disclaimer.txt",
        "strategy.json",
        "dataset_meta.json",
        "validation_result.json",
        "ohlcv_snapshot.csv",
    }
    assert set(manifest_data["files"]) == expected_files

    # Check that hashes correspond to file bytes
    for filename in expected_files:
        file_path = output_dir / filename
        file_bytes = file_path.read_bytes()
        expected_hash = hashlib.sha256(file_bytes).hexdigest()
        assert manifest_data["content_hashes"][filename] == expected_hash


def test_verifier_accepts_exported_folder(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """The exported folder must be successfully verified by ArchiveVerifier."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "export_test"
    disclaimer = "Research only. Not advice.\nNot financial advice."

    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text=disclaimer,
        output_dir=output_dir,
    )

    # Run verifier
    from archive.manifest import ArchiveManifest
    manifest = ArchiveManifest.read_from_folder(output_dir)
    verifier = ArchiveVerifier(manifest, output_dir)
    # This should pass without raising ArchiveIntegrityError
    assert verifier.verify_all() is True


def test_output_folder_pre_exists(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Exporter must work correctly even when the output folder already exists."""
    output_dir = tmp_path / "pre_existing_folder"
    output_dir.mkdir()
    # Add a dummy file to ensure it writes next to it
    (output_dir / "dummy.txt").write_text("hello", encoding="utf-8")

    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "strategy.json").exists()
    assert (output_dir / "dummy.txt").exists()


def test_export_raises_data_unavailable_if_strategy_missing_after_build(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """If strategy disappears from data source after builder passes, raise ExportDataUnavailableError."""
    calls = 0
    original_get = fake_source.get_strategy
    
    def mock_get_strategy(uid: str):
        nonlocal calls
        calls += 1
        if calls > 1:
            return None
        return original_get(uid)
        
    fake_source.get_strategy = mock_get_strategy
    
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)
    
    with pytest.raises(ExportDataUnavailableError, match="Strategy.*missing or unavailable"):
        exporter.export(
            strategy_uid="strat-001",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="Research only.",
            output_dir=tmp_path / "export_fail_strat",
        )


def test_export_raises_data_unavailable_if_dataset_missing_after_build(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """If dataset disappears from data source after builder passes, raise ExportDataUnavailableError."""
    calls = 0
    original_get = fake_source.get_dataset
    
    def mock_get_dataset(did: int):
        nonlocal calls
        calls += 1
        if calls > 1:
            return None
        return original_get(did)
        
    fake_source.get_dataset = mock_get_dataset
    
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)
    
    with pytest.raises(ExportDataUnavailableError, match="Dataset.*missing or unavailable"):
        exporter.export(
            strategy_uid="strat-001",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="Research only.",
            output_dir=tmp_path / "export_fail_dataset",
        )


def test_export_raises_data_unavailable_if_validation_missing_after_build(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """If validation result disappears after builder passes, raise ExportDataUnavailableError."""
    calls = 0
    original_get = fake_source.get_validation_result
    
    def mock_get_validation_result(uid: str):
        nonlocal calls
        calls += 1
        if calls > 1:
            return None
        return original_get(uid)
        
    fake_source.get_validation_result = mock_get_validation_result
    
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)
    
    with pytest.raises(ExportDataUnavailableError, match="Validation result.*missing or unavailable"):
        exporter.export(
            strategy_uid="strat-001",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="Research only.",
            output_dir=tmp_path / "export_fail_validation",
        )


# ---------------------------------------------------------------------------
# Project config files in archive  (Task 127-132)
# ---------------------------------------------------------------------------


def test_export_with_config_sources(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Exporter must copy config files from source paths into the archive."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    # Create source config files.
    config_dir = tmp_path / "config_src"
    config_dir.mkdir()
    (config_dir / "instruments.json").write_text('{"key": "instrument_value"}', encoding="utf-8")
    (config_dir / "sessions.json").write_text('{"key": "session_value"}', encoding="utf-8")

    config_sources = {
        "instruments.json": str(config_dir / "instruments.json"),
        "sessions.json": str(config_dir / "sessions.json"),
        "app_settings.json": str(config_dir / "app_settings.json"),  # missing, should be skipped
    }

    output_dir = tmp_path / "export_config"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
        config_sources=config_sources,
    )

    # Config files present in output.
    assert (output_dir / "instruments.json").is_file(), "instruments.json must be in archive"
    assert (output_dir / "sessions.json").is_file(), "sessions.json must be in archive"
    assert not (output_dir / "app_settings.json").exists(), "Missing config must be skipped"

    # Content preserved.
    assert json.loads((output_dir / "instruments.json").read_text(encoding="utf-8")) == {
        "key": "instrument_value",
    }
    assert json.loads((output_dir / "sessions.json").read_text(encoding="utf-8")) == {
        "key": "session_value",
    }

    # Manifest must include config files.
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert "instruments.json" in manifest["files"]
    assert "sessions.json" in manifest["files"]
    assert "app_settings.json" not in manifest["files"], "Missing config must not be in manifest"

    # Verify hashes are present.
    assert "instruments.json" in manifest["content_hashes"]
    assert "sessions.json" in manifest["content_hashes"]


def test_export_without_config_sources_unchanged(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Export without config_sources must not include any config files."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    output_dir = tmp_path / "no_config"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
    )

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    config_names = {"instruments.json", "sessions.json", "app_settings.json"}
    assert not (config_names & set(manifest["files"])), "Config files must not appear without config_sources"


def test_export_with_config_sources_passes_verifier(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Archive exported with config_sources must pass ArchiveVerifier.verify_all()."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    config_dir = tmp_path / "config_src"
    config_dir.mkdir()
    (config_dir / "instruments.json").write_text('{"symbol":"ES"}', encoding="utf-8")
    (config_dir / "app_settings.json").write_text('{"execution_model":"next_bar_open"}', encoding="utf-8")

    output_dir = tmp_path / "verifier_ok"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
        config_sources={
            "instruments.json": str(config_dir / "instruments.json"),
            "app_settings.json": str(config_dir / "app_settings.json"),
        },
    )

    manifest = ArchiveManifest.read_from_folder(output_dir)
    verifier = ArchiveVerifier(manifest, output_dir)
    assert verifier.verify_all() is True, "Verifier must accept archive with config files"


def test_export_config_tamper_detected_by_verifier(fake_source: FakeDataSource, snapshot_file: str, tmp_path: Path):
    """Tampering with an exported config file must cause verifier.verify_all() to fail."""
    builder = ArchiveBuilder(fake_source)
    exporter = ArchiveExporter(builder, fake_source)

    config_dir = tmp_path / "config_src"
    config_dir.mkdir()
    (config_dir / "instruments.json").write_text('{"symbol":"ES"}', encoding="utf-8")

    output_dir = tmp_path / "tamper_test"
    exporter.export(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        output_dir=output_dir,
        config_sources={"instruments.json": str(config_dir / "instruments.json")},
    )

    # Tamper with the exported config file.
    (output_dir / "instruments.json").write_text('{"symbol":"TAMPERED"}', encoding="utf-8")

    manifest = ArchiveManifest.read_from_folder(output_dir)
    verifier = ArchiveVerifier(manifest, output_dir)
    with pytest.raises(ArchiveIntegrityError, match="Hash mismatch"):
        verifier.verify_all()
