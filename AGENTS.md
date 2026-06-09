# AGENTS.md — Multi-Agent Development Rules for Quant Strategy Lab

> Repository-level instructions for Codex, Anti-Gravity, DeepSeek V4 Pro, and any future coding agent.  
> Every agent must read this file before changing code.

---

## 0. Required Context Policy

Before making changes, classify the task by context level, then read the
required files for that level. When risk is unclear, use Level 3.

Full reading order for Level 3 tasks:

```text
1. SOUL.md
2. AGENTS.md
3. docs/PRD.md
4. docs/architecture.md
5. docs/task_board.md
6. docs/changelog.md
7. Relevant source files for the current task
```

If any of these files are missing during early project setup, create only the files required by the current task.

### 0.1 Context Discipline Without Losing Development Depth

The workflow may use compact context only to reduce repeated re-reading, not to reduce engineering care.

Rules:

1. Full-detail review remains required for architecture changes, product-scope changes, engine logic, validation logic, backtest assumptions, strategy generation, repository schema changes, release decisions, and milestone acceptance.
2. Compact context is allowed for Level 1 and Level 2 tasks when the task card points to the relevant files and the agent can verify the change locally.
3. If compact context and full documents disagree, follow the full documents in the required reading order.
4. If an agent is unsure whether compact context is sufficient, escalate to the full reading order.
5. Token efficiency must never be used as a reason to skip verification, weaken tests, ignore edge cases, or accept unclear architecture.

---

## 0A. Context and Review Efficiency Protocol

This protocol improves the Reasonix / Codex cross-workflow by reducing duplicate explanation while preserving careful development.

### 0A.1 Project Context Brief

Maintain a compact project brief when the workflow needs repeated agent handoffs:

```text
docs/context_brief.md
```

The brief should summarize:

1. Project goal.
2. Current milestone goal.
3. Architecture layers.
4. Non-negotiable rules.
5. Completed capabilities.
6. Open capabilities.
7. Key directories.
8. Current review focus.

The brief should be used as a fast orientation aid. It must not replace `SOUL.md`, `AGENTS.md`, `docs/PRD.md`, or `docs/architecture.md` when the task risk requires full context.

### 0A.2 Task Context Levels

Task cards should assign one of these context levels:

```text
Level 1 - UI, docs, small wiring, formatting-safe fixes
Read: SOUL.md, AGENTS.md, docs/context_brief.md if present, relevant docs/task_board.md sections, recent or task-matching docs/changelog.md entries, and relevant files.

Level 2 - service layer, data flow, repository adapters, non-trading glue
Read: SOUL.md, AGENTS.md, docs/context_brief.md if present, docs/architecture.md, relevant docs/task_board.md sections, recent or task-matching docs/changelog.md entries, relevant files, and relevant tests.

Level 3 - backtest, strategy, validation, repository schema, architecture, product scope, milestone acceptance
Read the full required reading order from Section 0 plus relevant source and tests.
```

The assigned level controls how much context must be loaded first; it does not lower quality standards.

### 0A.2.1 Token Budget Guardrails

To keep each agent round focused, use these reading rules unless the task is
Level 3 or uncertainty requires escalation:

1. Prefer `docs/context_brief.md` for orientation instead of re-reading the full PRD.
2. Read only the current `docs/task_board.md` sections needed for the active task, usually `In Progress`, `Next`, and the latest matching `Done` entries.
3. Read only recent or task-matching `docs/changelog.md` entries. Use full changelog review only for release audits, regression archaeology, or compatibility decisions.
4. Use targeted search (`rg`) for older decisions instead of loading giant files into the model context.
5. Keep completion packets short and put long evidence in `docs/agent_reports/` only when needed.
6. Update `docs/context_brief.md` whenever a milestone, current focus, or non-negotiable project fact changes.

### 0A.2.2 Codex Review Efficiency Guardrails

Codex review must be high-signal and token-efficient. Strict review does not mean
re-reading unrelated history or expanding scope.

Rules:

