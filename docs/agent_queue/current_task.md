# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 062H-Impl + 062I-Design - WF Equity Chart Widget Implementation and Price-Noise UI Config Controls Design.

## Context Level

Level 2 for 062H because it changes a UI widget while consuming existing serialized validation data.

Level 2 for 062I because it is design-only for UI controls and must not change runtime behavior.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/wf_equity_widget_implementation_contract_062E.md`
9. `docs/wf_equity_widget_test_contract_062G.md`
10. `docs/review_notes/2026-06-08_task-062f-impl_062g-design_price-noise-pipeline-integration-and-wf-equity-widget-test-contract_codex-review.md`
11. Relevant UI widget source and tests
12. This task file

## Scope

### Task 062H-Impl - WF Equity Chart Widget Implementation

Do:

- Implement a small WF equity line chart in `app/widgets/validation_summary.py`.
- Use existing PySide6 dependencies only; no matplotlib, plotly, pyqtgraph, or new dependency.
- Prefer a private `_WFEquityChart` widget using `QGraphicsView` / `QGraphicsScene` or an equivalent PySide6-only drawing approach.
- Consume only existing `walk_forward_summary["windows"]` dictionaries with:
  - `index`
  - `equity_curve`
  - `passed`
- Render only windows whose `equity_curve` is a list with length >= 2.
- Use green for passed windows and red for failed windows.
- Constrain chart height so the dashboard layout does not expand uncontrollably.
- Preserve the existing WF Equity Summary text section.
- Add focused tests in `tests/test_validation_summary.py` proving:
  - chart appears when valid equity windows exist;
  - chart is omitted when `windows` is missing;
  - chart is omitted when all equity curves are `None`;
  - chart handles partial equity availability;
  - single-window length < 2 does not render a chart;
  - chart height is constrained.
- Update changelog and task board.

Do not:

- Do not change validation engine, backtest engine, or pipeline serialization.
- Do not add report chart rendering.
- Do not add interactive zoom/pan/tooltips.
- Do not add dependencies.
- Do not change existing text summary behavior except to insert the chart after it.

### Task 062I-Design - Price-Noise UI Config Controls Design

Do:

- Create `docs/price_noise_ui_controls_design_062I.md`.
- Design future Validate/Run UI controls for the already-default-off price-noise pipeline config.
- Include:
  - target file(s), likely `app/ui/main_window.py` and any existing validation config area;
  - exact controls for `run_price_noise_stress`, `price_noise_pct`, `price_noise_iterations`, and `price_noise_seed`;
  - defaults matching `PipelineConfig`;
  - validation ranges and user-facing guard text;
  - no-live-trading / research-only copy;
  - focused future tests;
  - out-of-scope items.

Do not:

- Do not implement UI controls in this task.
- Do not change `PipelineConfig`.
- Do not wire runtime behavior.
- Do not add dependencies.

## Verification

Run:

- `.\.venv\Scripts\python.exe -m pytest tests\test_validation_summary.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests\test_validation_pipeline_service.py -q`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-062h-impl_062i-design_wf-equity-chart-widget-and-price-noise-ui-controls-design_deepseek.md`

Use this packet:

```text
Completed:
Files changed:
Behavior changed:
Tests run:
Assumptions:
Known risks:
Reviewer focus:
```

Then stop.
