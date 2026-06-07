# Archive Import Filesystem Staging Design — Task 059Z

> Design-only. No production code changed.

## 1. Purpose

Define how files from an archive folder or zip are staged (copied) into the project's local directory structure during import, before repository writes.

## 2. Non-Goals

- Not implementing filesystem copy/staging — design only.
- Not zip extraction (deferred).
- Not coordinator orchestration (deferred).

## 3. Design

### 3.1 Source Archive Path Validation

| Rule | Implementation |
|---|---|
| Archive root is a folder | `Path.is_dir()` |
| Archive contains `manifest.json` | `(root / "manifest.json").is_file()` |
| Manifest parses and verifies | Call `ArchiveVerifier.verify_all()` |
| Dataset snapshot exists | `(root / "ohlcv_snapshot.csv").is_file()` |
| No symlinks outside archive | Reject paths with `..` or absolute components |

### 3.2 Destination Path Policy

| Artifact | Destination |
|---|---|
| `ohlcv_snapshot.csv` | `<project_root>/data/imported/<experiment_name>/ohlcv.csv` |
| Disclaimer | Not staged (tree-level info only) |
| Strategy JSON, validation JSON | Not staged (DB-write only) |

### 3.3 Temporary Staging Path

A temp directory `<project_root>/.staging/<experiment_name>_<timestamp>/` is used during staging to allow atomic move to final destination. If the import fails, the temp directory is deleted.

### 3.4 Hash Verification

After copy, SHA-256 of the staged file is compared to `manifest.content_hashes[filename]`. Mismatch → delete staged file, abort import.

### 3.5 Rollback Cleanup

Two distinct cleanup zones:

| Zone | Path | When cleaned |
|---|---|---|
| **Temp staging** | `<project_root>/.staging/<exp>_<ts>/` | On any failure before final dest move |
| **Final destination** | `<project_root>/data/imported/<exp>/` | Only if DB commit fails AFTER the final move |

If final move has already occurred but DB commit fails, the final destination files must be deleted to prevent orphaned data. The coordinator must not "commit" staging state until the SQLite transaction is durable.

### 3.6 Transaction Ordering (Safe: Stage → DB Commit → Final Move)

```
1. Verify archive (manifest + hashes)
2. Stage dataset snapshot to .staging/      # no DB writes yet
3. Verify staged file hash against manifest
4. Open DB transaction
5. Insert strategy row
6. Commit DB transaction (durable)          # strategy row is now persisted
     └─ if FAIL → rollback DB + delete .staging/ (both zones)
7. Move staged file from .staging/ to data/imported/   # safe: DB row is already committed
     └─ if FAIL at move → strategy row exists but no dataset file → repair task or manual fix
       (acceptable gap for MVP; future: add a pending_filesystem_move flag)
8. Write success audit log (optional second DB write)
```

**Key change**: DB commit happens BEFORE file move. This prevents orphaned destination files on transaction failure. The trade-off is a small window where a strategy row exists but the dataset file hasn't been moved yet — acceptable for MVP, to be addressed by a `pending_filesystem_move` flag in a future release.

## 4. Implementation Surface (Future)

| Component | File |
|---|---|
| `ArchiveStager` class | `archive/stager.py` |
| Tests | `tests/test_archive_stager.py` |
| Coordinator integration | Deferred |

## 5. Next Two-Task Batch

**Batch 060A-Design only — Archive Import Coordinator Architecture Design** (coordinator design, no implementation).

## 6. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
- **Dependencies**: 059Y (strategy insert adapter) — Done