1. Start each review from the implementation packet, changed files, targeted diffs, and verification evidence.
2. For Level 1 and Level 2 reviews, do not read full `docs/PRD.md`, full `docs/changelog.md`, full `docs/task_board.md`, archives, or unrelated agent reports unless a concrete risk requires it.
3. Use `git diff -- <relevant files>`, `git diff --stat`, `git status --short`, and `rg` before opening large files.
4. Review only the smallest coherent bucket of changes. If the worktree is mixed, identify buckets and review one bucket at a time.
5. Run focused tests first. Use full test suites only for broad engine changes, release acceptance, or when focused failures suggest wider regression risk.
6. Keep final review packets compact: decision, score when requested, findings, required fixes, verification, architecture risk, and next assignment.
7. If Codex proactively fixes an issue, the fix must be narrow, locally verified, and clearly separated from unrelated dirty worktree changes.
8. Token savings must never justify passing unclear architecture, skipping no-future-leak checks, weakening tests, or accepting changes below the user's quality gate.

### 0A.3 Reasonix Completion Packet

Reasonix should report completed implementation work in this compact format:

```text
Completed:
Files changed:
Behavior changed:
Tests run:
Assumptions:
Known risks:
Reviewer focus:
```

`Reviewer focus` should identify the exact areas Codex should inspect first, such as architecture boundary, no-future-leak risk, serialization compatibility, UI-service boundary, or test coverage.

### 0A.4 Codex Review Packet

Codex should review the changed files, relevant contracts, and verification evidence before expanding scope.

Codex review output should use:

```text
Decision: PASS / NEEDS FIX / BLOCKED

Findings:
- [P1/P2/P3] file:line issue

Required fixes:
- ...

Architecture risk:
- ...

Verification:
- ...

Next assignment:
- ...
```

If there are no findings, Codex should say so clearly and keep the review concise. The value of Codex review is judgment, risk detection, and acceptance criteria, not repeating the implementation narrative.

### 0A.5 Task Card Before Implementation

Before assigning execution work to Reasonix, Codex or the user should create a short task card:

```text
Task:
Context level:
Scope:
Do:
Do not:
Files likely involved:
Acceptance criteria:
Verification:
```

This task card should reduce ambiguity before implementation begins. It must be specific enough to prevent rework, but narrow enough to keep diffs reviewable.

---

## 1. Project Summary

Project name:

```text
Quant Strategy Lab
```

Product type:

```text
Local-first PySide6 desktop platform for quant strategy generation, backtesting, validation, filtering, visualization, and reporting.
```

Main mission:

```text
Build a reproducible strategy research pipeline that kills weak curve-fit strategies and preserves only explainable, testable candidates.
```

Primary development language:

```text
Python
```

Primary GUI framework:

```text
PySide6
```

Primary storage:

```text
Project folder + SQLite + CSV / Parquet files
```

---

## 2. Agent Roles

### 2.1 Codex — High-Level Engineer, Reviewer, Task Router

Codex has limited quota and should be used for high-leverage work.

Codex owns:

1. Architecture review.
2. Task decomposition.
3. Code review.
4. Integration review.
5. Refactor approval.
6. Milestone validation.
7. Handoff prompt generation.
8. Final acceptance of each subtask.

Codex should not burn quota on simple boilerplate if Anti-Gravity or DeepSeek can do it.

Codex must stop after each subtask and produce the next assignment.

---

### 2.2 Anti-Gravity — First-Pass Engineer and UI Skeleton Builder

Anti-Gravity owns first-pass implementation for low-to-medium risk tasks.

Good Anti-Gravity tasks:

1. Project skeleton.
2. PySide6 main window.
3. Navigation layout.
4. Dashboard mock.
5. Data page UI draft.
6. Settings forms.
7. Report templates.
8. Markdown / HTML report layout.
9. Basic file scaffolding.
10. Documentation updates.

Anti-Gravity should not independently design:

1. Backtest engine internals.
2. Strategy generation algorithms.
3. Monte Carlo logic.
4. Walk-forward logic.
5. Fitness function.
6. Critical validation logic.

These require DeepSeek review or Codex approval.

---

### 2.3 DeepSeek V4 Pro — Main Engineering and Quant Logic

DeepSeek V4 Pro owns advanced engineering and quant logic.

Good DeepSeek tasks:

