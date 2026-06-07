# Archive Import Coordinator Acceptance Test Contract — Task 060B (Fix)

> Design-only. Tests are **not implemented**. This document defines the contract for future implementation.

## 1. Test Strategy

Use spies/fakes for all collaborators. Each test verifies the safe ordering defined in 060A: verify → preflight → stage → write → finalise → audit.

## 2. Architecture Note: StrategyRepoAdapter Auto-Commit

`StrategyRepoAdapter.insert_strategy()` calls `self._conn.commit()` internally. The coordinator first pass **cannot roll back** a committed strategy row. Therefore:

- Preflight duplicate check (read-only) must happen **before** staging and durable insert.
- Staging must happen **before** durable insert.
- The first-pass test contract must verify that preflight UID scan + staging happen before `insert_strategy()` is called.
- The test contract must **not** assert unified rollback across strategy + staging.

## 3. Test Fixture: Fake Collaborator Spies

```python
class FakePreviewBuilder:
    def build_preview(self, root) -> ArchiveManifest:
        self.called_with = root
        return self.return_manifest

class FakeVerifier:
    def verify_all(self) -> bool:
        self.called = True
        if self.raise_error:
            raise ArchiveIntegrityError(self.raise_error)
        return True

class FakeStrategyAdapter:
    def validate_preflight(self, dto) -> None:
        """Read-only preflight: validates DTO + scans for duplicate UID."""
        self.preflight_called_with = dto
        if self.raise_duplicate:
            raise DuplicateStrategyUIDError(...)
        if self.raise_error:
            raise StrategyRepoAdapterError(...)

    def insert_strategy(self, dto) -> int:
        """Durable insert (auto-committed)."""
        self.insert_called_with = dto
        self.insert_call_count += 1
        return 42

class FakeAuditAdapter:
    def insert_failure_log(self, dto) -> None:
        self.called_with_dto = dto
        self.call_count += 1

class FakeStager:
    def stage_dataset_snapshot(self) -> str:
        self.stage_count += 1
        return "/tmp/staged/file.csv"

    def move_to_final_destination(self, path) -> str:
        self.move_count += 1
        return "/data/imported/exp/ohlcv.csv"
```

## 4. Safe Call Ordering (Per 060A Fix)

```
1. build_preview(archive_root_path)
2. verifier.verify_all()
3. ensure_import_audit_log_schema(connection)
4. strategy_adapter.validate_preflight(dto)   ← read-only, no DB write
5. stager.stage_dataset_snapshot()            ← filesystem, no DB write
6. stager.verify_staged_hash(path, expected)  ← filesystem, no DB write
7. strategy_adapter.insert_strategy(dto)      ← durable DB write (auto-commit)
8. stager.move_to_final_destination(path)     ← filesystem, no DB write
9. audit_adapter.insert_failure_log(...)      ← only on failure at steps 4-8
10. return ImportResult(...)
```

## 5. Test Cases

### 5.1 Success Path

| Step | Assertion |
|---|---|
| `build_preview` called with archive root | `fake_preview.called_with == archive_root` |
| `verify_all` called | `fake_verifier.called is True` |
| `validate_preflight` called with correct DTO | `fake_strat.preflight_called_with.strategy_uid == expected` |
| `stage_dataset_snapshot` called once | `fake_stager.stage_count == 1` |
| `insert_strategy` called once (after staging) | `fake_strat.insert_call_count == 1` |
| `move_to_final_destination` called once | `fake_stager.move_count == 1` |
| `insert_failure_log` NOT called | `fake_audit.call_count == 0` |
| Return `success=True` | `result.success is True` |

### 5.2 Duplicate UID Failure Path

`FakeStrategyAdapter.raise_duplicate = True` (raised during `validate_preflight`)

| Step | Assertion |
|---|---|
| `validate_preflight` raises DuplicateUIDError | Caught by coordinator |
| `stage_dataset_snapshot` NOT called | `fake_stager.stage_count == 0` |
| `insert_strategy` NOT called | `fake_strat.insert_call_count == 0` |
| `insert_failure_log` called once | `fake_audit.call_count == 1` |
| Return `skipped=True` | `result.skipped is True` |

### 5.3 Filesystem Staging Failure Path

`FakeStager.stage_dataset_snapshot` raises `FileNotFoundError` or `HashMismatchError`.

