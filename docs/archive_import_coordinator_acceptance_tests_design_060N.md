# ArchiveImportCoordinator Acceptance Tests Design — Task 060N

> Design-only. No production code changed.

## 1. Purpose

Define the next hardening slice of acceptance tests for the `ArchiveImportCoordinator`, moving from spy/fake unit tests to integration-style tests using real archive folders and SQLite connections.

## 2. Test File

`tests/test_archive_import_coordinator_acceptance.py` (future)

## 3. Test Scenarios

### 3.1 Manifest hash mismatch

| Step | Assertion |
|---|---|
| Alter one file in the archive after computing manifest hash | `ArchiveVerifier.verify_all()` raises |
| Coordinator catches error | `ImportResult(success=False)` |
| No DB writes, no staging | Strategy adapter not called; stager not called |

### 3.2 Duplicate strategy UID (integration)

| Step | Assertion |
|---|---|
| Pre-populate DB with one strategy | Strategy exists |
| Import same UID archive | `ImportResult(skipped=True)` |
| Pre-existing DB row unchanged | Original row still present |

### 3.3 Duplicate dataset hash

| Step | Assertion |
|---|---|
| Pre-populate DB with dataset having `snapshot_hash = X` | Dataset exists |
| Import archive with same hash | `DatasetRepoAdapter` raises `DuplicateDatasetError` |
| Coordinator returns failure, writes audit | `ImportResult(success=False)` |
| Strategy was rolled back | Strategy row NOT in DB |

### 3.4 Final move partial state

| Step | Assertion |
|---|---|
| Full import up to DB commit succeeds | Strategy + dataset rows committed |
| Force final move to fail (e.g. read-only dest dir) | `ImportResult(partial=True)` |
| DB rows still present | Strategy + dataset queryable |
| Staging file preserved | `stager._staged_path` not None; file exists |

### 3.5 Audit failure isolation

| Step | Assertion |
|---|---|
| Force duplicate UID error | `DuplicateStrategyUIDError` |
| Force audit adapter to also fail | `ImportResult(skipped=True)` |
| Original error message preserved in result | `result.error` contains "already exists", not audit error |

### 3.6 No UI/engine boundary (integration)

| Step | Assertion |
|---|---|
| Run full coordinator with real folders + real SQLite | `ImportResult(success=True)` |
| No `PySide6` or `backtest_engine` in coordinator's import namespace | Module-specific import check |

## 4. Next Two-Task Batch

Batch 060O-Impl only — Coordinator Acceptance Test Implementation + changelog sign-off.

## 5. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
