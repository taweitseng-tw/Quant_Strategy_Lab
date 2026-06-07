# Provenance Schema and Integrity Verification Design — Task 059B

> Design-only. No production code changed.

## 1. Required Provenance Fields

Every archive manifest must carry these fields, organized into logical groups.

### 1.1 Archive Metadata

| Field | Type | Required | Description |
|---|---|---|---|
| `archive_version` | `str` | Yes | Schema version, e.g. `"1.0.0"` |
| `generated_at` | `str` (ISO 8601) | Yes | Archive creation timestamp |
| `generator_version` | `str` | Yes | QSL software version |
| `git_commit` | `str` | No | Git commit hash at archive time |

### 1.2 Strategy Provenance (SOUL §3.4)

| Field | Source | Required |
|---|---|---|
| `strategy_uid` | `strategies.strategy_uid` | Yes |
| `strategy_name` | `strategies.name` | Yes |
| `strategy_json` | `strategies.strategy_json` | Yes |
| `build_task_id` | `strategies.build_task_id` | Yes |
| `random_seed` | `build_tasks.random_seed` | Yes |
| `generator_config` | `build_tasks.config_json` | Yes |
| `fitness_version` | Hard-coded constant | Yes |
| `created_at` | `strategies.created_at` | Yes |

### 1.3 Dataset Provenance

| Field | Source | Required |
|---|---|---|
| `dataset_id` | `datasets.id` | Yes |
| `symbol` | `datasets.symbol` | Yes |
| `timeframe` | `datasets.timeframe` | Yes |
| `start_datetime` | `datasets.start_datetime` | Yes |
| `end_datetime` | `datasets.end_datetime` | Yes |
| `row_count` | `datasets.row_count` | Yes |
| `source_type` | `datasets.source_type` | Yes |
| `source_path` | `datasets.source_path` | No |
| `ohlcv_hash` | Computed (SHA-256 of Parquet bytes) | Yes |

### 1.4 Instrument Profile

| Field | Source | Required |
|---|---|---|
| `symbol` | `instruments.symbol` | Yes |
| `tick_size` | `instruments.tick_size` | Yes |
| `point_value` | `instruments.point_value` | Yes |
| `commission_type` | `instruments.commission_type` | Yes |
| `commission_value` | `instruments.commission_value` | Yes |
| `slippage_type` | `instruments.slippage_type` | Yes |
| `slippage_value` | `instruments.slippage_value` | Yes |

### 1.5 Backtest Assumptions

| Field | Source | Required |
|---|---|---|
| `execution_model` | `backtest_results.assumptions` | Yes |
| `commission_per_side` | `backtest_results.assumptions` | Yes |
| `slippage_per_side_ticks` | `backtest_results.assumptions` | Yes |
| `same_bar_ambiguity` | `backtest_results.assumptions` | Yes |
| `stop_take_profit_enabled` | `backtest_results.assumptions` | Yes |
| `execution_delay_bars` | `backtest_results.assumptions` | Yes |
| `session_end_time` | `backtest_results.assumptions` | Yes (if enabled) |

### 1.6 Validation Config

| Field | Source | Required |
|---|---|---|
| `train_ratio` | `PipelineConfig` | Yes |
| `validation_ratio` | `PipelineConfig` | Yes |
| `oos_ratio` | `PipelineConfig` | Yes |
| `stress_tests_enabled` | `PipelineConfig` | Yes (list) |
| `mc_iterations` | `PipelineConfig` | Yes |
| `wf_train_bars` | `PipelineConfig` | Yes |
| `wf_test_bars` | `PipelineConfig` | Yes |
| `elimination_config` | `PipelineConfig` | Yes |

### 1.7 Results Summary

| Field | Source | Required |
|---|---|---|
| `baseline_metrics` | `PipelineResult` | Yes |
| `oos_metrics` | `PipelineResult` | Yes (if available) |
| `elimination_passed` | `PipelineResult` | Yes |
| `stress_pass_count` | `PipelineResult` | Derived |
| `wf_pass_rate` | `PipelineResult` | Yes |

## 2. Integrity Verification

### 2.1 Content Hashes

| Artifact | Hash Algorithm | Purpose |
|---|---|---|
| `ohlcv.parquet` | SHA-256 | Detect data corruption |
| `strategy.json` | SHA-256 | Detect tampering |
| `validation_result.json` | SHA-256 | Detect tampering |
| All other JSON files | SHA-256 (per file) | Tampering detection |

Hashes stored in `manifest.json` under `content_hashes`.

### 2.2 Schema Version Handling

```
archive_version "1.0.0" → import with current reader
archive_version "2.0.0" → import only if reader >= 2.0.0
```

Importer checks `archive_version` before reading. Unknown major version → refuse with clear error message. Minor version bumps are backward-compatible.

### 2.3 Missing-File Detection

Importer reads `manifest.files[]` and checks each file exists. Missing file → `ArchiveIntegrityError`. Extra files are ignored (not an error).

### 2.4 Non-Financial-Advice Disclaimer

Every archive must include `disclaimer.txt` with the standard research-only disclaimer:

```
This archive is for research and backtesting purposes only.
Backtested performance does not guarantee future results.
Not financial advice. No live trading.
```

The disclaimer is ASCII text, not generated from a template. Importer verifies `disclaimer.txt` exists and is non-empty.

## 3. Next Implementation Batch

**Task 059C-Impl + 059D-Design — Archive module skeleton (`archive/`) + `ArchiveManifest` dataclass + `ArchiveVerifier` content hash unit tests, followed by dataset snapshot format and dependency decision design.**

## 4. Metadata

- **Author**: DeepSeek V4 Pro
- **Date**: 2026-06-07
- **Dependencies**: 059A (archive architecture) — Done
