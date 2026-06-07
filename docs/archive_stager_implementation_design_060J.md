# ArchiveStager Implementation Design — Task 060J (Fix)

> Design-only. No production code changed.
> Aligned with `docs/archive_import_filesystem_staging_design_059Z.md`.

## 1. Purpose

Design a future `ArchiveStager` that copies the archive's `ohlcv_snapshot.csv` to a project-local staging directory, verifies its SHA-256 hash, and moves it to the final project destination only after DB commit.

## 2. Non-Goals

- Not implementing ArchiveStager.
- Not implementing coordinator integration.
- Not adding zip extraction.

## 3. Source Validation

| Check | Method |
|---|---|
| Archive root is a directory | `Path(archive_root).is_dir()` |
| `manifest.json` exists | `(root / "manifest.json").is_file()` |
| `ohlcv_snapshot.csv` exists | `(root / "ohlcv_snapshot.csv").is_file()` |
| No path traversal | Reject paths containing `..` |
| No symlinks outside archive | Reject `Path.resolve()` outside `archive_root` |

## 4. Project-Local Staging Directory

```python
from pathlib import Path

def _staging_dir(project_root: Path, experiment_name: str, run_id: str) -> Path:
    return project_root / ".staging" / f"{experiment_name}_{run_id}"
```

- `run_id` is a short unique string (timestamp or UUID) provided by the coordinator.
- The `.staging/` directory lives inside the project and is gitignored.

## 5. ArchiveStager API

```python
class ArchiveStager:
    """Copies, verifies, moves dataset snapshot files for archive import."""

    def __init__(
        self,
        archive_root: str | Path,
        project_root: str | Path,
        experiment_name: str,
        run_id: str,
    ) -> None:
        self._src = Path(archive_root)
        self._project_root = Path(project_root)
        self._staging = _staging_dir(self._project_root, experiment_name, run_id)
        self._final_dir = self._project_root / "data" / "imported" / experiment_name
        self._staged_path: Path | None = None

    # -- public -------------------------------------------------------------

    def stage_dataset_snapshot(self, expected_hash: str) -> Path:
        """Copy ohlcv_snapshot.csv to staging dir and verify hash.

        Returns the staging path.  Raises FileNotFoundError if source
        is missing, HashMismatchError if hash does not match.
        """
        self._validate_source()
        src = self._src / "ohlcv_snapshot.csv"
        self._staging.mkdir(parents=True, exist_ok=True)
        self._staged_path = self._staging / "ohlcv_snapshot.csv"
        _copy_file(src, self._staged_path)

        actual = _sha256_file(self._staged_path)
        if actual != expected_hash:
            self._staged_path.unlink(missing_ok=True)
            self._staged_path = None
            raise HashMismatchError(
                f"Staged file hash mismatch: expected {expected_hash[:16]}..., "
                f"got {actual[:16]}..."
            )
        return self._staged_path

    def move_to_final_destination(self) -> Path:
        """Move staged file to ``data/imported/<experiment>/ohlcv.csv``.

        Call AFTER DB commit.  On failure, the staging file is left
        intact — the coordinator must return a partial/repair-needed
        result and must NOT delete DB rows.
        """
        if self._staged_path is None:
            raise RuntimeError("No staged file to move.")
        self._final_dir.mkdir(parents=True, exist_ok=True)
        src = self._staged_path
        dest = self._final_dir / "ohlcv.csv"
        import shutil
        moved = Path(shutil.move(str(src), str(dest)))
        self._staged_path = None   # only nil AFTER successful move
        return moved

    def cleanup_temp(self) -> None:
        """Remove the staging directory and all contents."""
        import shutil
        if self._staging.exists():
            shutil.rmtree(self._staging, ignore_errors=True)
```

## 6. Hash Verification Helper

```python
def _sha256_file(path: Path, chunk_size: int = 8192) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()
```

## 7. Cleanup Policy

| Scenario | Action |
|---|---|
| Hash mismatch during staging | `staged_path` deleted by `stage_dataset_snapshot`; caller calls `cleanup_temp()` |
| DB commit fails (before final move) | Caller calls `cleanup_temp()`. No final destination files exist. |
| Final move succeeds | Staging dir is now empty (file moved). Caller calls `cleanup_temp()` to remove the empty dir. |
| Final move fails (after DB commit) | DB rows exist. Staging file still exists (``self._staged_path`` is NOT nil — the move failed before clearing it). Caller returns `ImportResult(partial=True)`. Caller does NOT delete DB rows. Caller must NOT call `cleanup_temp()` yet — the staging file is the only copy and must be preserved for manual repair/inspection. `cleanup_temp()` is called only after the coordinator gives up repair or after an operator confirms the file can be discarded. |
| Coordinator aborted (unclean exit) | Staging dir persists. A future repair/fixup task or manual cleanup removes it. |

## 8. Transaction Ordering (Aligned with 060A and 059Z)

```
1. Stager.validate_source()
2. Stager.stage_dataset_snapshot(expected_hash)     # filesystem, no DB
3. DB transaction open
4. Adapter.insert_strategy_no_commit(...)            # DB (no commit)
5. Adapter.insert_dataset_no_commit(...)             # DB (no commit)
6. conn.commit()                                      # DB durable
   └─ if FAIL → Stager.cleanup_temp()                # temp only, no final dest
7. Stager.move_to_final_destination()                 # filesystem, after commit
   └─ if FAIL → return ImportResult(partial=True)     # DB rows exist, staging preserved
   └─ if OK → self._staged_path = None; proceed to cleanup
8. Stager.cleanup_temp()                              # remove empty staging dir (only if move OK)
```

## 9. Focused Tests (Future Implementation)

| # | Test | Scope |
|---|---|---|
| 1 | Source folder sans `ohlcv_snapshot.csv` raises | Validation |
| 2 | Hash mismatch raises + staged file deleted | Integrity |
| 3 | Hash match returns staging path under `.staging/` | Success |
| 4 | `move_to_final_destination` to `data/imported/<exp>/ohlcv.csv` | Success |
| 5 | `cleanup_temp()` removes `.staging/` dir | Cleanup |
| 6 | DB failure before final move → only temp cleaned, no final files | DB failure cleanup |
| 7 | Move failure after DB commit → partial result, staging file intact | Orphan handling |
| 8 | Path traversal rejected | Security |
| 9 | Symlink outside archive rejected | Security |

## 10. Next Two-Task Batch

**Batch 060K-Impl + 060L-Design — ArchiveStager Implementation + ArchiveImportCoordinator First-Pass Wiring Design.**

- 060K: Implement ArchiveStager per this design.
- 060L: Design ArchiveImportCoordinator first-pass wiring — no implementation.

## 11. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07 (fix: project-local staging, cleanup policy, aligned ordering)
