# Validation Cancellation and Progress Feedback Design - Tasks 553-558

Date: 2026-06-12

## Purpose

Design the smallest safe follow-up after `ValidationWorker`: prevent concurrent validation runs, expose a cancel request path, and keep progress feedback honest without changing validation math.

This round is design-only. No production code changed.

## Current State

`ValidationWorker` runs `run_validation_pipeline(...)` outside the Qt main thread. Focused tests prove worker success/failure behavior and MainWindow export gating.

Remaining gaps:

- No user-facing cancel request.
- Progress is coarse because `run_validation_pipeline(...)` has no callback surface.
- A second validation run should be guarded while a worker is already running.
- The worker copies the DataFrame, which is safe but can increase memory use on large datasets.

## Important Constraint

`run_validation_pipeline(...)` is monolithic. A stop flag cannot interrupt it mid-call. In the first cancellation slice, cancel behavior can only be cooperative at boundaries:

- before the pipeline starts,
- after the pipeline returns,
- before success is emitted.

True mid-stage cancellation requires future service-level callback/checkpoint support.

## Proposed Implementation

### Stop Action Wiring

The toolbar already creates a `Stop` action, but it is not stored or connected. The implementation should:

- store it as `self.stop_action`,
- set object name `actionStop`,
- keep it disabled when idle,
- connect it to `_handle_stop_validation`.

### Worker Stop Flag

Add a stop request flag to `ValidationWorker`:

```python
def stop(self) -> None:
    self._stop_requested = True
```

In `run()`, check the flag before calling `run_validation_pipeline(...)` and again after the call returns. If cancelled, emit `failure("Validation cancelled by user.")` and do not emit success.

This does not stop the current monolithic pipeline call while it is running.

### MainWindow Stop Handler

`_handle_stop_validation()` should:

- check whether `self._validation_worker` exists and is running,
- call `self._validation_worker.stop()`,
- disable the Stop action,
- keep Run disabled,
- keep Export disabled,
- update the status label to `Cancelling...`,
- log a warning that cancellation will occur after the current stage returns.

### Stale Run Guard

At the top of `_handle_run()`, guard against a second run:

```python
if self._validation_worker and self._validation_worker.isRunning():
    self.log_panel.add_message("WARN", "Validation already running. Stop it first.")
    return
```

### UI State

| State | Run | Stop | Export | Status |
|---|---|---|---|---|
| Idle | enabled | disabled | depends on latest validation | Ready or hidden |
| Running | disabled | enabled | disabled | Validating... |
| Cancelling | disabled | disabled | disabled | Cancelling... |
| Success | enabled | disabled | enabled | Validation completed |
| Failure/cancelled | enabled | disabled | disabled | Failed or cancelled |

## Progress Decision

Keep coarse progress for Tasks 559-564. Do not add service-level progress callbacks yet.

A future task can add an optional `progress_callback` to `run_validation_pipeline(...)` if detailed stage progress becomes necessary.

## Tests for Tasks 559-564

Focused tests should prove:

1. `ValidationWorker.stop()` sets the stop flag.
2. Stop before `run()` emits a cancellation failure and no success.
3. Stop after a mocked pipeline result but before success emits cancellation failure.
4. `_handle_run()` ignores a second run while a worker is already running.
5. `_handle_stop_validation()` disables Stop, keeps Run/Export disabled, and logs the cancellation request.
6. Cancelled validation does not replace `latest_validation_result`.

Use monkeypatching to avoid slow real pipeline runs.

## Acceptance Criteria

- Stop action is wired and tested.
- Concurrent validation runs are blocked and logged.
- Cancel request preserves safe UI state and export remains disabled.
- Cancellation behavior is described honestly as cooperative boundary cancellation.
- No validation math or service function signature changes.
