"""Archive import preview contract acceptance test — Tasks 235-240.

Proves the full ``ArchiveImportPreviewService.build_preview()`` output
contract: schema version, top-level keys, config evidence keys, restore
plan entry shape, restore plan summary shape, JSON compatibility, and
read-only behavior — all in one place.
"""

from __future__ import annotations

import json
from pathlib import Path

from archive import (
    ARCHIVE_IMPORT_PREVIEW_SCHEMA_VERSION,
    ArchiveBuilder,
    ArchiveExporter,
)
from app.services.archive_import_preview_service import (
    ArchiveImportPreviewService,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeDataSource:
    """In-memory data source for ArchiveBuilder."""

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

    def strategy_exists(self, strategy_uid: str) -> bool:
        return self.strategy_exists_value

    def dataset_exists(self, dataset_id: int, symbol: str, timeframe: str) -> bool:
        return self.dataset_exists_value


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------


def test_full_contract_acceptance(tmp_path):
    """Full archive import preview contract: all layers exercised in one test."""
    # -- 1. Build archive with mixed config --------------------------------
    src = FakeDataSource()
    src.strategies["ctrct-001"] = {
        "strategy_uid": "ctrct-001",
        "name": "contract_strat",
        "strategy_json": (
            '{"strategy_uid":"ctrct-001","name":"contract_strat","conditions":[]}'
        ),
        "dataset_id": 7,
    }
    src.datasets[7] = {
        "id": 7, "symbol": "NQ", "timeframe": "1min", "row_count": 500,
    }
    src.validations["ctrct-001"] = {
        "passed": True, "elimination_result": {"passed": True},
    }

    # Archive config: instruments.json (will differ from current),
    # sessions.json (will be missing from current), no app_settings.json.
    archive_cfg = tmp_path / "archive_cfg"
    archive_cfg.mkdir()
    (archive_cfg / "instruments.json").write_text('{"symbol":"ORIG"}', encoding="utf-8")
    (archive_cfg / "sessions.json").write_text("[]", encoding="utf-8")

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        f.write("o,h,l,c,v\n100,102,99,101,1000\n")
        snap = f.name

    export_dir = tmp_path / "acceptance_export"
    try:
        builder = ArchiveBuilder(src)
        exporter = ArchiveExporter(builder, src)
        exporter.export(
            strategy_uid="ctrct-001",
            dataset_snapshot_path=snap,
            disclaimer_text="Research only. Not financial advice.",
            output_dir=export_dir,
            config_sources={
                "instruments.json": str(archive_cfg / "instruments.json"),
                "sessions.json": str(archive_cfg / "sessions.json"),
            },
        )
    finally:
        Path(snap).unlink(missing_ok=True)

    # -- 2. Create "current project config" with mixed status -------------
    current_cfg = tmp_path / "current_cfg"
    current_cfg.mkdir()
    (current_cfg / "instruments.json").write_text(
        '{"symbol":"CHANGED"}', encoding="utf-8",
    )

    # -- 3. Build preview through service ---------------------------------
    detector = FakeCollisionDetector(strategy_exists=False, dataset_exists=True)
    result = ArchiveImportPreviewService().build_preview(
        export_dir,
        collision_detector=detector,
        project_config_dir=current_cfg,
    )

    # -- 4. Assert top-level keys -----------------------------------------
    expected_top_keys = {
        "archive_import_preview_schema_version",
        "plan", "strategy_uid", "strategy_name",
        "dataset_id", "dataset_symbol", "dataset_timeframe",
        "validation_passed", "strategy_collision", "dataset_collision",
        "config",
    }
    assert result.keys() == expected_top_keys, (
        f"Top-level keys mismatch: extra={result.keys() - expected_top_keys}, "
        f"missing={expected_top_keys - result.keys()}"
    )

    # Schema version
    assert result["archive_import_preview_schema_version"] == ARCHIVE_IMPORT_PREVIEW_SCHEMA_VERSION
    assert isinstance(result["archive_import_preview_schema_version"], str)

    # Plan
    assert result["plan"]["archive_version"] == "1.0.0"
    assert result["plan"]["verified"] is True

    # Strategy / dataset
    assert result["strategy_uid"] == "ctrct-001"
    assert result["strategy_name"] == "contract_strat"
    assert result["dataset_symbol"] == "NQ"
    assert result["dataset_timeframe"] == "1min"
    assert result["validation_passed"] is True

    # Collision flags from detector
    assert result["strategy_collision"] is False
    assert result["dataset_collision"] is True

    # -- 5. Assert config evidence keys -------------------------------------
    config = result["config"]
    expected_config_keys = {
        "config_snapshot_files",
        "config_snapshot_evidence",
        "config_snapshot_comparisons",
        "config_snapshot_summary",
        "config_snapshot_restore_plan",
        "config_snapshot_restore_plan_summary",
    }
    assert config.keys() == expected_config_keys, (
        f"Config keys mismatch: extra={config.keys() - expected_config_keys}, "
        f"missing={expected_config_keys - config.keys()}"
    )

    # Config snapshot files and evidence
    assert set(config["config_snapshot_files"]) == {"instruments.json", "sessions.json"}
    evidence = {
        item["filename"]: item for item in config["config_snapshot_evidence"]
    }
    assert set(evidence) == {"instruments.json", "sessions.json"}
    assert len(evidence["instruments.json"]["sha256"]) == 64
    assert len(evidence["sessions.json"]["sha256"]) == 64

    # Config snapshot comparisons
    comparisons = {c["filename"]: c for c in config["config_snapshot_comparisons"]}
    assert comparisons["instruments.json"]["status"] == "different"
    assert comparisons["sessions.json"]["status"] == "missing_current"
    assert comparisons["app_settings.json"]["status"] == "no_archive_evidence"

    # Config snapshot summary
    sm = config["config_snapshot_summary"]
    assert sm["total"] == 3
    assert sm["match"] == 0
    assert sm["different"] == 1
    assert sm["missing_current"] == 1
    assert sm["no_archive_evidence"] == 1

    # -- 6. Assert restore plan entries -------------------------------------
    plan_entries = config["config_snapshot_restore_plan"]
    assert len(plan_entries) == 3

    expected_plan_entry_keys = {
        "filename", "comparison_status", "recommended_action",
        "reason", "severity", "requires_manual_review",
    }
    for entry in plan_entries:
        assert entry.keys() == expected_plan_entry_keys, (
            f"Restore plan entry keys mismatch for {entry['filename']}: "
            f"extra={entry.keys() - expected_plan_entry_keys}, "
            f"missing={expected_plan_entry_keys - entry.keys()}"
        )

    entry_map = {e["filename"]: e for e in plan_entries}
    assert entry_map["instruments.json"]["recommended_action"] == "review_difference"
    assert entry_map["instruments.json"]["severity"] == "warning"
    assert entry_map["instruments.json"]["requires_manual_review"] is True

    assert entry_map["sessions.json"]["recommended_action"] == "can_restore_missing_current"
    assert entry_map["sessions.json"]["severity"] == "info"
    assert entry_map["sessions.json"]["requires_manual_review"] is True

    assert entry_map["app_settings.json"]["recommended_action"] == "no_archive_snapshot"
    assert entry_map["app_settings.json"]["severity"] == "none"
    assert entry_map["app_settings.json"]["requires_manual_review"] is False

    # -- 7. Assert restore plan summary -------------------------------------
    rps = config["config_snapshot_restore_plan_summary"]
    expected_summary_keys = {
        "total", "no_action_for_match", "review_difference",
        "can_restore_missing_current", "no_archive_snapshot",
        "unknown", "manual_review_required",
    }
    assert rps.keys() == expected_summary_keys, (
        f"Restore plan summary keys mismatch: "
        f"extra={rps.keys() - expected_summary_keys}, "
        f"missing={expected_summary_keys - rps.keys()}"
    )
    assert rps["total"] == 3
    assert rps["no_action_for_match"] == 0
    assert rps["review_difference"] == 1      # instruments.json
    assert rps["can_restore_missing_current"] == 1  # sessions.json
    assert rps["no_archive_snapshot"] == 1    # app_settings.json
    assert rps["unknown"] == 0
    assert rps["manual_review_required"] == 2  # instruments + sessions

    # -- 8. Assert JSON compatibility --------------------------------------
    json_str = json.dumps(result)
    assert json_str, "Result must be JSON-serializable"
    roundtrip = json.loads(json_str)
    assert roundtrip["strategy_uid"] == "ctrct-001"
    assert roundtrip["config"]["config_snapshot_restore_plan_summary"]["total"] == 3

    # -- 9. Assert no file writes ------------------------------------------
    assert (current_cfg / "instruments.json").read_text(encoding="utf-8") == (
        '{"symbol":"CHANGED"}'
    )
    assert not (current_cfg / "sessions.json").exists()
