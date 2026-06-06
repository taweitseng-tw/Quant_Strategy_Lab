# Batch 057A-057B Codex Review - Validation Gap Design Batch

## Verdict

Accepted with follow-up required before 057A implementation.

## Score

8.3 / 10

## Review Summary

The two-task design batch stayed within scope: only documentation, changelog, task board, and the completion report changed. The paired design workflow is working and is less tiring for the user without creating large code diffs.

Task 057B is implementation-ready. The proposed `WalkForwardWindow.equity_curve: list[float] | None = None`, default-off `store_equity`, and conditional pipeline serialization are small, backward-compatible, and testable.

Task 057A is useful but needs one design hardening pass before implementation. The current design mixes v0.2 confidence intervals with deferred worst-case equity projection, and a few test assumptions are statistically unsafe.

## Findings

- 057A: Do not add `worst_case_equity` in v0.2 if worst-case equity projection is deferred. The current document says both "add field" and "defer to v0.3", which would confuse implementation.
- 057A: Avoid tests that assert bootstrap is always more conservative than baseline. Bootstrap resampling can improve or worsen metrics depending on sampled trades.
- 057A: Avoid tests claiming a single run proves "95% of means fall within CI"; use deterministic structural and boundary checks instead.
- 057A: Use local RNG state (`random.Random(base_seed + i)` or equivalent) rather than global `random.seed(...)`, matching the safer existing pattern in later MC code.
- 057B: Good to implement next, but keep display/report charts deferred. Implementation should only add the optional engine field, pipeline config flag, conditional serialization, and focused tests.

## Verification

- Reviewed `docs/monte_carlo_bootstrap_ci_design_057A.md`.
- Reviewed `docs/walk_forward_equity_persistence_design_057B.md`.
- Reviewed `docs/agent_reports/2026-06-06_task-057ab_validation-gap-design-batch_deepseek.md`.
- Inspected current `validation_engine/monte_carlo.py`, `validation_engine/walk_forward.py`, and `app/services/validation_pipeline_service.py`.
- Ran `git diff --check`: passed.
- Confirmed no production code or tests were changed.

## Next Task

Batch 057A-Fix + 057B-Impl.
