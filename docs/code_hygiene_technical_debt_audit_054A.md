# Code Hygiene and Technical Debt Audit (Task 054A)

## Overview
As Quant Strategy Lab has accrued sophisticated backtest, optimization, and risk-management functionalities (Tasks 052-053), accumulated technical debt and hygiene gaps pose maintainability and trust risks. This document categorizes these findings and proposes a remediation roadmap.

## P0: Correctness or Trust Risk
These items impact the financial validity or source-truth reliability of the platform.

### 1. Unresolved Quant/Research Assumptions
- **File(s)**: `core/models/`, `validation_engine/`, `backtest_engine/`
- **Issue**: Several critical quant limitations remain unresolved:
  - Walk-forward analysis (WFA) uses sliding Out-of-Sample (OOS) windows but lacks true re-optimization integration.
  - Monte Carlo scope remains narrow (trade randomization) without full parameter/data permutation.
  - GA/GP fitness lacks a complexity penalty (parsimony pressure), risking overfit curve-generation.
  - Cost models (commission/slippage) are basic multipliers.
  - MTF (Multi-Timeframe) candle evaluation lacks complete higher-timeframe alignment handling across session gaps.
- **Why it matters**: Strategy generation risks producing curve-fit outputs without robust constraints.
- **Suggested Future Task**: Task 056 - Advanced Quant Validation and Re-optimization Design.
- **Safety**: Needs extensive architectural design before implementation.

### 2. Lack of Version Control
- **File(s)**: Entire repository.
- **Issue**: The project folder lacks a `git` repository initialize.
- **Why it matters**: Severe risk of code loss, rollback inability, and compromised multi-agent accountability.
- **Suggested Future Task**: Task 055 - Git Initialization and Repository Setup.
- **Safety**: Safe to fix immediately via basic terminal setup.

## P1: Maintainability or Compatibility Risk
These items affect code clarity, module coupling, and future expansion safety.

### 3. Weak Test Assertions
- **File(s)**: `tests/test_strategy_json_import_results_wiring.py`, `tests/test_backtest_engine.py`
- **Issue**: Several tests merely evaluate whether a process completes without throwing exceptions ("does not crash") or use broad evaluations (e.g., `assert len(results) >= 0`) rather than deterministic value matching.
- **Why it matters**: Silent behavioral regressions might occur without failing the test suite.
- **Suggested Future Task**: Task 054C - Test Suite Assertion Hardening.
- **Safety**: Safe to fix immediately.

### 4. Boilerplate RiskManagement Parsing
- **File(s)**: `repository/strategy_repo.py`, `app/services/report_service.py`
- **Issue**: The fallback instantiation style for `RiskManagement()` inside validation blocks is duplicated and verbose.
- **Why it matters**: Repetitive defensive parsing logic makes schema evolution harder and invites bugs.
- **Suggested Future Task**: Task 054D - Strategy Serialization Service Abstraction.
- **Safety**: Needs minor design/refactoring boundaries.

## P2: Documentation and Test Hygiene
These items affect readability and accurate historical tracking.

### 5. Mojibake / Corrupted Encoding
- **File(s)**: `docs/changelog.md`, `docs/task_board.md`
- **Issue**: Em-dashes and special unicode characters have corrupted into `??` or similar replacement strings (e.g., `Task 053C ??Backtest`).
- **Why it matters**: Unprofessional appearance and loss of historical readability.
- **Suggested Future Task**: Task 054B - Documentation Hygiene and Mojibake Cleanup.
- **Safety**: Safe to fix immediately.

### 6. Duplicated and Inconsistent Task Board State
- **File(s)**: `docs/task_board.md`
- **Issue**: Task groups contain conflicting "Done" sections, and some completed items overlap.
- **Why it matters**: Project tracking becomes confused, risking duplicated effort by Codex.
- **Suggested Future Task**: Task 054B - Documentation Hygiene and Mojibake Cleanup.
- **Safety**: Safe to fix immediately.

### 7. Stale Design Claims
- **File(s)**: `docs/backtest_performance_optimization_design_052A.md`
- **Issue**: Contains stale claims regarding "Phase 4 Vectorized Signal Masks" and Genetic Programming (GP) scope that were explicitly deferred or descoped.
- **Why it matters**: Future agents might assume these features are active or mandated.
- **Suggested Future Task**: Task 054B - Documentation Hygiene and Mojibake Cleanup.
- **Safety**: Safe to fix immediately.

### 8. Acceptance Note Overconfidence
- **File(s)**: `docs/backtest_stop_take_profit_acceptance_053C.md`
- **Issue**: Although just created, the language may inadvertently imply high reliability. Needs reviewing for semantic humility per system instructions.
- **Why it matters**: Maintains project tone and realistic risk acknowledgment.
- **Suggested Future Task**: Task 054B - Documentation Hygiene and Mojibake Cleanup.
- **Safety**: Safe to fix immediately.

## P3: Cosmetic Cleanup
These items are minor nitpicks.

### 9. Inline / Local Imports
- **File(s)**: `backtest_engine/runner.py`
- **Issue**: `from core.models.strategy import RiskManagement` is imported locally within `run_backtest()` to bypass circular imports or lazy resolution.
- **Why it matters**: Minor performance hit per call and cluttered function bodies.
- **Suggested Future Task**: Task 054C - Test Suite Assertion and Local Import Hardening.
- **Safety**: Safe to fix immediately.

---

## Remediation Roadmap (Next 3 Tasks)
To systematically eliminate this technical debt without destabilizing the application, the following tasks should be executed sequentially:

1. **Task 054B - Documentation Hygiene and Mojibake Cleanup** (Safe)
   - *Scope*: Fix all UTF-8 corruptions (`??`) in markdown files, consolidate `task_board.md` structures, align changelog timelines, and sanitize overconfident terminology in 052/053 design docs.

2. **Task 054C - Test Assertions and Local Import Hardening** (Safe)
   - *Scope*: Rewrite "does not crash" tests into strict deterministic matchers. Extract inline local imports from `runner.py` by refactoring dependency graphs gracefully.

3. **Task 056A - True Walk-Forward Re-optimization Design Only** (Architecture)
   - *Scope*: Draft the structural data-flow changes required to integrate active parameter re-optimization during the sliding WFA windows, addressing the top P0 quant risk.
