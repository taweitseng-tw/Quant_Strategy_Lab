"""Tests for ProjectArchiveDataSource — Task 060W-Impl."""

from __future__ import annotations

import json

import pytest

from app.services.archive_project_data_source import ProjectArchiveDataSource
from app.services.validation_pipeline_service import PipelineResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _strategy_row(uid: str, name: str = "Test Strat", **kw) -> dict:
    payload = {"strategy_uid": uid, "name": name, **kw}
    return {
        "id": hash(uid) % 10000,
        "name": name,
        "strategy_json": json.dumps(payload),
    }


@pytest.fixture
def data_source() -> tuple[ProjectArchiveDataSource, dict, dict, dict]:
    strategies = {}
    datasets = {}
    validations = {}

    def get_strategies():
        return list(strategies.values())

    def get_dataset(did: int):
        return datasets.get(did)

    def get_validation(uid: str):
        return validations.get(uid)

    ds = ProjectArchiveDataSource(get_strategies, get_dataset, get_validation)
    return ds, strategies, datasets, validations


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_get_strategy_found(data_source):
    """get_strategy must return a strategy dict when UID matches."""
    ds, strats, dss, vals = data_source
    strats["s1"] = _strategy_row("s1", name="Strategy One", conditions=[])
    row = ds.get_strategy("s1")
    assert row is not None
    assert row["name"] == "Strategy One"
    payload = json.loads(row["strategy_json"])
    assert payload["strategy_uid"] == "s1"


def test_get_dataset_found(data_source):
    """get_dataset must return a dict when dataset ID exists."""
    ds, strats, dss, vals = data_source
    dss[1] = {"id": 1, "symbol": "ES", "timeframe": "1min"}
    row = ds.get_dataset(1)
    assert row is not None
    assert row["symbol"] == "ES"


def test_get_validation_found(data_source):
    """get_validation_result must return a dict when validation exists."""
    ds, strats, dss, vals = data_source
    vals["s1"] = {"passed": True, "elimination": {"passed": True}}
    row = ds.get_validation_result("s1")
    assert row is not None
    assert row["passed"] is True


def test_get_validation_accepts_pipeline_result(data_source):
    """PipelineResult dataclasses must be converted to archive dicts."""
    ds, strats, dss, vals = data_source
    vals["s1"] = PipelineResult(
        baseline_metrics={"total_trades": 3},
        elimination_result={"passed": True},
    )
    row = ds.get_validation_result("s1")
    assert row is not None
    assert row["baseline_metrics"] == {"total_trades": 3}
    assert row["elimination_result"] == {"passed": True}


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------


def test_get_strategy_missing_uid_returns_none(data_source):
    """Non-existent UID must return None."""
    ds, strats, dss, vals = data_source
    strats["s1"] = _strategy_row("s1")
    assert ds.get_strategy("nonexistent") is None


def test_get_strategy_malformed_json_returns_none(data_source):
    """Malformed strategy_json must be skipped and return None."""
    ds, strats, dss, vals = data_source
    strats["bad"] = {"id": 1, "name": "Bad", "strategy_json": "not-json{{{"}
    assert ds.get_strategy("s1") is None


def test_get_strategy_non_dict_json_skipped(data_source):
    """Non-dict strategy_json must be skipped."""
    ds, strats, dss, vals = data_source
    strats["arr"] = {"id": 2, "name": "Array", "strategy_json": '["a"]'}
    assert ds.get_strategy("s1") is None


def test_get_missing_dataset_returns_none(data_source):
    """Non-existent dataset ID must return None."""
    ds, strats, dss, vals = data_source
    assert ds.get_dataset(999) is None


def test_get_missing_validation_returns_none(data_source):
    """Non-existent UID validation must return None."""
    ds, strats, dss, vals = data_source
    assert ds.get_validation_result("no-such-uid") is None


# ---------------------------------------------------------------------------
# No UI import
# ---------------------------------------------------------------------------


def test_no_ui_imports():
    """Module must not import PySide6 or UI modules."""
    import app.services.archive_project_data_source as mod

    module_names = set()
    for _name, obj in vars(mod).items():
        module_name = getattr(obj, "__module__", "")
        if module_name:
            module_names.add(module_name)

    assert not any(name == "PySide6" or name.startswith("PySide6.") for name in module_names)
    assert not any(name == "app.ui" or name.startswith("app.ui.") for name in module_names)


def test_service_package_exports_project_archive_data_source():
    """Service package should expose ProjectArchiveDataSource."""
    from app.services import ProjectArchiveDataSource as ExportedDataSource

    assert ExportedDataSource is ProjectArchiveDataSource
