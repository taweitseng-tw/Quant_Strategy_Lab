# Codex Review - Task 062F-Impl + 062G-Design

Decision: PASS after Codex corrections

Score: 9.0/10 after corrections. Original DeepSeek output was close but below strict acceptance because it missed required assertions from the task card.

Findings:
- [P2] `tests/test_validation_pipeline_service.py`: opt-in price-noise test did not assert `pnl_degradation_ratio`, `survival_rate`, or `research_only=True`.
- [P3] `tests/test_validation_pipeline_service.py`: deterministic coverage compared only one metric instead of the serialized price-noise stress result.
- [P3] `docs/wf_equity_widget_test_contract_062G.md`: chart visibility table used ambiguous symbols instead of explicit visible/hidden states.

Required fixes completed:
- Added the missing contract assertions.
- Added explicit-off coverage.
- Tightened deterministic comparison to the full `price_noise` stress dict.
- Rewrote the 062G chart visibility table with explicit `Yes` / `No` values.

Architecture risk:
- Low. Pipeline integration is default-off, service-layer only, and appends the optional price-noise stress result before Monte Carlo.

Verification:
- `.\.venv\Scripts\python.exe -m pytest tests\test_validation_pipeline_service.py -q` - 40 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_stress_test.py -q` - 34 passed.
- `.\.venv\Scripts\python.exe -m pytest tests -q` - 1269 passed.
- `git diff --check` - passed.
- `powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1` - passed.

Next assignment:
- Batch 062H-Impl + 062I-Design: implement the WF equity chart widget in `ValidationSummary`, and design price-noise UI config controls without wiring them yet.
