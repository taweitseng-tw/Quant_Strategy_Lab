# Archive Import Audit Schema and Collision Detection Design — Task 059P

> [!NOTE]  
> **Design-only document.** No database migrations or SQL code are executed in this batch.

---

## 1. Purpose

This document details the database schema for the import audit logs, specifies the sql/logical queries for strategy and dataset collision detection, and designs the logging behavior for both successful and failed imports.

---

## 2. Import Audit Log SQLite Schema

To track import history, provenance, and applied conflict policies, a new database table `ImportAuditLog` will be introduced.

### 2.1 Table Definition (`ImportAuditLog`)
```sql
CREATE TABLE ImportAuditLog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    imported_at TEXT NOT NULL,                   -- ISO-8601 UTC timestamp of the import event
    archive_version TEXT NOT NULL,               -- e.g. "1.0.0"
    experiment_name TEXT NOT NULL,               -- Metadata identifier from archive manifest
    strategy_uid TEXT NOT NULL,                  -- Reference strategy UID
    original_filename TEXT NOT NULL,             -- Source directory name or zip filename
    conflict_policy_applied TEXT NOT NULL,       -- "REJECT", "OVERWRITE", "SKIP", "RENAME"
    status TEXT NOT NULL,                        -- "SUCCESS" or "FAILED"
    error_message TEXT                           -- Detail of error if status is "FAILED"
);
```

### 2.2 Strategy Provenance Meta
Upon successful import, the strategy's definition (`strategy_json`) will have an updated metadata object injected into its payload to ensure lineage:
```json
{
  "conditions": [...],
  "provenance": {
    "imported_from_archive": true,
    "imported_at": "2026-06-07T13:40:00Z",
    "original_strategy_uid": "strat-001",
    "archive_version": "1.0.0"
  }
}
```

---

## 3. Collision Detection Boundary & Queries

Before starting any database mutations, the importer performs checks to detect name, ID, or property collisions.

### 3.1 Strategy Collision Detection
Checks if the strategy exists by its unique identifier.
```sql
-- Query
SELECT strategy_uid, name FROM Strategy WHERE strategy_uid = :strategy_uid;
```
- **Evaluation**: If any row is returned, a strategy collision is declared.

### 3.2 Dataset Collision Detection
Dataset collision checks both the primary key (`id`) and the unique properties (`symbol`, `timeframe`).

```sql
-- Query A: ID check
SELECT id, symbol, timeframe, row_count FROM Dataset WHERE id = :dataset_id;

-- Query B: Properties check
SELECT id, symbol, timeframe, row_count FROM Dataset WHERE symbol = :symbol AND timeframe = :timeframe;
```

- **Evaluation rules**:
  1. **Strict Conflict (PK mismatch)**: If Query A returns a dataset, but the retrieved `symbol` or `timeframe` does not match the archive's metadata, it is a primary key collision.
  2. **Content Mismatch**: If Query B returns a dataset, but the retrieved `row_count` or binary snapshot differ, it is a content conflict.
  3. **Metadata Parity (Reuse)**: If Query B matches exactly, the importer can reuse the existing dataset rather than creating a duplicate.

---

## 4. MVP Default Behavior: Reject Duplicate

Under the MVP "Reject Duplicate" policy:
- If **any** strategy or dataset collision is detected, the importer must immediately abort.
- **Transaction Guarantee**: The main import transaction is rolled back. No rows are inserted into `Strategy`, `Dataset`, or `ValidationResult` tables.
- **Filesystem Guarantee**: Any copied CSV snapshot under `data/normalized/` is unlinked.

---

## 5. Failure Auditing Design

To ensure failed imports are logged without leaving partial data mutations:

1. **Transaction Isolation**:
   - The main import transaction (writing strategy, dataset, validation) and the audit logging write must be decoupled.
2. **Error Recovery & Logging Flow**:
   - The importer initiates the main transaction.
   - If an error is caught (e.g. `DuplicateStrategyImportError` or `RepositoryWriteError`), the importer issues a `ROLLBACK` on the main transaction.
   - The importer then opens a **new, independent database transaction** solely to write a record to `ImportAuditLog` with `status='FAILED'` and the corresponding `error_message`.
   - This ensures that a trace of the failure remains in the logs, while keeping the main application state clean.

---

## 6. Recommended Next Two-Task Batch

**Batch 059Q-Impl + 059R-Design - ArchiveImporter Read-Only Import Plan Builder and Import Transaction Sequence Design**
- **059Q-Impl**: Implement the read-only preview skeleton for `ArchiveImporter` (extracting strategy metadata, DTOs, and detecting strategy/dataset collisions in a read-only manner) to show import dry-run summaries to the user, without any database writes, file copy operations, or repository adapter implementation.
- **059R-Design**: Design the detailed SQL transaction sequence, file copy commit phases, failure rollback procedures, and the failed-audit logging execution sequence for future write integration.
