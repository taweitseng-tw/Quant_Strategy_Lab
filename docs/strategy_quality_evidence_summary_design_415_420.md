# Strategy Quality Evidence Summary Design - Tasks 415-420

> Design artifact only. No production code was changed.
> Generated: 2026-06-11.

## Purpose

Define a bounded evidence surface for strategy elimination decisions in the Validate page summary and exported reports.

The goal is to explain why a strategy passed or was eliminated without changing elimination formulas, ranking scores, or validation defaults.

## Current Evidence Flow

| Source | Current fields | Current display |
|---|---|---|
| `validation_engine.elimination.EliminationResult` | `passed`, `failed_rules`, `warnings`, `metrics_snapshot`, `config_snapshot` | Engine result only. |
| `app.services.validation_pipeline_service.PipelineResult.elimination_result` | `passed`, `failed_rules`, `warnings`, `config_snapshot` | Serialized into pipeline result. `metrics_snapshot` is not currently forwarded. |
| `app.widgets.validation_summary.ValidationSummary` | Reads `passed` and `failed_rules` | Single Elimination card line. |
| `reports.generator` markdown/html validation sections | Reads `passed` and `failed_rules` | Single Elimination line. |
| Ranking entries from `StrategyService.get_ranked_strategies()` | `elimination_passed`, `elimination_failed_rules`, `elimination_status` | Ranking/status surfaces only. |

## Design Decision

Tasks 421-426 should expand only the evidence that is already present in `PipelineResult.elimination_result`:

- `passed`
- `failed_rules`
- `warnings`
- `config_snapshot`

Do not add `metrics_snapshot` to the implementation slice. It exists on the engine dataclass, but the validation pipeline does not currently serialize it. Adding that field is a separate behavior/data-contract change.

## Validate Summary Widget Surface

Target file:

```text
app/widgets/validation_summary.py
```

Display rules:

- If `passed` is true, show `PASSED`.
- If `passed` is false, show `ELIMINATED`.
- If `failed_rules` is non-empty, list each rule on a separate indented line.
- If `warnings` is non-empty, add a `Warnings:` section with each warning on its own line.
- If `config_snapshot` has enabled thresholds, add one compact `Thresholds used:` line.
- Enabled thresholds are keys whose values are not `None` and are not `False`.
- Do not show all disabled thresholds.
- Do not display `metrics_snapshot` in the widget.
- Do not add financial advice wording to the widget.

Example body:

```text
ELIMINATED
Failed rules:
- min_profit_factor (0.30 < 0.50)
- max_drawdown_pnl (30000 > 5000)
Thresholds used: min_profit_factor=0.5, max_drawdown_pnl=5000
Warnings:
- OOS threshold set but OOS metrics were unavailable. Skipping rule.
```

## Report Surface

Target file:

```text
reports/generator.py
```

Markdown display rules:

- Keep the existing `Elimination` status line for compatibility.
- Add a small `Elimination Evidence` block when thresholds or warnings exist.
- Include enabled thresholds as bullets or a compact table.
- Include warnings as bullets.
- Escape or sanitize text in HTML output.
- Keep the research/backtesting disclaimer elsewhere in the report; do not duplicate it inside every elimination block unless the existing report layout requires it.

HTML display rules:

- Match the markdown information.
- Escape failed rules, threshold keys/values, and warnings.
- Do not render raw HTML from strategy names, rules, or warnings.

## Ranking Detail Surface

No change in Tasks 421-426.

Ranking entries already carry:

```text
elimination_passed
elimination_failed_rules
elimination_status
```

Adding richer ranking-detail UI is deferred to a later explainability task.

## Implementation Scope For Tasks 421-426

Do:

1. Add a small helper in `ValidationSummary` to format elimination evidence.
2. Add report helpers for enabled threshold formatting and warning formatting.
3. Update markdown and HTML validation report sections.
4. Add focused tests for widget and report output.

Do not:

- Change `EliminationConfig`.
- Change `evaluate_elimination()`.
- Change ranking scores or ordering.
- Add `metrics_snapshot` to `PipelineResult`.
- Change default thresholds.
- Move UI cards.
- Clean unrelated legacy mojibake comments.

## Focused Test Plan

Widget tests in `tests/test_validation_summary.py`:

1. Passed elimination still shows `PASSED`.
2. Failed elimination lists each failed rule separately.
3. Elimination warnings are displayed when present.
4. Enabled thresholds from `config_snapshot` appear in a compact thresholds line.
5. Disabled thresholds (`None` or `False`) are omitted.

Report tests in `tests/test_report_export.py`:

1. Markdown includes elimination evidence thresholds when present.
2. Markdown includes elimination warnings when present.
3. Markdown omits the thresholds block when no thresholds are enabled.
4. HTML includes escaped elimination evidence thresholds.
5. HTML escapes failed rules and warnings.

Suggested verification:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_summary.py tests/test_report_export.py -q
git diff --check
```

## Acceptance Criteria For Tasks 421-426

- Widget and report show clearer elimination evidence using existing serialized fields.
- No validation or ranking behavior changes.
- Disabled thresholds are not shown.
- HTML output escapes all dynamic elimination text.
- Focused tests pass.
- Changelog update is top-entry only and does not rewrite old history.
