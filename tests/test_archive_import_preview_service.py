"""Tests for ArchiveImportPreviewService - Tasks 187-192."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.archive_import_preview_service import (
    ArchiveImportPreviewService,
    ArchiveImportPreviewServiceError,
)


class FakeDataSource:
    """In-memory fake for ArchiveBuilder."""

    def __init__(self) -> None:
        self.strategies: dict[str, dict] = {}
        self.datasets: dict[int, dict] = {}
        self.validations: dict[str, dict] = {}

    def get_strategy(self, uid: str) -> dict | None:
        return self.strategies.get(uid)

    def get_dataset(self, did: int) -> dict | None:
        return self.datasets.get(did)

    def get_validation_result(self, uid: str) -> dict | None:
        return self.validations.get(uid)


def _export_minimal_archive(
    output_dir: Path,
    *,
    config_sources: dict[str, str] | None = None,
) -> None:
    """Export a minimal valid archive for testing."""
    from archive.builder import ArchiveBuilder
    from archive.exporter import ArchiveExporter

    src = FakeDataSource()
    src.strategies["svc-test"] = {
        "strategy_uid": "svc-test",
        "name": "svc",
        "strategy_json": '{"strategy_uid":"svc-test","name":"svc","conditions":[]}',
        "dataset_id": 1,
    }
    src.datasets[1] = {"id": 1, "symbol": "ES", "timeframe": "1min", "row_count": 100}
    src.validations["svc-test"] = {"passed": True, "elimination_result": {"passed": True}}

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        f.write("o,h,l,c,v\n100,101,99,100.5,1000\n")
        snap = f.name

    try:
        builder = ArchiveBuilder(src)
        exporter = ArchiveExporter(builder, src)
        exporter.export(
            strategy_uid="svc-test",
            dataset_snapshot_path=snap,
            disclaimer_text="Research only. Not financial advice.",
            output_dir=output_dir,
            config_sources=config_sources,
        )
    finally:
        Path(snap).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_service_build_preview_no_config_dir(tmp_path):
    """Service must return empty config evidence when no project_config_dir is given."""
    output_dir = tmp_path / "export_no_cfg"
    _export_minimal_archive(output_dir)

    svc = ArchiveImportPreviewService()
    result = svc.build_preview(output_dir)

    assert isinstance(result, dict)
    assert result["strategy_uid"] == "svc-test"
    assert result["dataset_symbol"] == "ES"
    assert result["plan"]["verified"] is True
    assert result["config"]["config_snapshot_files"] == []
    assert result["config"]["config_snapshot_evidence"] == []
    assert result["config"]["config_snapshot_comparisons"] == []
    assert result["config"]["config_snapshot_summary"] == {
        "total": 0, "match": 0, "different": 0,
        "missing_current": 0, "no_archive_evidence": 0,
    }
    json.dumps(result)


def test_service_build_preview_with_config_comparison(tmp_path):
    """Service must populate config comparison when project_config_dir matches archive."""
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "instruments.json").write_text('{"symbol":"ES"}', encoding="utf-8")
    (cfg_dir / "sessions.json").write_text("[]", encoding="utf-8")
    (cfg_dir / "app_settings.json").write_text("{}", encoding="utf-8")

    output_dir = tmp_path / "export_with_cfg"
    _export_minimal_archive(
        output_dir,
        config_sources={
            "instruments.json": str(cfg_dir / "instruments.json"),
            "sessions.json": str(cfg_dir / "sessions.json"),
            "app_settings.json": str(cfg_dir / "app_settings.json"),
        },
    )

    svc = ArchiveImportPreviewService()
    result = svc.build_preview(output_dir, project_config_dir=cfg_dir)

    config = result["config"]
    assert len(config["config_snapshot_files"]) == 3
    assert len(config["config_snapshot_evidence"]) == 3
    assert len(config["config_snapshot_comparisons"]) == 3
    assert config["config_snapshot_summary"]["match"] == 3

    # Verify plain dict serialization; no dataclass instances.
    assert json.dumps(result) is not None
    for c in config["config_snapshot_comparisons"]:
        assert c["status"] == "match"
        assert c["archive_sha256"] == c["current_sha256"]


def test_service_build_preview_invalid_archive_raises(tmp_path):
    """Service must raise ArchiveImportPreviewServiceError for invalid archives."""
    invalid_dir = tmp_path / "nonexistent"
    invalid_dir.mkdir()

    svc = ArchiveImportPreviewService()
    with pytest.raises(ArchiveImportPreviewServiceError, match="manifest"):
        svc.build_preview(invalid_dir)


def test_service_build_preview_missing_config_comparison(tmp_path):
    """Service must show no_archive_evidence when archive has no config but project_config_dir has files."""
    cfg_dir = tmp_path / "config_missing"
    cfg_dir.mkdir()
    (cfg_dir / "instruments.json").write_text("{}", encoding="utf-8")

    output_dir = tmp_path / "export_no_cfg_cmp"
    _export_minimal_archive(output_dir)

    svc = ArchiveImportPreviewService()
    result = svc.build_preview(output_dir, project_config_dir=cfg_dir)

    comparisons = result["config"]["config_snapshot_comparisons"]
    instr = [c for c in comparisons if c["filename"] == "instruments.json"][0]
    assert instr["status"] == "no_archive_evidence"


def test_service_does_not_import_pyside():
    """Service module must not import PySide6 or UI modules."""
    # Check the service module's imports
    import app.services.archive_import_preview_service as mod
    import_names = set()
    for _name, obj in vars(mod).items():
        mn = getattr(obj, "__module__", "")
        if mn:
            import_names.add(mn.split(".")[0])
    assert "PySide6" not in import_names
