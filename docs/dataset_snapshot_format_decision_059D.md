# Dataset Snapshot Format Decision — Task 059D

> Design-only. No production code changed.

## 1. Context

The archive architecture (059A) requires a dataset OHLCV snapshot as part of each archive. The format must be self-contained, verifiable (hash-stable), and readable without external dependencies beyond what QSL already requires.

## 2. Format Options

### A: CSV

| Aspect | Detail |
|---|---|
| **Storage** | Plain text, rows x columns |
| **Size** | Largest (no compression) |
| **Hash stability** | Fragile — float precision, line endings, and column ordering can change hash |
| **Readback** | `pd.read_csv()` — already in use |
| **Dependency** | None new |

### B: JSON-lines

| Aspect | Detail |
|---|---|
| **Storage** | One JSON object per line |
| **Size** | Larger than CSV (field names repeated per row) |
| **Hash stability** | Moderate — depends on key ordering and float precision |
| **Readback** | `pd.read_json(lines=True)` — already available |
| **Dependency** | None new |

### C: Parquet

| Aspect | Detail |
|---|---|
| **Storage** | Columnar binary, compressed |
| **Size** | Smallest (typically 5-10× smaller than CSV) |
| **Hash stability** | Excellent — binary format, byte-level deterministic |
| **Readback** | `pd.read_parquet()` — requires `pyarrow` or `fastparquet` |
| **Dependency** | **`pyarrow` — not currently in QSL dependencies** |

### D: Defer Snapshot Writer

| Aspect | Detail |
|---|---|
| **Approach** | Store dataset metadata only (symbol, timeframe, source path, SHA-256 of original source file). Do not snapshot OHLCV data into the archive yet. |
| **Size** | Minimal |
| **Risk** | Archive depends on source file still being present at the recorded path. Breaks reproducibility if source is moved/deleted. |

## 3. Dependency Impact

| Option | New Dependency | Cost |
|---|---|---|
| CSV | None | 0 |
| JSON-lines | None | 0 |
| Parquet | `pyarrow` (~30 MiB wheel, pure C++) | Adds to packaging footprint. Not yet in `requirements.txt`. |
| Defer | None | 0 |

## 4. Recommendation

### **A — CSV, with a disciplined write-then-hash pipeline.**

Rationale:
- CSV is already the import format for QSL. Round-tripping through `pd.to_csv() → pd.read_csv()` is well-tested.
- Hash stability is achieved by fixing float format (`.6f`), using `index=False`, and normalizing line endings (`\n`).
- No new dependency. The archive can be implemented immediately without `pyarrow`.
- Parquet is the better long-term format, but adds a dependency that should be decided by the user, not this design task.

### Implementation path:

1. Write dataset as CSV with `float_format="%.6f"`, `index=False`, `line_terminator="\n"`.
2. Compute SHA-256 of the written CSV bytes.
3. Store hash in manifest.
4. On import, re-hash and compare before parsing.

If the user wants Parquet later, it can be added as a parallel writer behind a config flag without changing the manifest schema.

## 5. Next Two-Task Batch

**Task 059E-Impl + 059F-Design** — CSV dataset snapshot writer + hash-verified round-trip test.

## 6. Metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-07
- **Dependencies**: 059A (archive architecture), 059C (verifier skeleton) — Done
