# Strategy Explainability Report Section Design - Tasks 439-444

Design document. No production code changed.

Generated: 2026-06-11

## Goal

Add a compact Strategy Explainability section to markdown and HTML reports so a
reviewer can quickly see:

- what strategy was tested
- where it came from
- what rule blocks it contains
- which ranking and validation evidence is available
- which assumptions and warnings affect interpretation

This section must reuse existing report inputs only. It must not change ranking,
validation, elimination, backtest behavior, or the report disclaimer.

## Existing Inputs

`reports/generator.py` already receives enough inputs:

- `strategy: Strategy`
  - `name`
  - `long_entry`
  - `long_exit`
  - `short_entry`
  - `short_exit`
  - `risk_management`
- `result: BacktestResult`
  - `metrics`
  - `assumptions`
  - `warnings`
- `provenance: dict | None`
  - `source_type`
  - `generator`
  - `generator_version`
  - `random_seed`
  - `rule_block_versions`
  - `generated_at`
- `validation_result: dict | None`
  - `elimination_result`
  - existing validation summaries such as split, stress, Monte Carlo, and
    walk-forward evidence

Important limitation:

- `fitness`, `rank`, and `total_strategies` are not guaranteed
  `validation_result` fields. The implementation may render them only when
  present in `validation_result` or `provenance`, but must omit them otherwise.

## Proposed Placement

Insert the new section after the financial safety notice and before the current
`Strategy Profile` section in markdown.

Insert the HTML panel near the top of the report, before the existing strategy
profile / metrics panels.

The current detailed sections should remain in place for compatibility. The new
section is a high-signal summary, not a replacement.

## Markdown Content

Suggested shape:

```markdown
## Strategy Explainability

- **Strategy**: `Example Strategy`
- **Source**: generated, generator=random_strategy_generator, version=1.0, seed=42
- **Rule Blocks**:
  - Long Entry: `close > SMA(period=20)`
  - Long Exit: `Inactive`
  - Short Entry: `Inactive`
  - Short Exit: `Inactive`
- **Ranking Evidence**:
  - Fitness: 0.563
  - Rank: 1 / 10
- **Validation Evidence**:
  - Elimination: PASSED
  - Thresholds Applied: min_trade_count=5, min_profit_factor=0.5
- **Risk Assumptions**:
  - Execution: next_bar_open, signal_confirmation=bar_close
  - Costs: commission_per_side=2.0, slippage_per_side_ticks=1.0, tick_size=0.1
  - Risk Management: stop_loss_ticks=10.0, take_profit=None, session_exit=False
- **Warnings**:
  - No warnings were generated during this backtest.
```

Render rules:

- Omit `Ranking Evidence` if no fitness or rank data exists.
- Omit `Validation Evidence` if `validation_result` is missing.
- Omit thresholds if `config_snapshot` is empty or all thresholds are disabled.
- Use `format_block_desc()` for rule block text.
- Use existing `result.assumptions` values for execution and cost assumptions.
- Use `strategy.risk_management` for configured risk-management values.
- Include `result.warnings` and `elimination_result.warnings` when present.

## HTML Content

Add a panel similar to existing report panels:

```html
<div class="panel explainability-panel">
  <h2 class="panel-title">Strategy Explainability</h2>
  ...
</div>
```

HTML requirements:

- Escape every dynamic string with `html.escape(str(value))`.
- Escape strategy names, provenance values, rule descriptions, failed rules,
  thresholds, warnings, and assumption values.
- Use fixed CSS class names such as `status-passed` and `status-eliminated`.
- Do not derive CSS class names directly from untrusted strings.

## Field Mapping

| Display item | Source | Required? | Behavior when missing |
|---|---|---:|---|
| Strategy name | `strategy.name` | Yes | Render current value |
| Rule blocks | `strategy.long_entry` etc. via `format_block_desc()` | Yes | `Inactive` from helper |
| Source type | `provenance.get("source_type")` | No | `generated` |
| Generator | `provenance.get("generator")` | No | Omit or `N/A` |
| Generator version | `provenance.get("generator_version")` | No | Omit or `N/A` |
| Random seed | `provenance.get("random_seed")` | No | Omit or `N/A` |
| Fitness | `validation_result.get("fitness")` or `provenance.get("fitness")` | No | Omit |
| Rank | `validation_result.get("rank")` or `provenance.get("rank")` | No | Omit |
| Total strategies | `validation_result.get("total_strategies")` or provenance equivalent | No | Omit |
| Elimination status | `validation_result["elimination_result"]["passed"]` | No | Omit |
| Failed rules | `elimination_result.failed_rules` | No | Omit when empty |
| Thresholds | `elimination_result.config_snapshot` | No | Omit disabled values |
| Execution assumptions | `result.assumptions` | Yes | Use existing report defaults |
| Risk management | `strategy.risk_management` | Yes | Render unset values as `None` |
| Warnings | `result.warnings` and elimination warnings | No | Render no-warning message |

## Implementation Scope For Tasks 445-450

Modify:

- `reports/generator.py`
  - add `_format_markdown_strategy_explainability(...)`
  - add `_format_html_strategy_explainability(...)`
  - call both helpers near the top of each report
- `tests/test_report_export.py`
  - add focused markdown and HTML coverage
- `docs/task_board.md`
- `docs/changelog.md`

Do not modify:

- ranking formulas
- validation or elimination logic
- UI widgets
- report service APIs unless absolutely required
- existing financial safety disclaimer

## Required Tests For Tasks 445-450

1. Markdown report contains `## Strategy Explainability`.
2. HTML report contains `explainability-panel`.
3. Strategy name and all four rule block descriptions render in both formats.
4. Provenance fields render when supplied and fall back cleanly when missing.
5. Ranking evidence is omitted when fitness/rank fields are absent.
6. Ranking evidence renders when fitness/rank fields are supplied.
7. Validation elimination status, failed rules, thresholds, and warnings render
   when supplied.
8. Disabled threshold values (`None` and `False`) are omitted.
9. HTML escapes malicious strategy names, provenance values, rule text, failed
   rules, thresholds, and warnings.
10. Financial safety disclaimer remains present in markdown and HTML reports.

## Acceptance Criteria For Tasks 445-450

- The new section is additive and backward-compatible.
- Reports still generate when `provenance` and `validation_result` are missing.
- No report output presents generated strategies as investment advice.
- Focused report tests pass.
- `git diff --check` passes.
