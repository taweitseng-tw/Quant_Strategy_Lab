"""Tests for DatasetRepository — Task 032D."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.models.dataset import DatasetMeta
from repository.db import DatabaseManager
from repository.dataset_repo import DatasetRepository
from repository.project_repo import ProjectRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project_with_db(tmp_path: Path) -> tuple[ProjectRepository, DatabaseManager]:
    repo = ProjectRepository()
    root = tmp_path / "proj"
    repo.create_project("test-proj", root)
    return repo, repo.db


def _make_meta(**overrides) -> DatasetMeta:
    defaults = {
        "name": "test-ds",
        "project_id": 1,
        "symbol": "ES",
        "timeframe": "1min",
        "source_type": "csv",
        "source_path": "/data/test.csv",
        "normalized_path": "/data/norm/test.csv",
        "row_count": 1000,
        "start_datetime": "2024-01-02 08:30:00",
        "end_datetime": "2024-01-02 18:00:00",
    }
    defaults.update(overrides)
    return DatasetMeta(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_dir() -> Path:
    base = Path(tempfile.mkdtemp())
    yield base
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture
def repo_and_db(tmp_dir):
    repo, db = _make_project_with_db(tmp_dir)
    yield repo, db
    repo.close()


# ---------------------------------------------------------------------------
# Insert + retrieve
# ---------------------------------------------------------------------------


def test_insert_and_get_by_name(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    meta = _make_meta(name="es-1min")
    row_id = dr.insert(meta)
    assert row_id is not None
    assert row_id > 0

    loaded = dr.get_by_name("es-1min")
    assert loaded is not None
    assert loaded.name == "es-1min"
    assert loaded.symbol == "ES"
    assert loaded.timeframe == "1min"
    assert loaded.row_count == 1000
    assert isinstance(loaded.created_at, datetime)


def test_get_by_name_nonexistent(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    assert dr.get_by_name("nonexistent") is None


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_all_returns_newest_first(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    dr.insert(_make_meta(name="first"))
    dr.insert(_make_meta(name="second"))

    results = dr.list_all()
    assert len(results) == 2
    assert results[0].name == "second"


def test_list_all_empty(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    assert dr.list_all() == []


# ---------------------------------------------------------------------------
# Save (insert-or-update)
# ---------------------------------------------------------------------------


def test_save_inserts_new(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    row_id = dr.save(_make_meta(name="new-ds"))
    assert row_id > 0
    assert dr.get_by_name("new-ds") is not None


def test_save_updates_existing(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    dr.insert(_make_meta(name="updatable", row_count=100))

    updated = _make_meta(name="updatable", row_count=9999)
    result = dr.save(updated)
    assert result == 0  # update, not insert

    loaded = dr.get_by_name("updatable")
    assert loaded.row_count == 9999


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_changes_all_fields(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    dr.insert(_make_meta(name="orig", symbol="ES", row_count=500))

    changed = _make_meta(name="orig", symbol="NQ", row_count=2000, timeframe="5min")
    assert dr.update(changed) is True

    loaded = dr.get_by_name("orig")
    assert loaded.symbol == "NQ"
    assert loaded.row_count == 2000
    assert loaded.timeframe == "5min"


def test_update_nonexistent(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    assert dr.update(_make_meta(name="ghost")) is False


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_removes_row(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    dr.insert(_make_meta(name="deletable"))
    assert dr.delete("deletable") is True
    assert dr.get_by_name("deletable") is None


def test_delete_nonexistent(repo_and_db):
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    assert dr.delete("no-such") is False


# ---------------------------------------------------------------------------
# created_at round-trip
# ---------------------------------------------------------------------------


def test_created_at_is_datetime(repo_and_db):
    """insert() sets created_at to now() regardless of input — verify type."""
    repo, db = repo_and_db
    dr = DatasetRepository(db)
    meta = _make_meta(name="dt-test")
    dr.insert(meta)

    loaded = dr.get_by_name("dt-test")
    assert isinstance(loaded.created_at, datetime)
    # created_at is set by the repository to the current time, so it
    # must be recent (within the last 60 seconds).
    now = datetime.now(timezone.utc)
    delta = (now - loaded.created_at).total_seconds()
    assert 0 <= delta < 60


# ---------------------------------------------------------------------------
# get_raw_by_id (Task 061A-Impl)
# ---------------------------------------------------------------------------


def test_get_raw_by_id_returns_row(repo_and_db):
    """get_raw_by_id must return a dict for an existing dataset."""
    proj_repo, db = repo_and_db
    from repository.dataset_repo import DatasetRepository
    from core.models.dataset import DatasetMeta

    dr = DatasetRepository(db)
    meta = DatasetMeta(name="ds-raw-test", symbol="ES", timeframe="1min")
    row_id = dr.insert(meta)
    assert row_id is not None

    raw = dr.get_raw_by_id(row_id)
    assert raw is not None
    assert raw["name"] == "ds-raw-test"
    assert raw["symbol"] == "ES"
    assert "normalized_path" in raw, "raw dataset dict must include normalized_path"


def test_get_raw_by_id_nonexistent_returns_none(repo_and_db):
    """get_raw_by_id must return None for a missing dataset."""
    proj_repo, db = repo_and_db
    from repository.dataset_repo import DatasetRepository

    dr = DatasetRepository(db)
    raw = dr.get_raw_by_id(99999)
    assert raw is None
