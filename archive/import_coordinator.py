"""ArchiveImportCoordinator first-pass import orchestrator.

Wires archive preview, verification, staging, and no-commit repository
adapters into a single sequential import flow. Uses dependency injection
so tests can pass fakes/spies.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass


@dataclass
class ImportResult:
    """Outcome of a coordinator import call."""

    success: bool
    partial: bool = False
    skipped: bool = False
    strategy_id: int | None = None
    dataset_id: int | None = None
    error: str | None = None
    audit_failed: bool = False


class ArchiveImportCoordinator:
    """Orchestrates archive preview, verify, stage, DB insert, and finalise."""

    def __init__(
        self,
        importer,
        verifier,
        stager,
        strategy_adapter,
        dataset_adapter,
        audit_adapter,
        connection: sqlite3.Connection,
    ) -> None:
        self._importer = importer
        self._verifier = verifier
        self._stager = stager
        self._strategy = strategy_adapter
        self._dataset = dataset_adapter
        self._audit = audit_adapter
        self._conn = connection

    def import_archive(
        self,
        archive_root: str,
        experiment_name: str,
        run_id: str,
        strategy_dto,
        dataset_dto,
        expected_snapshot_hash: str,
        disclaimer_text: str = "",
    ) -> ImportResult:
        """Run the full coordinator sequence."""
        try:
            return self._import_archive_impl(
                archive_root,
                experiment_name,
                run_id,
                strategy_dto,
                dataset_dto,
                expected_snapshot_hash,
                disclaimer_text,
            )
        except Exception as exc:
            audit_failed = not self._write_failure_audit(
                strategy_dto=strategy_dto, error=str(exc)
            )
            return ImportResult(success=False, error=str(exc), audit_failed=audit_failed)

    def _import_archive_impl(
        self,
        archive_root: str,
        experiment_name: str,
        run_id: str,
        strategy_dto,
        dataset_dto,
        expected_snapshot_hash: str,
        disclaimer_text: str,
    ) -> ImportResult:
        try:
            self._importer.build_preview(archive_root)
            self._verifier.verify_all()
        except Exception as exc:
            return ImportResult(success=False, error=str(exc))

        try:
            self._preflight_duplicates(strategy_dto=strategy_dto, dataset_dto=dataset_dto)
        except Exception as exc:
            exc_str = str(exc)
            audit_failed = not self._write_failure_audit(
                strategy_dto=strategy_dto, error=exc_str
            )
            if "already exists" in exc_str.lower():
                return ImportResult(
                    success=False,
                    skipped=True,
                    error=exc_str,
                    audit_failed=audit_failed,
                )
            return ImportResult(success=False, error=exc_str, audit_failed=audit_failed)

        try:
            self._stager.stage_dataset_snapshot(expected_snapshot_hash)
        except Exception as exc:
            self._stager.cleanup_temp()
            audit_failed = not self._write_failure_audit(
                strategy_dto=strategy_dto, error=str(exc)
            )
            return ImportResult(success=False, error=str(exc), audit_failed=audit_failed)

        try:
            strategy_id = self._strategy.insert_strategy_no_commit(strategy_dto)
            dataset_id = self._dataset.insert_dataset_no_commit(dataset_dto)
            self._conn.commit()
        except Exception as exc:
            self._conn.rollback()
            self._stager.cleanup_temp()
            audit_failed = not self._write_failure_audit(
                strategy_dto=strategy_dto, error=str(exc)
            )
            return ImportResult(success=False, error=str(exc), audit_failed=audit_failed)

        try:
            self._stager.move_to_final_destination()
        except Exception as exc:
            audit_failed = not self._write_failure_audit(
                strategy_dto=strategy_dto, error=str(exc)
            )
            return ImportResult(
                success=False,
                partial=True,
                strategy_id=strategy_id,
                dataset_id=dataset_id,
                error=str(exc),
                audit_failed=audit_failed,
            )

        self._stager.cleanup_temp()
        return ImportResult(
            success=True,
            strategy_id=strategy_id,
            dataset_id=dataset_id,
        )

    def _preflight_duplicates(self, *, strategy_dto, dataset_dto) -> None:
        """Run duplicate checks without inserting, committing, or rolling back."""
        if hasattr(self._strategy, "preflight_duplicate"):
            self._strategy.preflight_duplicate(strategy_dto)
        elif hasattr(self._strategy, "_reject_duplicate_uid"):
            self._strategy._reject_duplicate_uid(strategy_dto.strategy_uid)

        if hasattr(self._dataset, "preflight_duplicate"):
            self._dataset.preflight_duplicate(dataset_dto)
        elif hasattr(self._dataset, "_reject_duplicate"):
            self._dataset._reject_duplicate(dataset_dto)

    def _write_failure_audit(self, *, strategy_dto, error: str) -> bool:
        """Best-effort failure audit write. Returns False if audit fails."""
        try:
            dto = _make_audit_failure_dto(strategy_dto, error)
            self._audit.insert_failure_log(dto)
            return True
        except Exception:
            return False


def _make_audit_failure_dto(strategy_dto, error: str):
    """Build an audit DTO from a strategy DTO and error string."""
    try:
        from repository.import_audit_repo import ImportAuditLogDTO
    except ImportError:
        return None

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return ImportAuditLogDTO(
        imported_at=now,
        archive_version="1.0.0",
        experiment_name="import",
        strategy_uid=getattr(strategy_dto, "strategy_uid", "unknown"),
        archive_source="import",
        manifest_hash="",
        original_filename="",
        conflict_policy_applied="REJECT",
        status="FAILED",
        error_message=error,
    )
