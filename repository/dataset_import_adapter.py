"""Dataset import adapter — duplicate-reject insert-only slice for archive imports.

This module only inserts new dataset rows.  It does **not** overwrite,
update, upsert, rename, skip, or merge existing datasets.  No audit
or filesystem writes.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ImportDatasetDTO:
    """Immutable DTO for an imported dataset row.

    Fields
    ------
    name : str
        Dataset name.
    symbol : str
        Instrument symbol from the archive.
    timeframe : str
        Bar timeframe from the archive.
    snapshot_hash : str
        SHA-256 of ``ohlcv_snapshot.csv`` from manifest.  Primary dedup key
        when non-empty and column exists.
    source_type : str
        Always ``'archive_import'`` for archive-imported datasets.
    source_path : str
        Original archive source path (folder or zip path).
    normalized_path : str
        Final destination path after staging.
    row_count : int
        Number of rows in the dataset snapshot.
    start_datetime : str
        First bar timestamp.
    end_datetime : str
        Last bar timestamp.
    project_id : int | None
        Project database foreign key, if available.
    """
    name: str
    symbol: str
    timeframe: str
    snapshot_hash: str = ""
    source_type: str = "archive_import"
    source_path: str = ""
    normalized_path: str = ""
    row_count: int = 0
    start_datetime: str = ""
    end_datetime: str = ""
    project_id: int | None = None


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class DatasetRepoAdapterError(Exception):
    """Base for dataset repository adapter errors."""


class DuplicateDatasetError(DatasetRepoAdapterError):
    """Raised when a dataset with the same identity already exists."""


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class DatasetRepoAdapter:
    """Repository adapter for inserting imported dataset rows.

    Insert-only, duplicate-reject semantics.  No overwrite, update,
    or upsert.  Probes schema at init for ``snapshot_hash`` column.
    """

    _INSERT_SQL_POST = """
        INSERT INTO datasets
            (project_id, name, symbol, timeframe, source_type, source_path,
             normalized_path, row_count, start_datetime, end_datetime,
             snapshot_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    _INSERT_SQL_OLD = """
        INSERT INTO datasets
            (project_id, name, symbol, timeframe, source_type, source_path,
             normalized_path, row_count, start_datetime, end_datetime,
             created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        cursor = connection.execute("PRAGMA table_info(datasets)")
        column_names = {row[1] for row in cursor.fetchall()}
        self._has_snapshot_hash = "snapshot_hash" in column_names

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def insert_dataset(self, dto: ImportDatasetDTO) -> int:
        """Insert a new dataset row and commit.

        Auto-commit wrapper.  Rolls back only on SQLite write / commit
        failure.  Validation and duplicate errors do NOT rollback.
        """
        try:
            row_id = self._insert_dataset_core(dto)
        except DatasetRepoAdapterError as exc:
            if isinstance(exc.__cause__, sqlite3.Error):
                self._conn.rollback()
            raise
        try:
            self._conn.commit()
            return row_id
        except sqlite3.Error as exc:
            self._conn.rollback()
            raise DatasetRepoAdapterError(
                f"Failed to commit dataset '{dto.name}': {exc}"
            ) from exc

    def insert_dataset_no_commit(self, dto: ImportDatasetDTO) -> int:
        """Insert without commit or rollback.  Caller owns the transaction."""
        return self._insert_dataset_core(dto)

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _insert_dataset_core(self, dto: ImportDatasetDTO) -> int:
        """Validate, dedup, INSERT (no commit/rollback)."""
        if not dto.name or not dto.name.strip():
            raise DatasetRepoAdapterError("Dataset name is required.")
        if not dto.symbol or not dto.symbol.strip():
            raise DatasetRepoAdapterError("Dataset symbol is required.")

        self._reject_duplicate(dto)

        now = datetime.now(timezone.utc).isoformat()
        try:
            if self._has_snapshot_hash:
                cur = self._conn.execute(
                    self._INSERT_SQL_POST,
                    (
                        dto.project_id, dto.name, dto.symbol, dto.timeframe,
                        dto.source_type, dto.source_path, dto.normalized_path,
                        dto.row_count, dto.start_datetime, dto.end_datetime,
                        dto.snapshot_hash, now,
                    ),
                )
            else:
                cur = self._conn.execute(
                    self._INSERT_SQL_OLD,
                    (
                        dto.project_id, dto.name, dto.symbol, dto.timeframe,
                        dto.source_type, dto.source_path, dto.normalized_path,
                        dto.row_count, dto.start_datetime, dto.end_datetime,
                        now,
                    ),
                )
            return cur.lastrowid
        except sqlite3.Error as exc:
            raise DatasetRepoAdapterError(
                f"Failed to insert dataset '{dto.name}': {exc}"
            ) from exc

    def _dedup_where(self, dto: ImportDatasetDTO) -> tuple[str, list]:
        """Return SQL WHERE + params based on available schema."""
        if self._has_snapshot_hash and dto.snapshot_hash:
            return "snapshot_hash = ?", [dto.snapshot_hash]
        if dto.source_path:
            return "symbol = ? AND timeframe = ? AND source_path = ?", [
                dto.symbol, dto.timeframe, dto.source_path,
            ]
        return "symbol = ? AND timeframe = ?", [dto.symbol, dto.timeframe]

    def _reject_duplicate(self, dto: ImportDatasetDTO) -> None:
        """Raise DuplicateDatasetError if a matching dataset exists."""
        where, params = self._dedup_where(dto)
        existing = self._conn.execute(
            f"SELECT id FROM datasets WHERE {where}", params
        ).fetchone()
        if existing is not None:
            raise DuplicateDatasetError(
                f"Dataset '{dto.name}' ({dto.symbol}/{dto.timeframe}) "
                f"already exists (row id={existing['id']})."
            )
