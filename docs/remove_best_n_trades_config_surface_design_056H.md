# Remove Best N Trades Stress Config Surface Design — Task 056H

> Design-only. No production code changed.

## 1. Current Configuration Flow

### 1.1 Where `PipelineConfig` Is Constructed

`app/ui/main_window.py` line ~1094:

```python
result = run_validation_pipeline(
    df, strategy,
    config=PipelineConfig(mc_iterations=15, calc_wfe=calc_wfe),
    instrument=active_profile,
    ...
)
```

Only two settings are user-facing: `mc_iterations` (hard-coded) and `calc_wfe` (checkbox).

### 1.2 Existing User-Facing Control

```python
# app/ui/main_window.py line ~291
self.wfe_checkbox = QCheckBox("Calculate WFE")
self.wfe_checkbox.setToolTip("Runs an extra in-sample backtest per walk-forward window...")
# Used at line 1088:
if hasattr(self, "wfe_checkbox"):
    calc_wfe = self.wfe_checkbox.isChecked()
```

The WFE checkbox lives in the Validate page header layout.

### 1.3 What's Available But Not Exposed

| PipelineConfig field | Default | UI-visible? |
|---|---|---|
| `run_one_bar_delay_stress` | `True` | No |
| `run_parameter_perturbation` | `True` | No |
| `run_remove_best_n_trades_stress` | `False` | **No — target for this design** |
| `remove_best_n_trades_n` | `3` | No |
| `remove_best_n_trades_degradation_threshold` | `0.30` | No |

## 2. Design Decision: Where to Expose

### Option A: Validate Page Header (Alongside WFE Checkbox)

Pros: Minimal code change (add checkbox next to WFE). Follows existing pattern.

Cons: Three related settings (enable, n, threshold) are too many for a header. Header would need a small expandable group.

### Option B: Separate "Advanced Stress Settings" Panel on Validate Page

Pros: Room for future stress test configs. Clean separation.

Cons: Requires new panel/widget, larger change.

### Option C: Keep Off by Default, No UI — Config via PipelineConfig in Code Only

Pros: No UI work. Stays as developer/power-user feature.

Cons: No discoverability.

### Recommendation: Option A — Minimal Header Group

Follow the WFE checkbox pattern. Add a collapsible group in the Validate page header with:

```
☐ Remove Best N Trades Stress
  N: [3]   Max PnL Loss: [0.30]
```

- Checkbox enables/disables the stress test.
- Two numeric inputs appear only when checked.
- Collapsed by default (checkbox unchecked).

This keeps the change small (same file, same section, same pattern) while providing user-facing configuration.

## 3. Recommended Control Shape

```
┌─────────────────────────────────────────────────┐
│ ☐ Remove Best N Trades Stress                  │
│   N: [3]        Max PnL Loss: [0.30]           │
│   Tooltip: "Removes the top N best trades...    │
│            Requires >N baseline trades.         │
│            Off by default."                     │
└─────────────────────────────────────────────────┘
```

| Control | Type | Default | Constraints |
|---|---|---|---|
| Enable checkbox | `QCheckBox` | Unchecked (off) | N/A |
| N | `QSpinBox` | 3 | min=1, max=50 |
| Max PnL Loss | `QDoubleSpinBox` | 0.30 | min=0.01, max=1.00, step=0.05 |

## 4. Engine/UI Coupling Avoided

The UI only reads/writes `PipelineConfig` fields. No quant logic in the widget:

```python
# Construction in run handler:
cfg = PipelineConfig(
    mc_iterations=15,
    calc_wfe=calc_wfe,
    run_remove_best_n_trades_stress=self.remove_best_n_checkbox.isChecked(),
    remove_best_n_trades_n=self.remove_best_n_n_spin.value(),
    remove_best_n_trades_degradation_threshold=self.remove_best_n_threshold_spin.value(),
)
```

The UI collects user intent via standard Qt controls. `PipelineConfig` carries it to the pipeline service. The service calls the stress engine. Engine/UI boundary preserved.

## 5. Report/Summary Visibility

The detail sub-lines (Task 056G-Impl) already appear in widget/reports when the stress test runs. No additional report changes needed — the display surfaces already handle `assumptions`, `warnings`, and `threshold`.

Config snapshot in reports automatically includes the new fields since `PipelineConfig.to_dict()` uses `asdict()`.

## 6. Implementation Surface (Task 056H-Impl)

| File | Change |
|---|---|
| `app/ui/main_window.py` | Add checkbox + 2 spinboxes in Validate header; pass to `PipelineConfig()` |
| `tests/test_active_dataset.py` or closest run-flow test | Verify controls exist and pipeline config receives values |
| `docs/changelog.md` + `docs/task_board.md` | Standard update |

**Minimal test coverage**:
- Verify checkbox unchecked by default.
- Verify spinboxes disabled when checkbox is unchecked.
- Verify `PipelineConfig` receives correct values when enabled.

## 7. Design Decisions

1. **Off by default** — the test is only meaningful when trade count is sufficient.
2. **Minimal header group** — same pattern as WFE checkbox, low implementation cost.
3. **Engine/UI separation preserved** — UI collects user intent, PipelineConfig carries it, engine/service acts on it.
4. **Existing display surfaces unchanged** — widget and report detail sub-lines already work.
5. **No new widget class** — controls live directly in main_window.py, consistent with WFE checkbox.

## 8. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: Task 056G-Impl series (display surfaces) — Done
- **Blocked by**: Nothing
