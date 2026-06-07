"""Tests for ArchiveBuilder first-pass collector — Task 059I-Impl."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from archive.manifest import ArchiveManifest
from archive.builder import (
    ArchiveBuilder,
    MissingStrategyError,
    MissingDatasetError,
    MissingDatasetSnapshotError,
    MissingValidationResultError,
    StrategyValidationFailedError,
    MissingDisclaimerError,
)


# ---------------------------------------------------------------------------
# Fake data source
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
    f = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    f.write("col1,col2\n1,2\n")
    f.close()
    path = f.name
    yield path
    try:
        Path(path).unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Success
# ---------------------------------------------------------------------------


def test_build_returns_manifest(fake_source: FakeDataSource, snapshot_file: str):
    """Builder must return an ArchiveManifest on success."""
    builder = ArchiveBuilder(fake_source)
    manifest = builder.build(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
    )
    assert isinstance(manifest, ArchiveManifest)
    assert manifest.archive_version == "1.0.0"
    assert manifest.experiment_name == "test_strat"
    assert "disclaimer.txt" in manifest.files
    assert manifest.disclaimer_path == "disclaimer.txt"


def test_build_uses_custom_experiment_name(fake_source: FakeDataSource, snapshot_file: str):
    """Builder must use caller-provided experiment_name."""
    builder = ArchiveBuilder(fake_source)
    manifest = builder.build(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
        experiment_name="my_custom_archive",
    )
    assert manifest.experiment_name == "my_custom_archive"


def test_build_manifest_files_contain_required_names(fake_source: FakeDataSource, snapshot_file: str):
    """Builder must list all required relative filenames in manifest.files."""
    builder = ArchiveBuilder(fake_source)
    manifest = builder.build(
        strategy_uid="strat-001",
        dataset_snapshot_path=snapshot_file,
        disclaimer_text="Research only.",
    )
    expected_files = {
        "disclaimer.txt",
        "strategy.json",
        "dataset_meta.json",
        "validation_result.json",
        "ohlcv_snapshot.csv",
    }
    assert set(manifest.files) == expected_files
    # content_hashes must be empty during this first-pass builder phase
    assert manifest.content_hashes == {}


def test_validation_failed_raises_error(fake_source: FakeDataSource, snapshot_file: str):
    """If validation result passed is False, must raise StrategyValidationFailedError."""
    fake_source.validations["strat-001"] = {
        "passed": False,
        "elimination_result": {"passed": False},
    }
    builder = ArchiveBuilder(fake_source)
    with pytest.raises(StrategyValidationFailedError, match="failed validation"):
        builder.build(
            strategy_uid="strat-001",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="Research only.",
        )


# ---------------------------------------------------------------------------
# Hard failures
# ---------------------------------------------------------------------------


def test_missing_strategy_raises(fake_source: FakeDataSource, snapshot_file: str):
    """Missing strategy must raise MissingStrategyError."""
    builder = ArchiveBuilder(fake_source)
    with pytest.raises(MissingStrategyError, match="not found"):
        builder.build(
            strategy_uid="no-such-strat",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="Research only.",
        )


def test_missing_strategy_json_raises(fake_source: FakeDataSource, snapshot_file: str):
    """Strategy without strategy_json must raise MissingStrategyError."""
    fake_source.strategies["bad-strat"] = {"strategy_uid": "bad-strat", "dataset_id": 1}
    builder = ArchiveBuilder(fake_source)
    with pytest.raises(MissingStrategyError, match="no strategy_json"):
        builder.build(
            strategy_uid="bad-strat",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="Research only.",
        )


def test_missing_dataset_id_raises(fake_source: FakeDataSource, snapshot_file: str):
    """Strategy without dataset_id must raise MissingDatasetError."""
    fake_source.strategies["no-ds"] = {"strategy_uid": "no-ds", "strategy_json": "{}"}
    builder = ArchiveBuilder(fake_source)
    with pytest.raises(MissingDatasetError, match="no dataset_id"):
        builder.build(
            strategy_uid="no-ds",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="Research only.",
        )


def test_missing_dataset_raises(fake_source: FakeDataSource, snapshot_file: str):
    """Missing dataset in source must raise MissingDatasetError."""
    fake_source.strategies["no-ds"] = {
        "strategy_uid": "no-ds", "strategy_json": "{}", "dataset_id": 999,
    }
    builder = ArchiveBuilder(fake_source)
    with pytest.raises(MissingDatasetError, match="not found"):
        builder.build(
            strategy_uid="no-ds",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="Research only.",
        )


def test_missing_snapshot_file_raises(fake_source: FakeDataSource):
    """Missing snapshot file must raise MissingDatasetSnapshotError."""
    builder = ArchiveBuilder(fake_source)
    with pytest.raises(MissingDatasetSnapshotError, match="not found"):
        builder.build(
            strategy_uid="strat-001",
            dataset_snapshot_path="/nonexistent/file.csv",
            disclaimer_text="Research only.",
        )


def test_missing_validation_result_raises(fake_source: FakeDataSource, snapshot_file: str):
    """Missing validation must raise MissingValidationResultError."""
    fake_source.strategies["strat-002"] = {
        "strategy_uid": "strat-002",
        "name": "no_val",
        "strategy_json": "{}",
        "dataset_id": 42,
    }
    builder = ArchiveBuilder(fake_source)
    with pytest.raises(MissingValidationResultError, match="No validation result"):
        builder.build(
            strategy_uid="strat-002",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="Research only.",
        )


def test_missing_disclaimer_raises(fake_source: FakeDataSource, snapshot_file: str):
    """Empty disclaimer must raise MissingDisclaimerError."""
    builder = ArchiveBuilder(fake_source)
    with pytest.raises(MissingDisclaimerError, match="empty or missing"):
        builder.build(
            strategy_uid="strat-001",
            dataset_snapshot_path=snapshot_file,
            disclaimer_text="   ",
        )
