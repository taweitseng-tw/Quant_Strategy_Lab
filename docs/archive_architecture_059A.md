# Reproducible Experiment Archive Architecture — Task 059A

> Design-only. No production code changed.

## 1. Purpose

Package a complete strategy research experiment into a self-contained, verifiable archive so that any experiment can be re-loaded, re-validated, or shared without depending on the original project folder state.

## 2. Non-Goals

- Not real-time backup or continuous sync.
- Not multi-project merge or diff.
- Not live trading export.
- Not replacing SQLite project storage.
- Not cloud storage or distribution network.

## 3. What Goes Into an Archive

| Component | Source | Format |
|---|---|---|
| Strategy definition | `strategies/` or SQLite | JSON |
| Build config (seed, ranges, GA/GP config) | SQLite `build_tasks` | JSON |
| Dataset metadata (symbol, timeframe, date range, source) | SQLite `datasets` | JSON |
| Dataset OHLCV snapshot | `data/` | Parquet (compressed) |
| Instrument profile | SQLite `instruments` | JSON |
| Session template | SQLite `sessions` | JSON |
| Backtest result (IS + OOS) | SQLite `backtest_results` | JSON |
| Validation result (stress, MC, WF, elimination) | PipelineResult | JSON |
| Software version + git commit hash | Runtime | TEXT |
| Manifest | Generated | JSON |
| Disclaimer text | Static | TEXT |

## 4. Storage Format Comparison

### Option A: Folder + Manifest JSON

```
<experiment_name>/
  manifest.json
  disclaimer.txt
  strategy.json
  build_config.json
  dataset_meta.json
  ohlcv.parquet
  instrument.json
  session.json
  backtest_is.json
  backtest_oos.json
  validation_result.json
```

**Pros**: Human-readable, diff-friendly, no compression overhead, files individually inspectable.
**Cons**: Multiple files to manage, requires folder packaging for sharing.

### Option B: Zipped Archive Package

```
<experiment_name>.qsl.zip
  ├── manifest.json
  ├── strategy.json
  └── ...
```

**Pros**: Single file for sharing, compression reduces size for large OHLCV data.
**Cons**: Opaque — requires unzip to inspect. Harder to version-control individual components.

### Option C: Folder + Manifest JSON, Zip on Export (Recommended MVP)

Use Option A as the canonical on-disk format. Add optional zip packaging as an export step.

**Pros**: Folder format is inspectable and diff-friendly during development. Zip is a convenience export. No conflict — folder is canonical, zip is a distribution wrapper.
**Cons**: Two code paths (folder write + zip wrapper) — minor implementation overhead.

## 5. Module Boundaries

| Module | Responsibility |
|---|---|
| `archive/` (new) | `ArchiveBuilder` (collect), `ArchiveExporter` (write folder/zip), `ArchiveImporter` (read/validate), `ArchiveVerifier` (integrity) |
| `repository/` | Query strategies, datasets, instruments, build configs, backtest/validation results |
| `core/models/` | `ArchiveManifest`, `ArchiveProvenance` dataclasses |
| `app/` | UI trigger for export/import (future) |

No engine changes. Archive module depends on repository layer, not on engines directly.

## 6. User Workflow

```
User clicks "Export Experiment" on a validated strategy
  → ArchiveBuilder collects all provenance components
  → ArchiveExporter writes to folder (optional zip)
  → archive ready at <project_root>/archives/<name>/

User clicks "Import Experiment"
  → ArchiveImporter reads manifest
  → ArchiveVerifier checks integrity (hashes, schema version)
  → Strategy + dataset + config loaded into current project
```

## 7. Recommended MVP

**Option C — Folder + Manifest JSON canonical format, zip on export.**

- MVP scope: `ArchiveBuilder` + `ArchiveExporter` (folder only) + `ArchiveVerifier`.
- Zip wrapping deferred to a follow-up task.
- UI triggers deferred.

## 8. Next Implementation Batch

Task 059C-Impl + 059D-Design — `archive/` module skeleton + `ArchiveManifest` / `ArchiveVerifier` unit tests, followed by dataset snapshot format and dependency decision design.

## 9. Metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-07
