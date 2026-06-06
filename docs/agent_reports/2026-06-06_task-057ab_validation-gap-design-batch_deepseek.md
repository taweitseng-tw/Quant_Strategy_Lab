# Batch 057A-057B — Validation Gap Design Batch

> Agent: DeepSeek V4 Pro
> Date: 2026-06-06

## Completed

### 057A — Monte Carlo Bootstrap + CI Design

`docs/monte_carlo_bootstrap_ci_design_057A.md`:

- `run_bootstrap_monte_carlo()` — separate function, trade-sequence resampling with replacement.
- Reuses `MonteCarloResult` schema; adds `confidence_intervals` and `worst_case_equity` fields.
- Deterministic seeds, 200 iterations default.
- 9 test plan cases. Worst-case equity curve deferred to v0.3.

### 057B — Walk-Forward Per-Window Equity Design

`docs/walk_forward_equity_persistence_design_057B.md`:

- One new field: `WalkForwardWindow.equity_curve: list[float] | None`.
- `store_equity=False` default; ~16 KB typical memory overhead.
- Serialization via `asdict()`, backward-compatible, no persistence.
- 7 test plan cases.

### Independent & Reviewable

Both designs are self-contained — 057B does not depend on 057A.

## Files Changed

| File | Change |
|---|---|
| `docs/monte_carlo_bootstrap_ci_design_057A.md` | **Created** |
| `docs/walk_forward_equity_persistence_design_057B.md` | **Created** |
| `docs/changelog.md` | Batch entry |
| `docs/task_board.md` | 057A-057B -> Done |

## Verification

- **No production code changed**.
- **`git diff --check`**: passes.
