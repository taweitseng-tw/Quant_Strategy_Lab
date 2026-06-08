# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity, DeepSeek, Gemini, or Reasonix reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 062B-Design + 062C-Design - Price-Noise Stress Test Contract and WF Equity Evidence Surface Design.

## Context Level

Level 3 for both tasks because they affect validation assumptions, anti-overfitting evidence, and UI/report acceptance criteria.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/next_milestone_decision_062A.md`
9. Relevant validation/report/UI files only as needed for design grounding
10. This task file

## Context

Task 062A recommends Strategy Quality and Robustness Expansion as the next default milestone. The first batch is design-only to prevent accidental engine/UI churn.

This project prioritizes killing weak curve-fit strategies and preserving explainable, reproducible evidence. Do not implement new validation logic in this batch.

## Scope

### Task 062B-Design - Price-Noise Stress Test Contract

Do:

- Create `docs/price_noise_stress_contract_062B.md`.
- Define the proposed price-noise stress test:
  - purpose;
  - input data shape;
  - random seed / deterministic behavior;
  - price perturbation model;
  - no-future-leak constraints;
  - pass/fail metrics;
  - assumptions and warnings;
  - focused future tests.
- Specify how results should fit into existing validation pipeline structures.

Do not:

- Do not implement the stress test.
- Do not alter backtest, validation, UI, or report production code.
- Do not claim robustness or trading edge.

### Task 062C-Design - WF Equity Evidence Surface

Do:

- Create `docs/wf_equity_evidence_surface_design_062C.md`.
- Define how walk-forward equity evidence should be surfaced in UI/reports:
  - required data shape;
  - chart/table expectations;
  - empty/failure states;
  - report serialization expectations;
  - focused future tests.
- Keep the design compatible with existing walk-forward and WFE outputs.

Do not:

- Do not implement UI/report rendering.
- Do not add new dependencies.
- Do not broaden into portfolio, live trading, or broker scope.

## Acceptance Criteria

1. Both design docs are specific enough for a future implementation agent.
2. Designs explicitly preserve no-future-leak and research-only constraints.
3. Future test plans include deterministic and failure-path coverage.
4. Changelog and task board are updated.

## Verification

Run:

- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1`

## Completion Report

After completion, create:

`docs/agent_reports/2026-06-08_task-062b-design_062c-design_price-noise-stress-and-wf-equity-evidence_deepseek.md`

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
