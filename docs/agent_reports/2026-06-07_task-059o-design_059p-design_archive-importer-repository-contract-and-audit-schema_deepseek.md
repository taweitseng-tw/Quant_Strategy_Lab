# Batch 059O-Design + 059P-Design — ArchiveImporter Repository Contract and Import Audit Schema Design (Fix Report)

> Agent: Antigravity Core
> Date: 2026-06-07
> Note: This is an updated report incorporating requested corrections to next-batch recommendation (design-safe / read-only-safe next batch, no UI, no DB writes, no file copy) and transaction sequence details.

## Completed

### 059O-Design — ArchiveImporter Repository Contract Design

`docs/archive_import_repository_contract_design_059O.md` contains:
- Definition of interface contracts (`IImportStrategyRepositoryAdapter`, `IImportDatasetRepositoryAdapter`, `IImportValidationRepositoryAdapter`, and `IImportFilesystemAdapter`).
- Specification of DTO objects (`StrategyImportDTO`, `DatasetMetadataDTO`, and `ValidationResultImportDTO`).
- A comprehensive exception taxonomy representing import execution, database constraint, database lock, and OS filesystem failures.
- **Detailed Step-by-Step Transaction Sequence**: Defined step-by-step logic covering pre-transaction verification, collision checking (read-only queries), beginning SQLite transaction, file copy (snapshot) timing, database write timing, commit sequence, rollback cleanup (database rollback + unlinking partially copied CSV files), and writing failed audit logs within an independent transaction connection. Clearly demarcated which steps are already implemented vs. future implementation/design.

### 059P-Design — Import Audit Schema and Collision Detection Design

`docs/archive_import_audit_schema_design_059P.md` contains:
- Database schema for `ImportAuditLog` to log import history.
- Provenance metadata payload details to be injected into strategy JSON objects upon import.
- SQL-level collision detection queries for strategy and dataset key matching.
- Transaction isolation design for logging failed imports safely without causing database contamination.
- Recommendation for exactly one next two-task batch (`Batch 059Q-Impl + 059R-Design`), focusing on a read-only import plan builder and DTO extraction without UI, DB writes, or file copies.

## Files Changed

| File | Change |
|---|---|
| `docs/archive_import_repository_contract_design_059O.md` | **Created** — Repository contract design document with transaction sequence details |
| `docs/archive_import_audit_schema_design_059P.md` | **Created** — Audit schema and collision design document recommending read-only next steps |
| `docs/changelog.md` | **Modified** — Added changelog entry |
| `docs/task_board.md` | **Modified** — Updated status and proposed next read-only implementation batch |

## Verification

- Full test suite: **1150 passed**
- `git diff --check` passes.
- `git status --short` shows only files within this task scope.

## Known Issues
- None.

## Risks
- Low. This batch is design-only and makes no code modifications, leaving the importer verification skeleton fully intact and functional.

## Recommended Next Two-Task Batch
**Batch 059Q-Impl + 059R-Design - ArchiveImporter Read-Only Import Plan Builder and Import Transaction Sequence Design**
- **059Q-Impl**: Implement the read-only preview skeleton for `ArchiveImporter` (extracting strategy metadata, DTOs, and detecting strategy/dataset collisions in a read-only manner) to show import dry-run summaries to the user, without any database writes, file copy operations, or repository adapter implementation.
- **059R-Design**: Design the detailed SQL transaction sequence, file copy commit phases, failure rollback procedures, and the failed-audit logging execution sequence for future write integration.
- **Strict Constraint**: No UI, no DB writes, no file copy.
