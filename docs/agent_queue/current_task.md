# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 062D-Impl + 062E-Design - Price-Noise Stress Test Engine Slice and WF Equity Widget Implementation Contract.

## Context Level

Level 3 for 062D because it changes validation stress logic.

Level 2 for 062E because it is design-only for UI/report implementation.

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
9. `docs/wf_equity_evidence_surface_design_062C.md`
10. `docs/review_notes/2026-06-08_task-062b-design_062c-design_price-noise-stress-and-wf-equity-evidence_codex-review.md`
11. Relevant validation tests and source files
12. This task file

## Scope

### Task 062D-Impl - Price-Noise Stress Test Engine Slice

Do:

- Implement the minimal engine function for price-noise stress in `validation_engine/`.
- Preserve OHLC constraints exactly as specified in `docs/price_noise_stress_contract_062B.md`.
- Add deterministic seed handling.
- Add focused tests for:
  - expected result structure;
  - same seed same output;
  - zero noise identity;
  - OHLC constraints preserved;
  - non-positive baseline PnL warning / undefined degradation ratio.
- Keep default pipeline behavior unchanged unless explicitly enabled.
- Update docs/changelog/task board.

Do not:

- Do not wire UI controls yet.
- Do not add report rendering yet.
- Do not add new dependencies.
- Do not claim robustness or trading edge.

### Task 062E-Design - WF Equity Widget Implementation Contract

Do:

- Create `docs/wf_equity_widget_implementation_contract_062E.md`.
- Convert the 062C surface design into an implementation checklist:
  - target widget/file;
  - data adapters;
  - rendering strategy using existing dependencies only;
  - empty/failure states;
  - tests;
  - out-of-scope items.
- Keep this task design-only.

Do not:

- Do not implement the widget.
- Do not change reports or UI code.

## Verification

Run:

- `.\.venv\Scripts\python.exe -m pytest tests\test_stress_test.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests\test_validation_pipeline_service.py -q`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-062d-impl_062e-design_price-noise-engine-and-wf-equity-widget-contract_deepseek.md`

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
