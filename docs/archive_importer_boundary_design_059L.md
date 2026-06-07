# ArchiveImporter Boundary Design — Task 059L

> Design-only. No production code changed.

## 1. Purpose

Define the boundary, responsibilities, verification flow, and failure modes for the future `ArchiveImporter`. The importer is responsible for reading a reproducible experiment archive folder (or `.zip` file), verifying its integrity, and importing its contents (strategy definition, dataset metadata, validation results) back into the local application state (SQLite database, file structures).

## 2. Component Boundary

The `ArchiveImporter` acts as the gateway between external archive files and the internal application database/services.

```
Archive Folder (.zip / folder)
  ↓
[ ArchiveImporter ]  ──(reads & verifies)──> [ ArchiveVerifier ]
  ↓
  ├── Strategy JSON ─────────> StrategyRepository (inserts strategy)
  ├── Dataset Metadata ──────> DatasetRepository (inserts dataset record)
  ├── Dataset CSV Snapshot ──> Data Engine (writes to data/normalized/)
  └── Validation Results ────> ValidationRepository (inserts validation record)
```

## 3. Importer Responsibilities

- **Folder / ZIP Extraction**: Extract a zipped archive file into a temporary workspace directory if provided as a zip file.
- **Integrity Verification Delegation**: Delegate verification to `ArchiveVerifier` to check file existence, content hashes, and disclaimer.
- **Semantic Mapping**: Check if the strategy or dataset already exists in the local database (e.g., matching UID).
- **Import execution**:
  - Insert strategy metadata, definition, and config records.
  - Insert dataset metadata records.
  - Write dataset CSV snapshot to the application's local normalized data store.
  - Insert validation results, Monte Carlo simulations, and Walk-Forward results.

## 4. Non-Goals

- **No Auto-Rebacktesting**: The importer must NOT re-run backtests or validation pipelines. It only imports the historical provenance records.
- **No Automatic File Overwriting**: It must not silently overwrite existing files in the local data directory if a file name collision occurs; instead, it should raise an error or suffix the imported file name.
- **No Schema Upgrades**: It must not run database migrations. If the archive's schema version is incompatible, it must refuse to import.

## 5. Verification Sequence

When importing an archive folder, the sequence of checks is as follows:
1. **Locate Manifest**: Ensure `manifest.json` exists in the archive root.
2. **Schema Compatibility Check**: Parse `manifest.json` and read `archive_version`. If the major version is newer than the application's importer version, abort.
3. **Verify Integrity**: Instantiate `ArchiveVerifier` with the manifest and folder root, then run `verifier.verify_all()`.
4. **Collision Check**: Check local database for existing records matching the strategy's `strategy_uid`.

## 6. Failure Modes and Required Errors

The `ArchiveImporter` must raise specific errors for the following failure cases:
- **Incompatible Schema Version (`IncompatibleSchemaError`)**: Raised if the archive version cannot be read or is a newer major version.
- **Integrity Verification Failure (`ArchiveIntegrityError`)**: Raised if any file is missing, modified, or has a mismatched hash, or if `disclaimer.txt` is empty/missing.
- **Duplicate Strategy Failure (`DuplicateStrategyImportError`)**: Raised if a strategy with the same UID already exists in the database and the caller did not specify overwrite.
- **Database Insertion Failure (`ImportDatabaseError`)**: Raised if database constraints are violated during insert.

## 7. Recommended Next Two-Task Batch

**Batch 059M-Impl + 059N-Design - ArchiveImporter Verification Skeleton and Archive Import Conflict Policy Design**
- **059M-Impl**: Implement `ArchiveImporter` basic skeleton and import verification logic (verifying compatible schema version and delegating to `ArchiveVerifier`), without database insertion.
- **059N-Design**: Design the conflict resolution policies and options (e.g., overwrite, ignore, duplicate with suffix) when importing strategies or datasets that already exist in the database.
