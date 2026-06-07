# ArchiveImportCoordinator First-Pass Wiring Design — Task 060L

> Design-only. No production code changed.

## 1. Purpose

Define how the `ArchiveImportCoordinator` first pass wires together all existing components into a single sequential import flow. The coordinator orchestrates; it does not implement new repository, staging, or verification logic.

## 2. Existing Components Wired

| Component | Status | File |
|---|---|---|
| `ArchiveImporter.build_preview()` | ✅ 059Q | `archive/importer.py` |
| `ArchiveVerifier.verify_all()` | ✅ 059C | `archive/verifier.py` |
| `ArchiveStager` | ✅ 060K | `archive/stager.py` |
| `StrategyRepoAdapter.insert_strategy_no_commit()` | ✅ 060E | `repository/strategy_import_adapter.py` |
| `DatasetRepoAdapter.insert_dataset_no_commit()` | ✅ 060I | `repository/dataset_import_adapter.py` |
| `AuditLogRepositoryAdapter.insert_failure_log()` | ✅ 059W | `repository/import_audit_repo.py` |

## 3. Coordinator Sequence

```
COORDINATOR.import_archive(archive_root, project_root, conn) -> ImportResult

PHASE 1: VERIFY (read-only)
  1. manifest = ArchiveImporter.build_preview(archive_root)
  2. ArchiveVerifier(manifest, archive_root).verify_all()
     → raises ArchiveIntegrityError on failure; no audit write

PHASE 2: PREFLIGHT (read-only DB queries)
  3. strategy_adapter = StrategyRepoAdapter(conn)
     dataset_adapter = DatasetRepoAdapter(conn)
  4. Validate DTOs (payload JSON, UID match, snapshot_hash from manifest)
  5. Check duplicate strategy UID → if duplicate, write failure audit, return skipped
  6. Malformed legacy JSON → scan skips, coordinator logs warning

PHASE 3: STAGE FILESYSTEM
  7. stager = ArchiveStager(archive_root, project_root, experiment_name, run_id)
  8. stager.stage_dataset_snapshot(manifest.content_hashes["ohlcv_snapshot.csv"])
     → raises HashMismatchError on mismatch; cleanup_temp(); write failure audit

PHASE 4: DB WRITE (no-commit adapters)
  9. strategy_adapter.insert_strategy_no_commit(strategy_dto)
 10. dataset_adapter.insert_dataset_no_commit(dataset_dto)
 11. conn.commit()
     → if FAIL → stager.cleanup_temp(); write failure audit; return failure

PHASE 5: FILE FINALISE (after DB commit)
 12. stager.move_to_final_destination()
     → if FAIL → return ImportResult(partial=True, file_missing=True)
       staging file preserved; do NOT call cleanup_temp()
 13. stager.cleanup_temp()

PHASE 6: RESULT
 14. return ImportResult(success=True)
```

## 4. Failure Audit

| Failure point | Audit written? | Cleanup action |
|---|---|---|
| Verifier failure | No audit (pre-DB) | None |
| Duplicate UID | Yes (failure audit) | No staging |
| Hash mismatch | Yes (failure audit) | cleanup_temp() |
| DB commit failure | Yes (failure audit) | cleanup_temp() |
| Final move failure | Yes (failure audit) | staging preserved for repair |
| Audit write failure | Non-crashing secondary failure | Original error preserved |

## 5. ImportResult DTO

```python
@dataclass
class ImportResult:
    success: bool
    partial: bool = False      # DB rows exist but file move failed
    skipped: bool = False       # Duplicate UID
    strategy_id: int | None = None
    error: str | None = None
    audit_failed: bool = False  # Failure audit write itself failed
```

## 6. Focused Tests (Future, using spies/fakes)

| # | Scenario | Key assertion |
|---|---|---|
| 1 | Success | All components called in order; ImportResult(success=True) |
| 2 | Duplicate UID | strategy_adapter raises DuplicateUIDError; audit written; stager NOT called |
| 3 | Staging failure | `stage_dataset_snapshot` raises; cleanup_temp called; audit written |
| 4 | DB commit failure | conn.commit() raises; cleanup_temp called; audit written |
| 5 | Final move failure | `move_to_final_destination` raises; ImportResult(partial=True); staging preserved |
| 6 | Audit write failure | Audit adapter raises; non-crashing; original ImportResult preserved |
| 7 | No UI/engine imports | `PySide6`, `backtest_engine`, `validation_engine` not in sys.modules |

## 7. Next Two-Task Batch

**Batch 060M-Impl + 060N-Design — ArchiveImportCoordinator First-Pass Implementation + Coordinator Acceptance Test Implementation.**

## 8. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
