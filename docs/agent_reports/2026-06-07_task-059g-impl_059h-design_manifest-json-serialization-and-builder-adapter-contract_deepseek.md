# Batch 059G-Impl + 059H-Design — Manifest JSON Serialization and Builder Repository Adapter Design

> Agent: DeepSeek V4 Pro
> Date: 2026-06-07

## Completed

### 059G-Impl — Manifest JSON Serialization

- Added `to_dict()`, `from_dict()`, `to_json()`, `from_json()`, `write_to_folder()`, `read_from_folder()` to `ArchiveManifest`
- Deterministic field order, folder creation, round-trip support
- 6 new tests (dict round trip, JSON round trip, deterministic bytes, field order, folder write/read, subdirectory creation)

### 059H-Design

`docs/archive_builder_repository_adapter_059H.md`: `ArchiveDataSource` protocol with 8 methods, return types, `FakeArchiveDataSource` fixture. Enforces hard failures for missing required materials (strategy, dataset snapshot, validation result, disclaimer) and defines optional vs required provenance. Recommends ArchiveBuilder first pass next.

## Files Changed

| File | Change |
|---|---|
| `archive/manifest.py` | JSON serialization + folder helpers (using deterministic field order) |
| `tests/test_archive_manifest_json.py` | **Created** — 6 tests |
| `docs/archive_builder_repository_adapter_059H.md` | **Created** (enforcing hard failures) |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | Batch -> Done |

## Verification

```
JSON + snapshot + verifier: 18 passed (6 JSON + 5 snapshot + 7 verifier)
Full suite: 1121 passed, 0 warnings
git diff --check -> passes
```