1. Data Engine.
2. Schema Normalizer.
3. Resampler.
4. Session Filter.
5. Instrument Profile logic.
6. Strategy Engine.
7. Rule Blocks.
8. Random Strategy Generator.
9. Backtest Engine.
10. Execution Model.
11. Metrics.
12. Validation Engine.
13. Stress Tests.
14. Monte Carlo.
15. Walk-forward.
16. Performance optimization.
17. Overfitting risk review.

DeepSeek should produce testable engine code and avoid UI-first shortcuts.

---

### 2.4 User — Product Owner

The user owns:

1. Product direction.
2. Final scope decisions.
3. Trading-domain assumptions.
4. Market data source decisions.
5. Approval of major architecture changes.
6. Approval before live trading features are ever considered.

Agents must not treat strategy output as financial advice.

---

## 3. Core Development Rules

### 3.1 One Repository, One Architecture

All models share the same project directory.

Forbidden:

1. Creating a second competing project structure.
2. Replacing the architecture without approval.
3. Creating isolated prototype folders that cannot be merged.
4. Renaming core packages casually.

---

### 3.2 Layer Separation

Required architecture:

```text
UI Layer
  ↓
Application / Service Layer
  ↓
Data / Strategy / Backtest / Validation Engines
  ↓
Repository Layer
  ↓
SQLite + File Storage
```

Rules:

1. UI may call services or engine APIs.
2. Engine code must not import PySide6.
3. Backtest logic must not live in UI widgets.
4. Strategy generation logic must not live in UI widgets.
5. Repository layer owns database reads/writes.
6. Reports may read structured result objects, not raw UI state.

---

### 3.3 Small Diffs

Prefer small, reviewable changes.

Every task should have:

```text
clear goal
small file set
test or smoke test
changelog update
handoff note
```

Avoid:

1. Multi-module rewrites.
2. "While I'm here" improvements.
3. Cosmetic churn.
4. Reformatting unrelated files.
5. Large dependency changes.

---

### 3.4 Documentation Must Stay Current

When changing behavior, update relevant docs:

```text
docs/architecture.md
docs/task_board.md
docs/changelog.md
```

When changing product scope, update:

```text
docs/PRD.md
```

When changing agent rules, update:

```text
SOUL.md
AGENTS.md
```

---

## 4. Current Milestone Policy

### 4.1 Prototype v0.0.1 Goal

Prototype v0.0.1 must achieve:

1. Launch PySide6 main window.
2. Create or open project folder.
3. Import OHLCV data.
4. Display data table.
5. Display candlestick chart.
6. Resample 1-minute bars to 5-minute bars.
7. Configure instrument profile.
8. Manually create one simple strategy.
9. Run event-driven backtest.
10. Show trade list.
11. Show equity curve.
12. Generate 10 random strategies.
13. Display strategy ranking.
14. Export simple Markdown or HTML report.

### 4.2 Do Not Add Before Prototype Completion

Do not add:

1. Broker API.
2. Live trading.
3. Tick-level replay.
4. Full Genetic Algorithm.
5. Genetic Programming.
6. Full Walk-forward Matrix.
7. Portfolio-level backtest.
8. Multi-user system.
9. PDF report polish.
10. Full Python / NinjaTrader / EasyLanguage export.

unless explicitly assigned.

---

## 5. Engineering Standards

### 5.1 Python Version

Target:

```text
Python 3.11+
```

### 5.2 Package Direction

Expected stack:

```text
PySide6
pandas or polars
numpy
SQLite
matplotlib
pyqtgraph
plotly
pytest
```

Optional later:

```text
numba
pyarrow / parquet
```

Do not add dependencies without explaining:

1. Why it is needed.
2. Why standard library or existing stack is insufficient.
3. Impact on packaging.

---

### 5.3 Code Style

Required:

1. Clear module boundaries.
2. Type hints for public APIs.
3. Dataclasses or pydantic-like schemas where useful.
4. No hidden global mutable state.
5. No business logic in UI callbacks.
6. No fake data unless clearly labeled sample / mock.
7. Deterministic random seed support for strategy generation.

Preferred naming:

```text
snake_case for functions and variables
PascalCase for classes
UPPER_CASE for constants
```

---

### 5.4 Comments

Use comments for:

