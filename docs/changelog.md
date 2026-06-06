# Changelog

## 2026-06-06 - Task 056H-Impl Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056h-impl_remove-best-n-trades-stress-config-controls_codex-review.md` accepting the remove-best-N stress config controls with score 9.1 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056I.
- Updated `docs/task_board.md` to queue remove-best-N feature acceptance smoke coverage.

### Verification
- Ran focused UI wiring tests: 7 passed.
- Ran the full test suite: 1016 passed, 1 pre-existing warning.
- Ran `git diff --check`.
- Manually confirmed threshold spinbox step and decimals.

## 2026-06-06 - Task 056H-Impl: Remove Best N Trades Stress Config Controls

### Added
- `app/ui/main_window.py`: Added Validate page controls near WFE checkbox — enable checkbox, N spinbox (min 1, max 50, default 3), threshold double spinbox (min 0.01, max 1.00, default 0.30, step 0.05). Spinboxes disabled when checkbox is unchecked. Values passed into `PipelineConfig()`.
- `tests/test_wfe_ui_wiring.py`: Added 4 focused tests (controls exist + defaults, spinbox enable/disable toggle, unchecked passes False, checked passes custom values).
- Existing WFE checkbox behavior unchanged.

### Verification
- Focused UI wiring tests: 7 passed (3 WFE + 4 new).
- Full suite: 1016 passed, 1 pre-existing warning.
- `git diff --check` passes.
- Engine/UI separation preserved: UI reads controls -> PipelineConfig -> pipeline service.

## 2026-06-06 - Task 056H Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056h_remove-best-n-trades-stress-config-surface-design_codex-review.md` accepting the remove-best-N stress config surface design with score 8.8 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056H-Impl.
- Updated `docs/task_board.md` to queue remove-best-N stress config controls.

### Verification
- Reviewed `docs/remove_best_n_trades_config_surface_design_056H.md`.
- Confirmed current `PipelineConfig` construction and WFE checkbox wiring in `app/ui/main_window.py`.
- Ran `git diff --check`.

## 2026-06-06 - Task 056H: Remove Best N Trades Stress Config Surface Design Only

### Added
- Created `docs/remove_best_n_trades_config_surface_design_056H.md` — design for where users should enable/configure `remove_best_n_trades` stress.
- Recommend adding a minimal header group on the Validate page (checkbox + n spinbox + threshold spinbox), following the existing WFE checkbox pattern.
- Engine/UI separation preserved: UI reads controls → PipelineConfig → pipeline service → engine.
- Off by default; settings only active when checkbox is checked.

### Changed
- Updated `docs/task_board.md` (Task 056H -> Done).

### Verification
- No production code changed (design-only).
- `git diff --check` passes.

## 2026-06-06 - Task 056G-Impl/Fix/Fix2 Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056g-impl-fix2_escape-html-stress-detail-pnl-loss-value_codex-review.md` accepting the stress result details display implementation series with score 9.2 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056H.
- Updated `docs/task_board.md` to queue remove-best-N-trades stress config surface design.

### Verification
- Ran report tests: 30 passed.
- Ran combined validation summary and report tests: 41 passed.
- Ran the full test suite: 1012 passed, 1 pre-existing warning.
- Ran `git diff --check`.
- Manually confirmed HTML stress-detail output escapes malicious `<script>`, `<b>`, and `<img>` payloads.

## 2026-06-06 - Task 056G-Impl-Fix2: Escape HTML Stress Detail PnL Loss Value

### Fixed
- `reports/generator.py`: Escaped `pnl_loss` value in HTML stress-detail div — previously only escaped `removed`, `total`, `n_val`, `threshold` but not the non-float fallback of `pnl_loss_ratio`.
- `tests/test_report_export.py`: Strengthened `test_html_stress_detail_values_escaped` with `<img src=x>` payload as `pnl_loss_ratio`, asserting raw tag does not appear and escaped equivalent does.

### Verification
- Focused report tests: 30 passed.
- Combined widget + report: 41 passed.
- Full suite: 1012 passed, 1 warning.
- `git diff --check` passes.

## 2026-06-06 - Task 056G-Impl-Fix Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056g-impl-fix_html-stress-detail-value-escaping_codex-review.md` marking Task 056G-Impl-Fix as needing one more HTML escaping fix before acceptance.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056G-Impl-Fix2.
- Updated `docs/task_board.md` to queue the `pnl_loss` HTML escaping fix.

### Verification
- Ran focused report tests: 30 passed.
- Ran `git diff --check`.
- Manual HTML probe confirmed `n_val` and `threshold` are escaped, but non-float `pnl_loss_ratio` can still render raw `<img>` input.

## 2026-06-06 - Task 056G-Impl-Fix: HTML Stress Detail Value Escaping

### Fixed
- `reports/generator.py`: HTML-escaped all dynamic values (`removed`, `total`, `n_val`, `threshold`) in the `stress-detail` div for `remove_best_n_trades`. Previously bare values could render raw HTML from malformed validation dicts.
- `tests/test_report_export.py`: Added `test_html_stress_detail_values_escaped` asserting `<script>` and `<b>` payloads are escaped to `&lt;script&gt;` and `&lt;b&gt;`.

### Verification
- Focused report tests: 30 passed.
- Combined widget + report tests: 41 passed.
- Full suite: 1012 passed, 1 pre-existing warning.
- `git diff --check` passes.

## 2026-06-06 - Task 056G-Impl Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056g-impl_stress-result-details-display-implementation_codex-review.md` marking Task 056G-Impl as needing an HTML detail escaping fix before acceptance.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056G-Impl-Fix.
- Updated `docs/task_board.md` to queue the HTML stress detail value escaping fix.

### Verification
- Ran focused validation summary and report tests: 40 passed.
- Ran `git diff --check`.
- Manual HTML probe confirmed warning text is escaped but stress-detail values can still render raw `<script>` and `<b>` input.

## 2026-06-06 - Task 056G-Impl: Stress Result Details Display Implementation

### Added
- `app/widgets/validation_summary.py`: Extended stress rendering to show inline sub-lines for `remove_best_n_trades` — display `n`, `removed_count`, `surviving_count`, `pnl_loss_ratio`, `threshold["max_pnl_loss"]`, and `warnings` when present.
- `reports/generator.py`: Extended both `_format_markdown_validation()` and `_format_html_validation()` stress loops with matching sub-lines. HTML warnings are escaped.
- `tests/test_validation_summary.py`: 2 new tests (detail sub-lines present for remove_best_n, absent for basic tests).
- `tests/test_report_export.py`: 3 new tests (markdown detail lines, HTML detail + escaping, basic tests no detail).
- Existing stress tests (commission, slippage, delay, perturbation) display behavior unchanged.

### Verification
- Focused tests: 40 passed (validation_summary + report_export).
- Full suite: 1011 passed, 1 pre-existing warning.
- `git diff --check` passes.
- No engine, pipeline, or layout changes.

## 2026-06-06 - Task 056G Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056g_stress-result-details-reporting-surface-design_codex-review.md` accepting the stress result details reporting surface design with score 9.0 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056G-Impl.
- Updated `docs/task_board.md` to queue stress result details display implementation.

### Verification
- Reviewed `docs/stress_result_details_surface_design_056G.md`.
- Confirmed current widget, Markdown, and HTML report stress rendering only shows stress name, pass/fail, and PnL degradation.
- Ran `git diff --check`.

## 2026-06-06 - Task 056G: Stress Result Details Reporting Surface Design Only

### Added
- Created `docs/stress_result_details_surface_design_056G.md` — design for surfacing optional stress `assumptions`, `warnings`, and `threshold` in UI and reports.
- Decision: show sub-lines only for stress tests with user-configured parameters (currently only `remove_best_n_trades`).
- Proposed widget display: inline sub-lines after each stress test showing `n`, `removed_count`, `pnl_loss_ratio`, and `warnings`.
- Proposed markdown/HTML: matching sub-lines in validation evidence section.
- Implementation surface: 3 files (widget + generator + tests), no engine changes.

### Changed
- Updated `docs/task_board.md` (Task 056G -> Done).

### Verification
- No production code changed (design-only).
- `git diff --check` passes.

## 2026-06-06 - Task 056F-Fix Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056f-fix_remove-best-n-trades-pipeline-assumptions-serialization_codex-review.md` accepting the pipeline assumptions serialization fix with score 8.9 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056G.
- Updated `docs/task_board.md` to queue stress result details reporting surface design.

### Verification
- Ran focused validation pipeline and stress tests: 47 passed.
- Ran the full test suite: 1006 passed, 1 pre-existing warning.
- Ran `git diff --check`.
- Manually confirmed serialized remove-best-N-trades output includes `assumptions`, `warnings`, and `threshold`.

## 2026-06-06 - Task 056F-Fix: Remove Best N Trades Pipeline Assumptions Serialization

### Fixed
- `app/services/validation_pipeline_service.py`: Extended `_stress_to_dict()` to include `assumptions`, `warnings`, and `threshold` fields from `StressTestResult` when present. Previously these were dropped.
- `tests/test_validation_pipeline_service.py`: Updated opt-in pipeline test to assert `assumptions["n"]`, `assumptions["removed_count"]`, `assumptions["pnl_loss_ratio"]`, and `warnings` are in the serialized dict.

### Verification
- Focused tests: 47 passed (pipeline + stress).
- Full suite: 1006 passed, 1 pre-existing warning.
- `git diff --check` passes.
- Backward-compatible: existing tests that access `test_name`, `passed`, `degradation`, `stressed_metrics` continue to pass.

## 2026-06-06 - Task 056F Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056f_remove-best-n-trades-pipeline-integration_codex-review.md` marking the pipeline integration as needing assumptions serialization before acceptance.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056F-Fix.
- Updated `docs/task_board.md` to queue the pipeline assumptions serialization fix.

### Verification
- Ran focused validation pipeline and stress tests: 47 passed.
- Ran `git diff --check`.
- Reviewed `_stress_to_dict()` and confirmed it drops `StressTestResult.assumptions`.

## 2026-06-06 - Task 056F: Remove Best N Trades Pipeline Integration

### Added
- `app/services/validation_pipeline_service.py`:
  - Imported `stress_remove_best_n_trades`.
  - Added `PipelineConfig` fields: `run_remove_best_n_trades_stress: bool = False`, `remove_best_n_trades_n: int = 3`, `remove_best_n_trades_degradation_threshold: float = 0.30`.
  - Wired `stress_remove_best_n_trades()` into stress section when flag is true.
- `tests/test_validation_pipeline_service.py`: Added 3 pipeline tests (default off, opt-in on, config fields in snapshot).

### Verification
- Focused tests: 47 passed (pipeline + stress).
- Full suite: 1006 passed, 1 pre-existing warning.
- `git diff --check` passes.
- Default pipeline behavior unchanged (flag defaults to false).

## 2026-06-06 - Task 056E-Impl-Fix Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056e-impl-fix_remove-best-n-trades-deterministic-test-hardening_codex-review.md` accepting the remove-best-N-trades engine implementation and deterministic test hardening with score 9.0 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056F.
- Updated `docs/task_board.md` to queue remove-best-N-trades pipeline integration.
- Added `.reasonix/` to `.gitignore` so local Reasonix tool artifacts do not pollute agent status output.

### Verification
- Ran focused stress tests: 26 passed.
- Ran the full test suite: 1003 passed, 1 pre-existing warning.
- Ran `git diff --check`.
- Confirmed deterministic tests now assert stressed PnL, degradation sign, `pnl_loss_ratio`, and pass/fail behavior without generated trade-count guards.

## 2026-06-06 - Task 056E-Impl-Fix: Remove Best N Trades Deterministic Test Hardening

### Fixed
- `tests/test_stress_test.py`: Replaced the weak conditional-guarded tests with a deterministic synthetic baseline helper `_make_synthetic_baseline()` built from explicit `Trade` objects and `compute_metrics()`.
- Removed all `if baseline.metrics["total_trades"] >= N:` conditional guards that could silently skip core assertions.
- Added `test_remove_best_n_trades_exact_metrics` asserting exact `degradation["total_pnl"] == -0.833333` and `pnl_loss_ratio == 0.833333` against a known synthetic baseline (PnLs: 100, 50, -20, -10).
- Threshold tests (`fails_above_threshold`, `passes_within_threshold`) now deterministically verify pass/fail without conditional guards.

