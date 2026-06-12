# Desktop Workflow and Chart/Table Reliability Acceptance Audit - Tasks 529-534

Date: 2026-06-12

## Decision

PASS with residual test gap.

The Desktop Workflow and Chart/Table Reliability milestone is accepted for its stated scope: stale chart reset handling, ranking-table row limits, and validation-run busy cursor restoration. This is not a full desktop release decision.

## Audit Against Design

| Design Requirement | Implementation | Status |
|---|---|---|
| `CandlestickChart.clear()` | Clears rendered candlestick data, resets pyqtgraph/fallback state, and sets an empty title/message | PASS |
| Chart clear on new project | `self.data_chart.clear()` called in `_handle_new_project` | PASS |
| Chart clear on open project | `self.data_chart.clear()` called in `_handle_open_project` | PASS |
| Chart clear on import failure | `self.data_chart.clear()` called in `_on_import_failure` | PASS |
| Reuse `EquityCurveChart.clear()` | Existing clear behavior retained; no duplicate implementation needed | PASS |
| `RankingTable` 500-row guard | Top 500 rows displayed and status text shows the truncated total | PASS |
| Busy cursor in `_handle_run` | `setOverrideCursor(WaitCursor)` with `restoreOverrideCursor()` in `finally` | PASS by code review |
| Candlestick clear test | `test_candlestick_chart_clear_resets_state` | PASS |
| Ranking row-limit test | `test_ranking_table_500_row_display_guard` | PASS |
| Project-change clear coverage | Covered indirectly by active-dataset reset tests | PASS |
| Wait-cursor exception-path test | Not explicitly covered | RESIDUAL TEST GAP |

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_candlestick_chart.py tests/test_ranking_table.py tests/test_active_dataset.py -q
```

Result: 25 passed.

```powershell
git diff --check
```

Result: passed with CRLF warnings only.

## Findings Fixed by Codex

- Replaced mojibake-heavy audit text with ASCII-only acceptance wording.
- Corrected overclaiming from "all design items pass" to "pass with residual test gap" because wait-cursor exception-path behavior is accepted by code review but not explicitly tested.
- Preserved the remaining risk that validation still runs synchronously on the Qt main thread.
- Replaced `Next: None` with the next concrete milestone block.

## Remaining Risks

- Validation still blocks the Qt main thread. The busy cursor improves user feedback but does not make validation asynchronous or cancellable.
- Wait-cursor restoration does not yet have an explicit exception-path UI test.
- The ranking table row guard limits rendered rows only; the complete ranking data still needs a future paging/filtering design if users need to inspect thousands of strategies interactively.

## Next Recommended Direction

Proceed to validation pipeline responsiveness design. The next milestone should define a worker/cancel/progress architecture without implementing a broad threading rewrite in the same round.
