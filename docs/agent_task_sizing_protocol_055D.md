# Task 055D - Semi-Automated Agent Task Sizing Protocol

## Overview
This document defines the semi-automated task sizing protocol for the Codex -> Anti-Gravity/DeepSeek -> Codex review loop in the Quant Strategy Lab project. The goal is to maximize agent efficiency while preserving strict architecture and correctness boundaries. By categorizing tasks into Risk Tiers, we determine when it is safe to batch work into broader assignments versus when tasks must remain narrow and single-purpose.

## Risk Tiers and Batch Sizes

### Tier 1: Documentation & Hygiene
- **Scope**: Changelogs, task boards, markdown design docs, non-functional text fixes, `.gitignore` drafts, docstrings.
- **Recommended Batch Size**: Broad. Up to 3-6 related documentation or workflow files can be bundled.
- **Broadening Rule**: Anti-Gravity may be given broad documentation-sweep tasks across many files as long as production logic is untouched.
- **Review Requirements**: Fast, low-friction Codex review. Can be combined with Tier 2 reviews.
- **Verification Commands**: `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`

### Tier 2: UI Skeleton & Passive Components
- **Scope**: PySide6 layout structures, passive widgets, non-binding buttons, stylistic polish, report HTML templates.
- **Recommended Batch Size**: Medium. Usually 2-4 closely related passive UI files, e.g., "Build the layout for the entire results page and its sub-tabs."
- **Broadening Rule**: Safe to batch as long as no business logic or `core/` / `engine/` layers are modified.
- **Review Requirements**: Codex checks for PySide6 best practices and ensures no logic leaked into UI classes.
- **Verification Commands**: GUI launch test (manual or via smoke test runner), layout inspection.

### Tier 3: Service & Repository Wiring
- **Scope**: Connecting UI to services, updating SQLite repositories, simple serialization logic.
- **Recommended Batch Size**: Small to Medium. 1-2 API endpoints or one single service/repository flow.
- **Broadening Rule**: Batching is permitted only if the features are heavily related (e.g., "Wire Load/Save Strategy APIs in Repository").
- **Review Requirements**: Strict check by Codex to ensure data access layer boundaries and serialization invariants are respected.
- **Verification Commands**: `python -m pytest tests/` (specifically repository and service tests).

### Tier 4: Engine & Quant Logic
- **Scope**: Backtest execution, `evaluator.py`, strategy generation algorithms, walk-forward, Monte Carlo, MTF alignment.
- **Recommended Batch Size**: **STRICTLY NARROW AND SINGLE-PURPOSE.**
- **Broadening Rule**: **NEVER BROADEN.** DeepSeek or Anti-Gravity must be assigned one highly-specific mathematical or algorithmic phase at a time. Do not combine "Design," "Implement," and "Test" into one assignment for engine tasks.
- **Review Requirements**: Intense Codex review. Requires baseline regression checks, future-leak audits, and edge-case scrutiny.
- **Verification Commands**: Full pytest suite, performance profiling scripts, strict assertion limits (`pytest tests/test_backtest_engine.py -v`).
- **Routing Rule**: Prefer DeepSeek for first-pass implementation. Anti-Gravity may only touch Tier 4 docs, fixtures, or narrow follow-up fixes explicitly approved by Codex.

### Tier 5: Release & Git Operations
- **Scope**: `git init`, massive refactors, dependency bumps, version tagging.
- **Recommended Batch Size**: Strictly one step at a time.
- **Broadening Rule**: Never batch.
- **Review Requirements**: Human/Codex approval required before execution.
- **Verification Commands**: `git status`, pipeline runs.
- **Safety Rule**: A release or Git task may prepare instructions or safe files such as `.gitignore`, but commands that mutate repository history or initialize version control must be assigned separately.

## Reusable Assignment Template for Broader (Tier 1/2) Tasks

```markdown
# Agent Queue - Current Task

## Current Task
[Task ID] - [Descriptive Title]

## Scope

### Do
- [Goal 1 - e.g., Update 3 related passive widgets]
- [Goal 2 - e.g., Ensure layout stretches appropriately]
- Update `docs/task_board.md` and `docs/changelog.md`.
- Write one completion report in `docs/agent_reports/`.

### Do Not
- Do not modify `engine/`, `core/`, or `repository/` layers.
- Do not wire active callbacks yet.

## Files Likely Involved
- [File 1]
- [File 2]

## Acceptance Criteria
1. UI components render correctly.
2. No logic leaks into widgets.
3. Smoke tests pass.

## Verification
Run: `powershell -ExecutionPolicy Bypass -File scripts/run_smoke.ps1 -Quick`
```
