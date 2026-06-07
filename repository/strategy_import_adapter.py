"""Strategy import adapter — duplicate-reject insert-only slice for archive imports.

This module only inserts new strategy rows.  It does **not** overwrite,
update, upsert, rename, skip, or merge existing strategies.  No dataset,
validation, audit, or filesystem writes.

Duplicate rejection is by ``strategy_uid`` — the adapter scans existing
``strategies.strategy_json`` payloads to find a matching UID.  No schema
migration is required.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ImportStrategyDTO:
    """Immutable DTO for an imported strategy row.

    All fields are required except *project_id* and *dataset_id*.

    Fields
    ------
    name : str
        Display / human-readable strategy name.
    strategy_json : str
        Full serialized strategy JSON (includes rule blocks, provenance).
        Must contain a ``"strategy_uid"`` field that matches *strategy_uid*.
    strategy_uid : str
        Required unique import identifier from the archive.  Duplicate-reject
        key — no two rows with the same UID may be inserted.
    project_id : int | None
        Project database foreign key, if applicable.
    dataset_id : int | None
        Dataset foreign key, if resolved at insert time.
    """
    name: str
    strategy_json: str
    strategy_uid: str
    project_id: int | None = None
    dataset_id: int | None = None


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class StrategyRepoAdapterError(Exception):
    """Base for strategy repository adapter errors."""


class DuplicateStrategyUIDError(StrategyRepoAdapterError):
    """Raised when a strategy with the same UID already exists."""


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class StrategyRepoAdapter:
    """Repository adapter for inserting imported strategy rows.

    Insert-only, duplicate-reject semantics.  Does **not** overwrite,
    update, or merge existing rows.
    """

    _INSERT_SQL = """
        INSERT INTO strategies
            (project_id, name, strategy_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """

    _SCAN_ALL_SQL = "SELECT id, name, strategy_json FROM strategies ORDER BY id"

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def _insert_strategy_core(self, dto: ImportStrategyDTO) -> int:
        """Shared private: validate, scan for duplicates, INSERT (no commit/rollback).

        Parameters
        ----------
        dto : ImportStrategyDTO

        Returns
        -------
        int
            The new row id (uncommitted).

        Raises
        ------
        StrategyRepoAdapterError
            If *dto* fields are invalid, *strategy_json* is malformed, or
            the SQLite execution fails.
        DuplicateStrategyUIDError
            If a strategy with the same *dto.strategy_uid* already exists.
        """
        # -- validate DTO fields -------------------------------------------
        if not dto.strategy_uid or not dto.strategy_uid.strip():
            raise StrategyRepoAdapterError(
                "strategy_uid is required and must be non-empty."
            )
        if not dto.name or not dto.name.strip():
            raise StrategyRepoAdapterError(
                "Strategy name is required and must be non-empty."
            )
        if not dto.strategy_json or not dto.strategy_json.strip():
            raise StrategyRepoAdapterError(
                "strategy_json is required and must be non-empty."
            )

        # -- validate + parse strategy_json ---------------------------------
        try:
            payload = json.loads(dto.strategy_json)
        except (json.JSONDecodeError, ValueError) as exc:
            raise StrategyRepoAdapterError(
                f"strategy_json is not valid JSON: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise StrategyRepoAdapterError(
                "strategy_json must be a JSON object (dict)."
            )

        payload_uid = payload.get("strategy_uid")
        if not payload_uid:
            raise StrategyRepoAdapterError(
                "strategy_json is missing required field 'strategy_uid'."
            )
        if payload_uid != dto.strategy_uid:
            raise StrategyRepoAdapterError(
                f"strategy_json['strategy_uid'] ('{payload_uid}') does not match "
                f"dto.strategy_uid ('{dto.strategy_uid}')."
            )

        # -- duplicate-reject by UID (scan existing strategy_json payloads) --
        self._reject_duplicate_uid(dto.strategy_uid)

        # -- insert (no commit) ---------------------------------------------
        now = datetime.now(timezone.utc).isoformat()
        try:
            cur = self._conn.execute(
                self._INSERT_SQL,
                (dto.project_id, dto.name, dto.strategy_json, now, now),
            )
            return cur.lastrowid
        except sqlite3.Error as exc:
            raise StrategyRepoAdapterError(
                f"Failed to insert strategy '{dto.name}': {exc}"
            ) from exc

    def insert_strategy(self, dto: ImportStrategyDTO) -> int:
        """Insert a new strategy row and commit.

        Backward-compatible auto-commit wrapper.  Calls
        ``_insert_strategy_core()``, then commits on success, rolls back
        on SQLite write/commit failure.

        Parameters
        ----------
        dto : ImportStrategyDTO

        Returns
        -------
        int
            The new row id (committed).

        Raises
        ------
        StrategyRepoAdapterError
            If validation, JSON parse, UID duplicate, or SQLite failure.
        DuplicateStrategyUIDError
            If a strategy with the same *dto.strategy_uid* already exists.
        """
        try:
            row_id = self._insert_strategy_core(dto)
        except StrategyRepoAdapterError as exc:
            # Rollback only if the error was caused by a SQLite write failure
            # (e.g. INSERT execution error wrapped from sqlite3.Error).
            # Validation / JSON errors have no SQL to clean up.
            if isinstance(exc.__cause__, sqlite3.Error):
                self._conn.rollback()
            raise
        try:
            self._conn.commit()
            return row_id
        except sqlite3.Error as exc:
            self._conn.rollback()
            raise StrategyRepoAdapterError(
                f"Failed to commit strategy '{dto.name}': {exc}"
            ) from exc

    def insert_strategy_no_commit(self, dto: ImportStrategyDTO) -> int:
        """Insert a new strategy row **without** committing.

        Coordinator-facing method.  The caller owns the transaction and
        must call ``commit()`` or ``rollback()`` on the connection.
        No commit or rollback is performed inside this method.

        Parameters
        ----------
        dto : ImportStrategyDTO

        Returns
        -------
        int
            The new row id (uncommitted).

        Raises
        ------
        StrategyRepoAdapterError
            If validation, JSON parse, UID duplicate, or SQLite failure.
        DuplicateStrategyUIDError
            If a strategy with the same *dto.strategy_uid* already exists.
        """
        return self._insert_strategy_core(dto)

    # -- internal: duplicate UID scan ---------------------------------------

    def _reject_duplicate_uid(self, strategy_uid: str) -> None:
        """Raise ``DuplicateStrategyUIDError`` if *strategy_uid* exists."""
        rows = self._conn.execute(self._SCAN_ALL_SQL).fetchall()
        for row in rows:
            try:
                payload = json.loads(row["strategy_json"])
            except (json.JSONDecodeError, ValueError):
                continue  # skip unparseable rows (corner case)
            if isinstance(payload, dict) and payload.get("strategy_uid") == strategy_uid:
                raise DuplicateStrategyUIDError(
                    f"Strategy UID '{strategy_uid}' already exists "
                    f"(row id={row['id']}, name='{row['name']}'). "
                    "This adapter does not overwrite or update existing strategies."
                )