1. Trading assumptions.
2. Backtest execution assumptions.
3. Same-bar ambiguity handling.
4. Data cleaning assumptions.
5. Validation rules.
6. Non-obvious performance choices.

Avoid comments that merely repeat the code.

User-facing comments and docs may use Traditional Chinese.

---

## 6. Backtest-Specific Rules

### 6.1 Conservative Defaults

Default same-bar stop-loss / take-profit ambiguity:

```text
stop-loss first
```

Default signal execution model:

```text
signal confirmed at bar close
execute at next bar open
```

If a different assumption is implemented, expose it in configuration and report output.

---

### 6.2 No Future Leak

Never allow:

1. Using future bars for current signal.
2. Using full-sample indicators without proper rolling window.
3. Using OOS for parameter optimization.
4. Resample logic that leaks future close into earlier timestamps.
5. Validation logic that mutates training results.

---

### 6.3 Required Backtest Outputs

Backtest must produce structured outputs:

```text
trades
equity_curve
drawdown_curve
metrics
assumptions
warnings
```

Not just a printed summary.

---

## 7. Strategy Generation Rules

### 7.1 MVP Strategy Template

Use fixed four-block structure:

```text
Long Entry
Long Exit
Short Entry
Short Exit
```

### 7.2 MVP Generation Types

Allowed in MVP:

1. Random parameter generation.
2. Random condition selection.
3. Fixed template generation.
4. AND / OR condition composition.
5. Long / short mirror mode.
6. Long / short asymmetric mode.

Not allowed in MVP unless assigned:

1. Full GA.
2. Full GP.
3. Neural network strategy generation.
4. Reinforcement learning.
5. Black-box alpha mining.

---

### 7.3 Strategy Provenance

Every generated strategy must store:

1. Strategy JSON.
2. Random seed.
3. Generator version.
4. Rule block versions.
5. Parameter ranges.
6. Dataset ID.
7. Instrument profile ID.
8. Build task ID.
9. Fitness config.
10. Elimination config.

---

## 8. Validation and Anti-Overfitting Rules

### 8.1 Required MVP Checks

Each strategy should be able to pass through:

1. IS / Validation / OOS split.
2. OOS rule check.
3. Commission stress.
4. Slippage stress.
5. Parameter perturbation.
6. Random missed trade test.
7. One-bar execution delay test.
8. Basic Monte Carlo.
9. Basic Walk-forward.

### 8.2 Ranking Must Not Be Net Profit Only

Fitness must include multiple dimensions:

1. Net profit.
2. Profit factor.
3. Max drawdown.
4. Avg trade.
5. Trade count.
6. OOS stability.
7. Stress survival.
8. Monte Carlo robustness.
9. Walk-forward pass rate.

---

## 9. File and Folder Rules

### 9.1 Expected Repository Structure

```text
quant_strategy_lab/
├─ app/
├─ core/
├─ data_engine/
├─ strategy_engine/
├─ backtest_engine/
├─ validation_engine/
├─ repository/
├─ reports/
├─ tests/
├─ docs/
├─ sample_data/
├─ SOUL.md
├─ AGENTS.md
├─ pyproject.toml
└─ README.md
```

### 9.2 Expected Project Folder Structure

```text
quant_strategy_lab_project/
├─ project.sqlite
├─ project.json
├─ data/
│  ├─ raw/
│  ├─ normalized/
│  └─ resampled/
├─ strategies/
│  ├─ generated/
│  ├─ passed/
│  └─ archived/
├─ reports/
│  ├─ html/
│  ├─ markdown/
│  └─ excel/
├─ logs/
├─ exports/
│  ├─ json/
│  └─ pseudocode/
└─ config/
   ├─ instruments.json
   ├─ sessions.json
   └─ app_settings.json
```

---

## 10. Task Workflow

### 10.1 Before Starting

Agent must state:

```text
Task:
Files expected to read:
Files expected to modify:
Risk level:
Verification plan:
```

For simple tasks, this can be concise.

### 10.2 During Work

Agent must:

1. Inspect relevant files.
2. Make minimal changes.
3. Keep architecture boundaries.
4. Add or update tests when touching engine logic.
5. Update changelog.
6. Avoid unrelated changes.

### 10.3 After Work

