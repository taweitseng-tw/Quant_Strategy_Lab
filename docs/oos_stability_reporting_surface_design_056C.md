# OOS Stability Reporting Surface Design — Task 056C

> Design-only. No production code changed.

## 1. Current Data Flow Trace

```
run_validation_pipeline()
  -> PipelineResult (contains oos_metrics + elimination_result)
  -> Three consumers:

[1] ValidationSummary widget (app/widgets/validation_summary.py)
    update_from_result(result):
      reads every PipelineResult field EXCEPT oos_metrics
      -> Elimination card: "PASSED" or "ELIMINATED -- rules"
      -> No OOS metrics card exists

[2] Report generator (reports/generator.py)
    _format_markdown_validation(vr) / _format_html_validation(vr):
      reads split_metadata, baseline_metrics, stress, MC, WF, elimination_result
      -> Does NOT read oos_metrics
      -> passed as dict via asdict(PipelineResult) -> validation_result parameter

[3] Log panel (app/ui/main_window.py ~line 1124)
      -> "Elimination: PASSED / FAILED" only -- no OOS line
```

**Key finding**: `PipelineResult.oos_metrics` is computed (Task 056B) and stored in the dataclass, but **no consumer reads it**. The UI and reports are silent about OOS metrics and stability ratios.

## 2. Available Data in `PipelineResult.oos_metrics`

After Task 056B, `oos_metrics` contains standard `compute_metrics()` output:

```python
{
    "total_trades": ...,
    "total_pnl": ...,
    "profit_factor": ...,
    "max_drawdown_pnl": ...,
    "avg_trade": ...,
    "win_rate": ...,
}
```

Additionally, `elimination_result.warnings` may contain stability warnings like:

```
"max_oos_pf_degradation is set but IS profit factor is non-positive — ratio cannot be computed.  Skipping rule."
```

After Task 056B-Fix, these warnings also fire for uncomputable ratios.

## 3. Proposed Product Surface

### 3.1 ValidationSummary Widget — New "OOS Metrics" Card

Insert between Walk-Forward Matrix and Elimination cards:

```
OOS Metrics
PnL: XX  |  PF: X.XX  |  Trades: XX  |  Max DD: XX  |  Win Rate: XX%
```
(All values read from `result.oos_metrics` dict. No ratio computation in widget.)

- If OOS metrics are `None`: show "No OOS data."
- If OOS metrics exist: show the above line only.
- Stability failure text from `elimination_result.failed_rules` and `elimination_result.warnings` already surfaces in the existing Elimination card and warnings list. No separate stability ratio display at this stage.

### 3.2 Markdown Report — OOS Section

Insert after the Baseline line in `_format_markdown_validation()`:

```markdown
- **OOS**: PnL=XX, PF=X.XX, Trades=XX, Max DD=XX
```

- If OOS metrics are `None`: skip the line silently.

### 3.3 HTML Report — OOS Section

Insert after the Baseline line in `_format_html_validation()`:

```html
<p><b>OOS:</b> PnL=XX, PF=X.XX, Trades=XX, Max DD=XX</p>
```

- If OOS metrics are `None`: skip the line silently.

### 3.4 Log Panel — OOS Summary Line

After the elimination line:

```python
f"OOS: PnL={oos_pnl:,.0f}, PF={oos_pf:.2f}"
```

## 4. Implementation Surface Files (Task 056D)

| File | Change (minimal) |
|---|---|
| `app/widgets/validation_summary.py` | Add OOS Metrics card in `update_from_result()` — reads `result.oos_metrics` dict only |
| `reports/generator.py` | Add OOS metrics line to `_format_markdown_validation()` and `_format_html_validation()` — reads `vr.get("oos_metrics", {})` |
| `app/ui/main_window.py` | Add one-line OOS summary after elimination log line |
| (No change to pipeline service, elimination engine, or tests) |

## 5. Design Decisions

1. **Display only existing structured data** — all displayed values come from `PipelineResult.oos_metrics` (a plain `compute_metrics()` dict). No ratio computation in UI/report code.
2. **No new report format sections** — only a single additional line in the existing Validation Evidence section.
3. **No UI rearrangement** — OOS card is additive, inserted before Elimination.
4. **Stability ratio display is deferred** — `_compute_oos_stability()` runs inside `validation_engine/elimination.py` and is not exposed as a structured pipeline field. Stability gate outcomes are already visible via `elimination_result.failed_rules` and `elimination_result.warnings`. A future task can add an engine-layer `oos_stability` payload after this baseline display is done.
5. **Engine/UI separation preserved** — all formatting is text presentation only; no quant logic moves into widgets.

## 6. Risk Assessment

| Risk | Mitigation |
|---|---|
| `oos_metrics` is `None` (empty OOS segment) | Widget shows "No OOS data." Report silently skips the line. Log panel skips the line. |
| Engine/UI boundary: ratio computation leaks into presentation | Corrected: Task 056D displays only raw `oos_metrics` dict values. No ratio computation in UI/report. Stability gate pass/fail is already visible via existing `elimination_result`. |
| Report output changes break existing report tests | If report tests exist that check exact Validation Evidence output, add the new OOS line to expected output. If none exist, the new line is purely additive and won't break assertions. |

## 7. Recommended Follow-up Task: Task 056D

### Task 056D — OOS Metrics Display Surface Implementation

**Scope:**
- `app/widgets/validation_summary.py`: Add OOS Metrics card after Walk-Forward Matrix. Reads `result.oos_metrics` dict only. No ratio computation.
- `reports/generator.py`: Add one OOS metrics line after the Baseline line in both `_format_markdown_validation()` and `_format_html_validation()`. Reads `vr.get("oos_metrics", {})` only. No ratio computation.
- `app/ui/main_window.py`: Add one-line OOS summary after the elimination log line. Reads `result.oos_metrics` dict only.
- Update `docs/changelog.md` and `docs/task_board.md`.

**Do NOT:**
- Change engine, elimination rules, pipeline defaults, or test code.
- Add new dataclasses or change `PipelineResult` schema.
- Compute OOS/IS stability ratios in UI or report code.
- Add dependencies.

**Acceptance Criteria:**
1. ValidationSummary widget shows OOS metrics card between Walk-Forward Matrix and Elimination.
2. Markdown report headers under "Validation Evidence" include an OOS metrics line.
3. HTML report headers under "Validation Evidence" include an OOS metrics line.
4. Log panel prints a one-line OOS summary after the elimination line.
5. Empty/missing OOS segment does not crash any surface; widget shows "No OOS data.", report and log skip the line.
6. Full test suite passes (existing UI/report tests are not broken).
7. `git diff --check` passes.

**Estimated files**: 3 (widget + generator + main_window)
**Risk**: Low (pure display of existing data fields)

---

## 8. Triage metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Reviewed by**: Codex (pending)
- **Dependencies**: Task 056B (OOS metrics + stability rules) — ✅ Done
