# Codex Review — Task 053F — One-Bar Execution Delay Stress Test Design

**Date:** 2026-06-05  
**Verdict:** ✅ ACCEPTED  
**Reviewer:** Codex (acting)

---

## Acceptance Criteria Check

| # | Criterion | Status |
|---|---|---|
| 1 | Design note clearly defines one-bar delay stress behavior and scope | ✅ |
| 2 | Design identifies exact modules/files likely to change in future implementation | ✅ |
| 3 | Design preserves current baseline next-bar-open execution behavior | ✅ |
| 4 | Design explains no-future-leak assumptions and edge cases | ✅ |
| 5 | No production code is changed | ✅ |
| 6 | Agent report exists | ✅ |

## Findings

### Strengths

- **Clean API surface.** The `execution_delay_bars: int = 0` parameter on `run_backtest()` is a minimal, backward-compatible addition. Defaulting to 0 preserves byte-for-byte identical behavior — and the design explicitly specifies a test case for that.
- **State-machine approach is correct.** Using a 3-tuple `pending: ("enter", direction, countdown)` avoids the fundamental flaw of the current data-shift approach. No future-leak by construction.
- **In-flight signal blocking (Section 3.5).** The design correctly identifies that a delayed entry order should suppress new signals from overwriting it — treating it as "in flight and inescapable." This is conservative and correct.
- **SL/TP semantics preserved (Section 3.4).** The design correctly notes that SL/TP can only fire on open positions; during the delay window there is no position, so no intra-bar exit is possible. This accurately models real-world routing latency.
- **Edge-case coverage.** End-of-data handling (last-bar signal, second-to-last bar signal) is specified in the test requirements.

### Minor Observations (non-blocking)

- **Entry vs. Exit delay distinction.** The `pending` tuple is used for both entries and exits. The design focuses on entry delay but does not explicitly state whether exit signals are also delayed. For implementation, this should be clarified: either always delay only entry signals, or make it configurable. The simplest correct approach is to delay only entry signals (exits remain at next-bar-open).
- **`pending` tuple unpacking.** Changing from 2-tuple to 3-tuple will break any existing `action, direction = pending` unpacking. The implementation must audit all unpacking sites (there are 3 in the current `runner.py`). The existing code already unpacks `pending` in 2-tuple form at lines referencing `action, direction`.
- **Assumptions reporting.** The design correctly notes `execution_delay_bars` must appear in `BacktestResult.assumptions`. This is essential for provenance.

## Verification

```
python -m pytest tests/test_stress_test.py tests/test_backtest_engine.py -q
→ 70 passed in 1.29s

powershell -ExecutionPolicy Bypass -File scripts/agent_status.ps1
→ Clean: only docs/ changes + 2 new untracked docs files
→ No production code touched
```

## Conclusion

The design is thorough, correct, and respects all constraints. **Accepted.** Next task: Task 053F-Impl.
