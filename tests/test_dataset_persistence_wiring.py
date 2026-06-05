"""Tests for DataService ↔ DatasetRepository persistence wiring — Task 032D."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from repository.dataset_repo import DatasetRepository
from repository.db import DatabaseManager
from repository.project_repo import ProjectRepository
from app.services.data_service import DataService


SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "sample_ohlcv.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project_with_db(tmp_path: Path) -> tuple[ProjectRepository, DatabaseManager]:
    repo = ProjectRepository()
    root = tmp_path / "proj"
    repo.create_project("test-proj", root)
    return repo, repo.db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_dir() -> Path:
    base = Path(tempfile.mkdtemp())
    yield base
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture
def db(tmp_dir) -> DatabaseManager:
    repo, db = _make_project_with_db(tmp_dir)
    yield db
    repo.close()


# ---------------------------------------------------------------------------
# Persistence wiring
# ---------------------------------------------------------------------------


def test_import_with_db_persists_metadata(db):
    svc = DataService()
    svc.set_db(db)

    df, meta, qr = svc.import_file(SAMPLE_CSV, symbol="ES", timeframe="1min")

    assert len(df) > 0
    assert meta.name  # should be auto-derived from filename

    # Verify it was persisted.
    dr = DatasetRepository(db)
    loaded = dr.get_by_name(meta.name)
    assert loaded is not None
    assert loaded.symbol == "ES"
    assert loaded.timeframe == "1min"
    assert loaded.row_count == meta.row_count


def test_import_without_db_does_not_crash():
    svc = DataService()  # no DB set
    df, meta, qr = svc.import_file(SAMPLE_CSV, symbol="NQ")
    assert len(df) > 0
    assert meta is not None


def test_import_with_db_then_load_back_matches(db):
    svc = DataService()
    svc.set_db(db)

    _, meta, _ = svc.import_file(SAMPLE_CSV, symbol="GC", timeframe="5min")

    dr = DatasetRepository(db)
    loaded = dr.get_by_name(meta.name)

    assert loaded.symbol == "GC"
    assert loaded.timeframe == "5min"
    assert loaded.row_count == meta.row_count
    assert loaded.start_datetime == meta.start_datetime
    assert loaded.end_datetime == meta.end_datetime


def test_reimport_updates_existing_row(db):
    svc = DataService()
    svc.set_db(db)

    # First import.
    _, meta1, _ = svc.import_file(SAMPLE_CSV, symbol="CL", timeframe="1min")

    dr = DatasetRepository(db)
    first = dr.get_by_name(meta1.name)
    assert first.symbol == "CL"

    # Second import with different symbol.
    _, meta2, _ = svc.import_file(SAMPLE_CSV, symbol="CL_v2", timeframe="1min")

    second = dr.get_by_name(meta2.name)
    assert second is not None
    assert second.symbol == "CL_v2"  # updated


def test_db_can_be_cleared(db):
    svc = DataService()
    svc.set_db(db)

    _, meta, _ = svc.import_file(SAMPLE_CSV, symbol="TEST")

    # Clear the DB.
    svc.set_db(None)

    # Import again — should not crash.
    _, meta2, _ = svc.import_file(SAMPLE_CSV, symbol="TEST2")
    assert meta2 is not None


def test_no_ohlcv_data_in_sqlite(db):
    svc = DataService()
    svc.set_db(db)

    svc.import_file(SAMPLE_CSV)

    # Verify the strategies table (for schema context) and datasets table
    # only contain metadata, NOT OHLCV rows.
    conn = db.connection
    row = conn.execute("SELECT COUNT(*) as cnt FROM datasets").fetchone()
    assert row["cnt"] >= 1

    # There should be no table with OHLCV bars — the datasets table has
    # schema: id, project_id, name, …, row_count, start_datetime, end_datetime, created_at
    cols = [c[1] for c in conn.execute("PRAGMA table_info(datasets)").fetchall()]
    ohlcv_fields = {"open", "high", "low", "close", "volume"}
    assert not ohlcv_fields.intersection(cols)


def test_list_saved_datasets(db):
    """Importing the same file twice with different symbols updates the
    same row (name is derived from filename), so list_all returns 1 row."""
    svc = DataService()
    svc.set_db(db)

    svc.import_file(SAMPLE_CSV, symbol="A")
    svc.import_file(SAMPLE_CSV, symbol="B")  # updates same row

    dr = DatasetRepository(db)
    all_ds = dr.list_all()
    assert len(all_ds) == 1
    assert all_ds[0].symbol == "B"  # updated value
