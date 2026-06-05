# 2026-06-05 - Codex Review - Task 053E-Fix Session-End Validation and Pending Entry Hardening

## Verdict

Needs Fix.

## Findings

1. P2 - Strict serializer accepts semantically invalid session times.
   - File: `core/serialization/strategy_serializer.py`
   - Line: 57
   - Issue: strict mode validates `session_end_time` with a regex only, so values such as `99:99` pass JSON/import validation and create `RiskManagement(close_end_of_session=True, session_end_time="99:99")`.
   - Impact: `run_backtest` later rejects the same value with `ValueError`, so strict serializer/import validation and engine validation disagree. This weakens the "preview rejects invalid risk management" behavior and pushes a preventable config error into execution time.
   - Expected: strict serializer should validate parseable clock time using the same accepted formats as the runner: `HH:MM` or `HH:MM:SS`.

## Positive Checks

- Focused test suite passed: `.venv\Scripts\python.exe -m pytest tests/test_backtest_engine.py tests/test_strategy_serializer.py tests/test_strategy_repo.py tests/test_strategy_json_import_service.py -v`
- Manual check confirmed `run_backtest` now raises `ValueError` for clearly malformed `session_end_time="invalid"`.
- Manual check confirmed prior-bar pending entries are canceled at the session boundary instead of opening and immediately closing.
- Assumptions no longer report session-end behavior when `close_end_of_session=True` but `session_end_time=None`.

## Manual Reproduction

```python
from core.serialization.strategy_serializer import risk_management_from_dict

rm = risk_management_from_dict(
    {"close_end_of_session": True, "session_end_time": "99:99"},
    strict=True,
)

assert rm.session_end_time == "99:99"  # currently accepted, but runner rejects it
```

## Required Fix

- Replace regex-only strict validation with actual time parsing or an equivalent bounded validator.
- Add focused serializer tests that reject invalid clock ranges such as:
  - `24:00`
  - `99:99`
  - `12:60`
  - `09:30:60`
- Keep existing valid cases accepted:
  - `09:30`
  - `09:30:00`
- Do not change the event-loop session-end behavior unless needed for the validator.
