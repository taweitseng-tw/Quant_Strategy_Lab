# Codex Review - Task 056H-Impl Remove Best N Trades Stress Config Controls

## Verdict

Accepted.

## Score

9.1 / 10

## Review Summary

The implementation adds the planned Validate page controls for remove-best-N-trades stress and wires them into existing `PipelineConfig` fields without changing engine, pipeline service, or report behavior.

The controls are opt-in by default, the `n` and threshold spinboxes are disabled until enabled, and WFE behavior remains intact. The added tests verify defaults, enable/disable behavior, unchecked config propagation, and checked/custom config propagation.

## Verified

- `remove_best_n_checkbox` defaults unchecked.
- `remove_best_n_n_spin` defaults to `3`, min `1`, max `50`.
- `remove_best_n_threshold_spin` defaults to `0.30`, min `0.01`, max `1.00`, step `0.05`, decimals `2`.
- Spinboxes toggle enabled state with the checkbox.
- `_handle_run()` passes remove-best-N settings into `PipelineConfig`.
- Existing WFE tests still pass.
- No engine/pipeline/report generation changes.

## Verification Commands

```powershell
.venv\Scripts\python.exe -m pytest tests/test_wfe_ui_wiring.py -v
.venv\Scripts\python.exe -m pytest -q
git diff --check
```

Results:

- Focused UI wiring tests: 7 passed.
- Full suite: 1016 passed, 1 pre-existing warning.
- `git diff --check`: passed.

## Notes

- Minor non-blocking test gap: focused tests do not directly assert threshold spinbox `singleStep()` and `decimals()`, but Codex verified them manually and the implementation sets both correctly.
- Next step should be a narrow acceptance smoke that proves the remove-best-N feature chain remains coherent across pipeline, display, reports, and UI config.
