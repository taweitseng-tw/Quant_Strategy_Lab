# Task 056H — Remove Best N Trades Stress Config Surface Design Only

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### Current Config Flow Traced

`app/ui/main_window.py` constructs `PipelineConfig(mc_iterations=15, calc_wfe=calc_wfe)` with only the WFE checkbox exposed. Three remove-best-N fields exist in `PipelineConfig` but have no UI controls.

### Design (`docs/remove_best_n_trades_config_surface_design_056H.md`)

Recommended adding a minimal header group on the Validate page, following the existing WFE checkbox pattern:

```
☐ Remove Best N Trades Stress
  N: [3]        Max PnL Loss: [0.30]
```

| Control | Default | Constraints |
|---|---|---|
| `QCheckBox` | Unchecked (off) | N/A |
| `QSpinBox` (n) | 3 | min=1, max=50 |
| `QDoubleSpinBox` (threshold) | 0.30 | min=0.01, max=1.00 |

Engine/UI separation: UI reads controls → PipelineConfig → pipeline service → engine. No quant logic in widget.

### Implementation Surface (Task 056H-Impl)

Single file: `app/ui/main_window.py` — add 3 controls in Validate header, pass to `PipelineConfig()` call. Minimal tests verify defaults and enabled state propagation.

## Files Changed

| File | Change |
|---|---|
| `docs/remove_best_n_trades_config_surface_design_056H.md` | **Created** |
| `docs/changelog.md` | Task 056H entry |
| `docs/task_board.md` | 056H -> Done |

## Verification

- **No production code changed** (design-only).
- **`git diff --check`**: passes.

## Known Issues

- None.

## Risks

- None (design-only).

## Suggested Next Task

**Task 056H-Impl** — Add remove-best-N stress config controls to Validate page header.
