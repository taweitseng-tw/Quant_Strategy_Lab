"""Tests for CSV importer, normalizer, and dataset repository — Task 003."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from core.models.dataset import DatasetMeta
from data_engine.importers.csv_importer import CsvImporter
from data_engine.normalizer import INTERNAL_COLUMNS, NormalizerError, normalize
from repository.dataset_repo import DatasetRepository
from repository.db import DatabaseManager
from repository.project_repo import ProjectRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "sample_ohlcv.csv"


def _write_temp_csv(dir_path: Path, content: str, name: str = "test.csv") -> Path:
    p = dir_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _make_project_with_db(tmp_path: Path) -> tuple[ProjectRepository, DatabaseManager, Path]:
    """Create a temp project and return (repo, db, root_path)."""
    repo = ProjectRepository()
    root = tmp_path / "proj"
    repo.create_project("test-proj", root)
    return repo, repo.db, root


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_dir() -> Path:
    base = Path(tempfile.mkdtemp())
    yield base
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture
def importer() -> CsvImporter:
    return CsvImporter()


# ---------------------------------------------------------------------------
# Normalizer — happy path
# ---------------------------------------------------------------------------


def test_normalize_standard_two_column_datetime():
    """Date + Time columns should be combined into a single datetime column."""
    df = pd.DataFrame({
        "Date": ["2024-01-02", "2024-01-02", "2024-01-02"],
        "Time": ["08:30", "08:31", "08:32"],
        "Open": [4500.0, 4508.0, 4510.0],
        "High": [4512.0, 4515.0, 4510.0],
        "Low": [4498.0, 4505.0, 4495.0],
        "Close": [4508.0, 4510.0, 4498.0],
        "Volume": [12500, 9800, 11200],
    })
    result = normalize(df)
    assert list(result.columns) == list(INTERNAL_COLUMNS)
    assert len(result) == 3
    assert result["datetime"].dtype.kind == "M"  # datetime64
    assert result["open"].iloc[0] == 4500.0


def test_normalize_single_datetime_column():
    """A single datetime column should be parsed directly."""
    df = pd.DataFrame({
        "datetime": ["2024-01-02 08:30:00", "2024-01-02 08:31:00"],
        "open": [100.0, 101.0],
        "high": [102.0, 103.0],
        "low": [99.0, 100.0],
        "close": [101.0, 102.0],
        "volume": [5000, 6000],
    })
    result = normalize(df)
    assert list(result.columns) == list(INTERNAL_COLUMNS)
    assert len(result) == 2


def test_normalize_pascal_case_columns():
    """MultiCharts-style PascalCase column names should be mapped."""
    df = pd.DataFrame({
        "Date": ["2024-01-02"],
        "Time": ["08:30"],
        "Open": [4500.0],
        "High": [4512.0],
        "Low": [4498.0],
        "Close": [4508.0],
        "Volume": [12500],
    })
    result = normalize(df)
    assert list(result.columns) == list(INTERNAL_COLUMNS)


def test_normalize_sorts_by_datetime():
    """Output must be sorted by datetime ascending."""
    df = pd.DataFrame({
        "datetime": ["2024-01-02 08:32", "2024-01-02 08:30", "2024-01-02 08:31"],
        "open": [4510.0, 4500.0, 4508.0],
        "high": [4510.0, 4512.0, 4515.0],
        "low": [4495.0, 4498.0, 4505.0],
        "close": [4498.0, 4508.0, 4510.0],
        "volume": [11200, 12500, 9800],
    })
    result = normalize(df)
    assert result["datetime"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# Normalizer — error cases
# ---------------------------------------------------------------------------


def test_normalize_missing_ohlcv_columns_raises():
    """If OHLCV columns cannot be mapped, NormalizerError is raised."""
    df = pd.DataFrame({
        "Date": ["2024-01-02"],
        "Time": ["08:30"],
        "Foo": [1.0],
        "Bar": [2.0],
    })
    with pytest.raises(NormalizerError, match="Required columns missing"):
        normalize(df)


def test_normalize_no_datetime_column_raises():
    """A DataFrame with no recognizable datetime column must fail."""
    df = pd.DataFrame({
        "open": [100.0],
        "high": [102.0],
        "low": [99.0],
        "close": [101.0],
        "volume": [5000],
    })
    with pytest.raises(NormalizerError, match="No datetime column"):
        normalize(df)


def test_normalize_duplicate_datetimes_raises():
    """Duplicate timestamps must be rejected."""
    df = pd.DataFrame({
        "datetime": ["2024-01-02 08:30", "2024-01-02 08:30"],
        "open": [100.0, 101.0],
        "high": [102.0, 103.0],
        "low": [99.0, 100.0],
        "close": [101.0, 102.0],
        "volume": [5000, 6000],
    })
    with pytest.raises(NormalizerError, match="duplicate datetime"):
        normalize(df)


def test_normalize_malformed_datetime_raises():
    """Rows with unparseable datetimes must raise NormalizerError (no silent drop)."""
    df = pd.DataFrame({
        "datetime": ["not-a-date", "2024-01-02 08:31:00"],
        "open": [100.0, 101.0],
        "high": [102.0, 103.0],
        "low": [99.0, 100.0],
        "close": [101.0, 102.0],
        "volume": [5000, 6000],
    })
    with pytest.raises(NormalizerError, match="unparseable datetime"):
        normalize(df)


# ---------------------------------------------------------------------------
# CsvImporter — happy path
# ---------------------------------------------------------------------------


def test_import_sample_csv(importer, tmp_dir):
    """Import the sample MultiCharts-style CSV and verify normalized output."""
    df, meta = importer.import_file(SAMPLE_CSV, tmp_dir, symbol="ES", timeframe="1min")

    assert list(df.columns) == list(INTERNAL_COLUMNS)
    assert len(df) == 10
    assert df["datetime"].dtype.kind == "M"
    assert meta.symbol == "ES"
    assert meta.timeframe == "1min"
    assert meta.row_count == 10
    assert meta.source_type == "csv"


def test_import_saves_normalized_csv(importer, tmp_dir):
    """The normalized CSV must be written to data/raw/ inside the project."""
    _, meta = importer.import_file(SAMPLE_CSV, tmp_dir, symbol="ES", timeframe="1min")

    out_path = Path(meta.normalized_path)
    assert out_path.is_file()
    assert "data" in out_path.parts and "raw" in out_path.parts

    # Verify content round-trips.
    df2 = pd.read_csv(out_path)
    assert list(df2.columns) == list(INTERNAL_COLUMNS)
    assert len(df2) == 10


def test_import_file_not_found_raises(importer, tmp_dir):
    """A nonexistent source path must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        importer.import_file(tmp_dir / "nope.csv", tmp_dir)


