# Archive Builder Input Contract (Task 059F Design)

## Overview
This document defines the input boundaries and data sources for the future `ArchiveBuilder`. The goal of the `ArchiveBuilder` is to gather all required information from various sources to produce a complete and verifiable archive of a passed strategy, without executing any new backtests or data generation.

## Input Boundaries and Data Sources

The `ArchiveBuilder` will require inputs from three distinct sources to compile an archive. It does not generate data; it only aggregates and packages existing data.

### 1. Data from Repository
These are structured records retrieved via the application's repository layer:
- **Strategy Metadata:** Information about the generated strategy (e.g., generator version, parameter ranges, random seed).
- **Strategy JSON/Definition:** The complete rule blocks and conditions defining the strategy.
- **Instrument Profile:** The settings of the instrument used (e.g., symbol, tick size, point value).
- **Validation Results:** The outcomes of stress tests, Monte Carlo, walk-forward, and out-of-sample testing.
- **Fitness Metrics:** The performance metrics that the strategy achieved to pass validation.

### 2. Data from File Paths
These are bulk data files that exist on disk and will be ingested into the archive:
- **Dataset Snapshot:** The deterministic CSV file capturing the exact exact dataset used during the backtest and validation, created by the dataset snapshot writer.

### 3. Data Caller-Provided
These are runtime contexts provided by the component invoking the `ArchiveBuilder` (e.g., the UI or export service):
- **Disclaimer Text:** The mandatory financial safety disclaimer to be embedded in the archive.
- **Export Context/Metadata:** Timestamp of export, user/author details (if any), and optional user notes.
- **Archive Destination Path:** Where the final archive file should be written.

## Failure Modes and Required Errors

The `ArchiveBuilder` must fail fast and loudly if any required component is missing or invalid. It will throw specific exceptions for the following failure modes:

- **Missing Strategy (`MissingStrategyError`):** Raised if the strategy ID provided cannot be found in the repository or lacks a valid JSON definition.
- **Missing Dataset Snapshot (`MissingDatasetSnapshotError`):** Raised if the dataset snapshot file path does not exist, or if the metadata for the dataset cannot be found.
- **Missing Validation Result (`MissingValidationResultError`):** Raised if the strategy has no recorded validation results, or if the validation results indicate a failure (only passed strategies should be archived).
- **Missing Disclaimer (`MissingDisclaimerError`):** Raised if the caller fails to provide the required financial safety disclaimer string.

## Recommended Next Two-Task Batch

**Batch 059G-Impl + 059H-Design: Manifest JSON Serialization and Archive Builder Adapter Design**

- **059G-Impl:** Add manifest JSON serialization/deserialization helpers and a folder-level manifest writer/reader test. Keep this independent of repository and exporter logic.
- **059H-Design:** Design the repository adapter contract for a future `ArchiveBuilder`, including exact query responsibilities and fake-test fixtures. Do not implement end-to-end archive export yet.
