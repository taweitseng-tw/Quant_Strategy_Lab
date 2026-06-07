# Archive Import Repository Adapter Test Contract — Task 059T

> [!NOTE]  
> **Design-only document.** No production Python code is implemented in this batch. This document defines the testing contract, assertions, and verification criteria for future repository and filesystem adapters.

---

## 1. Purpose

This document defines the test contracts, mock/spy expectations, rollback assertions, failure logging behavior, and edge-case validation scenarios required to test the future transactional import adapters.

---

## 2. Test Doubles & Spy Expectations

To verify transactional guarantees without executing side-effects on a real database or disk, test suites must use structured spies/mocks conforming to the repository adapter protocols.

### 2.1 Strategy Repository Spy (`SpyStrategyRepositoryAdapter`)
- **State tracked**:
  - `exists_calls`: list of `strategy_uid` queried.
  - `insert_calls`: list of `StrategyImportDTO` passed to `insert_strategy`.
- **Behavior configuration**:
  - Can configure `exists_by_uid` to return `True` or `False`.
  - Can configure `insert_strategy` to raise `RepositoryWriteError` or `DuplicateStrategyImportError`.

### 2.2 Dataset Repository Spy (`SpyDatasetRepositoryAdapter`)
- **State tracked**:
  - `exists_calls`: list of `dataset_id` queried.
  - `properties_calls`: list of `(symbol, timeframe)` queried.
  - `insert_calls`: list of `DatasetMetadataDTO` passed to `insert_dataset_metadata`.
- **Behavior configuration**:
  - Can configure `exists_by_id` to return `True` or `False`.
  - Can configure `get_by_properties` to return a fake `DatasetMetadataDTO` or `None`.
  - Can configure `insert_dataset_metadata` to raise `RepositoryWriteError`.

### 2.3 Filesystem Adapter Spy (`SpyFilesystemAdapter`)
- **State tracked**:
  - `copy_calls`: list of `(source_path, target_filename)` copied.
  - `deleted_files`: list of target file paths unlinked during rollback.
- **Behavior configuration**:
  - Can configure `copy_dataset_snapshot` to raise `SnapshotWriteError` (e.g. simulate disk full or permission denied).

---

## 3. Core Test Contracts

### 3.1 Duplicate Rejection Tests

#### Test Case 1: Strategy UID Collision
- **Given**: A strategy with `strategy_uid = "strat-001"` already exists (spy returns `True`).
- **When**: The import transaction is executed.
- **Then**:
  - Raise `DuplicateStrategyImportError`.
  - Verify that `insert_strategy` was **never** called.
  - Verify that no database transaction was committed.

#### Test Case 2: Dataset ID Collision / Primary Key Conflict
- **Given**: A dataset with `id = 42` already exists, but has a different symbol or timeframe (e.g., `'SPY'`/`'1min'` in DB vs. `'ES'`/`'5min'` in archive).
- **When**: The import transaction is executed.
- **Then**:
  - Raise `ImportExecutionError`.
  - Verify that no database transaction was committed.

---

### 3.2 Rollback Acceptance Criteria

#### Test Case 3: Database Write Failure Rollback
- **Scenario**: Filesystem copy succeeds, but database insertion fails (e.g., SQLite constraint violation during `insert_strategy`).
- **Assertions**:
  - Verify `connection.rollback()` is explicitly called on the SQLite connection.
  - Verify the copied CSV snapshot file under `data/normalized/` is unlinked/deleted by the filesystem adapter to prevent dangling assets.

#### Test Case 4: Filesystem Copy Failure Rollback
- **Scenario**: Filesystem copy fails (raises `SnapshotWriteError` due to full disk) before writing database records.
- **Assertions**:
  - Verify the database transaction is rolled back.
  - Verify `insert_strategy`, `insert_dataset_metadata`, and `insert_validation_result` are never executed.

---

### 3.3 Failed Audit Logging Acceptance Criteria

#### Test Case 5: Audit Log Persistence on Failure
- **Scenario**: An import fails due to `DuplicateStrategyImportError`.
- **Assertions**:
  - Verify that a rollback was executed for the main transaction.
  - Verify that a new record is written to `ImportAuditLog`.
  - Verify the log contains: `status = 'FAILED'`, `strategy_uid = 'strat-001'`, `conflict_policy_applied = 'REJECT'`, and `error_message = 'DuplicateStrategyImportError...'`.
  - Verify that the audit log record is committed and persists in the database despite the import transaction failing.

---

### 3.4 Read/Write Boundary Tests

#### Test Case 6: Dry-Run Preview Isolation
- **Scenario**: `ArchiveImporter.build_preview()` is run with active spies.
- **Assertions**:
  - Verify `exists_by_uid` and `get_by_properties` may be called.
  - Verify `insert_strategy`, `insert_dataset_metadata`, `insert_validation_result`, and `copy_dataset_snapshot` are **never** called.
  - Verify `connection.commit()` is **never** called.

---

## 4. Edge-Case Error Scenarios

1. **Database Lock/Busy (`DatabaseLockError`)**:
   - Verify that if SQLite raises a database locked exception during writes, the transaction is rolled back, the CSV file is cleaned up, and a failure log is created.
2. **Invalid Data Constraints (`DatabaseConstraintError`)**:
   - Verify that if invalid foreign key references or null values violate SQLite constraints, the system handles it gracefully via `RepositoryWriteError` and aborts safely.

---

## 5. Recommended Next Two-Task Batch

**Batch 059U-Impl + 059V-Design - ImportAuditLog Migration Skeleton and Import Adapter Implementation Slice Design**
- **059U-Impl**: Implement the SQL migration script skeleton, helper functions (e.g. `create_audit_log_table()`), and tests verifying idempotent table creation, table exists checks, and index exists checks. No active importer database writes, filesystem adapters, or service/CLI wiring.
- **059V-Design**: Design the first minimal database adapter slice (e.g., `AuditLogRepositoryAdapter.insert_failure_log()`) for the write path, specifying mock expectations and transaction boundaries, without implementing it.