### Verification
- Focused stress tests: 26 passed (15 existing + 11 new).
- Full suite: 1003 passed, 1 pre-existing warning.
- `git diff --check` passes.
- No implementation changes needed — engine code already correct.

## 2026-06-06 - Task 056E-Impl Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056e-impl_remove-best-n-trades-stress-engine-implementation_codex-review.md` marking the engine implementation as needing deterministic test hardening before acceptance.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056E-Impl-Fix.
- Updated `docs/task_board.md` to queue deterministic test hardening.

### Verification
- Ran focused stress tests: 25 passed.
- Ran the full test suite: 1002 passed, 1 pre-existing warning.
- Ran `git diff --check`.
- Manually confirmed the generated test baseline currently has only one trade, allowing conditional core assertions to skip.

## 2026-06-06 - Task 056E-Impl: Remove Best N Trades Stress Test Engine Implementation

### Added
- `validation_engine/stress_test.py`: Added `stress_remove_best_n_trades(baseline, *, n=3, degradation_threshold=0.30) -> StressTestResult`.
  - Sorts trades by PnL descending, removes top N, recomputes metrics via `compute_metrics()`.
  - Preserves existing degradation sign convention: `(stressed - base) / abs(base)`.
  - Separates `pnl_loss_ratio` into `assumptions` for pass/fail (positive = worse).
  - Handles zero trades (vaporous pass), insufficient trades (`passed=False`), `n == 0`, negative/invalid inputs (`ValueError`).
  - Does not mutate `baseline.trades`.
  - Engine-only: no pipeline config or wiring.
- `tests/test_stress_test.py`: Added 10 focused tests (deterministic, worsens PnL, fail above threshold, pass within threshold, zero trades, insufficient trades fail, no mutation, structured output, negative n raises, negative threshold raises).

### Verification
- Focused stress tests: 25 passed (15 existing + 10 new).
- Full suite: 1002 passed, 1 pre-existing warning.
- `git diff --check` passes.
- No pipeline, UI, report, or elimination code changed.

## 2026-06-06 - Task 056E-Fix2 Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056e-fix2_remove-best-n-trades-design-duplicate-cleanup_codex-review.md` accepting the duplicate cleanup with score 9.1 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056E-Impl.
- Updated `docs/task_board.md` to queue the engine-only remove-best-N-trades implementation.

### Verification
- Confirmed stale duplicate pipeline strings and the old `degration_threshold` typo are gone.
- Ran `git diff --check`.

## 2026-06-06 - Task 056E-Fix2: Remove Best N Trades Design Duplicate Cleanup

### Fixed
- Deleted stale duplicated pipeline sections from `docs/remove_best_n_trades_stress_design_056E.md`:
  - `### 4.1 PipelineConfig Addition` (old)
  - `### 4.2 Pipeline Wires After Existing Stress Tests` (old, included `degration_threshold` typo)
- The corrected deferred pipeline sections (`### 4.1` through `### 4.4`) remain.

### Verification
- `rg -n "degration|PipelineConfig Addition|Pipeline Wires After Existing Stress Tests"` returns no matches.
- No production code changed.
- `git diff --check` passes.

## 2026-06-06 - Task 056E-Fix Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056e-fix_remove-best-n-trades-stress-design-hardening_codex-review.md` marking the design hardening as needing a narrow duplicate-section cleanup.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056E-Fix2.
- Updated `docs/task_board.md` to queue the duplicate cleanup task.

### Verification
- Reviewed the corrected design and found stale duplicated pipeline sections plus the old `degration_threshold` typo still present.
- Confirmed no production code or tests changed.

## 2026-06-06 - Task 056E Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056e_remove-best-n-trades-stress-design_codex-review.md` marking the remove-best-N-trades stress-test design as needing hardening before implementation.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056E-Fix.
- Updated `docs/task_board.md` to queue the design hardening task.

### Verification
- Reviewed the design against existing stress-test degradation semantics, pipeline stress collection, and elimination stress pass-rate behavior.
- Confirmed no production code or tests changed.

## 2026-06-06 - Task 056E-Fix: Remove Best N Trades Stress Test Design Hardening

### Fixed
- **P1 (degradation sign)**: Corrected pass/fail to use a separate `pnl_loss_ratio` stored in `assumptions`, preserving the existing `degradation = (stressed - base) / abs(base)` convention from `_build_result()`.
- **P1 (implementation scope)**: Split implementation into two tasks: engine-only first (`stress_test.py` + tests), pipeline wiring later.
- **P2 (low-trade-count)**: Changed `0 < trades <= n` from vacuously pass to explicitly **fail** (`passed=False`, `assumptions["insufficient_trades"]=True`).
- **P3 (typo)**: Removed `degration_threshold` typo from deferred pipeline wiring example.
- Added `ValueError` for invalid `n < 0` and negative `degradation_threshold`.

### Changed
- Updated `docs/task_board.md` (Task 056E-Fix -> Done).

### Verification
- No production code changed (design-only hardening).
- `git diff --check` passes.

## 2026-06-06 - Task 056E: Remove Best N Trades Stress Test Design Only

### Added
- Created `docs/remove_best_n_trades_stress_design_056E.md` — design for `stress_remove_best_n_trades()`:
  - Function signature: `stress_remove_best_n_trades(baseline, *, n=3, degradation_threshold=0.30) -> StressTestResult`.
  - Operates on trade-list only (no re-backtest), fully deterministic (no randomness).
  - Removes top N trades by PnL descending, recomputes metrics on survivors.
  - Degradation-threshold pass/fail; vacuously passes with 0 or fewer-than-N trades.
  - 8 test plan cases + 3 PipelineConfig fields for future integration.

### Changed
- Updated `docs/task_board.md` (Task 056E -> Done).

### Verification
- No production code changed (design-only).
- `git diff --check` passes.

## 2026-06-06 - Task 056D Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056d_oos-metrics-display-surface-implementation_codex-review.md` accepting the OOS metrics display implementation with score 8.8 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056E.
- Updated `docs/task_board.md` to queue the remove-best-N-trades stress-test design task.

### Verification
- Ran focused validation summary, report export, and active dataset tests: 46 passed.
- Ran the full test suite: 992 passed, 1 pre-existing warning.
- Ran `git diff --check`.
- Reviewed that UI/report/log code does not compute OOS/IS stability ratios.

## 2026-06-06 - Task 056D: OOS Metrics Display Surface Implementation

### Added
- `app/widgets/validation_summary.py`: Added "OOS Metrics" card between Walk-Forward Matrix and Elimination. Reads `oos_metrics` dict only. Shows "No OOS data." when absent.
- `reports/generator.py`: Added OOS metrics line after Baseline in both `_format_markdown_validation()` and `_format_html_validation()`. Reads `vr.get("oos_metrics", {})` only. Silently skips when absent.
- `app/ui/main_window.py`: Added one-line OOS summary after elimination log line. Reads `result.oos_metrics` only.
- `tests/test_validation_summary.py`: Added 2 OOS card tests (displayed + missing placeholder).
- `tests/test_report_export.py`: Added 4 OOS report tests (markdown present/absent, HTML present/absent).

### Verification
- Focused tests: 46 passed (validation_summary + report_export + active_dataset).
- Full suite: 992 passed, 1 pre-existing warning.
- `git diff --check` passes.
- No ratio computation in UI/report/log code.

## 2026-06-06 - Task 056C-Fix Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056c-fix_oos-stability-reporting-surface-design-correction_codex-review.md` accepting the corrected OOS metrics display design with score 8.8 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056D.
- Updated `docs/task_board.md` to queue OOS metrics display implementation.

### Verification
- Reviewed the corrected design against the prior Codex blocker.
- Confirmed the next implementation scope displays only existing `oos_metrics` values and defers stability ratio display.
- Ran `git diff --check`.

## 2026-06-06 - Task 056C Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056c_oos-stability-reporting-surface-design_codex-review.md` marking the OOS stability reporting surface design as needing correction before implementation.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056C-Fix.
- Updated `docs/task_board.md` to queue the design correction.

### Verification
- Reviewed the design against validation pipeline, elimination, validation summary widget, report generator, and main-window log surfaces.
- Confirmed the current design would require ratio computation outside the engine/service layer unless narrowed or backed by structured output.

## 2026-06-06 - Task 056C-Fix: OOS Stability Reporting Surface Design Correction

### Changed
- Revised `docs/oos_stability_reporting_surface_design_056C.md`:
  - **Removed all stability ratio display requirements from UI/report surfaces.** Task 056D now displays only raw `oos_metrics` dict values (PnL, PF, Trades, Max DD, Win Rate) with no ratio computation.
  - **Deferred ratio display** until a structured engine/service-layer `oos_stability` payload exists with its own tests.
  - **Added acceptance criteria** for Task 056D (7 items covering widget, markdown, HTML, log panel, empty-data handling, test compatibility, git diff).
  - **Fixed garbled symbols** in data flow diagram — replaced Unicode box-drawing characters with plain ASCII brackets and arrows.
- Updated `docs/task_board.md` (Task 056C-Fix -> Done).

### Verification
- No production code changed (design-only correction).
- `git diff --check` passes.
- Engine/UI separation preserved: corrected design displays only pre-computed structured data.

## 2026-06-06 - Task 056B-Fix Codex Acceptance

### Added
- Created `docs/review_notes/2026-06-06_task-056b-fix_oos-stability-undefined-ratio_codex-review.md` accepting the undefined-ratio hardening fix with score 8.9 / 10.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056C.
- Updated `docs/task_board.md` to queue OOS stability reporting surface design.

### Verification
- Ran focused elimination, validation pipeline, and strategy service tests: 63 passed.
- Ran the full test suite without ignored tests: 986 passed, 1 pre-existing warning.
- Ran `git diff --check`.
- Ran a manual behavior probe confirming warn-by-default and `require_optional=True` fail behavior.

## 2026-06-06 - Task 056C: OOS Stability Reporting Surface Design Only

### Added
- Created `docs/oos_stability_reporting_surface_design_056C.md` tracing the current validation result flow through UI widget, report generator, and log panel.
- Findings:
  - `PipelineResult.oos_metrics` is computed but no consumer reads it.
  - ValidationSummary widget, report generator, and log panel all lack OOS metrics display.
- Proposed minimal implementation scope (Task 056D): add OOS Metrics card to widget + OOS metrics line to both report formatters + one-line OOS summary in log panel.
- Design decisions preserve engine/UI separation.

### Changed
- Updated `docs/task_board.md` (Task 056C → Done).

### Verification
- No production code changed (design-only).
- `git diff --check` passes.

## 2026-06-06 - Task 056B-Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056b_is-oos-stability-gate_codex-review.md` marking the IS/OOS stability gate as needing narrow hardening.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056B-Fix.
- Updated `docs/task_board.md` to queue the undefined-ratio and test-quality hardening task.

### Verification
- Ran focused elimination, validation pipeline, and strategy service tests.
- Ran the full test suite without ignored tests.
- Ran `git diff --check`.

## 2026-06-06 - Task 056B-Fix: OOS Stability Undefined Ratio and Test Quality Hardening

### Fixed
- `validation_engine/elimination.py`: Enabled stability rules no longer silently skip when the IS denominator is non-positive.
  - When a stability threshold is set but the ratio cannot be computed:
    (IS PF=0, IS DD=0, or IS avg trade=0):
    - Warn by default (skip rule).
    - Fail when `require_optional=True`.
- `tests/test_validation_pipeline_service.py`: Replaced vacuous `assert ... or True` with concrete assertions verifying OOS metrics presence and zero stability warnings.

### Added
- 8 new focused tests in `tests/test_elimination.py` for uncomputable ratios:
  - 3 warn-by-default tests (PF, DD, avg trade with zero IS denominator).
  - 3 `require_optional=True` fail tests.
  - 2 helper fixtures (`_is_zero_pf`, `_is_zero_dd`, `_is_zero_avg_trade`).

### Verification
- Focused tests: 63 passed.
- Full suite: 986 passed, 1 pre-existing warning (no ignores).
- `git diff --check` passes.

## 2026-06-06 - Task 056B: IS/OOS Stability Gate Implementation

