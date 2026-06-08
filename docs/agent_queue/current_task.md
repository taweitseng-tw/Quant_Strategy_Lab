# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 062F-Impl + 062G-Design - Price-Noise Pipeline Integration and WF Equity Widget Test Contract.

## Context Level

Level 3 for 062F because it changes validation pipeline behavior.

Level 2 for 062G because it is design/test-contract only for the UI widget slice.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/price_noise_stress_contract_062B.md`
9. `docs/wf_equity_widget_implementation_contract_062E.md`
10. `docs/review_notes/2026-06-08_task-062d-impl_062e-design_price-noise-engine-and-wf-equity-widget-contract_codex-review.md`
11. Relevant validation pipeline source and tests
12. This task file

## Scope

### Task 062F-Impl - Price-Noise Pipeline Integration

Do:

- Import and wire `stress_price_noise()` into `app/services/validation_pipeline_service.py`.
- Add `PipelineConfig` fields:
  - `run_price_noise_stress: bool = False`
  - `price_noise_pct: float = 0.005`
  - `price_noise_iterations: int = 50`
  - `price_noise_seed: int = 42`
- Keep default behavior unchanged: `PipelineConfig()` must not include `price_noise` in `stress_results`.
- When `run_price_noise_stress=True`, append a `price_noise` stress result after existing optional stress tests.
- Pass the train split, strategy, baseline, instrument, and baseline backtest assumptions consistently through `stress_price_noise()`.
- Add focused tests in `tests/test_validation_pipeline_service.py` proving:
  - default config does not run price noise;
  - opt-in config appends a `price_noise` stress result;
  - config snapshot includes the four new fields;
  - opt-in result contains `pnl_degradation_ratio`, `survival_rate`, and `research_only=True`;
  - same seed/config gives deterministic pipeline stress results.
- Update changelog and task board.

Do not:

- Do not add UI controls yet.
- Do not run price-noise by default.
- Do not change existing stress result names or ordering except appending opt-in `price_noise`.
- Do not add dependencies.
- Do not claim live-trading robustness.

### Task 062G-Design - WF Equity Widget Test Contract

Do:

- Create `docs/wf_equity_widget_test_contract_062G.md`.
- Convert `docs/wf_equity_widget_implementation_contract_062E.md` into an implementation-ready test contract for the next UI slice.
- Include:
  - target file(s);
  - exact input shapes for `walk_forward_summary["windows"]`;
  - expected chart visibility rules;
  - skipped/missing equity behavior;
  - color/label expectations;
  - focused tests for `tests/test_validation_summary.py` or the existing closest UI test file;
  - out-of-scope items.

Do not:

- Do not implement the WF equity widget in this task.
- Do not change UI code.
- Do not change report rendering.

## Verification

Run:

- `.\.venv\Scripts\python.exe -m pytest tests\test_validation_pipeline_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests\test_stress_test.py -q`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-062f-impl_062g-design_price-noise-pipeline-integration-and-wf-equity-widget-test-contract_deepseek.md`

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
