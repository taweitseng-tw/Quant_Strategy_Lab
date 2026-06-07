# Folder Manifest Integration Design — Task 059J

> Design-only. No production code changed.

## 1. Current State

- `ArchiveBuilder` collects metadata, validates required materials, and produces an `ArchiveManifest` (059I).
- `ArchiveManifest` serializes to/from JSON and writes/reads from a folder (059G).
- `ArchiveVerifier` checks file existence, content hashes, and disclaimer (059C).
- `DatasetSnapshotWriter` produces a deterministic CSV (059E).

## 2. What an Archive Folder Looks Like

```
<experiment_name>/
  manifest.json
  disclaimer.txt
  strategy.json
  dataset_meta.json
  ohlcv_snapshot.csv
  validation_result.json
  backtest_result.json
  instrument.json
  build_task.json
```

## 3. Component Responsibilities

| Component | Responsibility | Status |
|---|---|---|
| `ArchiveBuilder` | Collect + validate + produce manifest | ✅ 059I |
| `ArchiveExporter` (future) | Write all files to folder + copy dataset snapshot + compute hashes + finalise manifest | ❌ Not yet implemented |
| `ArchiveVerifier` | Check integrity of an existing archive | ✅ 059C |
| `ArchiveImporter` (future) | Read archive folder, verify integrity, load into current project | ❌ Not yet implemented |

## 4. Exporter Responsibilities (Next Implementation)

```python
class ArchiveExporter:
    def __init__(self, builder: ArchiveBuilder, data_source: ArchiveDataSource):
        ...

    def export(
        self,
        strategy_uid: str,
        dataset_snapshot_path: str,
        disclaimer_text: str,
        output_dir: str,
        experiment_name: str | None = None,
    ) -> Path:
```

1. Call `builder.build(...)` to get manifest.
2. Copy `dataset_snapshot_path` → `output_dir / "ohlcv_snapshot.csv"`.
3. Write `disclaimer.txt`, `strategy.json`, `dataset_meta.json`, `validation_result.json`, `backtest_result.json`, `instrument.json`, `build_task.json`.
4. Compute SHA-256 hashes for each written file.
5. Update manifest `files` and `content_hashes`.
6. Write final `manifest.json`.
7. Return output directory path.

## 5. Why Exporter is Separate from Builder

- Builder is a pure validation + metadata producer (testable without disk I/O).
- Exporter has side effects (writes files, computes hashes).
- Separation allows testing builder logic independently.

## 6. Recommended Next Two-Task Batch

**Batch 059K-Impl + 059L-Design - ArchiveExporter Folder Writer First Pass and Importer Boundary Design**
- **059K-Impl**: ArchiveExporter folder writer first pass. Writes strategy, dataset metadata, validation result, and copies the dataset CSV snapshot into the destination directory, computes file hashes, and writes the final manifest.json. No zip, no UI/service/real repository wiring.
- **059L-Design**: Importer boundary design. Design the import verification process and boundaries for the future ArchiveImporter without implementation.

## 7. Metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-07
- **Dependencies**: 059I (ArchiveBuilder collector) — Done