### Added
- `validation_engine/elimination.py`:
  - Added `_compute_oos_stability(oos_metrics, is_metrics) -> dict` helper computing PF degradation, drawdown ratio, and avg trade degradation ratios.
  - Added 3 new `EliminationConfig` fields: `max_oos_pf_degradation`, `max_oos_drawdown_ratio`, `max_oos_avg_trade_degradation` (all `None` by default, backward-compatible).
  - Wired IS/OOS stability ratio rules into `evaluate_elimination()` — rules fire only when `oos_metrics` is provided and the threshold is set.
- `app/services/validation_pipeline_service.py`:
  - Added OOS backtest on `split.oos` (step 2.5) — runs `run_backtest(strategy, split.oos, ...)` when OOS segment exists.
  - Passes `oos_metrics=oos_baseline.metrics` into `evaluate_elimination()`.
  - Added `oos_metrics: dict | None` field to `PipelineResult` for UI/report inspection.
  - Graceful handling when OOS segment is empty or None (warning, no crash).
- `tests/test_elimination.py`: Added 13 focused tests covering all 3 stability rules (pass/fail), combined pass, missing OOS data (warn/fail), default None, and all-None skip.
- `tests/test_validation_pipeline_service.py`: Added 4 pipeline OOS data path tests (OOS metrics present, passed to elimination, default skip, empty segment warning).
- `tests/test_strategy_service_elimination_config.py`: Updated expected keys set to include 3 new stability fields.

### Verification
- Focused tests: 47 passed (test_elimination.py + test_validation_pipeline_service.py).
- Full test suite: 964 passed, 1 pre-existing warning (excluding pre-existing Qt abort in test_ga_build_wiring.py).
- `git diff --check` passes.

## 2026-06-06 - Task 056A-Fix-Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056a-fix_oos-stability-data-path-correction_codex-review.md` accepting the corrected OOS stability triage.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056B.
- Updated `docs/task_board.md` to queue IS/OOS stability gate implementation.

### Verification
- Reviewed corrected triage against validation pipeline and elimination code paths.
- Ran `git diff --check`.

## 2026-06-06 - Task 056A-Codex Review

### Added
- Created `docs/review_notes/2026-06-06_task-056a_next-validation-expansion-triage_codex-review.md` marking the triage as needing data-path correction before implementation.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 056A-Fix.
- Updated `docs/task_board.md` to queue the OOS stability triage correction.

### Verification
- Reviewed the triage note against `app/services/validation_pipeline_service.py` and `validation_engine/elimination.py`.
- Ran `git diff --check`.

## 2026-06-06 - Task 056A-Fix: OOS Stability Triage Data Path Correction

### Changed
- Revised `docs/next_validation_expansion_triage_056A.md` with explicit OOS data path trace:
  - Pipeline diagram showing `split.oos` exists but is never backtested.
  - Confirmed `evaluate_elimination()` already accepts `oos_metrics` but is never called with it.
  - Corrected scope for Task 056B to include OOS backtest + pipeline wiring + stability rules in one task.
- Corrected file references: `EliminationConfig` lives in `validation_engine/elimination.py`, not `core/models/validation.py`.

### Verification
- No production code changed (design-only correction).
- `git diff --check` passes.
- Only `docs/next_validation_expansion_triage_056A.md` and this changelog touched.

## 2026-06-06 - Task 056A: Next Validation Expansion Triage Design Only

### Added
- Created `docs/next_validation_expansion_triage_056A.md` reviewing current validation state and identifying 4 candidate gaps.
- Candidate A: IS/OOS Stability Checks (OOS max drawdown ratio, IS/OOS metric gap stability).
- Candidate B: Remove Best N Trades Stress Test.
- Candidate C: Monte Carlo Bootstrap + Confidence Intervals.
- Candidate D: IS Baseline Quality Gate.

### Changed
- Recommended **Task 056B — IS/OOS Stability Gate Implementation** as the next validation expansion task.
- Updated `docs/task_board.md` (Task 056A → Done, Task 056B → In Progress).

### Verification
- No production code changed (design-only triage).
- `git diff --check` passes.
- Working tree clean except for docs and report files.

## 2026-06-06 - Task 053K: Hosted Rounds Hygiene and Guardrail Fix

### Changed
- Stripped trailing whitespace from `validation_engine/stress_test.py` (11 lines in `stress_parameter_perturbation`).
- Added `execution_delay_bars` input guard in `backtest_engine/runner.py` (`run_backtest`): rejects non-int and negative values with `ValueError`.
- Added 5 focused guardrail tests in `tests/test_execution_delay.py` for invalid `execution_delay_bars` (negative, float, bool, str, None).

### Verification
- `git diff --check` passes (no trailing whitespace).
- Focused `test_execution_delay.py` tests: 9 passed (4 existing + 5 new).
- Full test suite: 965 passed, 1 warning.

## 2026-06-06 - Task 053K-Codex Re-entry Audit

### Added
- Created `docs/review_notes/2026-06-06_task-053k_codex-reentry-audit.md` accepting the hosted Tasks 053F through 053K and 054E batch.

### Changed
- Routed `docs/agent_queue/current_task.md` to Task 056A for the next validation expansion triage.

### Verification
- Ran focused execution-delay, stress-test, and validation-pipeline tests: 38 passed.
- Ran full test suite: 965 passed, 1 warning.
- Ran `git diff --check`; no whitespace errors.

## 2026-06-05 - Task 053J-Codex Sleep Check

### Added
- Created `docs/review_notes/2026-06-05_task-053j_sleep-check_codex-review.md` provisionally accepting the Task 053J acceptance smoke pending a full Codex re-entry audit.

### Changed
- Routed `docs/agent_queue/current_task.md` to `Task Codex-Reentry-053-Series-Audit`.

### Verification
- Ran full test suite: 960 passed, 1 warning.
- Ran `git diff --check`; trailing whitespace remains queued for the re-entry audit cleanup.

## 2026-06-05 - Task 053J: Parameter Perturbation Acceptance Smoke

### Verification
- Verified end-to-end parameter perturbation execution yielding 4 results by default (`commission_2.0x`, `slippage_2.0x`, `one_bar_delay`, `parameter_perturbation`).
- Confirmed configuration toggles disable the stress tests exactly as expected (shrinking test results count sequentially to 3 then 2).
- Validated UI components render successfully without crashes using `asdict(PipelineResult)` parsing workaround.
- Markdown HTML report exporter functions correctly, capturing `parameter_perturbation` tables successfully.
- All 960 system unit tests passed seamlessly (`pytest -q`).

## 2026-06-05 - Task 053I-Codex Review

### Added
- Created docs/review_notes/2026-06-05_task-053i_parameter-perturbation-wiring_codex-review.md accepting the wiring.

### Changed
- Updated docs/agent_queue/current_task.md with Task 053J for acceptance smoke.
- Updated docs/task_board.md with Task 053J in progress.

### Verification
- Full test suite: 960 passed, 0 failed.
- Confirmed seed determinism fix applied (random.seed + setstate restore).
- Pipeline now runs 4 stress tests by default.

## 2026-06-05 - Task 053I: Parameter Perturbation Stress Test Validation Pipeline Wiring

### Added
- Wired `stress_parameter_perturbation` into `app/services/validation_pipeline_service.py`.
- Exposed `run_parameter_perturbation: bool = True` in `PipelineConfig`.
- Ensured parameter perturbation execution is completely deterministic within the pipeline by tying it to `mc_base_seed`.

## 2026-06-05 - Task 053H-Impl-Codex Review

### Added
- Created docs/review_notes/2026-06-05_task-053h-impl_parameter-perturbation_codex-review.md accepting the implementation.

### Changed
- Updated docs/agent_queue/current_task.md with Task 053I for validation pipeline integration.
- Updated docs/task_board.md with Task 053I in progress.

### Verification
- Full test suite: 959 passed, 0 failed.
- Focused tests: 23 passed.
- Confirmed implementation matches design: deep-copy, additive/multiplicative perturbation, 4 tests.

## 2026-06-05 - Task 053H-Impl: Parameter Perturbation Stress Test Implementation

### Added
- Implemented `stress_parameter_perturbation` in `validation_engine/stress_test.py`.
- Added dynamic perturbation using additive shifts for integers and multiplicative shifts for floats, clamped to logical boundaries.
- Designed 4 fully automated tests covering no-leak mutability checks, generation constraints, pass logic, and fail logic (`test_parameter_perturbation.py`).
- Added a vacuous passing edge case when baseline contains zero trades.

## 2026-06-05 - Task 053H-Codex Review

### Added
- Created docs/review_notes/2026-06-05_task-053h_parameter-perturbation-design_codex-review.md accepting the design.

### Changed
- Updated docs/agent_queue/current_task.md with Task 053H-Impl for implementation.
- Updated docs/task_board.md with Task 053H-Impl in progress.

### Verification
- Full test suite: 955 passed, 0 failed.
- Confirmed no production code changed by design task.

## 2026-06-05 - Task 053H: Parameter Perturbation Stress Test Design Only

### Added
- Created `docs/parameter_perturbation_stress_design_053H.md`.
- Outlined API signatures, inputs, outputs, thresholds, and variant sampling methodology for parameter perturbation testing.
- Specified integer vs. float logic handling and no-leak policies.

## 2026-06-05 - Task 054E-Codex Review

### Added
- Created docs/review_notes/2026-06-05_task-054e_fix-validationsummary-dataclass_codex-review.md accepting the fix.

### Changed
- Updated docs/agent_queue/current_task.md with Task 053H for parameter perturbation stress test design.

### Verification
- Full test suite: 955 passed, 0 failed.
- Confirmed diff: exactly 1 line changed (validation_summary.py:57).
- Confirmed no other raw .get() calls remain in update_from_result().

## 2026-06-05 - Task 054E: Fix ValidationSummary Dataclass Compatibility

### Fixed
- Fixed an `AttributeError` in `app/widgets/validation_summary.py` where `.get("_is_mock")` was called directly on the `PipelineResult` dataclass object instead of routed through the internal `self._get()` compatibility helper.

## 2026-06-05 - Task 053-Acceptance-Codex Review

### Added
- Created docs/review_notes/2026-06-05_task-053-acceptance_backtest-execution-enhancements_codex-review.md accepting the acceptance smoke.

### Changed
- Updated docs/agent_queue/current_task.md with Task 054E for ValidationSummary dataclass compatibility fix.
- Updated docs/task_board.md with Task 054E in progress.

### Verification
- Full test suite: 955 passed, 0 failed.
- Confirmed acceptance verified: pipeline, UI, reports, config override all correct.
- Confirmed UI quirk root cause: ValidationSummary line 57 uses raw .get() instead of self._get().

## 2026-06-05 - Task 053-Acceptance: Backtest Execution Enhancements Acceptance Smoke

### Verification
- Ran headless end-to-end acceptance checks.
- Verified `stress_results` outputs 3 stress tests by default.
- Verified Markdown and HTML export generators correctly render `one_bar_delay` tests when enabled.
- Verified `ValidationSummary` widget successfully renders `one_bar_delay` test status.
- Validated disabling pipeline stress via `PipelineConfig` hides the one-bar delay output across data, UI, and reports.
- All 955 automated tests passed.
- **Known Quirks Documented**: `ValidationSummary` expects a dictionary format (`asdict()`) due to a bug natively calling `.get("_is_mock")` on `PipelineResult` dataclasses, but UI rendering behavior acts correctly otherwise.

## 2026-06-05 - Task 053G-Codex Review

### Added
- Created docs/review_notes/2026-06-05_task-053g_validation-pipeline-one-bar-delay_codex-review.md accepting the pipeline integration.

### Changed
- Updated docs/agent_queue/current_task.md with Task 053-Acceptance for backtest execution enhancements acceptance smoke.
- Updated docs/task_board.md with Task 053-Acceptance in progress.

### Verification
- Full test suite: 955 passed, 0 failed.
- Pipeline tests: 18 passed.
- Stress/delay tests: 19 passed.

## 2026-06-05 - Task 053G: Validation Pipeline Integration for One-Bar Delay Stress

### Added
- Imported `stress_one_bar_delay` in `app/services/validation_pipeline_service.py`.
- Added `run_one_bar_delay_stress: bool = True` to `PipelineConfig`.
- Added focused test `test_one_bar_delay_can_be_disabled` to verify pipeline handles the new stress test correctly.

