"""Audit log repository adapter — failed-import audit row writes only.

This module is scoped to writing ``ImportAuditLog`` rows with
``status='FAILED'``.  It does **not** write strategy, dataset, or
validation tables, nor does it copy files or stage archives.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from repository.db import ensure_import_audit_log_schema


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ImportAuditLogDTO:
    """Immutable DTO for an ImportAuditLog row.

    Parameters
    ----------
    imported_at : str
        ISO-8601 timestamp of the import attempt.
    archive_version : str
        Schema version from the archive manifest.
    experiment_name : str
        Archive experiment name.
    strategy_uid : str
        Strategy UID from the archive.
    archive_source : str
        Archive source path (folder path or zip path).
    manifest_hash : str
        SHA-256 hex digest of the manifest file.
    original_filename : str
        Original filename of the imported strategy JSON.
    conflict_policy_applied : str
        One of ``'REJECT'``, ``'OVERWRITE'``, ``'SKIP'``, ``'RENAME'``.
    status : str
        Audit status; must be ``'FAILED'`` for this adapter.
    error_message : str | None
        Human-readable failure reason.
    """

    imported_at: str
    archive_version: str
    experiment_name: str
    strategy_uid: str
    archive_source: str
    manifest_hash: str
    original_filename: str
    conflict_policy_applied: str
    status: str = "FAILED"
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class AuditLogWriteError(Exception):
    """Raised when an audit log write fails."""


class AuditLogStatusError(Exception):
    """Raised when a DTO status other than 'FAILED' is passed to insert_failure_log."""


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class AuditLogRepositoryAdapter:
    """Repository adapter for writing import audit log rows.

    This adapter only writes ``status='FAILED'`` audit rows.  It does
    not write strategy, dataset, or validation tables.
    """

    _INSERT_SQL = """
        INSERT INTO ImportAuditLog (
            imported_at, archive_version, experiment_name,
            strategy_uid, archive_source, manifest_hash,
            original_filename, conflict_policy_applied, status, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def insert_failure_log(self, dto: ImportAuditLogDTO) -> None:
        """Insert one failed-audit row.

        Parameters
        ----------
        dto : ImportAuditLogDTO
            Must have ``status='FAILED'``.

        Raises
        ------
        AuditLogStatusError
            If ``dto.status != 'FAILED'``.  No row is inserted.
        AuditLogWriteError
            If the SQLite write fails (constraint, schema, or IO error).
        """
        if dto.status != "FAILED":
            raise AuditLogStatusError(
                f"insert_failure_log() requires status='FAILED', got '{dto.status}'. "
                "This adapter writes audit failures only."
            )

        try:
            ensure_import_audit_log_schema(self._conn)
            self._conn.execute(
                self._INSERT_SQL,
                (
                    dto.imported_at,
                    dto.archive_version,
                    dto.experiment_name,
                    dto.strategy_uid,
                    dto.archive_source,
                    dto.manifest_hash,
                    dto.original_filename,
                    dto.conflict_policy_applied,
                    dto.status,
                    dto.error_message,
                ),
            )
            self._conn.commit()
        except sqlite3.Error as exc:
            raise AuditLogWriteError(
                f"Failed to write audit log for strategy '{dto.strategy_uid}': {exc}"
            ) from exc
