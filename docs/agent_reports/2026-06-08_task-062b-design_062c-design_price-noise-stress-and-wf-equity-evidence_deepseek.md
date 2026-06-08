Completed:
- Batch 062B-Design + 062C-Design — Price-Noise Stress Test Contract and WF Equity Evidence Surface Design.

Files changed:
- docs/price_noise_stress_contract_062B.md (created)
- docs/wf_equity_evidence_surface_design_062C.md (created)
- docs/changelog.md
- docs/task_board.md

Behavior changed:
- No production code changed (design-only batch).
- 062B: Price-noise stress test defined — Gaussian OHLC perturbation, deterministic seed, pnl_degradation_ratio pass/fail, pipeline config fields, 6 tests.
- 062C: WF equity evidence surface — line chart per window, empty/failure states, markdown/HTML expectations, 6 tests.

Tests run:
- N/A (design-only batch).

Assumptions:
- Gaussian noise model preserves no-future-leak property.
- WF equity chart uses existing PySide6 rendering (no new dependency).

Known risks:
- OHLC bar constraints may be violated after noise perturbation — documented as assumption with warning.

Reviewer focus:
- 062B: pass/fail metrics (pnl_degradation_ratio < 0.8 triggers flag).
- 062C: empty states (wf_store_equity=False, windows missing, all equity None).

Codex correction:
- The original OHLC-independent perturbation model was not accepted because it could emit invalid bars. Codex amended `docs/price_noise_stress_contract_062B.md` to require OHLC-preserving reconstruction.
- `pnl_degradation_ratio` is undefined when baseline PnL is non-positive; Codex added explicit warning/edge-case behavior.
- PDF chart embedding for WF equity is optional future polish, not required scope.