### Changed
- Integrated `stress_one_bar_delay` into `run_validation_pipeline()`.
- Pipeline now runs 3 stress tests by default (commission, slippage, and one-bar delay).

### Verification
- Focused test added and passed.
- All 955 tests passing.

## 2026-06-05 - Task 053F-Impl-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-053f-impl_one-bar-execution-delay-stress_codex-review.md` accepting the implementation.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 053G for validation pipeline integration.
- Updated `docs/task_board.md` with Task 053G in progress.

### Verification
- Full test suite: 954 passed, 0 failed.
- `agent_status.ps1`: 6 modified + 5 untracked (all docs/source, no unexpected files).
- Confirmed runner.py diff: clean, backward-compatible, no future-leak.
- Confirmed all 4 deterministic delay tests pass.

## 2026-06-05 - Task 053F-Impl: One-Bar Execution Delay Stress Test Implementation

### Added
- Added `execution_delay_bars` parameter to `run_backtest` to enable native execution delay without shifting price data.
- Added 4 deterministic execution delay tests.

### Changed
- Refactored `stress_one_bar_delay` to use `execution_delay_bars=1` rather than artificially shifting price data, preserving indicator accuracy and avoiding future leaks.
- Modified `pending` state variable from 2-tuple to 3-tuple to track delay countdown.
- Suppressed new entry signals while a pending entry is actively counting down in-flight.
- Updated backtest result `assumptions` to record `execution_delay_bars`.

### Verification
- 4 deterministic tests passing (`tests/test_execution_delay.py`).
- Full test suite passed (954 tests).

## 2026-06-05 - Task 053F-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-053f_one-bar-execution-delay-stress-design_codex-review.md` accepting the design.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 053F-Impl for implementation.
- Updated `docs/task_board.md` with Task 053F-Impl in progress.

### Verification
- Ran focused pytest: 70 passed, 0 failed.
- Ran `agent_status.ps1`: clean working tree, only docs dirty.
- Confirmed no production code was changed by design task.

## 2026-06-05 - Task 053F: One-Bar Execution Delay Stress Test Design Only

### Added
- Created design document `docs/one_bar_execution_delay_stress_design_053F.md` detailing how to implement a native execution delay in the backtest engine to properly replace the naive data-shift approach.

## 2026-06-05 - Task 053E-Fix2-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-053e-fix2_session-end-time-serializer-range-validation_codex-review.md` accepting strict session-end time serializer range validation.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 053F for one-bar execution delay stress test design.
- Updated `docs/task_board.md` to move Task 053F into progress.

### Verification
- Ran focused serializer and JSON import tests.
- Ran broader backtest, serializer, repository, and JSON import regression tests.
- Ran manual strict serializer probes for invalid and valid session-end clock values.

## 2026-06-05 - Task 053E-Fix2: Strict Session-End Time Serializer Range Validation

### Changed
- Enhanced strict strategy serializer logic for `session_end_time` by replacing the permissive string matcher with a strict range-bounded regex (`^(?:[01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$`). This explicitly rejects invalid clock times like `24:00`, `99:99`, or `12:60` during import.
- Added explicit unit tests to ensure strict rejection of invalid clock ranges while preserving acceptance of valid `HH:MM` and `HH:MM:SS` times.

## 2026-06-05 - Task 053E-Fix-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-053e-fix_session-end-validation-pending-entry_codex-review.md` marking the session-end validation fix as needing one serializer range-validation hardening pass.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 053E-Fix2.
- Updated `docs/task_board.md` to queue strict session-end serializer range validation.

### Verification
- Ran focused pytest command for backtest, serializer, repository, and JSON import tests.
- Ran manual edge-case checks for malformed engine time handling, pending-entry cancellation, and strict serializer acceptance of invalid clock ranges.

## 2026-06-05 - Task 053E-Fix: Session-End Exit Validation and Pending Entry Hardening

### Changed
- Refined `session_end_time` configuration in `run_backtest` to strictly throw a `ValueError` for invalid formats, preventing silent failures.
- Updated assumptions generation to correctly only report session-end fields when explicitly valid and enabled.
- Hardened `run_backtest` event loop to immediately cancel any pending entries that would execute at or after the configured `session_end_time` and log a specific warning.
- Enhanced strict strategy serialization to correctly reject malformed `session_end_time` formats.
- Expanded automated test coverage specifically for session-end format validation, assumptions rendering, and pending entry cancellation edge cases.

## 2026-06-05 - Task 053E-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-053e_session-end-exit-engine_codex-review.md` marking the session-end exit implementation as needing focused fixes.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 053E-Fix.
- Updated `docs/task_board.md` to queue the session-end validation and pending-entry hardening task.

### Verification
- Ran focused pytest command for backtest, serializer, repository, and JSON import tests.
- Ran manual edge-case checks for invalid `session_end_time` and pending entry at session boundary.

## 2026-06-05 - Task 053E: Session-End Exit Engine Implementation

### Added
- Added optional `close_end_of_session` and `session_end_time` parameters to `RiskManagement` to forcibly close positions intraday.
- Added session-end exit execution logic in `backtest_engine/runner.py` that checks the current bar's time against the configured boundary.
- Added comprehensive tests for session-end logic, including long/short exits, costs, missing final bars, and strict no future-row dependency.

### Changed
- Strategy serializer gracefully tolerates new session-end fields and safely defaults them to `False`/`None` for legacy strategies.
- Backtest metrics report session-end assumptions correctly.

## 2026-06-05 - Task 053D-Fix-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-053d-fix_session-end-exit-triage-hardening_codex-review.md` accepting the hardened session-end exit triage.
- Assigned Task 053E for narrow session-end exit engine implementation.

### Changed
- Updated `docs/agent_queue/current_task.md` and `docs/task_board.md` for the next DeepSeek implementation task.

### Verification
- Ran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`.

## 2026-06-05 - Task 053D-Fix: Session-End Exit Triage Hardening

### Changed
- Hardened `docs/backtest_execution_enhancement_triage_053D.md` by explicitly prohibiting future-leaking dataset scans for final-bar detection.
- Added strict backward compatibility requirements and expanded testing criteria for session-end logic.
- Corrected inaccurate file paths for Trade Assumption Reporting.

## 2026-06-05 - Task 053D-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-053d_backtest-execution-triage_codex-review.md` marking the execution triage as needing design hardening.

### Changed
- Updated `docs/agent_queue/current_task.md` with Task 053D-Fix.
- Updated `docs/task_board.md` to queue the focused triage hardening task.

### Verification
- Ran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`.
- Reviewed the triage document against current `runner.py`, `RiskManagement`, and backtest tests.

## 2026-06-05 - Task 053D: Backtest Execution Enhancements Triage

### Added
- Created `docs/backtest_execution_enhancement_triage_053D.md` to evaluate the next high-value execution features.
- Recommended implementing "Session-End Exit Behavior (Day Trading Enforcement)" as the next prioritized execution enhancement to ensure intraday strategies do not hold positions overnight inadvertently.

## 2026-06-05 - Task 055G-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-055g_git-aware-agent-status_codex-review.md` accepting the Git-aware status script update.
- Assigned Task 053D for design-only backtest execution enhancement triage.

### Changed
- Updated `docs/agent_queue/current_task.md` and `docs/task_board.md` to move the workflow loop back toward product/engine planning.

### Verification
- Ran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`.

## 2026-06-05 - Task 055G: Git-aware Agent Status Script

### Changed
- Updated `scripts/agent_status.ps1` to display current branch, latest commit hash/subject, short dirty status, and ignored file count when `.git` exists.
- Retained fallback behavior for workspaces without `.git`.

## 2026-06-05 - Task 055G Assignment

### Added
- Assigned Task 055G to update the agent status workflow for the newly initialized Git repository.

### Changed
- Updated `docs/agent_queue/current_task.md` with a narrow Anti-Gravity task for Git-aware status reporting.
- Updated `docs/task_board.md` to mark Task 055G in progress.

## 2026-06-05 - Task 055F: Git Init and Initial Baseline Commit

### Added
- Initialized Git for the repository and created the first baseline commit.

### Changed
- Hardened `.gitignore` before the baseline commit by keeping required test sample CSV files tracked while excluding local external manuals and generated sample project output.
- Updated `docs/agent_queue/current_task.md` and `docs/task_board.md` to record Task 055F completion.

### Verification
- Ran `git status --ignored` before staging.
- Ran `git status --short` before committing.

## 2026-06-05 - Task 055E-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-055e_safe-gitignore-creation_codex-review.md` accepting the safe `.gitignore` creation.

### Changed
- Updated `docs/agent_queue/current_task.md` to block Git initialization until explicit user authorization.
- Updated `docs/task_board.md` to show Task 055F as blocked pending user approval.

### Verification
- Ran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`.
- Confirmed `.gitignore` exists and `.git` does not exist.

## 2026-06-05 - Task 055E: Safe .gitignore Creation Only

### Added
- Created the root `.gitignore` file based on the validated safe draft.
- Ensured large data files (`TXF.txt`), virtual environments, and generated test outputs are untracked without omitting core application source packages.

## 2026-06-05 - Task 055D-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-055d_agent-task-sizing-protocol_codex-review.md` accepting the task sizing protocol and assigning Task 055E.

### Changed
- Polished `docs/agent_task_sizing_protocol_055D.md` with concrete batch-size guidance and routing/safety rules for higher-risk tiers.

### Verification
- Ran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`.

## 2026-06-05 - Task 055D: Semi-Automated Agent Task Sizing Protocol

### Added
- Created `docs/agent_task_sizing_protocol_055D.md` to formally document risk tiers and permissible batch sizes for Codex -> Anti-Gravity handoffs.
- Established strict rules forbidding the batching of engine/quant logic tasks while allowing broader scope for UI skeleton and documentation hygiene tasks.
- Provided a reusable assignment template for safe Anti-Gravity batching.

## 2026-06-05 - Task 055C-Fix-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-055c-fix_gitignore-source-safety_codex-review.md` accepting the Git ignore source-package safety fix.

### Changed
- Polished `docs/git_repository_setup_readiness_055C.md` so root `reports/` is consistently described as source code and `TXF.txt` ignore guidance uses valid, unambiguous `.gitignore` syntax.
- Updated `docs/task_board.md` to queue Task 055D.

### Verification
- Ran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`.
- Confirmed no `.git` directory or `.gitignore` file exists.

## 2026-06-05 - Task 055C-Fix: Git Ignore Draft Source Package Safety

### Fixed
- Updated `docs/git_repository_setup_readiness_055C.md` to ensure the proposed `.gitignore` does not inadvertently ignore the root `reports/` source code package.
- Added explicit warnings to never ignore the application source packages (`app/`, `core/`, etc.).
- Removed confusing `!TXF.txt` negation syntax from the ignore draft in favor of straightforward exclusion.

## 2026-06-05 - Task 055C-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-055c_git-readiness_codex-review.md` marking the Git readiness note as needing a focused `.gitignore` draft fix.

### Changed
- Updated `docs/task_board.md` to queue Task 055C-Fix.

### Verification
- Ran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`.
- Confirmed root `reports/` contains source files and must not be ignored by a proposed `.gitignore`.

## 2026-06-05 - Task 055C: Git Repository Setup Readiness

### Added
- Performed an audit of the workspace to assess readiness for initializing a Git repository.
- Created `docs/git_repository_setup_readiness_055C.md` containing a proposed `.gitignore` and manual setup instructions to avoid committing large data (`TXF.txt`) and ephemeral states.

## 2026-06-05 - Task 052-Acceptance-Fix-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-052-acceptance-fix_codex-review.md` accepting the conservative wording fix and assigning Task 055C.

### Changed
- Softened the remaining output invariance wording in `docs/backtest_performance_optimization_acceptance_052.md` from guarantee language to regression-bound language.
- Updated `docs/task_board.md` to move Task 055C into progress and remove completed Task 052 from the v0.2 next list.

### Verification
- Reviewed the latest Anti-Gravity report and corrected acceptance note.

## 2026-06-05 - Task 052-Acceptance-Fix: Conservative Performance Acceptance Wording

### Fixed
- Updated `docs/backtest_performance_optimization_acceptance_052.md` to frame performance gains strictly as runtime reductions based on profiling data rather than absolute speedup guarantees, and framed invariance bounds as test-driven regression limits rather than absolute mathematical certitudes.

