# Archive Import Audit Migration Plan — Task 059S

> [!NOTE]  
> **Design-only document.** No database migrations, SQL modifications, or production write integrations are executed in this batch. This document defines the blueprint for a future migration.

---

## 1. Purpose

This document outlines the SQLite schema migration plan for introducing the `ImportAuditLog` table. This table will record the history, metadata, and final status (success or failure) of importing Reproducible Experiment Archives into a Quant Strategy Lab workspace.

---

## 2. Proposed SQLite Schema

The migration introduces a single new table, `ImportAuditLog`, along with indexes designed for fast audit lookup.

### 2.1 Table Schema

```sql
CREATE TABLE ImportAuditLog (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    imported_at             TEXT NOT NULL,                      -- ISO-8601 UTC timestamp: 'YYYY-MM-DDTHH:MM:SSZ'
    archive_version         TEXT NOT NULL,                      -- e.g., '1.0.0'
    experiment_name         TEXT NOT NULL,                      -- Experiment name metadata from archive manifest
    strategy_uid            TEXT NOT NULL,                      -- Strategy UID associated with the import
    archive_source          TEXT NOT NULL,                      -- Absolute filesystem path or source file URL of the archive
    manifest_hash           TEXT NOT NULL,                      -- SHA-256 hash of the archive's manifest.json to guarantee data integrity
    original_filename       TEXT NOT NULL,                      -- Original archive directory path or zip filename
    conflict_policy_applied  TEXT NOT NULL,                      -- Applied policy: 'REJECT', 'OVERWRITE', 'SKIP', 'RENAME'
    status                  TEXT NOT NULL,                      -- Final state: 'SUCCESS', 'FAILED'
    error_message           TEXT,                               -- Detail of the error if status is 'FAILED', else NULL
    
    -- Constraints to enforce value integrity
    CONSTRAINT chk_conflict_policy CHECK (conflict_policy_applied IN ('REJECT', 'OVERWRITE', 'SKIP', 'RENAME')),
    CONSTRAINT chk_status CHECK (status IN ('SUCCESS', 'FAILED'))
);
```

### 2.2 Traceability Field Specifications

To guarantee audit traceability and historical lineage, the following fields are defined:

*   **`archive_source`** (`TEXT`, `NOT NULL`): Stores the absolute path of the directory or file from which the import was initiated (e.g. `D:/Imports/my_strat_archive`). This tracks the physical source location on the host environment and is **required** for all log entries.
*   **`manifest_hash`** (`TEXT`, `NOT NULL`): Stores the SHA-256 hash of the archive's `manifest.json`. This hash acts as a unique digital signature of the imported experiment. It is **required** and prevents tampering, allowing detection if the underlying files were altered post-generation.
*   **`strategy_uid`** (`TEXT`, `NOT NULL`): Stores the unique identifier of the imported strategy. This bridges the audit log with the `strategies` table and is **required** to trace the strategy's origin.
*   **`original_filename`** (`TEXT`, `NOT NULL`): Stores the name of the archive payload's primary input file or zip name. This is **required** to preserve the user's naming context.

### 2.3 Indexes

To support rapid filtering and sorting in audit reports (e.g., viewing logs for a specific strategy or sorting by date):

```sql
-- Index on strategy_uid to quickly fetch import history/provenance for any strategy
CREATE INDEX idx_import_audit_log_strategy_uid ON ImportAuditLog(strategy_uid);

-- Index on imported_at to support fast sorting of log history by execution time
CREATE INDEX idx_import_audit_log_imported_at ON ImportAuditLog(imported_at DESC);
```

---

## 3. Migration Rollback Plan

In the event of a migration failure, deployment rollback, or environment reset, the schema changes can be safely reverted.

### 3.1 Reversion Steps

The following drop commands will completely remove the audit logging infrastructure without affecting any core strategy or dataset records:

```sql
-- Drop indexes first
DROP INDEX IF EXISTS idx_import_audit_log_imported_at;
DROP INDEX IF EXISTS idx_import_audit_log_strategy_uid;

-- Drop table
DROP TABLE IF EXISTS ImportAuditLog;
```

### 3.2 Rollback Safety Analysis
- **Core Strategy Table**: Dropping the audit log table has zero impact on the `strategies`, `datasets`, or `projects` tables. No foreign keys reference `ImportAuditLog`.
- **Data Loss Boundary**: Reversion deletes all previous import audit history. It should only be run during schema downgrades or local environment teardowns.

---

## 4. Compatibility Notes

- **Additive Changes Only**: This schema migration is purely additive. It creates new tables and indexes and does not alter, rename, or drop existing columns/tables in the SQLite database.
- **SQLite Engine Compatibility**: The schema utilizes standard features (`CHECK` constraints, `AUTOINCREMENT`, and `TEXT` datetime formats) supported by SQLite 3.x.
- **No Retroactive Backfill**: Since no previous import audit records exist, no data backfill or transformation script is needed. Existing rows in other tables remain unaltered.

---

## 5. Migration Verification Criteria

Once the migration is implemented in a future batch, it must pass the following verification checks:

1. **Schema Existence Verification**:
   Query `sqlite_master` to ensure the table and indexes exist exactly as designed:
   ```sql
   SELECT name FROM sqlite_master WHERE type='table' AND name='ImportAuditLog';
   SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ImportAuditLog';
   ```
2. **Constraint Enforcement Checks**:
   - Verify that trying to insert an invalid status (e.g. `'PENDING'`) raises a `sqlite3.IntegrityError` due to the `chk_status` CHECK constraint.
   - Verify that trying to insert an invalid policy (e.g. `'MERGE'`) raises a `sqlite3.IntegrityError` due to the `chk_conflict_policy` CHECK constraint.
3. **Index Usage Check**:
   - Run `EXPLAIN QUERY PLAN` on log queries filtering by `strategy_uid` or ordering by `imported_at` to verify that SQLite is performing index scans rather than full table scans.
