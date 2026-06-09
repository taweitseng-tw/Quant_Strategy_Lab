# Post-063D/063E/063F Acceptance Smoke — Batch 064E

> Acceptance smoke for the MC worst-case equity, WF Efficiency display, and IS Baseline Precheck UI feature chain.
> Documentation only. No production code changed.
> Generated: 2026-06-09

---

## 1. Scope

This smoke verifies the three features implemented across Tasks 063D, 063E, and 063F:

| Feature | Engine (063D) | Widget (063E) | Report (063F) |
|---|---|---|---|
| MC worst-case equity curve | `worst_case_equity_curve` field, opt-in `collect_worst_case_equity`, labeled `curve_type="trade_step"` | Orange line chart, labeled `trade-step`, explicit surviving-trade disclaimer | Start/End equity + % change + trade-step disclaimer |
| WF Efficiency (WFE) display | Already in pipeline output | Widget line; `None` avg/median → `N/A` | Already present in reports |
| IS Baseline Quality Precheck UI | Existing PipelineConfig wiring | — (no widget surface needed) | — (controls only) |

---

## 2. Verification Results

### 2.1 MC Worst-Case Equity — Engine + Serialization

**Command:**
```
.venv/Scripts/python.exe -m pytest tests/test_monte_carlo.py tests/test_validation_pipeline_service.py -q
```
**Result: 98 passed in 3.50s**

Key verified behaviors:
- `worst_case_equity_curve` is `None` by default (opt-in)
- Collected when `collect_worst_case_equity=True`
- Not collected when `collect_worst_case_equity=False`
- Deterministic worst-iteration tie-break (lowest total_pnl → highest abs max_drawdown_pnl → lowest index)
- Zero-trades case returns empty list (not a crash)
- Serialized via PipelineConfig snapshot; opt-in wiring in `_mc_to_dict`

### 2.2 MC Worst-Case Equity — Widget + WFE + Precheck UI Wiring

**Command:**
```
.venv/Scripts/python.exe -m pytest tests/test_validation_summary.py tests/test_report_export.py tests/test_wfe_ui_wiring.py -q
```
**Result: 129 passed in 12.85s**

Key verified behaviors:
- MC equity chart shown when `worst_case_equity_curve` has ≥ 2 points
- MC equity chart absent when curve is `None` or has < 2 points
- Chart is an orange (`#FF8C00`) line, 150 px height
- **MC equity is explicitly labeled as `trade-step` evidence** — not bar-by-bar equity
- WFE line shown when WFE keys present; `None` average/median rendered as `N/A`
- WFE line absent when WFE keys missing from payload
- Precheck `run_is_baseline_quality_precheck` checkbox exists and default-off
- Precheck `fail_is_baseline_on_nonpositive_pnl` checkbox exists, dependent on parent
- Unchecking parent disables dependent; check parent re-enables dependent
- `_handle_run()` correctly wires both fields into `PipelineConfig`
- Price-noise controls: `Noise fraction:` label (not `%`), default-off

### 2.3 Data Workflow — Stale Failure Claim Retired

**Command:**
```
.venv/Scripts/python.exe -m pytest tests/test_data_page_wiring.py tests/test_dataset_persistence_wiring.py tests/test_project_service.py -q
```
**Result: 17 passed in 5.27s**

Key verified behaviors:
- Data import wiring tests pass
- Dataset persistence wiring passes
- Project service tests pass
- **No evidence of 13 pre-existing DataService failures** — this stale claim is retired from current context

### 2.4 git diff --check

**Command:**
```
git diff --check
```
**Result:** Passes with CRLF warnings only (standard for this project on Windows).

---

## 3. Feature Verification Matrix

| Surface | MC worst-case equity | WFE | Precheck |
|---|---|---|---|
| Engine serialization | ✅ 063D | ✅ (existing) | ✅ (existing) |
| UI controls | — | — | ✅ 063E |
| Widget display | ✅ 063E (trade-step disclaimer) | ✅ 063E (None→N/A) | — |
| Report display | ✅ 063F (trade-step disclaimer) | ✅ (existing) | — |

---

## 4. Key Wording Confirmation

Every surface that displays MC worst-case equity must clearly communicate that it is **trade-step surviving-trade evidence**, not bar-by-bar equity.

| Surface | Wording | Evidence |
|---|---|---|
| Widget chart label | `trade-step` | Codex review correction for 063E-Impl |
| Report label | `trade-step` | Codex review correction for 063F-Impl |
| Report disclaimer | "Explicitly states trade-step curve is from surviving trades only, not bar-by-bar equity" | changelog 063F-Impl entry |
| Engine field | `curve_type="trade_step"` | 063D-Impl changelog |

No surface was found to use raw `trade_step` as a user-facing label (all corrected to `trade-step`).

---

## 5. Remaining Known Limitations

| Limitation | Notes |
|---|---|
| MC worst-case equity only covers missed-trade MC | Other MC runners (slippage, combined) do not produce worst-case equity curves |
| MC worst-case equity is trade-step evidence, not bar-by-bar equity | This is an intentional limitation; bar-by-bar reconstruction is out of scope |
| WFE display covers average + median but not per-window equity chart | WF equity chart per window was implemented in 062H as a separate feature |
| No post-062/063 full-suite acceptance smoke exists | Feature-by-feature verification done per task; this doc provides the cross-feature view |

---

## 6. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Stale DataService failure claim could re-enter handoffs | Medium | Data workflow tests pass (17/17); context brief explicitly labels it as stale |
| MC worst-case equity could be mistaken for bar-by-bar equity | Low | Every surface carries explicit `trade-step` wording |
| WFE `None` handling in widget could regress | Low | Covered by widget tests (None avg/median → N/A) |
| .codegraph/ hygiene policy unresolved | Low | Flagged in 064D hygiene doc as needs Codex decision |

---

## 7. Next Suggested Task

**Codex decision on `.codegraph/` and repository hygiene policy.**

The 064D hygiene inventory identified:
- `.codegraph/` — local tool state (db, logs, PID); needs `.gitignore` policy or explicit leave-untracked decision
- `docs/archive/` — created but never committed; referenced by active docs
- 11 new agent reports + 8 design docs — untracked but standard task artifacts

Codex should decide the policy in a documentation-only review rather than a production implementation batch.
