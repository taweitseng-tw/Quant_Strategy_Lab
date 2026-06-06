# Codex Review - Task 056F Remove Best N Trades Pipeline Integration

Date: 2026-06-06
Reviewer: Codex
Verdict: Needs Fix
Score: 8.2 / 10

## Summary

Task 056F correctly wires `stress_remove_best_n_trades()` into the validation pipeline behind an opt-in flag, and the default flag is correctly `False`. The pipeline does not appear to change UI, report, or elimination behavior.

However, the task acceptance criteria require the serialized stress result to include assumptions such as `n`, `removed_count`, and `pnl_loss_ratio`. The current `_stress_to_dict()` helper does not serialize `assumptions`, so the pipeline output cannot expose those fields.

## Findings

### P1 - Pipeline stress serialization omits assumptions

`app/services/validation_pipeline_service.py` currently serializes stress results as:

```python
def _stress_to_dict(sr) -> dict:
    return {
        "test_name": sr.test_name,
        "passed": sr.passed,
        "degradation": sr.degradation,
        "stressed_metrics": sr.stressed_metrics,
    }
```

The new remove-best-N stress result puts `pnl_loss_ratio`, `n`, and removed/surviving counts in `sr.assumptions`. Since `_stress_to_dict()` drops `assumptions`, the pipeline integration does not meet the task requirement.

Required correction:

- Extend `_stress_to_dict()` to include `assumptions`, and preferably `warnings` and `threshold` if consistent with existing stress result reporting.
- Add/update tests to assert the opt-in `remove_best_n_trades` pipeline result includes:
  - `assumptions["n"]`
  - `assumptions["removed_count"]`
  - `assumptions["pnl_loss_ratio"]`
- Confirm existing stress-result consumers tolerate the additional keys.

## Verification

- `.venv\Scripts\python.exe -m pytest tests/test_validation_pipeline_service.py tests/test_stress_test.py -v`
  - Result: 47 passed.
- `git diff --check`
  - Result: passed, with LF/CRLF working-copy warnings only.
- Manual code review confirmed `_stress_to_dict()` omits `assumptions`.

## Decision

Do not accept yet. Run Task 056F-Fix to expose stress assumptions through pipeline serialization and test it.

## Next Task

Task 056F-Fix - Remove Best N Trades Pipeline Assumptions Serialization.