## 2026-06-05 - Task 052-Acceptance-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-052-acceptance_codex-review.md` marking the Task 052 acceptance note as needing wording fixes.
- Updated `docs/agent_queue/current_task.md` with a narrow Task 052-Acceptance-Fix assignment.

### Changed
- Updated `docs/task_board.md` to track Task 052-Acceptance-Fix as in progress.

### Verification
- Reran `powershell -ExecutionPolicy Bypass -File scripts/run_smoke.ps1 -Quick`; passed with compile checks and 92 focused pytest cases.
- Confirmed existing Task 052 profiling evidence includes documented measurements `758.75s -> 247.71s`, `247.71s -> 24.2s`, and final measured runtime `22.67s`.

## 2026-06-05 - Task 052-Acceptance: Backtest Performance Optimization Acceptance Review

### Added
- Created `docs/backtest_performance_optimization_acceptance_052.md` summarizing the successful performance improvements to the backtest engine.
- Officially closed out the Task 052 optimization chain, noting the ~33x cumulative speedup achieved through array extraction, condition pre-compilation, and population-level indicator caching without sacrificing MTF invariants or no-future-leak constraints.

## 2026-06-05 - Task 054D-Impl-Acceptance-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-054d-impl-acceptance_codex-review.md` accepting the strategy serialization abstraction chain.
- Updated `docs/agent_queue/current_task.md` with the next assignment: Task 052-Acceptance.

### Changed
- Corrected `docs/task_board.md` so Task 054D-Impl-Acceptance is marked done and no longer listed as in progress/next.

### Verification
- Reran `.venv\Scripts\python.exe -m pytest tests/test_strategy_repo.py tests/test_strategy_json_import_service.py tests/test_strategy_serializer.py -v`; passed with 35 focused tests.
- Reran `powershell -ExecutionPolicy Bypass -File scripts/run_smoke.ps1 -Quick`; passed with compile checks and 92 focused pytest cases.

## 2026-06-05 - Task 054D-Impl-Phase3B-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-054d-impl-phase3b_codex-review.md` accepting the strict serializer parity audit.
- Updated `docs/agent_queue/current_task.md` with the final Task 054D acceptance/hygiene assignment.

### Changed
- Corrected `docs/task_board.md` so Phase3B is no longer listed in both `In Progress` and `Done`.
- Chose an acceptance/hygiene pass as the next step instead of full strict parser implementation, because the parity audit shows that replacing `ReportService.preview_strategy_json()` would require a larger validation refactor.

### Verification
- Reran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`; passed and found the latest Phase3B report.

## 2026-06-05 - Task 054D-Impl-Phase3B: Strict Strategy Serializer Parity Audit and Design Only

### Added
- Created `docs/strict_strategy_serializer_parity_audit_054D_phase3B.md` to map validation gaps between the current `ReportService.preview_strategy_json()` and `core.serialization.strategy_serializer.strategy_from_dict(strict=True)`.
- Recommended deferring full integration into `ReportService` until the serializer is hardened with proper list/type/enum enforcement and an error accumulation strategy.

## 2026-06-05 - Task 054D-Impl-Phase3A-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-054d-impl-phase3a_codex-review.md` accepting the ReportService risk-management strict serializer wiring.
- Updated `docs/agent_queue/current_task.md` with a design-only parity audit task for strict full-strategy serializer behavior.

### Changed
- Updated `docs/task_board.md` to mark Task 054D-Impl-Phase3B as in progress.

### Verification
- Reran `powershell -ExecutionPolicy Bypass -File scripts/run_smoke.ps1 -Quick`; passed with compile checks and 92 focused pytest cases.
- Reran `.venv\Scripts\python.exe -m pytest tests/test_strategy_json_import_service.py tests/test_strategy_serializer.py -v`; passed with 18 focused tests.
- Confirmed `ReportService` only wires `risk_management_from_dict`; block and condition parsing remains local.

## 2026-06-05 - Task 054D-Impl-Phase3A: Report Service RiskManagement Strict Serializer Wiring Only

### Changed
- Refactored `app/services/report_service.py` (`preview_strategy_json`) to parse `risk_management` payloads using `core.serialization.strategy_serializer.risk_management_from_dict(..., strict=True)`.
- Maintained exact JSON import validation parity (including name, provenance, block, and condition validation) without broadening the serializer abstraction prematurely.
- Explicitly tested boolean, negative, and malformed type rejections in `tests/test_strategy_json_import_service.py`.

## 2026-06-05 - Task 054D-Impl-Phase2-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-054d-impl-phase2_codex-review.md` accepting repository tolerant serializer wiring.
- Updated `docs/agent_queue/current_task.md` with a bounded Phase3A task for ReportService risk-management parsing only.

### Changed
- Updated `docs/task_board.md` to mark Task 054D-Impl-Phase3A as in progress and split strict report-service work from broader strict strategy parser parity.

### Verification
- Reran `powershell -ExecutionPolicy Bypass -File scripts/run_smoke.ps1 -Quick`; passed with compile checks and 92 focused pytest cases.
- Reran `.venv\Scripts\python.exe -m pytest tests/test_strategy_repo.py tests/test_strategy_serializer.py -v`; passed with 23 focused tests.
- Confirmed `ReportService` and JSON import were untouched during Phase2.

## 2026-06-05 - Task 054D-Impl-Phase2: Strategy Repository Tolerant Serializer Wiring

### Changed
- Refactored `repository/strategy_repo.py` to route all SQLite JSON deserialization through `core.serialization.strategy_serializer.strategy_from_dict(..., strict=False)`.
- Removed duplicated internal parse functions (`_dict_to_strategy`, `_dict_to_risk_management`, `_dict_to_block`, `_dict_to_condition`) from the repository layer.
- Expanded `tests/test_strategy_repo.py` to explicitly verify that legacy malformed boolean/negative values fail safe (defaulting gracefully) when loaded from SQLite.

## 2026-06-05 - Task 054D-Impl-Phase1-Fix-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-054d-impl-phase1-fix_codex-review.md` accepting the bool validation fix.
- Updated `docs/agent_queue/current_task.md` with the next bounded assignment: Task 054D-Impl-Phase2.

### Changed
- Updated `docs/task_board.md` to mark Task 054D-Impl-Phase2 as in progress and split the remaining serializer implementation into repository wiring, report-service wiring, and acceptance.

### Verification
- Reran `powershell -ExecutionPolicy Bypass -File scripts/run_smoke.ps1 -Quick`; passed with compile checks and 92 focused pytest cases.
- Reran `.venv\Scripts\python.exe -m pytest tests/test_strategy_serializer.py -v`; passed with 6 serializer tests, including bool strict/tolerant assertions.
- Confirmed no production caller was wired to the serializer before Phase 2.

## 2026-06-05 - Task 054D-Impl-Phase1-Fix: Reject Bool Risk-Management Numeric Values

### Fixed
- Updated `core/serialization/strategy_serializer.py` to explicitly reject boolean values (`isinstance(val, bool)`) that otherwise bypass the standard `(int, float)` numeric type checking.
- Added explicit test cases in `tests/test_strategy_serializer.py` to assert that `True`/`False` trigger strict validation failures or gracefully default to `None` in tolerant mode.

## 2026-06-05 - Task 054D-Impl-Phase1-Codex Review

### Added
- Created `docs/review_notes/2026-06-05_task-054d-impl-phase1_codex-review.md` marking Phase 1 as needs-fix before repository wiring.
- Updated `docs/agent_queue/current_task.md` with a narrow Phase1-Fix assignment to reject bool risk-management numeric values.

### Changed
- Updated `docs/task_board.md` to track Task 054D-Impl-Phase1-Fix as in progress.

### Verification
- Reran `powershell -ExecutionPolicy Bypass -File scripts/run_smoke.ps1 -Quick`; passed with compile checks and 92 focused pytest cases.
- Reran `.venv\Scripts\python.exe -m pytest tests/test_strategy_serializer.py -v`; passed with 6 serializer tests.
- Confirmed the new serializer has not been wired into production callers yet.

## 2026-06-05 - Task 054D-Impl-Phase1: Strategy Serializer Helper Without Production Wiring

### Added
- Created `core/serialization/strategy_serializer.py` and `core/serialization/__init__.py` to implement the `strategy_from_dict` abstraction in both strict (UI) and tolerant (Legacy) modes.
- Added comprehensive unit tests in `tests/test_strategy_serializer.py` demonstrating correct type validation, negative number clamping/rejection, and fallback injection. No production caller pathways (e.g. `StrategyRepository` or `ReportService`) were modified during this phase.

## 2026-06-05 - Task 055B-Codex: File-Based Handoff Trial Acceptance

### Added
- Created `docs/review_notes/2026-06-05_task-055b_codex-review.md` accepting the Task 055B workflow trial.
- Updated `docs/agent_queue/current_task.md` with the next bounded implementation assignment: Task 054D-Impl-Phase1.

### Changed
- Marked Task 054D-Impl-Phase1 as in progress in `docs/task_board.md`.

### Verification
- Reran `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1`; passed and found the latest Anti-Gravity report.
- Reran `powershell -ExecutionPolicy Bypass -File scripts/run_smoke.ps1 -Quick`; passed with compile checks and 92 focused pytest cases.

## 2026-06-05 - Task 055B: Trial file-based handoff workflow

### Added
- Created `docs/agent_reports/2026-06-05_task-055b_anti-gravity.md` to successfully trial the file-based agent handoff workflow.
- Executed `scripts/agent_status.ps1` and `scripts/run_smoke.ps1 -Quick` seamlessly.

## 2026-06-05 - Task 055A: Lightweight Agent Handoff Workflow

### Added
- Added `docs/agent_queue/current_task.md` as the shared task file for Codex-to-agent assignments.
- Added `docs/agent_reports/README.md` and `docs/review_notes/README.md` to standardize completion reports and Codex review notes.
- Added `scripts/agent_status.ps1` to summarize the current task, latest agent report, version-control status when available, and recent modified files when the folder is not a Git repository.
- Added `scripts/run_smoke.ps1` with quick and full verification modes.

### Changed
- Updated `docs/task_board.md` with Task 055A completion and proposed Task 055B trial workflow.

### Verification
- `powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1` passed and printed current task, report status, non-Git fallback, and task board snapshot.
- `powershell -ExecutionPolicy Bypass -File scripts/run_smoke.ps1 -Quick` passed with compile checks and 92 focused pytest cases.

## 2026-06-05 - Task 054D: Strategy Serialization Service Abstraction Design Only

### Added
- Created `docs/strategy_serialization_abstraction_design_054D.md` to design a unified `RiskManagement` and `Strategy` serialization helper.
- Outlined a plan to remove duplicate, divergent parsing logic from `repository/strategy_repo.py` and `app/services/report_service.py` by introducing `core/serialization/strategy_serializer.py` with strict (JSON import) and tolerant (DB legacy) modes.

## 2026-06-05 - Task 054C-Fix: Task Board Accuracy, Assertion Tightening, and Honest Import-Hygiene Note

### Fixed
- Moved `Task 054C` cleanly into the `Done` section of `docs/task_board.md` and removed it from `Next`.
- Tightened assertions in `tests/test_strategy_json_import_results_wiring.py` by removing the broad `len >= 1` check.
- Retained the `RiskManagement` local import within `backtest_engine/runner.py` as a known and documented hygiene tradeoff, given that module-level hoisting triggers a PySide6 access violation.

## 2026-06-05 - Task 054C: Test Assertions and Local Import Hardening

### Changed
- Hardened test assertions in `tests/test_backtest_engine.py` and `tests/test_strategy_json_import_results_wiring.py`, replacing weak `is not None` and `does not crash` smoke tests with strict type checking, dictionary key assertions, and list length validations.
- Left `RiskManagement` as a local import inside `backtest_engine/runner.py` because moving it to module scope caused a fatal access violation (segfault) in PySide6 GUI test initialization (`test_ga_build_wiring.py`), indicating a delicate event-loop initialization boundary that should not be forcefully refactored.

## 2026-06-05 - Task 054B-Fix2: Final Documentation Hygiene Polish and Honest Acceptance Report

