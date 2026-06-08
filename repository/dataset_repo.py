"""Dataset repository — persists dataset metadata to project.sqlite."""

from __future__ import annotations

from datetime import datetime, timezone

from core.models.dataset import DatasetMeta
from repository.db import DatabaseManager


class DatasetRepository:
    """CRUD for dataset metadata rows in the ``datasets`` table.

    Requires an open :class:`DatabaseManager` (e.g. from an open project).
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def insert(self, meta: DatasetMeta) -> int:
        """Insert a new dataset row.  Returns the new row id."""
        now = datetime.now(timezone.utc).isoformat()
        cur = self._db.connection.execute(
            "INSERT INTO datasets "
            "(project_id, name, symbol, timeframe, source_type, source_path, "
            "normalized_path, row_count, start_datetime, end_datetime, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                meta.project_id,
                meta.name,
                meta.symbol,
                meta.timeframe,
                meta.source_type,
                meta.source_path,
                meta.normalized_path,
                meta.row_count,
                meta.start_datetime,
                meta.end_datetime,
                now,
            ),
        )
        self._db.connection.commit()
        return cur.lastrowid

    def get_by_name(self, name: str) -> DatasetMeta | None:
        row = self._db.connection.execute(
            "SELECT * FROM datasets WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_meta(row)

    def get_raw_by_id(self, dataset_id: int) -> dict | None:
        """Return a dataset row as a raw dict, or None."""
        row = self._db.connection.execute(
            "SELECT * FROM datasets WHERE id = ?", (dataset_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_all(self) -> list[DatasetMeta]:
        rows = self._db.connection.execute(
            "SELECT * FROM datasets ORDER BY created_at DESC"
        ).fetchall()
        return [_row_to_meta(r) for r in rows]

    def save(self, meta: DatasetMeta) -> int:
        """Insert-or-update: insert if *meta.name* is new, else update.

        Returns the row id (insert) or 0 (update).
        """
        existing = self.get_by_name(meta.name)
        if existing is not None:
            self.update(meta)
            return 0
        return self.insert(meta)

    def update(self, meta: DatasetMeta) -> bool:
        """Update all metadata columns for an existing row by name.

        Returns ``True`` if a row was updated.
        """
        cur = self._db.connection.execute(
            "UPDATE datasets SET "
            "project_id=?, symbol=?, timeframe=?, source_type=?, source_path=?, "
            "normalized_path=?, row_count=?, start_datetime=?, end_datetime=? "
            "WHERE name=?",
            (
                meta.project_id, meta.symbol, meta.timeframe, meta.source_type,
                meta.source_path, meta.normalized_path, meta.row_count,
                meta.start_datetime, meta.end_datetime, meta.name,
            ),
        )
        self._db.connection.commit()
        return cur.rowcount > 0

    def delete(self, name: str) -> bool:
        """Delete a dataset row by name.

        Returns ``True`` if a row was removed.
        """
        cur = self._db.connection.execute(
            "DELETE FROM datasets WHERE name = ?", (name,)
        )
        self._db.connection.commit()
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _row_to_meta(row: "sqlite3.Row") -> DatasetMeta:
    """Convert a sqlite3.Row to a DatasetMeta, converting created_at to datetime."""
    return DatasetMeta(
        name=row["name"],
        project_id=row["project_id"],
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        source_type=row["source_type"],
        source_path=row["source_path"],
        normalized_path=row["normalized_path"],
        row_count=row["row_count"],
        start_datetime=row["start_datetime"],
        end_datetime=row["end_datetime"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
