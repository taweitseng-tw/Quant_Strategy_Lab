# Batch 059A-Design + 059B-Design — Experiment Archive Architecture and Provenance Integrity Design

> Agent: DeepSeek V4 Pro
> Date: 2026-06-07

## Completed

### 059A — Archive Architecture

`docs/archive_architecture_059A.md`:
- 11 provenance components defined
- 3 storage format options compared
- Recommends Option C: folder + manifest JSON canonical, zip on export
- Module boundaries: `archive/` (new), depends on `repository/`, no engine coupling

### 059B — Provenance Integrity

`docs/provenance_integrity_design_059B.md`:
- 7 provenance field groups: archive meta, strategy, dataset, instrument, backtest, validation, results
- Content hashes (SHA-256), schema version handling, missing-file detection, disclaimer
- Next batch: 059C — `archive/` module skeleton + `ArchiveManifest` + tests

### Architecture Update

`docs/architecture.md`: Added "Archives and Reproducibility" design-phase section.

## Files Changed

| File | Change |
|---|---|
| `docs/archive_architecture_059A.md` | **Created** |
| `docs/provenance_integrity_design_059B.md` | **Created** |
| `docs/architecture.md` | Archive section added |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | Batch -> Done |

## Verification

```
git diff --check -> passes
No production code changed
```

## Recommended Next Batch

**Task 059C-Impl + 059D-Design** — `archive/` module skeleton + `ArchiveManifest` dataclass + unit tests.