### Fixed
- Replaced the remaining non-ASCII check mark in `docs/task_board.md` and normalized milestone spacing.
- Softened overconfident language in `docs/backtest_stop_take_profit_acceptance_053C.md` to clearly frame all reliability claims as tested regression boundaries rather than absolute mathematical guarantees.
- Ensured the `docs/code_hygiene_technical_debt_audit_054A.md` retains intentional examples of old issues for context, while remaining honest about scope limits.

## 2026-06-05 - Task 054B: Documentation Hygiene and Mojibake Cleanup

### Fixed
- Extensively scrubbed targeted documentation for mojibake encoding corruption, safely restoring standard ASCII hyphens in targeted files.
- Re-structured `task_board.md` to remove duplicated "Done" segments and enforce explicit milestone segregation.
- Removed stale text within `docs/backtest_performance_optimization_design_052A.md` claiming deferred components were active (Phase 4 Vectorized Masks, Genetic Programming integration).
- Corrected logic ambiguity and semantic humility gaps in `docs/backtest_stop_take_profit_acceptance_053C.md`.

## 2026-06-05 - Task 054A: Code Hygiene Audit and Technical Debt Reduction Design Only

### Added
- Created formal audit document: `docs/code_hygiene_technical_debt_audit_054A.md` categorizing P0-P3 risks across quant gaps, weak tests, local imports, and documentation mojibake.

### Verification
- Audited documentation, core files, and test files explicitly without initiating state modifications.
- Confirmed compileall passes cleanly.

## 2026-06-05 - Task 053C-Acceptance: Backtest Stop-Loss / Take-Profit Acceptance Review

### Added
- Created formal acceptance note: `docs/backtest_stop_take_profit_acceptance_053C.md`

### Verification
- Audited complete 053 chain including intra-bar SL/TP behavior, baseline execution fidelity, backward-compatible defaults, and dataset persistence parity.
- Confirmed full test suite cleanly passes with 929 test cases.
- Validated no external frameworks, dependencies, or Genetic Programming modules were touched.

## 2026-06-05 - Task 053B-Fix2: RiskManagement Backward-Compatible Default Object and Full Import Regression Fix

### Fixed
- Fixed `_dict_to_strategy()` in `StrategyRepository` to ensure missing or malformed `risk_management` JSON properties fallback to an empty `RiskManagement()` object instead of `None`.
- Fixed `preview_strategy_json()` in `ReportService` to behave identically and securely instantiate an empty `RiskManagement()` object for missing/null properties.
- Resolved `run_backtest` crashes (`AttributeError`) induced by injecting mocked strategies with missing properties.

### Verification
- Tested strategy JSON imports and DB loadings failing over to disabled properties securely.
- Confirmed total pass across 929 Pytest suites locally.

## 2026-06-04 - Task 053B-Fix: Stop-Loss / Take-Profit Persistence and Import Hardening

### Fixed
- Fixed `StrategyRepository` to correctly persist and reconstruct `RiskManagement` block.
- Fixed `ReportService.preview_strategy_json` to parse and validate `risk_management` schema safely, failing safely on invalid data.
- Fixed `run_backtest` assumptions block to dynamically reflect `stop_take_profit_enabled` and config precedence.
- Removed self-talk and review comments from production code in `runner.py`.

### Verification
- Ran 6 regression tests for `StrategyRepository` persistence and fail-safe loading.
- Ran 3 tests for JSON import validation with valid, invalid, and negative risk management fields.
- Ran test for BacktestResult assumptions generation.

## 2026-06-05 - Task 053B - Task 053B Backtest Stop-Loss / Take-Profit Implementation

### Added
- Created `RiskManagement` configuration model for the `Strategy` block.
- Implemented intra-bar Stop-Loss (SL) and Take-Profit (TP) check logic in `runner.py`'s event loop.
- Ensured gap-through fill uses `open` price, rather than just `sl_price` or `tp_price`.
- Enabled the conservative `stop-loss-first` policy for same-bar ambiguity resolution.
- Updated `exit_reason` inside trades to be either `"stop_loss"`, `"take_profit"`, `"signal"`, or `"end_of_data"`.

### Verification
- Focus-tested 11 SL/TP behaviors successfully.
- Baseline equivalence maintained when SL/TP logic is disabled.

## 2026-06-05 - Task 053A Backtest Stop-Loss / Take-Profit Execution Design Only

### Added
- Created `docs/backtest_stop_take_profit_design_053A.md` detailing the insertion of Stop-Loss (SL) and Take-Profit (TP) intra-bar execution checks into the event loop.
- Outlined a new `RiskManagement` configuration model for the Strategy block to define SL/TP logic while preserving the ability to disable it for legacy equivalence.
- Defined a conservative same-bar ambiguity handling policy (Stop-Loss wins) to avoid survival bias in backtests.

### Verification
- This task is exclusively design-oriented. Self-audited for absence of code changes or tests alterations. All existing 909 tests continue to pass.

## 2026-06-05 - Task 052B Phase 3C Indicator Cache Acceptance, Safety Hardening, and Full Profiling Audit

### Changed
- Hardened `IndicatorCache` fingerprint to use `pd.util.hash_pandas_object` over all datetime and OHLCV columns across all rows.
- Fixed a parameter collision in MTF MACD generation where columns were not uniquely suffixed with parameters.
- Restored missing `macd_line_12_26_9` logic in `evaluator.py`.

### Verification
- Checked that caching MTF MACD handles unique parameters correctly without collision.
- Run focused tests and full test suite (909 passed).
- Verified `profile_large_ga.py` output saved to `docs/perf_baselines/post_phase3_acceptance.prof` shows `_precompute_indicators` is securely caching.
- Confirmed total wall-clock speedup holds at 22.67s.

## 2026-06-05 - Task 052B Phase 3C-Fix MACD Test Integrity and Design Doc Cleanup

### Changed
- Fixed stale parameterless `macd_line` columns in `tests/test_backtest_engine.py` and `tests/test_indicators.py` that caused conditions to fall back to False.
- Fixed `test_macd_condition_evaluates`, `test_rsi_condition_evaluates`, and `test_atr_condition_evaluates` assertions that used `assert found or True` to instead inject valid data and strictly assert evaluator returns `True`.
- Removed overly confident language ("absolute", "mathematically") in `docs/backtest_performance_optimization_design_052A.md` in favour of sober, test-driven guarantees.

### Verification
- Full test suite passed (909 passed).
- All evaluator tests strictly pass with strict `True`/`False` assertions instead of bypass statements.

## 2026-06-04 - Task 052B Phase 3B Indicator Cache Implementation

### Added
- Implemented `IndicatorCache` class in `backtest_engine/runner.py`.
- Integrated `IndicatorCache` exclusively into GA evaluation (`strategy_engine/ga_fitness.py`).
- Cache validates `df_fingerprint` to fail safe on dataset changes.
- Deduplicates identical indicator computations for `run_backtest`.

### Verification
- Achieved significant reduction in indicator compute time during 5,000 bar GA workloads.
- Cache disabled vs enabled produces identical metrics/PNL/trades.
- Deterministic random seed yields identical best_score with and without cache.

## 2026-06-04 - Task 052B Phase 3A-Fix Indicator Cache Design Hardening

### Changed
- Hardened `IndicatorCache` design in `docs/backtest_performance_optimization_design_052A.md` to ensure zero data leakage.
- Enforced strict GA-only rollout initially, deferred GP.
- Defined robust DataFrame fingerprinting (hashing boundary samples instead of just length/time).
- Added explicit test plan invariants and profiling requirements.

## 2026-06-04 - Task 052B Phase 3A Backtest Performance Optimization Design

### Added
- Created the design and implementation sequence for `IndicatorCache` (Phase 3) within `docs/backtest_performance_optimization_design_052A.md`, detailing cache key structures, MTF safety invariants, and integration with `make_fitness_adapter` and `run_backtest`.

## 2026-06-04 - Task 052B-Phase2-Fix Compiled Evaluator Missing-Value Safety

### Fixed
- Replaced `math.isnan` with `pd.isna` in `compile_condition` lambdas to safely handle Pandas nullable types (`pd.NA`) and `np.nan` without raising `TypeError`.
- Added exhaustive behavior-matching tests covering missing columns, missing rows, nullable types, and invalid thresholds across all indicator types.

## 2026-06-04 - Task 052B Phase 2 Backtest Performance Optimization

### Added
- Added `compile_condition` and `compile_block` to `strategy_engine/evaluator.py` to parse condition strings into fast Numpy-backed closures.
- Added strict behavior matching tests proving that compiled blocks evaluate identically to legacy block evaluations.

### Changed
- `backtest_engine/runner.py` now pre-compiles strategy blocks into closures prior to the main evaluation loop.
- Achieved an additional ~10x speedup over Phase 1 (247.7s -> 24.2s runtime for 5,000 bars x 500 strategies), eliminating all remaining per-bar string parsing and Pandas lookup overhead.

## 2026-06-04 - Task 052B-Fix Backtest Performance Optimization Fix

### Fixed
- Fixed an issue from Phase 1 where `data["datetime"].values` caused `Trade.entry_time` and `Trade.exit_time` to become `numpy.datetime64` instead of `pd.Timestamp`. Switched to `tolist()` to preserve correct type.
- Added strict type assertions in `test_backtest_engine.py`.
- Updated profiling harness to write to `post_phase1_baseline.prof` to avoid overwriting the original baseline.

## 2026-06-04 - Task 052B Phase 1 Backtest Performance Optimization

### Added
- Created a reproducible large-load profiling harness (`tests/profile_large_ga.py`) utilizing 5,000 bars and 500 strategy evaluations.

### Changed
- Refactored `backtest_engine/runner.py` main loop to extract Pandas columns into local Numpy arrays before iteration (Phase 1).
- Achieved a ~3.06x speedup (758.75s -> 247.71s cumulative runtime) without altering any event-driven or MTF correct-execution semantics.

## 2026-06-04 - Task 052A-Fix2 Backtest Performance Profiling Plan Correction

### Fixed
- Corrected the profiling plan in `backtest_performance_optimization_design_052A.md` to reference a valid smoke test (`test_ga_search_returns_structured_result`).
- Formally mandated that Task 052B must first create a dedicated large-load profiling script (5,000 bars, 500 strategies) to capture wall-clock and `cProfile` baseline metrics before starting optimization.

## 2026-06-04 - Task 052A-Fix Backtest Performance Optimization Design Hardening

### Added
- Strengthened the Backtest Performance Optimization Design with concrete profiling steps.
- Defined explicit output invariance rules (trades, equity curve, metrics, etc.) for validation.
- Segmented candidate optimizations into 4 distinct phases based on risk, deferring full vectorization.
- Re-stated absolute constraints on MTF boundaries and `available_at` semantics.

## 2026-06-04 - Task 052A Backtest Performance Optimization Design Only

### Added
- Created `backtest_performance_optimization_design_052A.md` analyzing current row-by-row iteration bottlenecks in `runner.py`.
- Proposed safe array-based evaluation and population-level indicator caching to dramatically improve GA/GP speeds without risking the conservative execution model.

## 2026-06-04 - Task 051C GP MTF Integration Final Acceptance Note

### Added
- Created formal acceptance note `gp_mtf_integration_acceptance_051C.md` summarizing the GP MTF integration lifecycle.
- Closed out Task 051 on the task board and handoff documentation.
- Proposed Task 052 (Backtest Performance Optimization) as the next major focus.

## 2026-06-04 - Task 051B-Fix2 GP MTF Test Hardening

### Added
- Added direct test proving `_generate_random_condition` injects timeframe into `SMA`, `RSI`, `MACD`, and `ATR` paths.
- Added UI wiring test proving `MainWindow._handle_run_gp` correctly parses and forwards `allowed_timeframes` and `mtf_probability` down to `GPSearchConfig`.

## 2026-06-04 - Task 051B-Fix GP MTF Injection Hardening

### Fixed
- Fixed early returns in `_generate_random_condition` that caused SMA, RSI, MACD, and ATR conditions to bypass MTF parameter injection.

### Verification
- Strengthened tests to verify `mtf_probability=1.0` injects timeframes into every supported indicator type.
- Added tests to prove that mutation and tree growth branches correctly inherit MTF configurations.

## 2026-06-04 - Task 051B GP MTF Integration Implementation

