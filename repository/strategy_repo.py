"""Strategy repository — persists Strategy definitions as JSON in project.sqlite.

Uses :func:`dataclasses.asdict` for serialisation and
`core.serialization.strategy_serializer.strategy_from_dict` for deserialisation.
No PySide6 / UI imports.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from core.models.strategy import Strategy
from repository.db import DatabaseManager


class StrategyRepository:
    """CRUD for strategy rows in the ``strategies`` table.

    Requires an open :class:`DatabaseManager` (e.g. from an open project).
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # write
    # ------------------------------------------------------------------

    def insert(self, strategy: Strategy, *, project_id: int | None = None) -> int:
        """Insert a new strategy row.  Returns the new row id."""
        now = datetime.now(timezone.utc).isoformat()
        strategy_json = json.dumps(asdict(strategy), ensure_ascii=False)
        cur = self._db.connection.execute(
            "INSERT INTO strategies "
            "(project_id, name, strategy_json, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (project_id, strategy.name, strategy_json, now, now),
        )
        self._db.connection.commit()
        return cur.lastrowid

    def update(self, strategy: Strategy) -> bool:
        """Update the JSON for an existing strategy row by name.

        Returns ``True`` if a row was updated, ``False`` if no matching name
        was found.
        """
        now = datetime.now(timezone.utc).isoformat()
        strategy_json = json.dumps(asdict(strategy), ensure_ascii=False)
        cur = self._db.connection.execute(
            "UPDATE strategies SET strategy_json = ?, updated_at = ? WHERE name = ?",
            (strategy_json, now, strategy.name),
        )
        self._db.connection.commit()
        return cur.rowcount > 0

    def save(self, strategy: Strategy, *, project_id: int | None = None) -> int:
        """Insert-or-update: insert if *strategy.name* is new, else update.

        Returns the row id (insert) or 0 (update).
        """
        existing = self.get_by_name(strategy.name)
        if existing is not None:
            self.update(strategy)
            return 0
        return self.insert(strategy, project_id=project_id)

    # ------------------------------------------------------------------
    # read
    # ------------------------------------------------------------------

    def get_by_name(self, name: str) -> Strategy | None:
        """Load a strategy by its ``name`` column."""
        row = self._db.connection.execute(
            "SELECT * FROM strategies WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_strategy(row)

    def list_all(self) -> list[Strategy]:
        """Return every saved strategy, newest first."""
        rows = self._db.connection.execute(
            "SELECT * FROM strategies ORDER BY created_at DESC, id DESC"
        ).fetchall()
        return [_row_to_strategy(r) for r in rows]

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    def delete(self, name: str) -> bool:
        """Delete a strategy row by name.

        Returns ``True`` if a row was removed.
        """
        cur = self._db.connection.execute(
            "DELETE FROM strategies WHERE name = ?", (name,)
        )
        self._db.connection.commit()
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _row_to_strategy(row: "sqlite3.Row") -> Strategy:
    """Reconstruct a :class:`Strategy` from a sqlite3.Row."""
    from core.serialization.strategy_serializer import strategy_from_dict
    data = json.loads(row["strategy_json"])
    return strategy_from_dict(data, strict=False, source="db")
