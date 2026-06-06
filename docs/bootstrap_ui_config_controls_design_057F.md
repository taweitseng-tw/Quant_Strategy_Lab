# Bootstrap UI Config Controls Design — Task 057F

> Design-only. No production code changed.

## 1. Current State

Bootstrap is wired into the pipeline behind `PipelineConfig.run_bootstrap_monte_carlo` (default `False`). Display surfaces exist. No UI controls.

## 2. Proposed Controls

Following the remove-best-N controls pattern (Task 056H-Impl), add a group in the Validate page header after the existing remove-best-N group:

```
☐ Bootstrap Monte Carlo
  Iterations: [200]   Confidence: [0.95]
```

| Control | Type | Default | Constraints | Tooltip |
|---|---|---|---|---|
| Enable checkbox | `QCheckBox` | Unchecked (off) | N/A | "Resamples trades with replacement to compute 95% confidence intervals. Heavier (200 iterations). Off by default." |
| Iterations | `QSpinBox` | 200 | min=50, max=2000, step=50 | "Number of bootstrap iterations. More = smoother CIs but slower." |
| Confidence level | `QDoubleSpinBox` | 0.95 | min=0.80, max=0.99, step=0.01, decimals=2 | "Confidence level for CI computation (0.80-0.99)." |

## 3. PipelineConfig Mapping

```python
# In _handle_run():
config = PipelineConfig(
    ...
    run_bootstrap_monte_carlo=self.bootstrap_checkbox.isChecked(),
    bootstrap_iterations=self.bootstrap_iter_spin.value(),
    bootstrap_confidence_level=self.bootstrap_conf_spin.value(),
)
```

## 4. Implementation Surface

| File | Change |
|---|---|
| `app/ui/main_window.py` | Add controls group in Validate page |
| `tests/test_wfe_ui_wiring.py` | 3-4 UI wiring tests |
| `docs/changelog.md` + `docs/task_board.md` | Standard update |

## 5. Non-Goals

- Not implemented in this design-only task.
- No pipeline/engine/report changes.
- No `worst_case_equity`.

## 6. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: 057D-Impl (pipeline wiring) — Done