### Added
- Implemented GP MTF Integration based on 051A design.
- Added `allowed_timeframes` and `mtf_probability` to `GPSearchConfig` and `GPConfig`.
- Propagated MTF config to `_generate_random_condition` to support injecting timeframes into newly generated GP conditions.
- Updated `MainWindow._handle_run_gp` to read passive MTF settings and forward to `GPSearchConfig`.

### Verification
- Full test suite passed (897 tests), ensuring RNG determinism is strictly preserved when MTF is disabled.

## 2026-06-04 - Task 051A GP MTF Integration Design Only

### Added
- Created `docs/gp_mtf_integration_design_051A.md` containing the proposed design for GP MTF Integration.
- Defined config routing path through `GABuildPanel`, `GPSearchConfig`, and `GPConfig` into the GP tree generator.
- Specified strict constraints for avoiding state leak and preserving base-case determinism.

## 2026-06-04 - Task 050D MTF UI / GA Integration Milestone Acceptance

### Verification
- Milestone accepted. Multi-Timeframe Strategy generation is now fully available and safely gated via UI controls on the GA Build Panel.
- Proved complete end-to-end flow from passive UI configuration, passing through `GASearchConfig` and `GAConfig`, to active strategy generation in `generate_strategies`.
- Proved formatting logic clearly isolates and labels `[TF: Nm]` in the `StrategyDetailWidget` without exposing engine references or risking HTML injection.
- Validated base-case backwards compatibility, safe fail-safes on invalid user input, and stable non-mutating Result interactions.

## 2026-06-04 - Task 050C-Acceptance Strategy Detail MTF Display Acceptance

### Verification
- Full test suite passed (895 passed tests).
- Verified `StrategyDetailWidget` correctly parses and isolates MTF conditions and escapes dynamic input securely.
- Confirmed `[TF: Nm]` is rendered safely alongside standard indicator parameters without duplication.

## 2026-06-04 - Task 050C-Codex Strategy Detail MTF Display Review & Hardening

### Strengthened Tests
- `tests/test_results_strategy_detail_wiring.py`: Added comprehensive validation for every supported MTF indicator type (SMA, RSI, MACD, ATR, VOLUME, VOLUME_SMA), proving they format their base components securely while appending `[TF: Nm]`.

## 2026-06-04 - Task 050C Strategy Detail MTF Display Polish

### Changed
- `app/widgets/strategy_detail.py`: Improved the strategy detail condition display to format MTF conditions clearly by appending `[TF: Nm]`. The `timeframe` key is extracted and no longer shown redundantly inside the parameters list.
- Malicious HTML from condition timeframe or parameters is fully escaped.

### Strengthened Tests
- `tests/test_results_strategy_detail_wiring.py`: Added 3 tests validating the formatting of base conditions, MTF conditions, and preventing HTML injection from MTF keys.

## 2026-06-04 - Task 050B-Acceptance MTF GA UI Wiring Acceptance

### Verification
- Full test suite passed (892 passed tests).
- Verified MTF GA Build Panel controls correctly generate primitive config dicts.
- Verified disabled states and invalid timeframe inputs degrade safely to base-only generation.
- Verified forwarding from `MainWindow` through `GASearchConfig` to `GAConfig`.
- Verified `create_initial_population` passes MTF parameters to `generate_strategies`.
- GP functionality remains completely intact and unaffected.
- Architecture passivity of `GABuildPanel` confirmed.
## 2026-06-04 - Task 050B MTF GA Config and Passive UI Controls Implementation

### Added
- Added passive `GABuildPanel` UI controls for enabling MTF candidates (checkbox, timeframes input, probability input), strictly disabled by default.
- Added `GASearchConfig` support for `allowed_timeframes` and `mtf_probability`.
- Added `GAConfig` support for `allowed_timeframes` and `mtf_probability`, passing them to the generator.

### Changed
- Wired `MainWindow._handle_run_ga` to read the passive config from `GABuildPanel` and forward it into `GASearchConfig` for execution.

## 2026-06-04 - Task 050A MTF UI Integration Design Only

### Added
- Created `docs/mtf_ui_integration_design_050A.md` to define the safe MVP UI integration path for multi-timeframe strategy generation.

### Design Decisions
- Place first MTF controls in the Build page via passive `GABuildPanel` controls, not in Results or Data pages.
- Route MTF config through `GASearchConfig` and `GAConfig` before reaching `generate_strategies()`.
- Keep MTF disabled by default and preserve existing Results fallback behavior.
- Avoid direct mutation of ranked strategies; MTF generation creates new candidates through the generator path.

### Verification
- Design-only task. No production Python files modified.
- `reports/python_exporter.py`: Added support for handling `VOLUME` and `VOLUME_SMA` MTF indicators. Python export gracefully handles `VOLUME` and `VOLUME_SMA` base metrics as well as references to exact MTF suffixed columns (`volume_tf_{timeframe}`, `volume_sma_{period}_tf_{timeframe}`). 
- `tests/test_strategy_json_export_ui_wiring.py`: Fixed a test fixture contamination bug where the JSON UI export test mutated a shared MainWindow fixture state (added a MTF condition without restoring original list), risking subsequent test suite stability.

### Strengthened Tests
- `tests/test_strategy_code_export.py`: Added comprehensive tests for Python exporter `VOLUME` and `VOLUME_SMA` both for base timeframe logic and properly-suffixed MTF reference generation.

## 2026-06-04 -Task 049F MTF Report and Export Safety Handling

### Fixed
- `reports/generator.py`: Updated `format_block_desc()` to explicitly extract and format `params["timeframe"]` as `[TF: {timeframe}m]` in condition descriptions.
- `reports/python_exporter.py`: Updated `export_strategy_to_python()` to safely degrade MTF indicators. Precomputation blocks emit descriptive comments instead of incorrect computations, and condition strings reference the expected `_tf_{N}` columns.
- `reports/ninjatrader_exporter.py`: Updated `export_strategy_to_ninjatrader()` to safely degrade MTF conditions to `false /* Unsupported multi-timeframe reference; manually review. */`, preventing compilation of non-executable logic while alerting the researcher.

### Strengthened Tests
- `tests/test_report_export.py`: Added tests to ensure condition descriptions correctly format timeframe metadata and that reports do not crash on MTF strategies.
- `tests/test_strategy_code_export.py`: Added tests to verify Python and NinjaTrader exporters safely degrade MTF logic, reference correct columns, include explanatory comments, and preserve forbidden-keyword safety.
- `tests/test_strategy_json_export_ui_wiring.py`: Added test to ensure JSON export preserves `timeframe` parameter logic.
- `tests/test_strategy_json_import_service.py`: Added test to ensure JSON import correctly reads `timeframe` metadata into condition instances.

## 2026-06-04 -Task 049E-Codex Generator MTF Injection Review & Hardening

### Changed
- `strategy_engine/generator.py`: Added explicit docstring detailing that while the generator validates that timeframes are positive integers, it is the runner's responsibility to validate that they are valid integer multiples of the actual data's base timeframe during backtesting.

### Strengthened Tests
- `tests/test_strategy_generator.py`: Hardened `test_generator_mtf_disabled_does_not_consume_rng` using `sys._getframe()` monkeypatching to strictly assert that `random()` is not called by `_maybe_add_timeframe` when MTF is disabled.
- `tests/test_strategy_generator.py`: Added `test_generator_mtf_allowed_timeframes_normalizes_duplicates` to explicitly prove that `(15, 5, 5)` normalizes predictably to `[5, 15]` in the provenance configuration.
- `tests/test_strategy_generator.py`: Hardened `test_generator_mtf_probability_one_adds_timeframes` to assert that *every* generated non-empty condition receives a `"timeframe"` parameter when `mtf_probability = 1.0`.
## 2026-06-04 -Task 049E Strategy Generator MTF Condition Injection

### Added
- `strategy_engine/generator.py`: Added `allowed_timeframes` (tuple of positive ints) and `mtf_probability` (float between 0.0 and 1.0) to `generate_strategies`. This allows the generator to optionally inject a `"timeframe"` parameter into the generated condition params to create multi-timeframe strategies.
- `strategy_engine/generator.py`: Added provenance recording for `allowed_timeframes` and `mtf_probability`.
- `tests/test_strategy_generator.py`: Added 11 focused unit tests verifying the new MTF generator controls, including deterministic behavior checks, validation, provenance, and backtestability.

### Changed
- `strategy_engine/generator.py`: The generator now defaults to MTF disabled (`mtf_probability=0.0`, `allowed_timeframes=()`). Default RNG calls remain entirely identical to ensure backward compatibility and test determinism for base-timeframe strategies.
## 2026-06-04 -Task 049D-Codex MTF Engine Integration Review & Hardening

### Fixed
- `backtest_engine/runner.py`: Fixed `_compute_indicator_on_htf()` for `VOLUME_SMA` so that it returns both the `VOLUME_SMA` column and the underlying `VOLUME` column. This ensures the evaluator can correctly compare MTF volume against its MTF SMA.

### Strengthened Tests
- `tests/test_backtest_engine.py`: Added 9 integration tests proving `run_backtest` correctly generates signals for `SMA`, `RSI`, `ATR`, `VOLUME`, `VOLUME_SMA`, and `MACD` using MTF conditions.
- `tests/test_backtest_engine.py`: Proven that MTF SMA triggers no trades before HTF availability and that entries are strictly at the next bar open (no future leak).
- `tests/test_backtest_engine.py`: Proven that incomplete final HTF candles are dropped and do not generate false signals at the end of the backtest.
- `tests/test_indicators.py`: Added `test_evaluate_volume_sma_mtf_missing_volume_tf_false` to prove graceful degradation when MTF SMA exists but MTF volume is missing.
## 2026-06-04 -Task 049C-Codex Evaluator MTF Resolution Review & Hardening

