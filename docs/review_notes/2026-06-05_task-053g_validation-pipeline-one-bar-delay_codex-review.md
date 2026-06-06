# Codex Review — Task 053G — Validation Pipeline Integration for One-Bar Delay Stress

**Date:** 2026-06-05  
**Verdict:** ✅ ACCEPTED  
**Reviewer:** Codex (acting)

---

## Acceptance Criteria Check

| # | Criterion | Status |
|---|---|---|
| 1 | `run_validation_pipeline()` runs `stress_one_bar_delay` by default | ✅ |
| 2 | `PipelineConfig.run_one_bar_delay_stress = False` skips it | ✅ |
| 3 | Pipeline `stress_results` has 3 entries by default | ✅ |
| 4 | Existing pipeline tests still pass | ✅ |
| 5 | New focused test passes | ✅ |

## Findings

### `app/services/validation_pipeline_service.py` — minimal, correct wiring

- **Import**: `stress_one_bar_delay` added alongside existing imports [validation_pipeline_service.py:17](app/services/validation_pipeline_service.py:17).
- **Config field**: `run_one_bar_delay_stress: bool = True` on `PipelineConfig` — defaults to `True` so the test runs automatically for all pipeline users [validation_pipeline_service.py:45](app/services/validation_pipeline_service.py:45). Uses `asdict()` so it auto-appears in `config_snapshot`.
- **Integration**: Called in stress test section with `if cfg.run_one_bar_delay_stress:` guard, appended via `_stress_to_dict()` — same pattern as commission/slippage [validation_pipeline_service.py:152-155](app/services/validation_pipeline_service.py:152-155). Parameter wiring is correct: `strategy, split.train, baseline, instrument=instrument`.
- **No scope creep**: No UI, report, runner, or stress_test.py changes.

### `tests/test_validation_pipeline_service.py` — updated + new test

- **`test_stress_results_contain_both_tests` → `test_stress_results_contain_all_three_tests`**: Renamed, updated assertions to check for `"one_bar_delay"` in test names and `len(test_names) == 3`.
- **`test_one_bar_delay_can_be_disabled`**: Creates `PipelineConfig(run_one_bar_delay_stress=False)`, asserts `len(test_names) == 2` and no `"one_bar_delay"` in results. Clean.

## Verification

```
.venv\Scripts\python.exe -m pytest tests/ -k "pipeline" -v
→ 18 passed

.venv\Scripts\python.exe -m pytest tests/test_stress_test.py tests/test_execution_delay.py -v
→ 19 passed

.venv\Scripts\python.exe -m pytest -q
→ 955 passed, 1 warning (pre-existing)
```

## Conclusion

The wiring is the minimum viable change — one import, one config field, one guarded call, one existing test updated, one new test. No regressions. The one-bar execution delay feature is now fully integrated: engine → stress function → pipeline → tests. **Accepted.**

---

## Next Task Recommendation

The 053-series (Backtest Execution Enhancements) is now complete: session-end exit (053E), one-bar delay stress (053F), pipeline integration (053G). The natural capstone is an acceptance smoke test verifying end-to-end behavior: run the full pipeline, confirm Validate page displays all 3 stress results, and verify reports include the one-bar delay result.
