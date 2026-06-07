# ArchiveImporter Repository Contract Design — Task 059O

> [!NOTE]  
> **Design-only document.** No production Python code is implemented in this batch. The `ArchiveImporter` remains verification-only.

---

## 1. Purpose

This document defines the repository and service adapter interfaces, data objects, transaction expectations, and exception taxonomy required to import verified strategy archives into the workspace database and filesystem.

---

## 2. Adapter Interface Taxonomy

To isolate the `ArchiveImporter` from SQL queries, filesystem details, and service orchestrators, it will interact with the application state via three dedicated repository adapters and one filesystem adapter.

```
[ ArchiveImporter ]
        │
        ├───> [ IImportStrategyRepositoryAdapter ]  ──> SQLite (Strategy Table)
        ├───> [ IImportDatasetRepositoryAdapter ]   ──> SQLite (Dataset Table)
        ├───> [ IImportValidationRepositoryAdapter ]──> SQLite (Validation Table)
        └───> [ IImportFilesystemAdapter ]          ──> data/normalized/ File Store
```

### 2.1 Strategy Repository Adapter Contract
Responsible for strategy duplicate detection and database insertion.

```python
class IImportStrategyRepositoryAdapter(Protocol):
    def exists_by_uid(self, strategy_uid: str) -> bool:
        """Check if a strategy with the given UID already exists in the SQLite database."""
        ...

    def insert_strategy(self, strategy_data: StrategyImportDTO) -> None:
        """Insert strategy metadata, name, and JSON definition.
        
        Raises
        ------
        DuplicateStrategyImportError
            If a strategy with the same UID already exists.
        RepositoryWriteError
            If a database constraint or write failure occurs.
        """
        ...
```

### 2.2 Dataset Repository Adapter Contract
Responsible for dataset metadata persistence and duplicate/compatibility checks.

```python
class IImportDatasetRepositoryAdapter(Protocol):
    def exists_by_id(self, dataset_id: int) -> bool:
        """Check if a dataset with the given ID already exists."""
        ...

    def get_by_properties(self, symbol: str, timeframe: str) -> DatasetMetadataDTO | None:
        """Retrieve dataset metadata matching the unique symbol and timeframe."""
        ...

    def insert_dataset_metadata(self, metadata: DatasetMetadataDTO) -> int:
        """Insert dataset metadata and return the generated or specified dataset ID.
        
        Raises
        ------
        RepositoryWriteError
            If insertion fails due to constraint violations.
        """
        ...
```

### 2.3 Validation Repository Adapter Contract
Responsible for validation, Monte Carlo, and Walk-Forward results insertion.

```python
class IImportValidationRepositoryAdapter(Protocol):
    def insert_validation_result(self, validation: ValidationResultImportDTO) -> None:
        """Insert validation results linked to the strategy.
        
        Raises
        ------
        RepositoryWriteError
            If insertion fails.
        """
        ...
```

### 2.4 Filesystem Adapter Contract
Handles the placement of the OHLCV CSV dataset snapshot.

```python
class IImportFilesystemAdapter(Protocol):
    def copy_dataset_snapshot(self, source_path: Path, target_filename: str) -> Path:
        """Copy the snapshot CSV file from the archive folder to the project's normalized data folder.
        
        Returns
        -------
        Path
            The absolute path to the newly written file.
            
        Raises
        ------
        SnapshotWriteError
            If file copy fails or space is insufficient.
        """
        ...
```

---

## 3. Data Transfer Objects (DTOs)

The importer will extract data from the verified archive and pass these immutable DTOs into the adapters.

### 3.1 `StrategyImportDTO`
```python
@dataclass(frozen=True)
class StrategyImportDTO:
    strategy_uid: str
    name: str
    strategy_json: str
    generator_version: str
    build_task_id: int | None
    provenance_meta: dict[str, Any]  # Track import time and original source
```

### 3.2 `DatasetMetadataDTO`
```python
@dataclass(frozen=True)
class DatasetMetadataDTO:
    dataset_id: int
    symbol: str
    timeframe: str
    row_count: int
    data_format: str  # e.g., "CSV"
```

### 3.3 `ValidationResultImportDTO`
```python
@dataclass(frozen=True)
class ValidationResultImportDTO:
    strategy_uid: str
    passed: bool
    metrics_json: str
    elimination_result_json: str
    stress_test_results_json: str | None
    monte_carlo_results_json: str | None
    walk_forward_results_json: str | None
```

---

## 4. Transaction Boundaries & Rollback Expectations

Importing an archive requires modifications to both SQLite (database) and the local disk storage (CSV file). To preserve integrity, the following transaction sequence must be followed:

### 4.1 Step-by-Step Transaction Sequence

| Step | Operation | Scope / State | Transaction Boundary | Description |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Integrity Verification** | **Current Implemented** | N/A (Read-Only) | Parse `manifest.json`, validate major version compatibility, and run `ArchiveVerifier.verify_all()`. |
| **2** | **Collision Check** | **Future Implementation** | N/A (Read-Only) | Query Strategy and Dataset tables for UID/key collisions prior to opening any write transactions. |
| **3** | **Begin DB Transaction** | **Future Implementation** | Begin SQLite Transaction | Open a `BEGIN TRANSACTION` block on the database connection. |
| **4** | **File Copy (Snapshot)** | **Future Implementation** | Filesystem mutation | Write the OHLCV CSV snapshot to the local directory (e.g., `data/normalized/`). If file write fails, raise `SnapshotWriteError` and skip to Step 8. |
| **5** | **Database Write** | **Future Implementation** | Within SQLite Transaction | Write the Dataset metadata, Strategy payload, and Validation/Monte Carlo/WF results into SQLite. If any query fails, raise `RepositoryWriteError` and skip to Step 7. |
| **6** | **Commit Transaction** | **Future Implementation** | Commit SQLite Transaction | Issue `COMMIT` on the database connection. The import is now complete and persisted. |
| **7** | **Rollback SQLite** | **Future Implementation** | Rollback SQLite Transaction | If an error occurs in Step 5, issue `ROLLBACK` on the database connection to revert all database mutations. Proceed to Step 8. |
| **8** | **Rollback Filesystem** | **Future Implementation** | Filesystem Cleanup | If Step 4 executed but the transaction failed/aborted, delete (unlink) the written CSV file to prevent dangling assets on disk. |
| **9** | **Write Failure Audit Log**| **Future Implementation** | Independent SQLite Transaction | Open a separate SQLite connection or new independent transaction block, insert a record into `ImportAuditLog` with `status = 'FAILED'`, and log the `error_message`. |

This sequence ensures that a failed import leaves no orphaned CSV files, registers database schema entries atomically, and logs failure telemetry independently of the aborted transaction.

---

## 5. Exception Taxonomy

All repository and adapter failures must bubble up into a structured hierarchy:

```
ArchiveImporterError (Base)
  ├── IncompatibleSchemaError
  └── ImportExecutionError
        ├── DuplicateStrategyImportError
        ├── RepositoryWriteError
        │     ├── DatabaseConstraintError
        │     └── DatabaseLockError
        └── SnapshotWriteError
```

- **`ImportExecutionError`**: Base exception for all failure modes during the active import transaction.
- **`DuplicateStrategyImportError`**: Raised specifically during collision checks under the Reject policy.
- **`RepositoryWriteError`**: Wrap SQLite failures, database constraint violations, or database locking issues.
- **`SnapshotWriteError`**: Wrap OS filesystem errors during CSV copy operations.
