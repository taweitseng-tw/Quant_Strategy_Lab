# Backtest Correctness Hardening Acceptance Audit - Tasks 487-492

Date: 2026-06-11

## Decision

PASS after Codex correction.

The Event-Driven Backtest Performance / Correctness Hardening milestone is accepted for its stated scope: same-bar stop-loss / take-profit ambiguity coverage and conservative tick-size fill alignment. This is a milestone acceptance, not a full formal release decision.

## Scope Reviewed

- Same-bar stop-loss-first behavior for long and short positions.
- Gap-through ambiguity behavior where stop-loss and take-profit are both reachable on the same bar.
- Conservative tick-size alignment for buy-side and sell-side fills.
- Explicit `end_of_data` mark-to-close exception for forced liquidation.
- Regression coverage in `tests/test_backtest_engine.py`.

## Accepted Capabilities

### Same-Bar Ambiguity

The current runner keeps the project rule that same-bar ambiguity is resolved conservatively: stop-loss wins before take-profit when both are touched in the same bar.

Regression coverage includes:

- Short same-bar ambiguity where stop-loss wins.
- Long gap-through ambiguity where stop-loss wins at the conservative open path.
- Short gap-through ambiguity where stop-loss wins at the conservative open path.

### Conservative Tick Alignment

The runner aligns transaction fills to tick size in the unfavorable direction:

- Buy fills use ceiling alignment.
- Sell fills use floor alignment.
- Stop-loss, take-profit, entry, and session-end exit paths route through the correct side-aware alignment.

The accepted design keeps forced `end_of_data` liquidation at the last close without slippage or tick rounding. This is a documented accounting mark-to-close exception, not a tradable fill assumption.

## Verification

Focused verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_backtest_engine.py -q
```

Expected result for this acceptance round: all focused backtest engine tests pass.

Cleanliness check:

```powershell
git diff --check
```

Expected result: no whitespace errors; CRLF warnings are acceptable in this repository.

## Findings Fixed by Codex

- Removed overclaiming that the milestone is a formal release-ready decision.
- Replaced stale test-count language with command-based verification expectations.
- Clarified that accepted scope is backtest correctness hardening only.
- Added a clear boundary for the `end_of_data` mark-to-close exception.

## Remaining Risk

No blocker remains inside this milestone scope. Future release work still needs broader desktop workflow acceptance, packaging evidence, and end-to-end user walkthrough coverage before a formal public release.

## Next Recommended Direction

Create a compact version roadmap and 1.0 gap rebaseline so future rounds can report:

- completed six-task rounds,
- remaining milestone rounds,
- formal 1.0 blockers,
- and the difference between developer-alpha readiness and formal release readiness.
