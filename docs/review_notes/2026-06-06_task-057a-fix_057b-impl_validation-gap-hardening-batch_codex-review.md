# Batch 057A-Fix + 057B-Impl Codex Review - Validation Gap Hardening

## Verdict

Accepted.

## Score

9.0 / 10

## Review Summary

This batch is a good example of the new two-task workflow working safely. It paired one documentation hardening task with one narrow implementation task, without expanding into UI, reports, persistence, or Monte Carlo production code.

Task 057A-Fix resolved the key design contradictions: `worst_case_equity` is no longer part of the v0.2 bootstrap schema, the test plan no longer claims bootstrap is always more conservative, and the design now specifies local RNG use.

Task 057B-Impl is accepted. Walk-forward equity persistence is default-off, backward-compatible, and covered by focused engine and pipeline tests. Serialization only includes `windows` when equity curves are actually present.

## Findings

- No blocking findings.
- Minor follow-up for 057A implementation: the future bootstrap test named `test_bootstrap_stressed_metrics_differ_from_baseline` should use deliberately heterogeneous synthetic trades. Bootstrap samples can equal baseline by chance or by homogeneous input, so the assertion must be deterministic and data-aware.
- `_wf_to_dict()` now imports `asdict` locally even though the module already imports it at the top. This is harmless, but a later cleanup can remove the local import if desired.

## Verification

- Reviewed `validation_engine/walk_forward.py`.
- Reviewed `app/services/validation_pipeline_service.py`.
- Reviewed `tests/test_walk_forward.py` and `tests/test_validation_pipeline_service.py`.
- Reviewed `docs/monte_carlo_bootstrap_ci_design_057A.md`.
- Confirmed `validation_engine/monte_carlo.py` was not changed.
- Ran focused tests: 69 passed.
- Ran full suite: 1047 passed, 1 pre-existing warning.
- Ran `git diff --check`: passed.

## Next Task

Batch 057A-Impl + 057C-Design - Monte Carlo Bootstrap Engine and Surface Design.
