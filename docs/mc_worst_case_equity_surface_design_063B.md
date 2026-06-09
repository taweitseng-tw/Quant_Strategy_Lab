# Monte Carlo Worst-Case Equity Evidence Surface Design - Task 063B

> Design-only. No production code changed.

## 1. Current State

`MonteCarloResult` currently has `worst_case`, a dict of percentile-derived worst metric values, such as `worst_case["total_pnl"] = p5 PnL`.

It does not store any per-iteration equity curve. The existing Monte Carlo runners collect aggregate metrics and discard any bar-by-bar or trade-step equity path.

## 2. Data Shape Requirement

To display worst-case equity, the engine should optionally retain only the single selected worst-case equity curve:

```python
# Current: MonteCarloResult.all_metrics = [{total_pnl, profit_factor, ...}, ...]
# Needed addition:
worst_case_equity_curve: list[float] | None = None
```

The result field name is `worst_case_equity_curve` everywhere. Do not introduce `worst_case_equity` as a second alias.

The "worst iteration" is selected deterministically:

1. Lowest `total_pnl`.
2. If tied, highest absolute `max_drawdown_pnl`.
3. If still tied, lowest iteration index.

## 3. Engine Change Scope

| Change | Impact |
|---|---|
| Add `worst_case_equity_curve: list[float] | None = None` to `MonteCarloResult` | Backward-compatible default `None` |
| Add an opt-in collection parameter to MC runners, default `False` | Keeps current default memory/runtime behavior |
| Track the current worst iteration during the loop | O(N), avoids storing every equity curve |
| Store the selected iteration equity curve as `list[float]` | Medium risk because missed-trade MC does not currently return true equity data |

`app/services/validation_pipeline_service._mc_to_dict()` must include `worst_case_equity_curve` only when present. Existing consumers must continue to work when the key is absent or `None`.

## 4. Equity Curve Source Rules

- For MC modes that re-run backtests, use the produced `BacktestResult.equity_curve` when available.
- For `run_missed_trade_monte_carlo`, do not pretend a true bar-by-bar curve exists if the engine only recomputes trade metrics. Either reconstruct a clearly labeled trade-step equity curve from surviving trades and assumptions, or return `None` with a warning.
- Do not store all per-iteration curves in `all_metrics`.
- Do not mutate the baseline `BacktestResult`.
- Do not change the existing percentile semantics of `worst_case`.

## 5. Widget Display

In `ValidationSummary`, after the existing Monte Carlo card, add a worst-case equity line chart only when `monte_carlo_summary["worst_case_equity_curve"]` is a list with at least 2 numeric points.

Example text:

```text
Monte Carlo (15 iter): p05=1,000  p50=4,800  p95=9,000  Worst-case PnL: 1,000

[MC Worst-Case Equity] line chart of the selected worst iteration equity curve
```

The chart should reuse the same PySide6-only `QGraphicsView` pattern as `_WFEquityChart`. No new charting dependency.

## 6. Report Display

Show only when `worst_case_equity_curve` is non-empty and has at least 2 numeric points.

### Markdown

```markdown
- **MC Worst-Case Equity** (selected worst iteration):
  | Start | End | Change |
  |---|---|---|
  | 100,000 | 95,000 | -5.0% |
```

### HTML

```html
<p><b>MC Worst-Case Equity</b></p>
<table><tr><th>Start</th><th>End</th><th>Change</th></tr>
<tr><td>100,000</td><td>95,000</td><td class="pnl-negative">-5.0%</td></tr>
</table>
```

All dynamic HTML values must be escaped or numeric-formatted before rendering.

## 7. Focused Tests (Future)

| # | Test | File |
|---|---|---|
| 1 | `MonteCarloResult.worst_case_equity_curve` exists and is `None` by default | `test_monte_carlo.py` |
| 2 | Opt-in MC collection stores only the selected worst-case curve | `test_monte_carlo.py` |
| 3 | Worst-case tie-break is deterministic: lowest PnL, highest drawdown, lowest index | `test_monte_carlo.py` |
| 4 | Pipeline serialization includes `worst_case_equity_curve` only when present | `test_validation_pipeline_service.py` |
| 5 | Widget shows worst-case equity chart when present | `test_validation_summary.py` |
| 6 | Widget omits chart when curve is `None`, missing, non-list, or has fewer than 2 points | `test_validation_summary.py` |
| 7 | Markdown and HTML include escaped worst-case equity table when present and omit it when absent | `test_report_export.py` |

## 8. Out of Scope

- Persisting all per-iteration equity curves.
- New charting dependencies.
- Interactive chart features.
- Changing elimination rules that read `MonteCarloResult.worst_case`.

## 9. Next Batch

**Batch 063D-Impl - MC worst-case equity engine and serialization slice.**

Keep widget/report implementation as a separate follow-up if the engine slice reveals ambiguity in equity reconstruction for missed-trade MC.

## 10. Metadata

- **Author**: DeepSeek V4
- **Date**: 2026-06-08
- **Codex review correction**: 2026-06-08
