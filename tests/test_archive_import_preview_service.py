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


class FakeCollisionDetector:
    """Read-only collision detector test double."""

    def __init__(self, *, strategy_exists: bool, dataset_exists: bool) -> None:
        self.strategy_exists_value = strategy_exists
        self.dataset_exists_value = dataset_exists
        self.calls: list[str] = []

    def strategy_exists(self, strategy_uid: str) -> bool:
        self.calls.append(f"strategy:{strategy_uid}")
        return self.strategy_exists_value

    def dataset_exists(self, dataset_id: int, symbol: str, timeframe: str) -> bool:
        self.calls.append(f"dataset:{dataset_id}:{symbol}:{timeframe}")
        return self.dataset_exists_value


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


def test_service_collision_detector_omitted_defaults_false(tmp_path):
    """Service must preserve no-detector collision defaults."""
    output_dir = tmp_path / "export_collision_omitted"
    _export_minimal_archive(output_dir)

    result = ArchiveImportPreviewService().build_preview(output_dir)

    assert result["strategy_collision"] is False
    assert result["dataset_collision"] is False


def test_service_strategy_collision_true(tmp_path):
    """Service must pass through strategy collision detector result."""
    output_dir = tmp_path / "export_strategy_collision"
    _export_minimal_archive(output_dir)
    detector = FakeCollisionDetector(strategy_exists=True, dataset_exists=False)

    result = ArchiveImportPreviewService().build_preview(
        output_dir,
        collision_detector=detector,
    )

    assert result["strategy_collision"] is True
    assert result["dataset_collision"] is False
    assert "strategy:svc-test" in detector.calls


def test_service_dataset_collision_true(tmp_path):
    """Service must pass through dataset collision detector result."""
    output_dir = tmp_path / "export_dataset_collision"
    _export_minimal_archive(output_dir)
    detector = FakeCollisionDetector(strategy_exists=False, dataset_exists=True)

    result = ArchiveImportPreviewService().build_preview(
        output_dir,
        collision_detector=detector,
    )

    assert result["strategy_collision"] is False
    assert result["dataset_collision"] is True
    assert "dataset:1:ES:1min" in detector.calls


def test_service_collision_detector_both_false(tmp_path):
    """Service must pass through false collision detector results."""
    output_dir = tmp_path / "export_collision_false"
    _export_minimal_archive(output_dir)
    detector = FakeCollisionDetector(strategy_exists=False, dataset_exists=False)

    result = ArchiveImportPreviewService().build_preview(
        output_dir,
        collision_detector=detector,
    )

    assert result["strategy_collision"] is False
    assert result["dataset_collision"] is False
    assert detector.calls == ["strategy:svc-test", "dataset:1:ES:1min"]


# ---------------------------------------------------------------------------
# Mixed config evidence (Task 199)
# ---------------------------------------------------------------------------


def test_service_build_preview_mixed_config_evidence(tmp_path):
    """Service must return correct summary counts for mixed config statuses."""
    # Archive has instruments.json (different content) and sessions.json (missing current).
    # Archive does NOT have app_settings.json.
    archive_cfg = tmp_path / "archive_cfg"
    archive_cfg.mkdir()
    (archive_cfg / "instruments.json").write_text(
        '{"symbol":"ORIGINAL"}', encoding="utf-8"
    )
    (archive_cfg / "sessions.json").write_text("[]", encoding="utf-8")

    output_dir = tmp_path / "export_mixed"
    _export_minimal_archive(
        output_dir,
        config_sources={
            "instruments.json": str(archive_cfg / "instruments.json"),
            "sessions.json": str(archive_cfg / "sessions.json"),
        },
    )

    # Current config: instruments.json is different, sessions.json is missing,
    # and app_settings.json has no archive evidence.
    current_cfg = tmp_path / "current_cfg"
    current_cfg.mkdir()
    (current_cfg / "instruments.json").write_text(
        '{"symbol":"CHANGED"}', encoding="utf-8"
    )

    result = ArchiveImportPreviewService().build_preview(
        output_dir,
        project_config_dir=current_cfg,
    )
    summary = result["config"]["config_snapshot_summary"]
    comparisons = {
        c["filename"]: c for c in result["config"]["config_snapshot_comparisons"]
    }

    assert summary["total"] == 3
    assert summary["match"] == 0
    assert summary["different"] == 1  # instruments.json
    assert summary["missing_current"] == 1  # sessions.json
    assert summary["no_archive_evidence"] == 1  # app_settings.json

    assert comparisons["instruments.json"]["status"] == "different"
    assert comparisons["sessions.json"]["status"] == "missing_current"
    assert comparisons["app_settings.json"]["status"] == "no_archive_evidence"

    assert comparisons["instruments.json"]["archive_sha256"] != comparisons[
        "instruments.json"
    ]["current_sha256"]
    assert json.dumps(result)