def test_import_empty_csv_raises(importer, tmp_dir):
    """An empty CSV must raise NormalizerError."""
    p = _write_temp_csv(tmp_dir, "Date,Time,Open,High,Low,Close,Volume\n")
    with pytest.raises(NormalizerError, match="no data rows"):
        importer.import_file(p, tmp_dir)


def test_import_missing_columns_raises(importer, tmp_dir):
    """A CSV without OHLCV columns must raise NormalizerError."""
    csv_content = "Date,Time,Foo,Bar\n2024-01-02,08:30,1,2\n"
    p = _write_temp_csv(tmp_dir, csv_content)
    with pytest.raises(NormalizerError):
        importer.import_file(p, tmp_dir)


# ---------------------------------------------------------------------------
# DatasetRepository — DB persistence
# ---------------------------------------------------------------------------


def test_dataset_repo_insert_and_retrieve(tmp_dir):
    """Insert a dataset row and then read it back — verify project_id and
    created_at type."""
    repo, db, root = _make_project_with_db(tmp_dir)
    ds_repo = DatasetRepository(db)

    meta = DatasetMeta(
        name="test-ds",
        project_id=42,
        symbol="ES",
        timeframe="1min",
        row_count=10,
        normalized_path=str(root / "data" / "raw" / "test_normalized.csv"),
    )
    row_id = ds_repo.insert(meta)
    assert row_id is not None

    got = ds_repo.get_by_name("test-ds")
    assert got is not None
    assert got.name == "test-ds"
    assert got.project_id == 42
    assert got.symbol == "ES"
    assert got.timeframe == "1min"
    assert got.row_count == 10

    # created_at must round-trip as datetime, not str.
    from datetime import datetime
    assert isinstance(got.created_at, datetime)

    repo.close()


def test_dataset_repo_list_all(tmp_dir):
    """list_all() should return multiple rows in insertion order (newest first)."""
    repo, db, root = _make_project_with_db(tmp_dir)
    ds_repo = DatasetRepository(db)

    ds_repo.insert(DatasetMeta(name="ds-a"))
    ds_repo.insert(DatasetMeta(name="ds-b"))

    all_ds = ds_repo.list_all()
    assert len(all_ds) == 2
    assert all_ds[0].name == "ds-b"  # newest first

    repo.close()


def test_dataset_repo_get_nonexistent(tmp_dir):
    """get_by_name on an unknown name must return None."""
    repo, db, root = _make_project_with_db(tmp_dir)
    ds_repo = DatasetRepository(db)

    assert ds_repo.get_by_name("no-such-ds") is None

    repo.close()


# ---------------------------------------------------------------------------
# End-to-end: import + persist
# ---------------------------------------------------------------------------


def test_e2e_import_and_persist(importer, tmp_dir):
    """Full flow: create project, import CSV, persist dataset metadata."""
    repo, db, root = _make_project_with_db(tmp_dir)

    df, meta = importer.import_file(SAMPLE_CSV, root, symbol="ES", timeframe="1min")
    # Wire project_id from the project row.
    proj_row = db.connection.execute("SELECT id FROM projects LIMIT 1").fetchone()
    meta.project_id = proj_row["id"]

    ds_repo = DatasetRepository(db)
    row_id = ds_repo.insert(meta)
    assert row_id is not None

    got = ds_repo.get_by_name(meta.name)
    assert got is not None
    assert got.row_count == 10
    assert got.symbol == "ES"
    assert got.project_id == proj_row["id"]

    from datetime import datetime
    assert isinstance(got.created_at, datetime)

    repo.close()
