# Validation Pipeline Responsiveness Design - Tasks 535-540

Date: 2026-06-12

## Purpose

Design the smallest safe implementation slice that moves the validation pipeline off the Qt main thread while preserving existing validation behavior, export gating, log output, and report eligibility rules.

This round is design-only. No production code changed.

## Current State

`MainWindow._handle_run()` currently prepares the dataset, default strategy, instrument profile, and `PipelineConfig`, then calls `run_validation_pipeline(...)` synchronously on the Qt main thread.

Tasks 523-528 added a wait cursor with `try/finally`, which improves feedback but does not solve the freeze. Long runs can still block tab changes, scrolling, repainting, and window interaction until `run_validation_pipeline(...)` returns.

## Main Constraint

`run_validation_pipeline(...)` is currently a monolithic synchronous function. It does not expose progress callbacks between split, backtest, stress, Monte Carlo, walk-forward, and elimination stages.

Therefore the first worker slice must use coarse progress only:

- starting,
- running validation pipeline,
- finalizing,
- success or failure.

Fine-grained stage progress requires a later service-level callback refactor and is out of scope for Tasks 541-546.

## Proposed Implementation

### ValidationWorker

Add `ValidationWorker` beside the existing `ImportWorker`, `GAWorker`, and `GPWorker` in `app/workers/__init__.py`.

Signals:

```python
progress_updated = Signal(str)
success = Signal(object)
failure = Signal(str)
```

Inputs:

- normalized OHLCV DataFrame,
- strategy,
- `PipelineConfig`,
- instrument profile,
- data source label,
- backtest keyword arguments.

Worker rules:

- Copy the DataFrame in `__init__` when possible.
- Do not mutate UI widgets from `run()`.
- Call `run_validation_pipeline(...)` from `run()`.
- Emit `success(result)` or `failure(message)`.
- Emit only coarse progress unless the service later gains callbacks.

### MainWindow Wiring

Refactor `_handle_run()` into smaller pieces without changing validation behavior:

- Keep dataset and config preparation on the UI thread.
- Start `ValidationWorker` after `_set_validation_running()`.
- Store it on `self._validation_worker` to prevent garbage collection.
- Connect:
  - `progress_updated` to `_on_validation_progress`,
  - `success` to `_on_validation_success`,
  - `failure` to `_on_validation_failure`,
  - `finished` to `_on_validation_finished`.

Important: `finished` must only clean worker references and restore generic UI state that is independent of success or failure. It must not override export eligibility already set by success or failure handlers.

### Preserve Current Success Behavior

`_on_validation_success(result)` should preserve the current synchronous behavior:

- set `self.latest_validation_result`,
- call `self.validation_summary.update_from_result(...)`,
- add the same log panel messages,
- update inspector text,
- set validation status to completed,
- call `_set_validation_idle(export_ok=True)`.

### Preserve Current Failure Behavior

`_on_validation_failure(message)` should preserve current failure behavior:

- log error,
- update inspector text,
- show validation failed status,
- call `_set_validation_idle(export_ok=False, reason=...)`,
- do not enable report export.

### Cursor Handling

Once the worker is asynchronous, the wait cursor should be removed or limited to the short startup section. A long-running override cursor is not the right feedback mechanism for an async worker. The persistent feedback should be the validation status label and disabled Run action.

## Out of Scope for Tasks 541-546

- Cancellation button.
- Fine-grained internal pipeline progress.
- Refactoring `run_validation_pipeline(...)` into callbacks or staged services.
- Broad validation engine changes.
- Full UI performance overhaul.

## Tests for Tasks 541-546

Focused tests should prove:

1. `ValidationWorker` emits `success` when `run_validation_pipeline(...)` succeeds.
2. `ValidationWorker` emits `failure` when the pipeline raises.
3. Worker copies the input DataFrame, so later UI-side mutation does not affect the worker payload.
4. MainWindow starts a worker instead of calling `run_validation_pipeline(...)` directly.
5. MainWindow success handler preserves export enablement and latest result storage.
6. MainWindow failure handler preserves export disabled state and error logging.

Use monkeypatching for `run_validation_pipeline(...)` where possible to keep tests fast and deterministic.

## Acceptance Criteria

- Validation run is executed through `ValidationWorker`.
- UI thread no longer directly runs `run_validation_pipeline(...)`.
- Existing validation result handling and export gating stay behaviorally equivalent.
- Tests cover worker success/failure and MainWindow success/failure wiring.
- No changes to engine logic, trading assumptions, or validation math.