# ---------------------------------------------------------------------------
# No file writes (Task 200)
# ---------------------------------------------------------------------------


def test_service_build_preview_does_not_modify_config_files(tmp_path):
    """Service must not change bytes of config files on disk."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    cfg_path = cfg_dir / "instruments.json"
    original_content = '{"symbol":"PRESERVE"}'
    cfg_path.write_text(original_content, encoding="utf-8")

    output_dir = tmp_path / "export_nowrite"
    _export_minimal_archive(
        output_dir,
        config_sources={"instruments.json": str(cfg_path)},
    )

    ArchiveImportPreviewService().build_preview(
        output_dir,
        project_config_dir=cfg_dir,
    )

    assert cfg_path.read_text(encoding="utf-8") == original_content


# ---------------------------------------------------------------------------
# Error cause preservation (Task 201)
# ---------------------------------------------------------------------------


def test_service_error_preserves_cause(tmp_path):
    """ArchiveImportPreviewServiceError must preserve the underlying exception in __cause__."""
    invalid_dir = tmp_path / "missing_manifest"
    invalid_dir.mkdir()

    svc = ArchiveImportPreviewService()
    with pytest.raises(ArchiveImportPreviewServiceError) as exc_info:
        svc.build_preview(invalid_dir)

    assert exc_info.value.__cause__ is not None, "__cause__ must be preserved"
    assert "manifest" in str(exc_info.value.__cause__).lower()


# ---------------------------------------------------------------------------
# Restore plan summary service tests (Tasks 211-216)
# ---------------------------------------------------------------------------


def test_service_restore_plan_summary_omitted_config(tmp_path):
    """Service must return empty restore plan summary when no project_config_dir."""
    output_dir = tmp_path / "export_rs_omit"
    _export_minimal_archive(output_dir)

    result = ArchiveImportPreviewService().build_preview(output_dir)
    summary = result["config"]["config_snapshot_restore_plan_summary"]

    assert summary["total"] == 0
    assert summary["no_action_for_match"] == 0
    assert summary["review_difference"] == 0
    assert summary["can_restore_missing_current"] == 0
    assert summary["no_archive_snapshot"] == 0
    assert summary["unknown"] == 0


def test_service_restore_plan_summary_all_match(tmp_path):
    """Service must return all-match restore plan summary."""
    cfg_dir = tmp_path / "cfg_rs_all"
    cfg_dir.mkdir()
    (cfg_dir / "instruments.json").write_text('{"s":"ES"}', encoding="utf-8")
    (cfg_dir / "sessions.json").write_text("[]", encoding="utf-8")
    (cfg_dir / "app_settings.json").write_text("{}", encoding="utf-8")

    output_dir = tmp_path / "export_rs_all"
    _export_minimal_archive(
        output_dir,
        config_sources={
            "instruments.json": str(cfg_dir / "instruments.json"),
            "sessions.json": str(cfg_dir / "sessions.json"),
            "app_settings.json": str(cfg_dir / "app_settings.json"),
        },
    )

    result = ArchiveImportPreviewService().build_preview(
        output_dir, project_config_dir=cfg_dir,
    )
    summary = result["config"]["config_snapshot_restore_plan_summary"]

    assert summary["total"] == 3
    assert summary["no_action_for_match"] == 3
    assert summary["review_difference"] == 0
    assert summary["can_restore_missing_current"] == 0
    assert summary["no_archive_snapshot"] == 0
    assert summary["unknown"] == 0

    # Plan entries are also present.
    assert len(result["config"]["config_snapshot_restore_plan"]) == 3


def test_service_restore_plan_summary_mixed(tmp_path):
    """Service must return correct summary for mixed config evidence."""
    archive_cfg = tmp_path / "acfg_mixed"
    archive_cfg.mkdir()
    (archive_cfg / "instruments.json").write_text('{"s":"A"}', encoding="utf-8")
    (archive_cfg / "sessions.json").write_text("[]", encoding="utf-8")

    output_dir = tmp_path / "export_rs_mixed"
    _export_minimal_archive(
        output_dir,
        config_sources={
            "instruments.json": str(archive_cfg / "instruments.json"),
            "sessions.json": str(archive_cfg / "sessions.json"),
        },
    )

    current_cfg = tmp_path / "ccfg_mixed"
    current_cfg.mkdir()
    (current_cfg / "instruments.json").write_text('{"s":"B"}', encoding="utf-8")
    # sessions.json and app_settings.json not created → missing_current / no_archive_evidence

    result = ArchiveImportPreviewService().build_preview(
        output_dir, project_config_dir=current_cfg,
    )
    summary = result["config"]["config_snapshot_restore_plan_summary"]

    assert summary["total"] == 3
    assert summary["no_action_for_match"] == 0
    assert summary["review_difference"] == 1   # instruments differs
    assert summary["can_restore_missing_current"] == 1  # sessions missing from current
    assert summary["no_archive_snapshot"] == 1  # no app_settings in archive
    assert summary["unknown"] == 0

    # Plan entries present
    assert len(result["config"]["config_snapshot_restore_plan"]) == 3


# ---------------------------------------------------------------------------
# Restore plan UI-readiness flags service tests (Tasks 217-222)
# ---------------------------------------------------------------------------


def test_service_restore_plan_flags_omitted_config(tmp_path):
    """Service must return empty flags when no project_config_dir."""
    output_dir = tmp_path / "export_flags_omit"
    _export_minimal_archive(output_dir)

    result = ArchiveImportPreviewService().build_preview(output_dir)
    plan = result["config"]["config_snapshot_restore_plan"]
    summary = result["config"]["config_snapshot_restore_plan_summary"]

    assert plan == []
    assert summary["manual_review_required"] == 0


def test_service_restore_plan_flags_all_match(tmp_path):
    """Service must return match flags for all-match config."""
    cfg_dir = tmp_path / "cfg_flags_all"
    cfg_dir.mkdir()
    (cfg_dir / "instruments.json").write_text('{"s":"ES"}', encoding="utf-8")
    (cfg_dir / "sessions.json").write_text("[]", encoding="utf-8")
    (cfg_dir / "app_settings.json").write_text("{}", encoding="utf-8")

    output_dir = tmp_path / "export_flags_all"
    _export_minimal_archive(
        output_dir,
        config_sources={
            "instruments.json": str(cfg_dir / "instruments.json"),
            "sessions.json": str(cfg_dir / "sessions.json"),
            "app_settings.json": str(cfg_dir / "app_settings.json"),
        },
    )

    result = ArchiveImportPreviewService().build_preview(
        output_dir, project_config_dir=cfg_dir,
    )
    plan = result["config"]["config_snapshot_restore_plan"]
    summary = result["config"]["config_snapshot_restore_plan_summary"]

    assert len(plan) == 3
    for entry in plan:
        assert entry["severity"] == "none"
        assert entry["requires_manual_review"] is False

    assert summary["manual_review_required"] == 0


def test_service_restore_plan_flags_mixed(tmp_path):
    """Service must return correct flags for mixed config evidence."""
    archive_cfg = tmp_path / "acfg_flags"
    archive_cfg.mkdir()
    (archive_cfg / "instruments.json").write_text('{"s":"A"}', encoding="utf-8")
    (archive_cfg / "sessions.json").write_text("[]", encoding="utf-8")

    output_dir = tmp_path / "export_flags_mixed"
    _export_minimal_archive(
        output_dir,
        config_sources={
            "instruments.json": str(archive_cfg / "instruments.json"),
            "sessions.json": str(archive_cfg / "sessions.json"),
        },
    )

    current_cfg = tmp_path / "ccfg_flags"
    current_cfg.mkdir()
    (current_cfg / "instruments.json").write_text('{"s":"B"}', encoding="utf-8")

    result = ArchiveImportPreviewService().build_preview(
        output_dir, project_config_dir=current_cfg,
    )
    plan = {e["filename"]: e for e in result["config"]["config_snapshot_restore_plan"]}
    summary = result["config"]["config_snapshot_restore_plan_summary"]

    assert plan["instruments.json"]["severity"] == "warning"
    assert plan["instruments.json"]["requires_manual_review"] is True

    assert plan["sessions.json"]["severity"] == "info"
    assert plan["sessions.json"]["requires_manual_review"] is True

    assert plan["app_settings.json"]["severity"] == "none"
    assert plan["app_settings.json"]["requires_manual_review"] is False

    assert summary["manual_review_required"] == 2


# ---------------------------------------------------------------------------
# Schema version marker service tests (Tasks 223-228)
# ---------------------------------------------------------------------------


def test_service_schema_version_omitted_config(tmp_path):
    """Service must include schema version without config comparison."""
    output_dir = tmp_path / "svc_schema_omit"
    _export_minimal_archive(output_dir)

    result = ArchiveImportPreviewService().build_preview(output_dir)

    assert result["archive_import_preview_schema_version"] == "1.0.0"
    assert isinstance(result["archive_import_preview_schema_version"], str)
    json.dumps(result)


def test_service_schema_version_with_config_comparison(tmp_path):
    """Service must include schema version with config comparison."""
    cfg_dir = tmp_path / "svc_schema_cfg"
    cfg_dir.mkdir()
    (cfg_dir / "instruments.json").write_text('{"s":"ES"}', encoding="utf-8")

    output_dir = tmp_path / "svc_schema_cfg_out"
    _export_minimal_archive(
        output_dir,
        config_sources={"instruments.json": str(cfg_dir / "instruments.json")},
    )

    result = ArchiveImportPreviewService().build_preview(
        output_dir, project_config_dir=cfg_dir,
    )

    assert result["archive_import_preview_schema_version"] == "1.0.0"
    assert result["config"]["config_snapshot_restore_plan_summary"]["total"] == 3
    json.dumps(result)


def test_service_schema_version_all_keys_present(tmp_path):
    """Service output must include all expected top-level keys."""
    output_dir = tmp_path / "svc_schema_keys"
    _export_minimal_archive(output_dir)

    result = ArchiveImportPreviewService().build_preview(output_dir)

    expected = {
        "archive_import_preview_schema_version", "plan", "strategy_uid",
        "strategy_name", "dataset_id", "dataset_symbol", "dataset_timeframe",
        "validation_passed", "strategy_collision", "dataset_collision", "config",
    }
    assert expected.issubset(result.keys())
    json.dumps(result)


def test_service_schema_version_no_file_writes(tmp_path):
    """Generating schema version must not modify config files."""
    cfg_dir = tmp_path / "svc_schema_nowrite"
    cfg_dir.mkdir()
    cfg_path = cfg_dir / "instruments.json"
    original = '{"s":"ES"}'
    cfg_path.write_text(original, encoding="utf-8")

    output_dir = tmp_path / "svc_schema_nowrite_out"
    _export_minimal_archive(
        output_dir,
        config_sources={"instruments.json": str(cfg_path)},
    )

    ArchiveImportPreviewService().build_preview(output_dir, project_config_dir=cfg_dir)

    assert cfg_path.read_text(encoding="utf-8") == original
