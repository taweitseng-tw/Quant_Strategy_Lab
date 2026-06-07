# Archive Import Adapter Slice Design — Task 059V

> [!NOTE]  
> **Design-only document.** No production Python code is implemented in this batch. This document defines the architectural boundaries and test criteria for the first minimal repository adapter slice.

---

## 1. Purpose

This document designs the first minimal adapter slice for the import audit log write path, specifically focusing on `AuditLogRepositoryAdapter.insert_failure_log()`. It defines the DTO fields, transaction isolation boundary, failure logging sequence, and test contracts for future implementation.

---

## 2. Data Transfer Object (DTO)

The importer will pass log metadata using an immutable DTO.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ImportAuditLogDTO:
    imported_at: str                    # ISO-8601 UTC timestamp: 'YYYY-MM-DDTHH:MM:SSZ'
    archive_version: str                # e.g., '1.0.0'
    experiment_name: str                # Experiment name metadata from archive manifest
    strategy_uid: str                   # Unique identifier of the strategy being imported
    archive_source: str                 # Absolute path or URL of the imported archive
    manifest_hash: str                  # SHA-256 hash of the archive's manifest.json
    original_filename: str              # Original archive directory path or zip filename
    conflict_policy_applied: str        # 'REJECT', 'OVERWRITE', 'SKIP', 'RENAME'
    status: str                         # 'SUCCESS', 'FAILED'
    error_message: str | None = None    # Detailed exception message if status is 'FAILED'
```

---

## 3. Adapter Interface Contract

The `AuditLogRepositoryAdapter` encapsulates the raw SQL queries and connection handling for the `ImportAuditLog` table.

```python
from typing import Protocol

class IImportAuditLogRepositoryAdapter(Protocol):
    def insert_failure_log(self, dto: ImportAuditLogDTO) -> None:
        """Insert a failed import record into the database.
        
        This method must execute inside a dedicated, isolated transaction or
        on an independent connection to ensure the log is committed even if 
        the main import transaction has been rolled back.
        
        Raises
        ------
        RepositoryWriteError
            If database writes fail or connection is lost.
        """
        ...
```

---

## 4. Transaction Boundaries & Isolation

To prevent database locks and ensure telemetry logging integrity, the failure logging flow must execute as follows:

```
[ Main Import Flow ] 
        │
        ▼
 ( Exception Caught )
        │
        ├───> 1. Revert Database Mutations (ROLLBACK Main Connection)
        ├───> 2. Revert Filesystem Mutations (Unlink copied snapshot)
        │
        ▼
[ Isolated Audit Flow ]
        │
        ├───> 3. Open Independent Transaction (or Separate SQLite Connection)
        ├───> 4. Write Failure Audit Log (INSERT status='FAILED')
        └───> 5. Commit Failure Audit Log (COMMIT Audit Connection)
```

1. **Transaction Decoupling**: The main transaction must be fully rolled back *before* the failure log is written.
2. **Dedicated Connection**: If SQLite's serializable transaction limits are hit, the adapter should open a separate database connection specifically to write the log, preventing locks on the primary connection.

---

## 5. Test Specifications & Assertions

Future unit tests for this slice must satisfy the following contract:

### Test Case 1: Successful Failure Log Persistence
- **Input**: `ImportAuditLogDTO` with `status = 'FAILED'` and `error_message = 'DuplicateStrategyImportError'`.
- **Action**: Call `adapter.insert_failure_log(dto)`.
- **Assertions**:
  - Verify that a row is created in `ImportAuditLog`.
  - Verify that all columns (including `archive_source` and `manifest_hash`) match the DTO exactly.
  - Verify that the transaction is committed.

### Test Case 2: Database Locked Isolation
- **Scenario**: The main connection has a pending, locked transaction.
- **Action**: Call `adapter.insert_failure_log(dto)` from an independent connection.
- **Assertions**:
  - Verify that the audit logging waits for the lock or fails gracefully with `RepositoryWriteError` rather than deadlocking the application.

---

## 6. Recommended Next Two-Task Batch

**Batch 059W-Impl + 059X-Design - ImportAuditLog Repository Adapter and Main Transaction Sequence Integration Design**
- **059W-Impl**: Implement the `AuditLogRepositoryAdapter` (including `insert_failure_log()`) and write unit tests for it, verifying isolated failed audit logging without executing main database writes or copying snapshot files.
- **059X-Design**: Design the integration of the main transaction coordinator (weaving `ArchiveImporter`, `DatabaseManager`, repository adapters, and filesystem copy), detailing failure scenarios and transaction rollback boundaries.
