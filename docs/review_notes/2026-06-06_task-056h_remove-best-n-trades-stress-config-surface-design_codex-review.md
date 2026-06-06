# Codex Review - Task 056H Remove Best N Trades Stress Config Surface Design

## Verdict

Accepted.

## Score

8.8 / 10

## Review Summary

The design correctly traces the current Validate page flow: `app/ui/main_window.py` constructs `PipelineConfig(mc_iterations=15, calc_wfe=calc_wfe)`, and the existing user-facing validation option is the WFE checkbox in the Validate header. The recommended minimal surface is reasonable: keep remove-best-N disabled by default, add an enable checkbox plus `n` and max PnL loss spinboxes, and pass those values into existing `PipelineConfig` fields.

The design preserves architecture boundaries: UI collects user intent, `PipelineConfig` carries configuration, the pipeline service invokes the engine, and display surfaces remain unchanged.

## Verified

- No production code changed.
- `docs/remove_best_n_trades_config_surface_design_056H.md` covers current config flow, recommended controls, defaults, coupling boundary, report visibility, and future tests.
- Source inspection confirms the current `PipelineConfig` construction and WFE checkbox wiring.
- `git diff --check` passed.

## Notes

- Minor precision issue: the design says `mc_iterations` is user-facing, but it is hard-coded in `_handle_run()`.
- Minor documentation quality issue: one control-shape block contains mojibake/box drawing artifacts. The surrounding text and tables are clear enough for implementation.
- The next implementation should add tests beside the existing WFE UI wiring tests rather than using a broader active-dataset test unless local constraints require it.
