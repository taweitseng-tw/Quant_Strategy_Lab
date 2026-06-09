# WF Efficiency Display Polish and IS-Baseline Precheck UI Toggle Contract - Task 063C

> Design-only. No production code changed.

## 1. WF Efficiency Display Polish

### Current State

WF Efficiency is computed and serialized in `walk_forward_summary` as:

```python
"average_wfe": float | None
"median_wfe": float | None
"defined_wfe_count": int
"undefined_wfe_count": int
```

Reports already render this as a single line. `ValidationSummary` does not currently display it in the widget.

### Widget Addition

Add a WF Efficiency line to the existing Walk-Forward card when the WFE keys are present:

```text
Walk-Forward: Windows: 5  |  Passed: 3  |  Pass Rate: 60%
WFE: Avg=1.25, Median=0.85, Defined=3, Undefined=2
```

Display rules:

- Show the line when `walk_forward_summary` includes `average_wfe` or `median_wfe`.
- Render `None` values as `N/A`.
- Do not show the line when WFE keys are absent, preserving current default UI behavior.

### Report Display

Current report display is adequate and should not be changed in this batch:

```markdown
- **WF Efficiency**: Avg=1.25, Median=0.85, Defined Windows=3, Undefined Windows=2
```

### Focused Widget Tests

| # | Test | File |
|---|---|---|
| 1 | Widget shows WFE line when WFE keys are present with numeric values | `test_validation_summary.py` |
| 2 | Widget omits WFE line when WFE keys are absent | `test_validation_summary.py` |
| 3 | Widget renders `None` avg/median as `N/A` and still shows defined/undefined counts | `test_validation_summary.py` |

## 2. IS-Baseline Precheck UI Toggle Contract

### Current State

The IS baseline quality precheck is controlled by `PipelineConfig`:

```python
run_is_baseline_quality_precheck: bool = False
fail_is_baseline_on_nonpositive_pnl: bool = False
```

There is no UI toggle. The user must edit code to enable it.

### Proposed Controls

Add a group to the Validate page after the price-noise controls:

```text
[ ] IS Baseline Quality Precheck
    [ ] Fail on non-positive PnL
```

| Control | Type | Default | Enabled State | Tooltip |
|---|---|---|---|---|
| Enable precheck | `QCheckBox` | Unchecked | Always enabled | "Skips stress/MC/WF when baseline has zero trades. Opt-in." |
| Fail on non-positive PnL | `QCheckBox` | Unchecked | Enabled only when precheck is checked | "Also fails strategies with total_pnl <= 0. Works only when precheck is enabled." |

### PipelineConfig Mapping

```python
config = PipelineConfig(
    ...
    run_is_baseline_quality_precheck=self.precheck_checkbox.isChecked(),
    fail_is_baseline_on_nonpositive_pnl=(
        self.precheck_checkbox.isChecked()
        and self.precheck_nonpositive_checkbox.isChecked()
    ),
)
```

The dependent checkbox must not silently enable `fail_is_baseline_on_nonpositive_pnl=True` when the parent precheck checkbox is unchecked.

### Focused UI Tests

| # | Test | File |
|---|---|---|
| 1 | Precheck controls exist with unchecked defaults | `test_wfe_ui_wiring.py` |
| 2 | Dependent non-positive checkbox is disabled while parent precheck is unchecked | `test_wfe_ui_wiring.py` |
| 3 | Checking parent enables dependent checkbox; unchecking parent disables it again | `test_wfe_ui_wiring.py` |
| 4 | Unchecked parent passes `run_is_baseline_quality_precheck=False` and `fail_is_baseline_on_nonpositive_pnl=False`, even if dependent was previously checked | `test_wfe_ui_wiring.py` |
| 5 | Checked parent passes `run_is_baseline_quality_precheck=True`; checked dependent also passes `fail_is_baseline_on_nonpositive_pnl=True` | `test_wfe_ui_wiring.py` |
| 6 | Existing pipeline default tests still pass with both config fields defaulting to `False` | `test_validation_pipeline_service.py` |

## 3. Implementation Surface

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | Add WFE line to Walk-Forward card |
| `app/ui/main_window.py` | Add precheck controls to Validate page and wire `PipelineConfig` |
| `tests/test_validation_summary.py` | 3 WFE widget tests |
| `tests/test_wfe_ui_wiring.py` | 5 precheck UI tests |
| `tests/test_validation_pipeline_service.py` | Keep or strengthen default config regression |

## 4. Out of Scope

- Changing WFE computation semantics.
- Changing precheck engine behavior.
- Adding new precheck report output.
- Combining this UI work with MC worst-case equity engine internals.

## 5. Next Batch

**Batch 063E-Impl - WFE widget display and precheck UI controls.**

Keep this separate from 063D MC engine work to preserve reviewable diffs.

## 6. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
- **Codex review correction**: 2026-06-08
