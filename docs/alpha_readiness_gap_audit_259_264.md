# Alpha Readiness Gap Audit - Tasks 259-264

Evidence-based audit. This document does not claim production readiness.
Generated: 2026-06-10

## Current Alpha Runnable Evidence

| Evidence | Source | Status |
|---|---|---|
| Desktop entrypoint imports and `main()` is callable | `test_app_main_imports_and_callable` | Passing |
| MainWindow imports without error | `test_main_window_imports` | Passing |
| Project root is available for local imports | `test_main_window_import_path` | Passing |
| Offscreen MainWindow constructs and closes without event loop | `test_offscreen_main_window_construct_and_close` | Passing |
| `app/main.py` subprocess launch exits through `QSL_EXIT_AFTER_MS` | `test_subprocess_desktop_entrypoint_exits_cleanly` | Passing |
| Archive import preview full contract acceptance | `test_full_contract_acceptance` | Passing |
| Archive import preview no-config contract | `test_no_config_preview_contract_acceptance` | Passing |
| Archive invalid input preserves service error cause | `test_invalid_archive_preserves_service_error_cause` | Passing |
| Unknown restore action is manual-review-required | `test_unknown_restore_action_is_manual_review_required` | Passing |

Desk-check summary: the desktop startup path is verified in-process and through
a real subprocess smoke. The archive import preview contract is verified for
schema version, config comparison, restore plan evidence, JSON compatibility,
collision flags, and read-only behavior.

## Alpha Blockers

These are the remaining gaps before calling the current build a stronger
developer-evaluator alpha.

| # | Blocker | Evidence / Gap |
|---|---|---|
| 1 | No real-data end-to-end workflow smoke. | Existing desktop smoke proves startup only. It does not import sample OHLCV data, run a strategy/backtest flow, and export a report. |
| 2 | No human walkthrough for the desktop workflow. | There is no concise step-by-step evaluator script for create/open project, import data, build, validate, inspect results, and export report. |
| 3 | Hold artifacts remain outside release scope. | `AGENT_LOOP_README.md`, `scripts/agent_loop.ps1`, and `tools/` remain untracked by policy and should not be included unless explicitly accepted. |

Verdict: the application is close to developer-alpha readiness, but the next
high-value proof is an end-to-end workflow smoke using sample data.

## Formal Desktop Release Gaps

These are formal desktop release gaps. They are not blockers for a developer
alpha, but they must be tracked before a polished user-facing release.

| # | Gap | Notes |
|---|---|---|
| 1 | Installer / packaging path. | Users still run from a Python environment; no packaged Windows installer is accepted. |
| 2 | CI pipeline. | Tests are run manually in this workflow. |
| 3 | Automated UI/visual regression coverage. | Current GUI proof is startup/offscreen smoke, not visual workflow coverage. |
| 4 | User-facing quickstart and troubleshooting. | Current documentation is more developer- and agent-oriented than user-facing. |
| 5 | Release artifact policy. | Hold artifacts and generated workflow tools need an explicit accept/ignore decision before formal release. |

## Recommended Next 3 Engineering Tasks

1. Tasks 265-270 - Sample Data Workflow Service Smoke
   Add a focused non-UI workflow smoke that imports sample OHLCV data, creates or loads a simple strategy, runs a backtest or validation path, and verifies structured output.

2. Tasks 271-276 - Desktop Evaluator Walkthrough
   Add a concise developer-facing walkthrough document for launching the app, importing sample data, running a strategy workflow, validating results, and exporting a report.

3. Tasks 277-282 - Hold Artifact Final Decision
   Review `AGENT_LOOP_README.md`, `scripts/agent_loop.ps1`, and `tools/` as a bucket and decide whether to keep them untracked, commit them, or remove them from the release workspace.

## Summary

| Category | Count |
|---|---:|
| Passing desktop startup smoke tests | 5 |
| Passing archive preview acceptance tests | 4 |
| Alpha blockers | 3 |
| Formal desktop release gaps | 5 |
| Recommended next tasks | 3 |

The current build has credible startup and archive-preview evidence. The main
remaining alpha proof is a real sample-data workflow smoke rather than more
archive-preview contract hardening.
