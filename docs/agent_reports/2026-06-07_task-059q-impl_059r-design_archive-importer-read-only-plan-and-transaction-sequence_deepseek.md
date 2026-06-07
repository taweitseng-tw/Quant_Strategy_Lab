# Batch 059Q-Impl + 059R-Design — ArchiveImporter Read-Only Import Plan Builder and Import Transaction Sequence Design

> Agent: Antigravity Core
> Date: 2026-06-07

## Completed

### 059Q-Impl — ArchiveImporter Read-Only Import Plan Builder

`archive/importer.py` has been extended with:
- `ArchiveImportPreview` dataclass: holds verified plan, strategy name, dataset ID/symbol/timeframe, validation status, and collision status flags.
- `IImportCollisionDetector` protocol: defines check methods `strategy_exists` and `dataset_exists`.
- `ArchiveImporter.build_preview()`: 
  - Verification phase calls existing `verify()` logic.
  - Loads and verifies strategy, dataset metadata, and validation result JSON payload structures.
  - Resolves strategy name and dataset details.
  - Intercepts malformed payload JSON files to raise `ArchiveImporterError`.
  - Runs collision queries through the `IImportCollisionDetector` interface to mark dry-run summary collision flags.
- `tests/test_archive_importer.py` contains 5 new tests covering:
  - Valid archive preview (asserts DTO metadata matches exported content).
  - Missing payload file (asserts raises `ArchiveIntegrityError`).
  - Invalid JSON payload corruption (asserts raises `ArchiveImporterError`).
  - Strategy collision reported read-only (using a fake collision double).
  - Dataset collision reported read-only (using a fake collision double).
- Updated `archive/__init__.py` to export the new classes and protocols.

### 059R-Design — Import Transaction Sequence Design Hardening

`docs/archive_import_transaction_sequence_design_059R.md` contains:
- Complete flowchart separating read-only and write transactional phases by user approval boundaries.
- Precise definition of all phases (integrity verification, collision preview, user approval boundary, database transaction begin, file copy staging, database writes, transaction commit, rollback, file cleanup, and isolated failed audit logging).
- Detailed mapping of what is currently implemented vs. future implementation.
- Recommendation for exactly one next two-task batch (`Batch 059S-Design + 059T-Design`).

## Files Changed

| File | Change |
|---|---|
| `archive/importer.py` | **Modified** — Added `IImportCollisionDetector`, `ArchiveImportPreview`, and `build_preview()` |
| `archive/__init__.py` | **Modified** — Exported new preview types and protocols |
| `tests/test_archive_importer.py` | **Modified** — Added 5 preview/collision test cases |
| `docs/archive_import_transaction_sequence_design_059R.md` | **Created** — Detailed transaction sequence document |
| `docs/changelog.md` | **Modified** — Added Batch 059Q + 059R entry |
| `docs/task_board.md` | **Modified** — Updated status and proposed next implementation batch |

## Verification

- Focused archive tests (importer + exporter + builder + verifier + manifest + snapshot): **52 passed**
- Full test suite: **1155 passed**
- `git diff --check` passes.
- `git status --short` shows only files within this task scope.

## Known Issues
- None.

## Risks
- Low. The preview features make no filesystem mutations and no database writes, ensuring that all actions remain read-only.

## Recommended Next Two-Task Batch
**Batch 059S-Design + 059T-Design - ImportAuditLog Migration Plan and Repository Adapter Test Contract Design**
- **059S-Design**: Design the SQLite database schema migration plan for the `ImportAuditLog` table and define the required schema changes, without executing the migration.
- **059T-Design**: Design the repository adapter test contracts (including mock and spy behavior verification), rollback acceptance criteria, and edge-case error scenarios, without implementing DB writes or CLI/UI/service orchestration.
