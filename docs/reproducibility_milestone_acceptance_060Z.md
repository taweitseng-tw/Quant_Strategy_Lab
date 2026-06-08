# Reproducibility Milestone Acceptance — Task 060Z

> Signoff only. No production code changed.

## 1. Accepted Chain Summary

| Layer | Component | Status | Batch |
|---|---|---|---|
| **Archive manifest** | `ArchiveManifest` dataclass, JSON serialization, folder read/write | ✅ Done | 059A–059G |
| **Archive verifier** | `ArchiveVerifier` — file existence, SHA-256, disclaimer | ✅ Done | 059C |
| **Dataset snapshot** | `write_dataset_snapshot()` — deterministic CSV | ✅ Done | 059E |
| **Archive builder** | `ArchiveBuilder` — validates inputs, produces manifest | ✅ Done | 059I |
| **Archive exporter** | `ArchiveExporter` — writes metadata + snapshot + manifest to folder | ✅ Done | 059K |
| **Archive importer** | `ArchiveImporter.build_preview()` — read-only manifest listing | ✅ Done | 059Q |
| **Archive stager** | `ArchiveStager` — project-local `.staging/`, hash verify, final move | ✅ Done | 060K |
| **Coordinator** | `ArchiveImportCoordinator` — 6-phase sequence with fakes + acceptance | ✅ Done | 060M, 060O |
| **Strategy adapter** | `StrategyRepoAdapter` — UID-based dedup, no-commit, rollback guard | ✅ Done | 060E |
| **Dataset adapter** | `DatasetRepoAdapter` — hash/fallback dedup, dual schema, no-commit | ✅ Done | 060I |
| **Audit log** | `ImportAuditLog` schema + `insert_failure_log()` | ✅ Done | 059U, 059W |
| **Schema migration** | `snapshot_hash` column (idempotent, PRAGMA-probed) | ✅ Done | 060G |
| **Export service** | `ArchiveExportService` — application-layer wrapper | ✅ Done | 060Q |
| **Project data source** | `ProjectArchiveDataSource` — scanning strategy JSON for UID | ✅ Done | 060W |
| **Round-trip** | Export → verify → import → assert repository state | ✅ Done | 060S |
| **UI guard** | Export Archive button on Results page with 4 guards | ✅ Done | 060U |

## 2. Remaining Gaps

### Required Before Full UI Export

| Gap | Effort | Solution |
|---|---|---|
| No raw-row provider for `StrategyRepository` | Small | Add `list_all_raw()` per 060Y Option A |
| Dataset snapshot path not always tracked | Small | Dataset ID → `DatasetRepository.get_raw_by_id()` → `normalized_path` |
| Validation result not keyed by `strategy_uid` | Small | Adapt `MainWindow.latest_validation_result` lookup |

### Optional Polish

| Gap | Priority | Notes |
|---|---|---|
| Zip archive support | Low | Folder-only MVP; zip is convenience export |
| Success audit writes | Low | Only failure audit implemented so far |
| Import UI | Low | Coordinator is ready; no UI trigger yet |

### Explicitly Out of Scope

- Live trading, broker API, real-time data.
- GA/GP expansion, portfolio backtest.
- Multi-user, cloud storage, distributed computation.
- Investment advice, performance guarantees.

## 3. Verdict

### **Reproducibility milestone is complete for production archive export at the engine, adapter, service, and round-trip acceptance levels.**

The remaining gap before a user can click "Export Archive" and get a verifiable archive is:
1. Add `StrategyRepository.list_all_raw()` (or equivalent).
2. Wire `ProjectArchiveDataSource` with real repository providers in `MainWindow._handle_export_archive()`.
3. Resolve the dataset snapshot path from the dataset repository.

All three are well-understood, small-scope tasks.

## 4. Recommended Next Two-Task Batch

**Batch 060Y-Impl + Reproducibility Final Changelog — Add raw-row provider + wire ProjectArchiveDataSource + close milestone.**

- 060Y-Impl: Implement `StrategyRepository.list_all_raw()` and `DatasetRepository.get_raw_by_id()`.
- Follow-up single task: Wire `ProjectArchiveDataSource` in `MainWindow._handle_export_archive()` with real providers.

## 5. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