| Step | Assertion |
|---|---|
| `validate_preflight` called (success) | `fake_strat.preflight_called_with` is set |
| `insert_strategy` NOT called | `fake_strat.insert_call_count == 0` |
| `insert_failure_log` called once | `fake_audit.call_count == 1` |
| `move_to_final_destination` NOT called | `fake_stager.move_count == 0` |
| Return `success=False` | `result.success is False` |

### 5.4 DB Insert Failure Path

`FakeStrategyAdapter.insert_strategy` raises `StrategyRepoAdapterError`.

| Step | Assertion |
|---|---|
| `validate_preflight` called (success) | `fake_strat.preflight_called_with` is set |
| `stage_dataset_snapshot` called (completed) | `fake_stager.stage_count == 1` |
| `insert_strategy` called (and failed) | `fake_strat.insert_call_count == 1` |
| `insert_failure_log` called once | `fake_audit.call_count == 1` |
| `move_to_final_destination` NOT called | `fake_stager.move_count == 0` |
| Return `success=False` | `result.success is False` |

### 5.5 Final Move Failure Path (After DB Commit)

`FakeStager.move_to_final_destination` raises `OSError`.

| Step | Assertion |
|---|---|
| `insert_strategy` called and succeeded | `fake_strat.insert_call_count == 1` |
| `move_to_final_destination` called (and failed) | `fake_stager.move_count == 1` |
| `insert_failure_log` called once | `fake_audit.call_count == 1` |
| Return `partial=True` | `result.partial is True` |

### 5.6 Failed Audit Log Write Itself

`FakeAuditAdapter.insert_failure_log` raises `AuditLogWriteError`.

| Step | Assertion |
|---|---|
| Coordinator does NOT crash | No exception escapes coordinator |
| Coordinator logs a warning | (manual inspection) |
| Original failure reason preserved in `ImportResult` | `result.error == original_failure` |
| `result.audit_failed is True` | Secondary failure flag set |

### 5.7 Malformed Legacy strategy_json Scenario

`FakeStrategyAdapter.validate_preflight` encounters unparseable JSON rows and does NOT find the target UID (proceeds with warning).

| Step | Assertion |
|---|---|
| `validate_preflight` returns with warning | `fake_strat.preflight_warning` is not None |
| `stager.stage_dataset_snapshot` called | `fake_stager.stage_count == 1` |
| `insert_strategy` called | `fake_strat.insert_call_count == 1` |
| `insert_failure_log` NOT called | `fake_audit.call_count == 0` |
| Return `success=True, warning=True` | `result.warning` contains "unparseable" |

### 5.8 No-UI / No-CLI / No-Engine Boundary

| Step | Assertion |
|---|---|
| Coordinator does not import `PySide6` | `"PySide6" not in sys.modules` |
| Coordinator does not call backtest engine | Spy assertion |
| Coordinator does not call strategy generator | Spy assertion |
| Coordinator does not call validation engine | Spy assertion |
| Coordinator does not call UI widgets | Spy assertion |

## 6. Expected No-Call Assertions (Safe Ordering)

| Test Scenario | Must NOT Call |
|---|---|
| Duplicate UID (preflight reject) | `stage_dataset_snapshot`, `insert_strategy`, `move_to_final_destination` |
| Staging failure | `insert_strategy`, `move_to_final_destination` |
| DB insert failure | `move_to_final_destination`, `ensure_import_audit_log_schema` (already called before) |
| Manifest failure | `ensure_import_audit_log_schema`, `validate_preflight`, `stage`, `insert_strategy`, `move`, `audit` |
| Verifier failure | `ensure_import_audit_log_schema`, `validate_preflight`, `stage`, `insert_strategy`, `move`, `audit` |

## 7. StrategyRepoAdapter Auto-Commit — Explicit First-Pass Limitation

| Limitation | Effect |
|---|---|
| `insert_strategy()` auto-commits | Staging success → insert failure: temp file exists, strategy NOT committed. `insert_failure_log` written. |
| No unified transaction in first pass | No rollback of staging on DB failure; stager cleans temp independently. |
| No rollback after auto-commit | If `insert_strategy()` succeeds but `move_to_final_destination` fails, strategy row is durable. Coordinator cannot undo it. |

## 8. Next Two-Task Batch

**Batch 060C-Design + 060D-Design — StrategyRepoAdapter Transaction Boundary Refactor Design + DatasetRepoAdapter Insert-Only Slice Design**

Both design-only. Coordinator implementation deferred until transaction boundary is resolved.

## 9. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
- **Last fix**: 2026-06-07 — corrected call ordering (staging before durable insert). Added malformed legacy JSON scenario. Added auto-commit limitation note. Added preflight-specific spy methods.
