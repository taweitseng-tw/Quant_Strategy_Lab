# Archive Import Coordinator Architecture — Task 060A (Fix)

> Design-only. No production code changed.

## 1. Purpose

Define the future `ArchiveImportCoordinator` that sequences a verified archive import: verify → preflight → stage → write → finalise — with precise transaction, rollback, and cleanup boundaries.

## 2. Non-Goals

- Not implementing the coordinator.
- Not implementing filesystem staging.
- Not implementing dataset/validation repository adapters.
- Not adding audit success writes.

## 3. Collaborators

| Component | Status | Responsibility |
|---|---|---|
| `ArchiveImporter.build_preview()` | ✅ Done (059Q) | Read-only manifest + file listing from archive folder |
| `ArchiveVerifier.verify_all()` | ✅ Done (059C) | File existence, SHA-256 hashes, disclaimer |
| `StrategyRepoAdapter.insert_strategy()` | ✅ Done (059Y) | Insert strategy row; rejects duplicate UID |
| `AuditLogRepositoryAdapter.insert_failure_log()` | ✅ Done (059W) | Write `FAILED` audit row |
| `ensure_import_audit_log_schema()` | ✅ Done (059U) | Idempotent schema helper |
| **ArchiveStager** (future) | ❌ Not implemented | Filesystem copy + hash verify + temp cleanup |
| **DatasetRepoAdapter** (future) | ❌ Not implemented | Insert dataset metadata row |
| **ValidationRepoAdapter** (future) | ❌ Not implemented | Insert validation result row |

## 4. Key Design Constraint: StrategyRepoAdapter Auto-Commit

`StrategyRepoAdapter.insert_strategy()` internally calls `self._conn.commit()` after INSERT. This means:

- **The coordinator first pass cannot roll back a committed strategy row.**
- All preflight checks (duplicate UID, payload validation, JSON grammar) must happen **before** calling `insert_strategy()`.
- The staging and hash-verification steps must also happen **before** the durable DB write.
- The coordinator first pass must not pretend a unified transaction exists across strategy + dataset + validation + staging.

### First-Pass Coordinator Constraint Table

| Action | Can rollback? | Notes |
|---|---|---|
| Preflight UID scan (JSON parse) | N/A — read-only | OK before any write |
| Preflight payload validation | N/A — read-only | OK before any write |
| Staging (copy to temp) | N/A — filesystem | Temp cleanup on failure |
| Staged hash verification | N/A — reads only | OK before any write |
| `insert_strategy()` (auto-commit) | ❌ No | Must be last DB write before file move |
| File move (temp → final) | N/A — filesystem | On failure → strategy committed, no dataset file |
| Dataset/validation writes (future) | Only with own adapter | Require separate adapter with explicit transaction control |
| `insert_failure_log()` | N/A — standalone | Always called after failure, own commit |

### Future Refactor Prerequisite

To support unified transaction across strategy + dataset + validation writes, the `StrategyRepoAdapter` must be refactored to accept an external transaction (remove its internal `commit()`). This is a separate prerequisite task, not part of the coordinator first pass.

## 5. Coordinator Sequence (Safe Ordering)

```
FUNCTION: Coordinator.import_archive(archive_root, project_id, conn) -> ImportResult

── PHASE 1: VERIFY (read-only, no DB writes) ──────────────────────────

1.  [VERIFY MANIFEST]
    manifest = ArchiveImporter.build_preview(archive_root)
    # raises on malformed manifest; no DB writes

2.  [VERIFY ARCHIVE INTEGRITY]
    verifier = ArchiveVerifier(manifest, archive_root)
    verifier.verify_all()
    # raises ArchiveIntegrityError on missing/hash-mismatch files

── PHASE 2: PREFLIGHT (read-only DB queries, no durable writes) ───────

3.  [ENSURE AUDIT SCHEMA]
    ensure_import_audit_log_schema(conn)

4.  [PREFLIGHT — VALIDATE DTO]
    Validate dto.strategy_uid, dto.strategy_json grammar,
    payload["strategy_uid"] presence, payload["strategy_uid"] matches dto.
    # raises StrategyRepoAdapterError; no DB writes

5.  [PREFLIGHT — DUPLICATE UID SCAN]
    Scan existing strategies for matching UID (read-only JSON parse).
    # if duplicate → insert_failure_log() + return ImportResult(skipped=True)
    # no staging, no durable insert

6.  [PREFLIGHT — MALFORMED LEGACY JSON CHECK]
    If unparseable JSON rows are encountered during the UID scan,
    the scan silently skips them (adapter behaviour).
    Coordinator-level outcome: if the target UID is NOT found but
    unparseable rows exist, the import proceeds.  Those rows may
    contain the same UID in an unreadable format, creating a latent
    duplicate risk.  The coordinator logs a warning:
    "N unparseable strategy_json rows found during UID preflight scan.
     Duplicate detection is incomplete."
    # Future: add a repair/audit task to flag unparseable rows.

── PHASE 3: STAGE (filesystem only, no DB writes) ─────────────────────

7.  [STAGE DATASET TO TEMP — future]
    stager = FutureArchiveStager(archive_root, project_staging_root)
    staged_path = stager.stage_dataset_snapshot()
    # copies to .staging/tmp/, returns temp path
    # raises on missing source file or copy failure

8.  [VERIFY STAGED FILE HASH — future]
    stager.verify_staged_hash(staged_path, manifest.content_hashes[...])
    # raises on mismatch; deletes staged file

── PHASE 4: WRITE (durable DB writes, no filesystem changes) ──────────

9.  [INSERT STRATEGY ROW — durable, auto-committed]
    adapter = StrategyRepoAdapter(conn)
    row_id = adapter.insert_strategy(dto)
    # If this fails after its internal commit, the row is already durable.
    # There is no rollback possible.

── PHASE 5: FINALISE (file move + audit, no DB rollback) ─────────────

10. [MOVE TO FINAL DESTINATION — future]
    final_path = stager.move_to_final_destination(staged_path)
    # if move fails → strategy row exists, dataset file orphaned.
    # Coordinator writes failure audit; does NOT delete strategy row.
    # Returns ImportResult(success=False, partial=True).

── PHASE 6: AUDIT (always runs if failure occurred) ───────────────────

11a. [ON FAILURE AT ANY PREVIOUS STEP]
    log_adapter = AuditLogRepositoryAdapter(conn)
    try:
        log_adapter.insert_failure_log(failure_dto)
    except AuditLogWriteError:
        # NON-CRASHING secondary failure.
        # Original failure reason is preserved in ImportResult.
        # Log the audit failure separately (e.g. print/warning).
        # Do NOT overwrite the original error.

11b. [ON SUCCESS — future: insert success audit]
    # Not implemented in first pass.

── FINAL ──────────────────────────────────────────────────────────────

12. [RETURN RESULT]
    return ImportResult(success=True, strategy_id=row_id, ...)
```

