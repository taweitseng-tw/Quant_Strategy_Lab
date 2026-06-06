# Task 056H-Impl — Remove Best N Trades Stress Config Controls

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### UI Controls (`app/ui/main_window.py`)

Added three controls in the Validate page header, following the WFE checkbox pattern:

```
☐ Remove Best N Trades Stress   N: [3]   Max PnL Loss: [0.30]
```

| Control | Type | Default | Constraints |
|---|---|---|---|
| Enable checkbox | `QCheckBox` | Unchecked | N/A |
| N spinbox | `QSpinBox` | 3 | min=1, max=50 |
| Threshold spinbox | `QDoubleSpinBox` | 0.30 | min=0.01, max=1.00, step=0.05 |

Spinboxes disabled when unchecked, enabled when checked (via `toggled` signal).

### PipelineConfig Wiring

```python
config=PipelineConfig(
    mc_iterations=15, calc_wfe=calc_wfe,
    run_remove_best_n_trades_stress=run_remove_best_n,
    remove_best_n_trades_n=remove_best_n_n,
    remove_best_n_trades_degradation_threshold=remove_best_n_threshold,
)
```

All values guarded by `hasattr` for pages where controls don't exist.

### Tests (`tests/test_wfe_ui_wiring.py`)

| Test | What it verifies |
|---|---|
| `test_remove_best_n_controls_exist_and_defaults` | Controls exist, correct defaults, spinboxes disabled |
| `test_remove_best_n_spins_enabled_when_checked` | Toggle enables/disables spinboxes |
| `test_remove_best_n_unchecked_passes_false` | Unchecked -> False + defaults in PipelineConfig |
| `test_remove_best_n_checked_passes_custom_values` | Checked with custom n=5, threshold=0.25 |

Existing WFE tests (3) unchanged and still pass.

## Files Changed

| File | Change |
|---|---|
| `app/ui/main_window.py` | Added 3 Validate page controls + PipelineConfig wiring |
| `tests/test_wfe_ui_wiring.py` | 4 new tests |
| `docs/changelog.md` | Task 056H-Impl entry |
| `docs/task_board.md` | 056H-Impl -> Done |

## Verification

```
test_wfe_ui_wiring.py: 7 passed (3 WFE + 4 new)
Full suite: 1016 passed, 1 warning
git diff --check -> passes
```

Acceptance criteria:
1. ✅ Controls exist on Validate page.
2. ✅ Checkbox unchecked by default.
3. ✅ N spinbox defaults 3, min 1, max 50.
4. ✅ Threshold spinbox defaults 0.30, min 0.01, max 1.00.
5. ✅ Spinboxes disabled when unchecked, enabled when checked.
6. ✅ Unchecked passes False + defaults to PipelineConfig.
7. ✅ Checked passes custom values to PipelineConfig.
8. ✅ WFE checkbox unchanged.
9. ✅ Focused tests pass.
10. ✅ Full suite passes.
11. ✅ `git diff --check` passes.

## Known Issues

- None.

## Risks

- None. No engine/pipeline/report changes. Controls only active when Validate page is visited.
