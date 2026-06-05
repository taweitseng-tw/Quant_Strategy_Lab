# Task 053E - Session-End Exit Engine Implementation - Codex Review

## Verdict

Needs fix.

## Findings

### P1 - Invalid `session_end_time` silently disables execution while assumptions report it as enabled

In `backtest_engine/runner.py`, invalid `session_end_time` parsing sets `has_session_end = False`, but the assumptions block still records:

- `close_end_of_session = True`
- `session_end_time = <invalid value>`

Observed manual check:

```text
risk_management=RiskManagement(close_end_of_session=True, session_end_time="bad")
```

Result:

- No session-end exit occurs.
- The position exits only via `end_of_data`.
- `BacktestResult.assumptions` still claims session-end exit is enabled.

This creates a dangerous mismatch between execution behavior and reported assumptions.

Required fix:

- Strictly validate `session_end_time` when `close_end_of_session` is enabled.
- Prefer failing fast with a clear `ValueError` from `run_backtest`, or reject invalid time format during strict serializer/import validation.
- Add tests for invalid time strings.
- Ensure assumptions only report session-end behavior when the engine actually applies it.

### P1 - Pending entry can execute exactly at session end and immediately exit

Current behavior allows a signal from the prior bar to queue an entry, then execute that pending entry at `16:00`, immediately followed by a `session_end` exit on the same bar.

Observed manual check:

```text
15:55 signal -> pending entry
16:00 open -> enter
16:00 close -> session_end exit
```

This is not a future leak, but it violates the intended day-trading boundary. If `close_end_of_session` is enabled, pending entries should not execute at or after the configured session end.

Required fix:

- Before executing a pending `enter`, check whether the current bar is at or after session end.
- Cancel the pending entry instead of opening a position.
- Add a warning or assumption note for canceled session-end entries.
- Add a test proving a prior-bar signal does not open at the session boundary.

## Accepted Parts

- No full-dataset grouping/scanning for final bars was introduced.
- Session-end exit uses configured time and current bar timestamp.
- Stop-loss/take-profit priority appears to remain above session-end exit.
- Focused tests pass for the implemented happy path.
- DeepSeek did not create a Git commit.

## Required Follow-Up

Task 053E-Fix - Session-End Exit Validation and Pending Entry Hardening.

This is a narrow engine fix. Do not broaden into session templates, dynamic slippage, one-bar delay, or UI work.

## Verification

- Ran `.venv\Scripts\python.exe -m pytest tests/test_backtest_engine.py tests/test_strategy_serializer.py tests/test_strategy_repo.py tests/test_strategy_json_import_service.py -v`; result: 89 passed.
- Ran manual edge-case checks for invalid `session_end_time` and pending entry at the session boundary.
- Reviewed `backtest_engine/runner.py`, `core/serialization/strategy_serializer.py`, and session-end tests.