## 6. Error Handling Matrix (Corrected)

| Step | Failure | Strategy row inserted? | Dataset file staged? | Audit written? | Notes |
|---|---|---|---|---|---|
| 1 (manifest) | Malformed manifest | ❌ | ❌ | ❌ | Abort |
| 2 (verifier) | Missing/hash mismatch | ❌ | ❌ | ❌ | Abort |
| 3+4 (preflight) | Invalid DTO / UID match | ❌ | ❌ | ✅ | Non-crashing audit |
| 5 (legacy JSON) | Unparseable rows | Proceeds with warning | ❌ | ❌ | Warning only |
| 7+8 (stage) | Copy failure / hash mismatch | ❌ | ❌ | ✅ | Temp cleaned by stager |
| 9 (insert) | SQLite failure after auto-commit | ⚠️ Partial (may or may not exist) | ❌ | ✅ | Adapter auto-commit — coordinator cannot guarantee consistency |
| 10 (move) | Move failure | ✅ | ⚠️ Temp cleaned | ✅ | Orphaned final destination |
| 11 (audit) | Audit write failure | As per previous step | As per previous step | ❌ | Non-crashing secondary failure; original reason preserved |

## 7. Malformed Legacy strategy_json — Coordinator-Level Handling

| Scenario | What happens | Coordinator outcome |
|---|---|---|
| No unparseable rows | Normal scan | Proceed |
| Unparseable rows exist, target UID not found | Scan skips them, UID not detected | Log warning, **proceed** (latent risk) |
| Unparseable rows exist, target UID actually present but invisible | Latent duplicate | Not detectable at coordinator level; future repair tool needed |
| Unparseable rows exist, insert proceeds | Strategy inserted; a later import with same UID will also skip | Creates true duplicate; future UID migration/repair required |

## 8. Duplicate UID Handling (Precise)

```
Preflight step 5 (read-only scan) checks existing strategy_json.
  → If duplicate found → DuplicateUIDError.
  → Coordinator catches → write failure audit → return ImportResult(skipped=True).
  → No staging, no durable DB insert.
```

## 9. Final File Move Failure (After DB Commit)

Acknowledged design risk. Coordinator:
1. Writes failure audit (non-crashing).
2. Returns `ImportResult(success=False, partial=True, strategy_row_created=True)`.
3. Does NOT delete committed strategy row.
4. Future: `pending_filesystem_move` flag on strategy row enables repair tools.

## 10. Failure Audit Write Failure — Non-Crashing Rule

If `insert_failure_log()` itself fails:
- Coordinator catches `AuditLogWriteError`.
- The **original failure reason** (e.g. `DuplicateUIDError`, `StrategyRepoAdapterError`) is preserved in `ImportResult`.
- Coordinator logs a warning about the audit failure.
- The coordinator returns the original `ImportResult` — the audit failure is secondary.

## 11. Next Two-Task Batch

**Batch 060C-Design + 060D-Design — StrategyRepoAdapter Transaction Boundary Refactor Design + DatasetRepoAdapter Insert-Only Slice Design**

- 060C: Design how to refactor `StrategyRepoAdapter.insert_strategy()` to accept an external transaction (remove internal `commit()`). This is a prerequisite for the coordinator to use a unified transaction.
- 060D: `DatasetRepoAdapter` insert-only slice design (analogous to 059Y strategy slice).

Both design-only. Coordinator implementation deferred until transaction boundary is resolved.

## 12. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
- **Last fix**: 2026-06-07 — reordered to safe verify → preflight → stage → write → finalise sequence. Added auto-commit constraint. Added legacy JSON coordinator-level handling. Fixed audit failure non-crashing rule.
