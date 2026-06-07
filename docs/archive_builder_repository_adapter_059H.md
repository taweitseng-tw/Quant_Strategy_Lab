# ArchiveBuilder Repository Adapter Contract — Task 059H

> Design-only. No production code changed.

## 1. Purpose

Define a clear adapter/protocol boundary between the future `ArchiveBuilder` and the repository layer, so that builder implementation and testing can proceed without coupling to the real SQLite repository.

## 2. Protocol: `ArchiveDataSource`

```python
from __future__ import annotations
from typing import Protocol, Any


class ArchiveDataSource(Protocol):
    """Interface for repository reads needed by ArchiveBuilder."""

    def get_strategy(self, strategy_uid: str) -> dict[str, Any] | None: ...
    def get_build_task(self, build_task_id: int) -> dict[str, Any] | None: ...
    def get_dataset(self, dataset_id: int) -> dict[str, Any] | None: ...
    def get_instrument(self, symbol: str) -> dict[str, Any] | None: ...
    def get_session(self, session_id: int) -> dict[str, Any] | None: ...
    def get_backtest_result(self, strategy_uid: str) -> dict[str, Any] | None: ...
    def get_validation_result(self, strategy_uid: str) -> dict[str, Any] | None: ...
    def get_backtest_assumptions(self, strategy_uid: str) -> dict[str, Any] | None: ...
```

## 3. Return Values

| Method | Expected Return |
|---|---|
| `get_strategy` | `{"strategy_uid", "name", "strategy_json", "build_task_id", "created_at", ...}` |
| `get_build_task` | `{"id", "random_seed", "config_json", ...}` |
| `get_dataset` | `{"id", "symbol", "timeframe", "start_datetime", "end_datetime", "row_count", "source_type", "normalized_path", ...}` |
| `get_instrument` | `{"symbol", "tick_size", "point_value", "commission_type", "commission_value", "slippage_type", "slippage_value", ...}` |
| `get_session` | `{"id", "name", "time_start", "time_end", "days_of_week", ...}` |
| `get_backtest_result` | `{"metrics", "trades", "assumptions", ...}` |
| `get_validation_result` | PipelineResult dict (already serialized) |
| `get_backtest_assumptions` | `{"execution_model", "commission_per_side", "slippage_per_side_ticks", ...}` |

## 4. Failure Behavior and Required vs. Optional Provenance

To guarantee archive reproducibility and integrity, we strictly distinguish between required archive materials (which trigger a **hard failure** if missing) and optional provenance fields (which can be omitted or set to `None` or generate a warning without aborting).

### 4.1 Required Provenance and Hard Failures

The following materials are critical for reproducibility. If any of these are missing (e.g., the adapter methods return `None` or files do not exist), the `ArchiveBuilder` **must abort immediately and raise a hard failure exception**:

| Missing Component | Source / Adapter Method | Exception to Raise (Hard Failure) |
|---|---|---|
| **Strategy & Definition** | `get_strategy(uid)` | `MissingStrategyError` |
| **Dataset Metadata** | `get_dataset(id)` | `MissingDatasetError` |
| **Dataset Snapshot (CSV)** | Provided file path on disk | `MissingDatasetSnapshotError` |
| **Validation Result** | `get_validation_result(uid)` | `MissingValidationResultError` |
| **Disclaimer Text** | Caller-provided parameter | `MissingDisclaimerError` |
| **Instrument Profile** | `get_instrument(symbol)` | `MissingInstrumentError` |
| **Build Task** | `get_build_task(id)` | `MissingBuildTaskError` |
| **Backtest Assumptions** | `get_backtest_assumptions(uid)` | `MissingBacktestAssumptionsError` |

### 4.2 Optional Provenance and Warnings

The following fields are optional. If they are missing or unavailable, the `ArchiveBuilder` will populate them with `None` or empty defaults, and may write a warning to the log, but **will not abort the archive process**:

| Component | Source / Adapter Method | Behavior when Missing |
|---|---|---|
| **Git Commit Hash** | Git repository context | Left as `None` or omitted from manifest |
| **Dataset Source Path** | `datasets.source_path` | Left as `None` or omitted |
| **Session Settings** | `get_session(id)` | Left as `None` (only required if session exits are enabled) |
| **Out-of-sample (OOS) Metrics** | `PipelineResult` | Omitted or set to `None` |
| **User/Author Notes** | Caller-provided parameter | Left empty |

## 5. Fake Test Fixture

```python
class FakeArchiveDataSource:
    """In-memory fake for ArchiveBuilder tests."""

    def __init__(self):
        self.strategies: dict[str, dict] = {}
        self.build_tasks: dict[int, dict] = {}
        self.datasets: dict[int, dict] = {}
        self.instruments: dict[str, dict] = {}
        self.sessions: dict[int, dict] = {}
        self.backtests: dict[str, dict] = {}
        self.validations: dict[str, dict] = {}
        self.assumptions: dict[str, dict] = {}

    def get_strategy(self, uid: str) -> dict | None:
        return self.strategies.get(uid)

    # ... same pattern for other methods
```

## 6. Recommended Next Two-Task Batch

**Task 059I-Impl + 059J-Design** — ArchiveBuilder first pass (collect + manifest) + dataset folder manifest integration design.

## 7. Metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-07
- **Dependencies**: 059G (manifest JSON serialization) — Done
