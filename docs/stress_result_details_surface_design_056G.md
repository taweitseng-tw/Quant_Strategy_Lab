# Stress Result Details Reporting Surface Design — Task 056G

> Design-only. No production code changed.

## 1. Current Stress Result Display

### 1.1 ValidationSummary Widget (`app/widgets/validation_summary.py`)

```python
# Current — only test_name + passed + degradation PnL:
for s in stress:
    name = s.get("test_name", "?")
    passed = "✓" if s.get("passed", False) else "✗"
    deg = s.get("degradation", {})
    pnl_deg = deg.get("total_pnl", 0)
    stress_lines.append(f"{name}: {passed}  PnL Δ={pnl_deg:.1%}")
```

**What it shows**: one line per stress test with name, pass/fail, and PnL degradation %.

**What it does NOT show**: `assumptions`, `warnings`, `threshold` — all three are available in the serialized dicts after Task 056F-Fix but not displayed.

### 1.2 Markdown Report (`reports/generator.py`)

```python
# Current:
for s in vr.get("stress_results", []):
    deg = s.get("degradation", {}).get("total_pnl", 0)
    passed = "✓ passed" if s.get("passed") else "✗ failed"
    lines.append(f"- **Stress ({s.get('test_name','?')})**: {passed} PnL Δ={deg:.1%}")
```

### 1.3 HTML Report (`reports/generator.py`)

```python
# Current:
for s in vr.get("stress_results", []):
    deg = s.get("degradation", {}).get("total_pnl", 0)
    name = html.escape(str(s.get("test_name", "?")))
    parts.append(f'<p><b>Stress ({name}):</b> PnL Δ={deg:.1%}</p>')
```

## 2. Available Data (After Task 056F-Fix)

Each stress result dict now includes:

| Key | Type | Always present? | Example (remove-best-N) |
|---|---|---|---|
| `test_name` | `str` | Yes | `"remove_best_n_trades"` |
| `passed` | `bool` | Yes | `True`/`False` |
| `degradation` | `dict` | Yes | `{"total_pnl": -0.833333, ...}` |
| `stressed_metrics` | `dict` | Yes | `{"total_pnl": 20.0, ...}` |
| `assumptions` | `dict` | Most | `{"n": 2, "pnl_loss_ratio": 0.833, ...}` |
| `warnings` | `list` | Most | `["Insufficient trades..."]` |
| `threshold` | `dict` | Most | `{"max_pnl_loss": 0.30}` |

Existing stress tests (commission, slippage, one-bar delay, parameter perturbation) also have these fields, but their assumptions are implementation details the user rarely needs to see. Only remove-best-N trades has assumptions the user explicitly configured.

## 3. Design Decisions

### 3.1 Which Fields to Show

| Stress Test | Show assumptions? | Rationale |
|---|---|---|
| `commission_2.0x`, `slippage_2.0x` | No | Named multiplier; assumptions are obvious from test_name |
| `one_bar_delay` | No | Always 1-bar delay; name is self-documenting |
| `parameter_perturbation` | No | Variant count is in assumptions but not user-configured |
| `remove_best_n_trades` | **Yes** | User configured `n` and `degradation_threshold`; needs to see `pnl_loss_ratio`, `removed_count`, and `warnings` |

**Decision**: Only display assumptions/warnings/threshold for stress tests that have user-configured parameters. For now, this means only `remove_best_n_trades`. Future stress tests can follow the same pattern.

### 3.2 Where to Show — Inline vs. Separate Card

**Decision: Inline sub-lines under each stress entry.**

A separate "Stress Details" card would require dynamic layout changes and increase widget complexity. Inline sub-lines keep the display compact and identical across widget/report formats.

### 3.3 Widget Display (Proposed)

Current:
```
Stress Tests
commission_2.0x: ✓  PnL Δ=-15.0%
slippage_2.0x: ✓  PnL Δ=-8.0%
one_bar_delay: ✓  PnL Δ=-12.0%
remove_best_n_trades: ✗  PnL Δ=-83.3%
```

Proposed (only remove-best-n gains sub-lines):
```
Stress Tests
commission_2.0x: ✓  PnL Δ=-15.0%
slippage_2.0x: ✓  PnL Δ=-8.0%
one_bar_delay: ✓  PnL Δ=-12.0%
remove_best_n_trades: ✗  PnL Δ=-83.3%
  → Removed: 2 of 4 trades (n=2, pnl_loss=0.833, threshold=0.30)
  → ⚠ Insufficient trades for remove-best-n stress test (trades=2, n=5)
```

**Implementation logic**:
- After the main stress line, check if `assumptions` exists with meaningful user-configured keys.
- For `remove_best_n_trades`: show `n`, `removed_count`, `surviving_count`, `pnl_loss_ratio`, and `threshold["max_pnl_loss"]`.
- If `warnings` is non-empty, append each warning as a sub-line.
- Skip sub-lines for stress tests whose assumptions are entirely engine-generated.

### 3.4 Markdown Report (Proposed)

```markdown
- **Stress (remove_best_n_trades)**: ✗ failed PnL Δ=-83.3%
  - Removed: 2 of 4 trades, pnl_loss_ratio=0.833, threshold=0.30
  - ⚠ Insufficient trades for remove-best-n stress test (trades=2, n=5)
```

### 3.5 HTML Report (Proposed)

```html
<p><b>Stress (remove_best_n_trades):</b> <span class="fail">✗ failed</span> PnL Δ=-83.3%</p>
<div class="stress-detail">Removed: 2 of 4 trades, pnl_loss_ratio=0.833, threshold=0.30</div>
<div class="warning-item">⚠ Insufficient trades for remove-best-n stress test (trades=2, n=5)</div>
```

## 4. Implementation Surface (Task 056G-Impl)

| File | Change |
|---|---|
| `app/widgets/validation_summary.py` | Extend stress loop: after main line, emit sub-lines for rich-assumptions tests |
| `reports/generator.py` | Extend both `_format_markdown_validation()` and `_format_html_validation()` stress loops with sub-lines |
| `tests/test_validation_summary.py` | Verify stress detail sub-lines appear for remove-best-N |
| `tests/test_report_export.py` | Verify stress detail sub-lines in both formats |
| `docs/changelog.md` + `docs/task_board.md` | Standard update |

## 5. Acceptance Criteria (Task 056G-Impl)

1. ValidationSummary widget sub-lines appear for `remove_best_n_trades` when `assumptions` exist.
2. Widget sub-lines include `n`, `removed_count`, `surviving_count`, `pnl_loss_ratio`, and `warnings` when present.
3. Widget sub-lines do NOT appear for existing stress tests (commission, slippage, delay, perturbation).
4. Markdown report includes stress detail sub-lines matching widget output.
5. HTML report includes stress detail sub-lines matching widget output.
6. Missing `assumptions` or empty `warnings` does not crash any surface.
7. Existing stress display behavior is unchanged.
8. Full test suite passes.

## 6. Design metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-06
- **Dependencies**: Task 056F-Fix (assumptions serialization) — Done
- **Blocked by**: Nothing