### Fixed
- `strategy_engine/evaluator.py`: Fixed `VOLUME` and `VOLUME_SMA` multi-timeframe condition evaluation to correctly read `volume_tf_{N}` when a timeframe is specified, rather than hardcoding the base `"volume"` column.
- `strategy_engine/evaluator.py`: Cleaned non-ASCII characters (`) from docstrings to prevent encoding artifacts.

### Strengthened Tests
- `tests/test_indicators.py`: Added comprehensive unit tests for MTF `VOLUME` and MTF `VOLUME_SMA` evaluations, proving correct column selection and graceful degradation to `False` for missing/NaN MTF values.
## 2026-06-04 -Task 049C Evaluator MTF Column Resolution

### Changed
- `strategy_engine/evaluator.py`: Updated `_eval_macd()` to support multi-timeframe condition evaluation by checking `params.get("timeframe")` and using the `_tf_{N}` suffixed column names (e.g. `macd_line_tf_5`).
- `strategy_engine/evaluator.py`: Updated `evaluate_condition()` to pass `cond.params` into `_eval_macd()`.
- Base MACD behavior remains completely unchanged. Missing or NaN MTF columns safely return `False`.

### Added
- `tests/test_indicators.py`: Added evaluator tests for MTF MACD crossover (`test_evaluate_macd_mtf_crossover`), missing MTF MACD columns (`test_evaluate_macd_mtf_missing_columns_false`), and NaN MTF MACD values (`test_evaluate_macd_mtf_nan_values_false`).
- `tests/test_backtest_engine.py`: Added full backtest smoke test for MTF MACD condition to prove it runs without crashing (`test_mtf_macd_condition_in_backtest`).
## 2026-06-04 -Task 049B-Codex3 Encoding Artifact Cleanup

### Fixed
- Replaced non-ASCII CP1252-corrupted encoding artifacts with standard ASCII characters (`-`, `...`, `<=`, `->`) in `runner.py`, `test_mtf_precompute.py`, and `changelog.md`.

## 2026-06-04 -Task 049B-Codex Runner MTF Precompute Review & Hardening

### Fixed
- `backtest_engine/runner.py`: Fixed resample deduplication -resampled DataFrames are now cached per timeframe via `resampled_cache` dict (was per-indicator+timeframe key, causing redundant resamples for SMA(tf=5) + RSI(tf=5)).
- `backtest_engine/runner.py`: `_validate_mtf_timeframe()` now explicitly rejects `bool` values (`isinstance(tf, bool)` guard) since `bool` is a subclass of `int` and would silently accept `True`/`False`.
- `tests/test_mtf_precompute.py`: Removed generic `pytest.raises(Exception)` test for missing volume; replaced with specific `ResamplerError` assertion.

### Strengthened Tests
- 2 spy-based dedup tests: `test_mtf_resample_called_once_per_timeframe` (3 indicators on tf=5 -> 1 resample), `test_mtf_resample_called_once_per_distinct_timeframe` (tf=5 + tf=15 -> 2 resamples).
- 2 exact alignment tests: `test_mtf_basic_alignment_exact_values` (deterministic close -> exact NaN/value at each bar), `test_mtf_no_future_leak_available_at_source` (per-row source-candle verification).
- 2 incomplete-candle tests: `test_mtf_incomplete_final_candle_does_not_create_new_value` (partial group dropped -> no value), `test_mtf_last_complete_value_forward_fills` (3 complete candles -> forward-fill behavior).
- `test_mtf_timeframe_bool_rejected` -verifies `True`/`False` are rejected.
- `test_mtf_missing_volume_column_clear_error` -asserts specific `ResamplerError` with 'volume' in message.
- 6 `_col()` tests: SMA/RSI/ATR/VOLUME/VOLUME_SMA save base name, suffixed MTF name, and base-without-timeframe name.

### Verification
- `python -m pytest tests/test_mtf_precompute.py -v` -**36 passed** in 1.54 s.
- `python -m pytest tests/ -q` -**841 passed**, 1 known benign warning.


## 2026-06-04 -Task 049B Runner MTF Precompute Implementation

### Added
- `strategy_engine/evaluator.py`: Updated `_col()` to append `_tf_{timeframe}` suffix when params includes `"timeframe"` key -column naming consistent between precompute and future evaluator use.
- `backtest_engine/runner.py`: Extended `_precompute_indicators()` with MTF code path. Added 6 private helpers: `_infer_base_minutes()`, `_validate_mtf_timeframe()`, `_resample_for_mtf()`, `_drop_incomplete_final_htf_group()`, `_compute_indicator_on_htf()`, `_merge_htf_indicator()`, `_compute_base_indicator()`.  Conditions with `params["timeframe"]` are resampled -> indicator computed -> `merge_asof(direction="backward")` merged back via `available_at`.  Base-only behavior fully preserved.
- `tests/test_mtf_precompute.py`: 23 focused tests covering base-behavior unchanged, timeframe validation (equal-base no-op, too-small, not-multiple, non-int), timeframe inference, no-future-leak merge alignment, exact-boundary visibility, incomplete-final-candle dropped/not-dropped, indicator column existence (SMA/RSI/ATR/MACD/VOLUME_SMA), multiple independent timeframes, dedup, missing-column safety, and full backtest smoke.

### Changed
- `backtest_engine/runner.py`: `_precompute_indicators()` refactored -base indicator logic extracted to `_compute_base_indicator()`.

### Verification
- `python -m pytest tests/test_backtest_engine.py tests/test_mtf_precompute.py tests/test_indicators.py tests/test_resampler.py tests/test_strategy_generator.py -v` -**112 passed** in 3.12 s.
- `python -m pytest tests/ -q` -**828 passed**, 1 known benign warning.


## 2026-06-04 -Task 049A-DocPolish MTF Design Encoding Cleanup

### Cleaned
- Removed duplicated ------------------------------------------------------2.7.
- Verified no `?` artifacts, `To be verified` stale wording, or `partial candle available` language remain.
- Confirmed incomplete final HTF candle rule is consistently documented as *dropped* across ------4.6, -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------8.1.6).

### Changed

- `backtest_engine/runner.py`: `run_backtest()` now accepts optional `point_value` and `instrument` parameters.  When an `InstrumentProfile` is provided, `point_value`, `tick_size`, `commission_value`, and `slippage_ticks` are sourced from it (individual keyword args take precedence).  All PnL calculations (trade exit, MTM equity, end-of-data close) now multiply raw price movement by `point_value` to produce dollar-denominated PnL.  Assumptions dict now includes `point_value` and `instrument` symbol.  Default behaviour (no instrument, point_value=1.0) is unchanged.

### Added tests

- `test_instrument_point_value_scales_pnl` - ES futures (point_value=50) -> PnL is exactly 50-?
- `test_instrument_tick_size_slippage_interaction` - same ES instrument with/without slippage -> slippage reduces PnL.
- `test_instrument_accounting_identity_holds` - identity holds with point_value -?兜?1 and non-zero commission.
- `test_instrument_assumptions_recorded` - point_value and instrument symbol in assumptions.
- `test_instrument_default_behavior_unchanged` - no instrument -> backward-compatible defaults.

### Verification

- `python -m compileall app core data_engine strategy_engine backtest_engine repository reports tests` - passed, zero errors.
- `python -m pytest tests/ -q` - **99 passed**, 1 benign warning.

## 2026-06-01 - Prototype v0.0.1 Acceptance Notes

### Acceptance Status: --?ACCEPTED

The Prototype v0.0.1 milestone is **complete**.  All 14 items in SOUL.md ----------------------------------------------------------------------------------------------------------------------------------------------------------------3.8 Goal | Status | Module / evidence |
|---|---|---|---|
| 1 | Launch PySide6 main window | --?| `app/main.py`, `app/ui/main_window.py` |
| 2 | Create or open project folder | --?| `repository/project_repo.py` (SQLite + folder tree) |
| 3 | Import OHLCV data | --?| `data_engine/importers/csv_importer.py`, normalizer |
| 4 | Display data table | --?| `CandlestickChart` on Data page |
| 5 | Display candlestick chart | --?| `app/widgets/candlestick_chart.py` (pyqtgraph) |
| 6 | Resample 1-min -> 5-min bars | --?| `data_engine/resampler.py` (+ timestamp safety) |
| 7 | Configure instrument profile | WARNING嚙?| Default `config/instruments.json` template only |
| 8 | Manually create one simple strategy | --?| `core/models/strategy.py` - four-block SMA strategy |
| 9 | Run event-driven backtest | --?| `backtest_engine/runner.py` - bar-by-bar, next-bar-open |
| 10 | Show trade list | --?| Report export (Markdown/HTML trade tables) |
| 11 | Show equity curve | WARNING嚙?| Structured `equity_curve` + `drawdown_curve` produced; not yet charted |
| 12 | Generate 10 random strategies | --?| `strategy_engine/generator.py` - deterministic, full provenance |
| 13 | Display strategy ranking | --?| `app/widgets/ranking_table.py` - color-coded, multi-dimensional |
| 14 | Export Markdown or HTML report | --?| `reports/generator.py` - XSS-safe, modern UI, disclaimer |

### Test Coverage

**94 tests, 0 failures, 1 benign pandas datetime-parsing warning.**

| Test file | Count | Area |
|---|---|---|
| `test_backtest_engine.py` | 21 | SMA, evaluator, backtest execution, metrics, accounting |
| `test_candlestick_chart.py` | 3 | Chart widget init, set_data, invalid-data logging |
| `test_csv_importer.py` | 17 | Normalizer, CSV import, dataset repository |
| `test_project_repo.py` | 9 | Project create, open, overwrite, close, DB constraints |
| `test_ranking_table.py` | 3 | Strategy service pipeline, ranking widget, determinism |
| `test_report_export.py` | 7 | Markdown/HTML templates, HTML escaping, service export |
| `test_resampler.py` | 19 | Resampling, timestamp safety, future-leak guards |
| `test_strategy_generator.py` | 15 | Generator determinism, provenance, ranking contract |

### Engine Integrity Checklist

- [x] No future leak in SMA calculation (backward-looking rolling window)
- [x] No future leak in resampler (`available_at` contract, `datetime` = candle start)
- [x] Signal confirmed at bar close, execute at **next** bar open
- [x] Per-side commission accounting (Trade.pnl = round-trip)
- [x] Accounting identity: `sum(Trade.pnl) == final_equity - initial_capital`
- [x] Max drawdown derived from equity/drawdown curve, not just closed-trade PnL
- [x] Last-bar unexecuted signals warn, not silently drop
- [x] No engine logic inside UI widgets (service-layer separation)
- [x] Deterministic random seed support for strategy generation
- [x] Multi-dimensional ranking (not net-profit-only)
- [x] Financial safety disclaimer in all report templates
- [x] HTML report output is XSS-safe (`html.escape` on all dynamic fields)

### Known Prototype Limitations

1. **Instrument profiles** are only a default JSON template - no UI editor, no tick-size/point-value hook in the backtest.
2. **Equity curve chart** - the structured `equity_curve` and `drawdown_curve` DataFrames are produced but not plotted in the UI (trade list only via reports).
3. **Short-side strategies** are structurally supported but not validated with short-specific test data patterns.
4. **Only one indicator (SMA)** - RSI, MACD, ATR, and cross-over conditions require extending `Condition`, `indicators.py`, and `evaluator.py`.
5. **CSV importer** handles single-file MultiCharts/TradeStation format only - no batch import, no Excel, no column-mapping wizard.
6. **Resampler** works on in-memory DataFrames - no persistence of resampled data to `data/resampled/` via the importer pipeline.
7. **No session filtering** - all bars are used, no day/night session templates applied.
8. **UI project wiring** - the toolbar buttons (New/Open Project, Save, Run, etc.) remain disabled; the app runs on mock data only.
9. **No OOS/validation/Monte Carlo/Walk-forward** - these are deliberate deferrals per MVP scope.
10. **No data quality checker** - the normalizer validates columns and datetimes but doesn't flag OHLC inconsistencies, gaps, or outlier jumps.

### Verification

- `python -m pytest tests/ -v` - **94 passed**, 1 known benign warning.
- `python -m compileall app core data_engine strategy_engine backtest_engine repository reports tests` - zero errors.
- `python app/main.py` - app launches, Data page shows candlestick chart, Results page shows ranked strategy table, Export Report produces valid Markdown and HTML.

### v0.1 Roadmap - Proposed Task Sequence

The v0.1 milestone focuses on **validation and anti-overfitting** - filling the
gap between "generates strategies" and "kills weak curve-fit strategies."
The sequence is ordered by dependency:

| # | Task | Rationale | Depends on |
|---|---|---|---|
| 008 | Instrument profile editor + backtest integration | Unblocks realistic PnL in points/dollars with proper tick size and point value | 002 |
| 009 | Equity curve & drawdown chart widget | Visualizes what reports already produce; closes SOUL ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------8.1.4: open=first, high=max, low=min, close=last, volume=sum.  Validates columns, dtypes, duplicate timestamps, NaT, empty input, and source/target ratio.
- `tests/test_resampler.py` - 17 pytest tests covering exact 5-min grouping, OHLCV correctness, timestamp convention, incomplete final group, unsorted input, 1->15 and 1->60 min resampling, identity no-op, and 8 error-case tests.

### Verification

- `python -m compileall app core data_engine repository tests` - passed, zero errors.
- `python -m pytest tests/ -v` - **43 passed** (17 new + 26 prior) in 5.06 s.

## 2026-05-31 - Task 003A Dataset contract hardening

### Changed

- `core/models/dataset.py`: added `project_id: int | None = None` field to `DatasetMeta` (PRD ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------15.2).
- `data_engine/normalizer.py` - `normalize()` function that maps MultiCharts/TradeStation-style column names to the internal OHLCV schema (`datetime, open, high, low, close, volume`). Handles two-column Date+Time, single-column datetime, PascalCase column aliases, sorting, and duplicate detection.
- `data_engine/importers/csv_importer.py` - `CsvImporter.import_file()` that reads a source CSV, normalizes it, saves the output to `data/raw/`, and returns a `(DataFrame, DatasetMeta)` tuple.
- `repository/dataset_repo.py` - `DatasetRepository` with `insert()`, `get_by_name()`, and `list_all()` for persisting dataset metadata in the project SQLite database.
- `sample_data/sample_ohlcv.csv` - 10-bar MultiCharts-style sample OHLCV data for tests.
- `tests/test_csv_importer.py` - 17 pytest tests covering normalizer column mapping, two-column datetime, single datetime, PascalCase columns, sorting, missing columns, duplicate datetimes, malformed dates, CSV import happy path, saved output verification, file-not-found, empty CSV, missing columns, DB insert/retrieve/list/get_nonexistent, and end-to-end import+persist.

### Changed

- `repository/db.py` - added `datasets` table to `SCHEMA_SQL` (PRD ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
