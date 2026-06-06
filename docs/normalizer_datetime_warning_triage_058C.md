# Normalizer Datetime Warning Triage — Task 058C

> Design-only. No code changed in `data_engine/normalizer.py`.

## 1. Current Warning

```
UserWarning: Could not infer format, so each element will be parsed individually, falling back to dateutil.
To ensure parsing is consistent and as-expected, please specify a format.
df["datetime"] = pd.to_datetime(df[dt_col], errors="coerce")
```

Location: `data_engine/normalizer.py:80`. Test: `test_normalize_malformed_datetime_raises`.

## 2. Why Non-Blocking

- Only triggers on the **malformed datetime test** — deliberately malformed input.
- Normal data paths (sample OHLCV, TXF, generated DataFrames) use `pd.to_datetime()` with explicit formats or well-formed ISO strings that don't trigger this warning.
- Warning is from pandas internals, not from QSL logic defects.

## 3. Candidate Fixes

| Option | Description | Risk |
|---|---|---|
| A: Suppress via `warnings.filterwarnings` in test | Hide the warning in the specific test | Low |
| B: Add explicit `format=` param to `pd.to_datetime` call | Parse with known format when possible | Medium — format may differ per data source |
| C: Leave as-is | Accept the pre-existing warning | None |

## 4. Recommendation

**Option A — suppress in the specific failing test using `pytest.warns` or `pytest.mark.filterwarnings`.**

- Single-line change in `tests/test_csv_importer.py`.
- Does not change production normalizer behavior.
- Removes the only warning from CI output.

## 5. Next Batch

**Task 058D — Suppress normalizer datetime warning in test + verify full suite reports 0 warnings.**

## 6. Metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-07
