# Task 056G — Stress Result Details Reporting Surface Design Only

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### Current State Survey

Inspected all three stress result consumption surfaces:

| Surface | What it shows today | What's available but not shown |
|---|---|---|
| `validation_summary.py` | `test_name`, pass/fail, PnL degradation | `assumptions`, `warnings`, `threshold` |
| `reports/generator.py` (markdown) | `test_name`, pass/fail, PnL degradation | `assumptions`, `warnings`, `threshold` |
| `reports/generator.py` (HTML) | `test_name`, pass/fail, PnL degradation | `assumptions`, `warnings`, `threshold` |

### Design Decisions (`docs/stress_result_details_surface_design_056G.md`)

1. **Selective display** — only show assumptions/warnings for stress tests with user-configured parameters (currently only `remove_best_n_trades`). Existing tests (commission, slippage, delay, perturbation) unchanged.
2. **Inline sub-lines** — append detail lines after each stress test entry instead of creating separate cards/sections.
3. **Consistent across surfaces** — widget, markdown, and HTML all follow the same sub-line pattern.

### Proposed Implementation Surface (Task 056G-Impl)

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | Sub-lines for rich-assumptions stress tests |
| `reports/generator.py` | Sub-lines in both `_format_markdown_validation()` and `_format_html_validation()` |
| `tests/test_validation_summary.py` + `tests/test_report_export.py` | Assertions for sub-lines |

## Files Changed

| File | Change |
|---|---|
| `docs/stress_result_details_surface_design_056G.md` | **Created** |
| `docs/changelog.md` | Task 056G entry |
| `docs/task_board.md` | 056G -> Done |

## Verification

- **No production code changed** (design-only).
- **`git diff --check`**: passes.
- **Git status**: Dirty only with expected docs files.

## Known Issues

- None.

## Risks

- None (design-only).

## Suggested Next Task

**Task 056G-Impl** — Stress Result Details Display Implementation.
