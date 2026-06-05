# Task 053D - Backtest Execution Enhancements Triage - Codex Review

## Verdict

Needs fix.

## Findings

### P1 - Session-end exit design needs a no-future-leak boundary

The recommendation to prioritize Session-End Exit Behavior is directionally correct. However, the triage currently says no future leak is possible because the feature uses the current bar timestamp. That is only true if the implementation uses an explicit configured session boundary, such as `session_end_time`, a session template, or a predeclared schedule.

It must not detect "the day's final trading session bar" by grouping the full dataset and looking ahead to the last row for each date. That would leak future knowledge into the current bar.

Required fix:

- State explicitly that session-end exit detection must be based on configured session rules, not full-dataset last-bar discovery.
- If the dataset has missing bars, document a conservative behavior such as exiting when `bar_datetime.time() >= session_end_time` or using a configured fallback.
- Add tests that prove session-end behavior does not depend on future rows being present.

### P2 - Implementation target should preserve backward compatibility

Adding fields to `RiskManagement` is plausible, but the design should note compatibility with existing strategy JSON, repository loading, and serializer behavior. Defaults must preserve current behavior: no session-end exit unless explicitly enabled.

Required fix:

- Add expected default fields, such as `close_end_of_session: bool = False` and `session_end_time: str | None = None`.
- State that old strategies without these keys must load as disabled session-end exit.
- Identify serializer/import/repository tests required if fields are added.

### P3 - Candidate E lists inaccurate file paths

The triage references `reports/report_service.py` and `ui/pages/results_page.py`, but the current codebase uses paths such as `app/services/report_service.py` and UI/widgets under `app/`. The triage should use current repository paths to stay actionable.

## Accepted Parts

- The task remained design-only.
- The recommendation to prioritize session-end exit is reasonable for intraday strategy realism.
- The document compares execution delay, same-bar ambiguity, slippage/commission interaction, and assumption reporting.

## Required Follow-Up

Task 053D-Fix - Session-End Exit Triage Hardening.

This should update the triage document only, preserving the recommendation but hardening the no-future-leak boundary and compatibility/test requirements.

## Verification

- Ran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`.
- Reviewed `docs/backtest_execution_enhancement_triage_053D.md`.
- Inspected `backtest_engine/runner.py`, `core/models/strategy.py`, and `tests/test_backtest_engine.py`.