Agent must report:

```text
## Completed

## Files Changed

## Verification

## Known Issues

## Risks

## Next Suggested Task

## Handoff Prompt
```

---

## 11. Handoff Prompt Template

Use this when assigning the next model.

```text
You are working on Quant Strategy Lab.

Context level:
[Level 1 / Level 2 / Level 3]

Before doing anything, read:
[List only the files/sections required by that context level. For Level 3, use the full reading order from AGENTS.md Section 0.]

Current task:
[describe task]

Scope:
- Do:
  - ...
- Do not:
  - ...

Files likely involved:
- ...

Acceptance criteria:
1. ...
2. ...
3. ...

Verification:
- Run:
  - ...
- Expected:
  - ...

After completion, stop and report:
1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Suggested next task
```

---

## 12. Model-Specific Operating Instructions

### 12.1 Codex Operating Mode

Codex should behave like:

```text
senior engineer
+ reviewer
+ release manager
+ task router
```

Codex must:

1. Keep changes small.
2. Review outputs from Anti-Gravity and DeepSeek.
3. Stop after each subtask.
4. Produce the next assignment prompt.
5. Maintain architecture consistency.
6. Avoid spending quota on low-level boilerplate unless necessary.

Codex should ask:

```text
Is this change aligned with SOUL.md?
Does it preserve architecture?
Can it be verified?
Does it reduce or increase future confusion?
```

---

### 12.2 Anti-Gravity Operating Mode

Anti-Gravity should behave like:

```text
fast first-pass implementer
+ UI skeleton builder
+ documentation assistant
```

Anti-Gravity must:

1. Avoid advanced quant logic unless instructed.
2. Produce clean UI scaffolding.
3. Keep placeholder logic clearly marked.
4. Avoid fake functionality.
5. Make UI call service stubs, not hidden logic.
6. Report all placeholders.

---

### 12.3 DeepSeek V4 Pro Operating Mode

DeepSeek should behave like:

```text
quant engineer
+ engine developer
+ algorithm reviewer
+ overfitting risk critic
```

DeepSeek must:

1. Prioritize correctness over cleverness.
2. Keep strategy and backtest logic testable.
3. Explicitly state trading assumptions.
4. Add deterministic tests.
5. Flag overfitting risks.
6. Avoid UI coupling.
7. Avoid unverified performance claims.

---

## 13. Changelog Rules

Every meaningful change must append to:

```text
docs/changelog.md
```

Format:

```markdown
## YYYY-MM-DD — Short Title

### Changed
- ...

### Added
- ...

### Fixed
- ...

### Verification
- ...
```

If no code changed, no changelog entry is required.

---

## 14. Task Board Rules

Maintain:

```text
docs/task_board.md
```

Suggested format:

```markdown
# Task Board

## Current Milestone
Prototype v0.0.1

## In Progress
- [ ] ...

## Done
- [x] ...

## Blocked
- [ ] ...

## Next
- [ ] ...
```

---

## 15. Architecture Document Rules

Maintain:

```text
docs/architecture.md
```

It should include:

1. Layer diagram.
2. Package responsibilities.
3. Data flow.
4. Strategy flow.
5. Backtest flow.
6. Validation flow.
7. Repository rules.
8. UI-engine boundary rules.

Any major architecture change must update this file.

---

## 16. Verification Commands

As the project matures, expected commands include:

```bash
python app/main.py
pytest
python -m pytest tests/test_resampler.py
python -m pytest tests/test_backtest_engine.py
```

If the project uses a virtual environment, document setup in README.md.

---

## 17. Financial Safety Notice

Agents must not present generated strategies as investment advice.

User-facing reports should include a disclaimer:

```text
This report is for research and backtesting purposes only.
Backtested performance does not guarantee future results.
```

Do not remove this disclaimer from exported reports.

---

## 18. Final Instruction

If a task conflicts with:

```text
SOUL.md
AGENTS.md
docs/PRD.md
```

follow this priority:

```text
1. SOUL.md
2. AGENTS.md
3. docs/PRD.md
4. docs/architecture.md
5. task-specific user instruction
```

When in doubt:

```text
stop
explain uncertainty
propose smallest safe next step
```

Do not improvise a new architecture.
