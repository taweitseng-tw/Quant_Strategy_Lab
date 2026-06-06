# IS Baseline Precheck Visibility Surface Design — Task 056K

> Design-only. No production code changed.

## 1. Current Display Behavior When `precheck_failed=True`

### 1.1 Precheck-Failed PipelineResult Shape

```python
PipelineResult(
    precheck_failed=True,
    split_metadata={...},
    baseline_metrics={...},         # e.g. total_trades=0
    oos_metrics={...} | None,
    stress_results=[],              # empty
    monte_carlo_summary=None,
    walk_forward_summary=None,
    walk_forward_matrix_summary=None,
    elimination_result={"passed": False, "failed_rules": [reason]},
    warnings=["Validation precheck failed: ... Stress/MC/WF skipped."],
)
```

### 1.2 Widget Display (Current)

| Section | What appears |
|---|---|
| Split | Train/Val/OOS rows (normal) |
| Baseline | Zero PnL, zero PF, zero trades (accurate) |
| Stress | "No stress results." |
| OOS Metrics | Present or absent (normal) |
| Monte Carlo | "No MC data." |
| Walk-Forward | "Walk-forward skipped..." |
| Elimination | "**ELIMINATED** — reason text" |
| **Precheck warnings** | **NOT shown** |

### 1.3 Report Display (Current)

| Section | What appears |
|---|---|
| Split | Rows (normal) |
| Baseline | Zero metrics (accurate) |
| Stress | No lines (empty loop) |
| MC | No lines |
| WF | No lines |
| Elimination | ELIMINATED with reason |
| **Precheck warnings** | **NOT shown** |

### 1.4 Assessment

The current display is **functional but not obvious**. A user seeing "No stress results." + "No MC data." + "Walk-forward skipped..." may not immediately understand that this is an intentional precheck short-circuit rather than a data/configuration problem.

The `warnings` list contains the explicit reason (`"Validation precheck failed: strategy has zero baseline trades. Stress/MC/WF skipped."`) but is **not displayed in either the widget or reports**. Adding a small precheck indicator would make the state unambiguous.

## 2. Recommendation: Add Minimal Precheck Indicator

### 2.1 Widget — Small Header Banner

Before the Split metadata section, add a single-line precheck banner when `precheck_failed` is True:

```
⚠ Precheck Failed — {reason}
```

Since the widget currently starts rendering with "Data Source" at the top, the precheck banner should appear immediately after it (or before Split, as the first section card).

**Format**:
```python
if self._get(result, "precheck_failed", False):
    reason = (self._get(result, "elimination_result", {}) or {}).get("failed_rules", ["Unknown"])[0]
    self._add_section("Precheck", f"⚠ FAILED — {reason}", passed=False)
```

### 2.2 Markdown Report — Precheck Line

Add before Split line in `_format_markdown_validation()`:

```markdown
- **Precheck**: FAILED — strategy has zero baseline trades. Stress/MC/WF skipped.
```

Only rendered when `vr.get("precheck_failed")` is True.

### 2.3 HTML Report — Precheck Line

Add before Split paragraph in `_format_html_validation()`:

```html
<p><b>Precheck:</b> <span style="color:#ef5350;font-weight:bold;">FAILED</span> — reason text</p>
```

Only rendered when `vr.get("precheck_failed")` is True. Reason text is escaped.

### 2.4 What NOT to Change

- **No new sections** — the precheck indicator is a single line/card, not a new section.
- **No layout changes** — the indicator reuses existing `_add_section()` / format-line patterns.
- **No change to non-precheck flow** — when `precheck_failed` is False, nothing changes.
- **No engine/pipeline changes** — display-only.

## 3. Implementation Surface (Task 056K-Impl)

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | Add precheck indicator card (after Data Source, before Split) |
| `reports/generator.py` | Add precheck line in `_format_markdown_validation()` and `_format_html_validation()` |
| `tests/test_validation_summary.py` | Verify precheck card appears when `precheck_failed=True` and absent otherwise |
| `tests/test_report_export.py` | Verify precheck line in both formats |
| `docs/changelog.md` + `docs/task_board.md` | Standard update |

## 4. Acceptance Criteria (Task 056K-Impl)

1. Widget shows precheck failure banner when `precheck_failed=True`.
2. Widget does NOT show precheck banner when `precheck_failed=False`.
3. Markdown report includes precheck line when `precheck_failed=True`.
4. HTML report includes precheck line when `precheck_failed=True` (with HTML escaping).
5. Precheck text includes the precheck failure reason from `elimination_result.failed_rules[0]`.
6. No precheck text in any surface when `precheck_failed=False`.
7. Existing widget/report tests still pass.
8. Full suite passes.
9. `git diff --check` passes.

## 5. Design metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: Task 056J-Impl (precheck fields) — Done
- **Blocked by**: Nothing
