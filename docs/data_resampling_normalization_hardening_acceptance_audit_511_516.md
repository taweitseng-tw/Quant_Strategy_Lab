# Data Resampling and Normalization Hardening Acceptance Audit - Tasks 511-516

Date: 2026-06-11

## Decision

PASS after Codex correction.

The Data Resampling and Normalization Hardening milestone is accepted for its stated scope: schema normalizer hardening, duplicate timestamp diagnostics, resampler bounds validation, and partial constituent-bar warnings.

---

## Scope Reviewed

- **Normalizer Validation**: Added checks for price bounds (`open/high/low/close > 0`), volume bounds (`volume >= 0`), and finite values (rejecting `NaN` and `inf` in OHLCV).
- **Out-of-Order Warnings**: Emitted a `UserWarning` if input datetimes are not monotonic increasing, without halting execution.
- **Duplicate Diagnostics**: Improved duplicate timestamp reporting by showing specific duplicate timestamps and total count.
- **Resampler Bounds Checks**: Re-validated OHLCV bounds inside the resampler to prevent corrupt data from propagating.
- **Identity-Mode Validation**: Ensured validations are not bypassed when resampling with `target_minutes == source_minutes`.
- **Constituent-Bar Warnings**: Added warnings for non-boundary target bars that contain fewer source bars than expected while still producing a resampled bar.
- **Unit Tests**: Verified 46 focused tests in `tests/test_csv_importer.py` and `tests/test_resampler.py`.

---

## Accepted Capabilities

### 1. Normalizer Hardening
- Rejects rows with price values `<= 0` or volume `< 0` with descriptive error messages.
- Rejects infinite or null value entries in OHLCV columns.
- Safely sorts out-of-order datetimes but issues a `UserWarning` so that data pipeline issues are visible to the caller.
- Lists sample duplicate timestamps (up to 5) to help developers quickly spot source errors.

### 2. Resampler Hardening
- Runs the same logical OHLC price/volume relationships and finite value checks.
- Identifies and issues warnings for resampled bars containing incomplete constituent counts, except naturally partial boundary bars.
- Still drops fully empty time slots; this remains an accepted limitation for this slice and is tracked as future session/gap-aware work.

---

## Verification

### Tests Executed
```bash
.\.venv\Scripts\python.exe -m pytest tests/test_csv_importer.py tests/test_resampler.py -q
```
Result: **46 passed**.

### Whitespace Verification
```bash
git diff --check
```
Result: **Clean** (CRLF warnings only).

---

## Findings Fixed by Codex

- **Identity-Mode Validation Bypass**: Verified the prior Codex correction that moved same-period resampling after validation blocks, with regression coverage.
- **Changelog Hygiene**: Removed unrelated legacy encoding churn from the changelog diff during acceptance review.
- **Scope Hygiene**: Removed non-functional production-code formatting churn from the acceptance audit bucket.

---

## Remaining Risk

- **Session Naivety**: The resampler relies on a simple time grid via `pd.Grouper`. Gaps or session transitions that do not align with the target period grid are still handled naively. Fully empty inner-session buckets can still be dropped without a dedicated gap metadata surface.
- **Database Type Parity**: SQLite storage does not enforce the same strict float/integer restrictions as NumPy/Pandas. Importers must remain the primary gatekeepers.

---

## Next Recommended Direction

Proceed to **Desktop Workflow and Chart Reliability** (Tasks 517-522) to polish user-facing chart components, dataset tables, and UI stability.
