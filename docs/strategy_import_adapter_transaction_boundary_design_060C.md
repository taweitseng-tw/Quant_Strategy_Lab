# StrategyRepoAdapter Transaction Boundary Refactor Design — Task 060C

> Design-only. No production code changed.

## 1. Problem

`StrategyRepoAdapter.insert_strategy()` calls `self._conn.commit()` internally. The future `ArchiveImportCoordinator` needs a unified transaction across strategy insert + dataset insert + validation insert + audit log write. The current auto-commit prevents this — if the dataset insert fails after the strategy insert, the strategy row is already durable with no rollback possible.

## 2. Existing Callers

| Caller | File | Usage |
|---|---|---|
| `StrategyRepoAdapter.insert_strategy()` | `repository/strategy_import_adapter.py` | Archive import path |
| `StrategyRepository.insert()` | `repository/strategy_repo.py` | Manual UI/non-archive strategy creation |
| `StrategyRepository.update()` | `repository/strategy_repo.py` | Manual strategy edit |
| `StrategyRepository.save()` | `repository/strategy_repo.py` | Insert-or-update |

**Constraint**: Any refactoring must not break `StrategyRepository.insert/update/save()` callers (UI path).

## 3. Option Comparison

### Option A: `commit: bool = True` Parameter

Add a `commit` parameter to `insert_strategy()`.

```python
def insert_strategy(self, dto: ImportStrategyDTO, *, commit: bool = True) -> int:
    ...
    try:
        cur = self._conn.execute(self._INSERT_SQL, ...)
        if commit:
            self._conn.commit()
        return cur.lastrowid
    except sqlite3.Error as exc:
        if commit:
            self._conn.rollback()
        raise StrategyRepoAdapterError(...) from exc
```

| Pro | Con |
|---|---|
| Backward-compatible (default `True`) | No single caller can tell if it's committing or not without reading the code |
| Single method, no duplication | Coordinator still cannot control the exact commit point if preflight work is interleaved |

### Option B: Split into `insert_strategy()` (auto-commit) + `insert_strategy_no_commit()` (no commit, coordinator-only) + `_insert_strategy_core()` (shared private)

```python
def _insert_strategy_core(self, dto: ImportStrategyDTO) -> int:
    """Shared private: validation + UID scan + INSERT execute (no commit/rollback)."""
    # (all current body except commit/rollback)

def insert_strategy(self, dto: ImportStrategyDTO) -> int:
    """Backward-compatible: insert + commit.  Use for UI and direct callers."""
    row_id = self._insert_strategy_core(dto)
    try:
        self._conn.commit()
        return row_id
    except sqlite3.Error as exc:
        self._conn.rollback()
        raise StrategyRepoAdapterError(...) from exc

def insert_strategy_no_commit(self, dto: ImportStrategyDTO) -> int:
    """Coordinator-facing: insert without commit.  Caller owns the transaction."""
    return self._insert_strategy_core(dto)
```

**No `commit=False` parameter on `insert_strategy()`.** The coordinator must call `insert_strategy_no_commit()` explicitly.

| Pro | Con |
|---|---|
| Clean API — two public methods with distinct intent | Slightly more total lines |
| No boolean-parameter ambiguity | — |
| Coordinator cannot accidentally auto-commit | — |
| Backward-compatible — existing callers use `insert_strategy()` unchanged | — |

### Option C: External Transaction Object

```python
def insert_strategy(self, dto: ImportStrategyDTO, *, transaction: sqlite3.Connection | None = None) -> int:
    conn = transaction or self._conn
    # use conn for all operations
    if not transaction:
        conn.commit()
```

| Pro | Con |
|---|---|
| Cleanest for coordinator (passes same connection + manages commit itself) | Changes signature; existing callers pass nothing (backward-compatible) |
| Transaction object could be a future wrapper with `commit/rollback` | Over-engineering for first pass |

## 4. Recommendation

**Option B — split into `insert_strategy_no_commit()` + backward-compatible wrapper.**

### Rationale

- The no-commit variant is an explicit public method, making the coordinator intent clear.
- The existing `insert_strategy(commit=True)` stays unchanged for UI callers.
- Implementation is small and testable.
- The coordinator sequence (060A) calls `insert_strategy_no_commit()` and manages its own `conn.commit()`.

### Migration Path

```
1. Extract `_insert_strategy_core()` (private) containing all validation + UID scan + INSERT execute.
2. Refactor `insert_strategy()` to call `_insert_strategy_core()` + explicit `commit()` + `rollback()` on error.
3. Add `insert_strategy_no_commit()` (public, no commit, no rollback) as coordinator-facing method.
4. Update `test_strategy_import_adapter.py` with:
   - Existing tests unchanged (continue testing via `insert_strategy()`).
   - New test: `insert_strategy_no_commit` does not commit (rollback succeeds after).
   - New test: coordinator calls `insert_strategy_no_commit` then explicit `conn.commit()`.
5. No changes to `StrategyRepository` (UI path).
```

### Rollback Expectations

| Scenario | rollback expected? |
|---|---|
| `insert_strategy()` (auto-commit) fails | ✅ Adapter calls `conn.rollback()` |
| `insert_strategy_no_commit()` fails | ❌ No rollback inside method. Caller must rollback. |
| Coordinator calls `no_commit` + dataset insert fails | Coord calls `conn.rollback()` — strategy + dataset both undone |

### Exception Semantics

- `insert_strategy_no_commit()` raises the same exceptions as `insert_strategy()`:
  - `StrategyRepoAdapterError` (validation, JSON, SQLite)
  - `DuplicateStrategyUIDError` (UID scan)
- No rollback is performed inside `no_commit`. The caller owns the transaction.

## 5. Backward Compatibility

| Existing call | After refactor | Behavior change? |
|---|---|---|
| `adapter.insert_strategy(dto)` | Calls `_insert_strategy_core()` + `commit()` | ✅ Identical |
| `adapter.insert_strategy_no_commit(dto)` | New method, calls `_insert_strategy_core()` only, no commit/rollback | ✅ New — coordinator only |

**No `commit=False` parameter exists on `insert_strategy()`.** The API is clean — two methods, no boolean ambiguity.

## 6. Focused Tests (Future Implementation)

| # | Test | Scope |
|---|---|---|
| 1 | `insert_strategy` with default `commit=True` inserts + commits | Existing, unchanged |
| 2 | `insert_strategy_no_commit` inserts without commit (rollback succeeds after) | New |
| 3 | Coordinator calls `insert_strategy_no_commit` then explicit `conn.commit()` | New (coordinator test per 060B contract) |
| 4 | `insert_strategy_no_commit` raises `DuplicateUIDError` without any commit | New |
| 5 | `insert_strategy` auto-commits on success, rolls back on error | Existing + refactored |

## 7. Next Two-Task Batch

**Batch 060E-Impl + 060F-Design — StrategyRepoAdapter Transaction Refactor Implementation + Dataset Snapshot Hash Schema Migration Design**

- 060E: Implement Option B (no-commit split) following this design.
- 060F: Design-only — dataset `snapshot_hash` schema migration (ALTER TABLE + SCHEMA_SQL update). Do NOT implement migration.
- No coordinator implementation.
- No DatasetRepoAdapter implementation (hash schema prerequisite not yet designed/completed).

## 8. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-07
