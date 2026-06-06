# Batch 057E-Fix + 057F-Impl — Bootstrap Display Hardening and UI Controls

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 057E-Fix — Display Hardening

| Fix | Detail |
|---|---|
| Empty CI guard | `if ci:` check before rendering in widget/markdown/HTML |
| PF decimal format | `.2f` for profit_factor CI values in all 3 surfaces |
| Tests | 5 new tests (empty CI widget, empty CI markdown, empty CI HTML, PF decimals widget) |

### 057F-Impl — UI Controls

Validate page controls:

```
☐ Bootstrap Monte Carlo   Iterations: [200]   Confidence: [0.95]
```

| Control | Type | Default |
|---|---|---|
| Checkbox | `QCheckBox` | Unchecked (default off) |
| Iterations | `QSpinBox` | 200 (50-2000, step 50) |
| Confidence | `QDoubleSpinBox` | 0.95 (0.80-0.99, decimals 2) |

Wired into `PipelineConfig` via `_handle_run()`. 4 UI tests.

## Files Changed

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | Empty-CI guard + PF format |
| `reports/generator.py` | Empty-CI guard + PF format in both formatters |
| `app/ui/main_window.py` | Bootstrap controls + PipelineConfig wiring |
| `tests/test_validation_summary.py` | 3 tests |
| `tests/test_report_export.py` | 2 tests |
| `tests/test_wfe_ui_wiring.py` | 4 tests |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | Batch -> Done |

## Verification

```
widget + report + UI: 68 passed
Full suite: 1074 passed, 1 warning
git diff --check -> passes
```
