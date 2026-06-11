# v0.3.0-dev Release Notes

> Developer-oriented packaged release candidate.
> Not a public production release.

## Summary

`v0.3.0-dev` is a Windows developer pre-release for Quant Strategy Lab. It
captures the current desktop startup smoke evidence, sample-data workflow smoke,
archive preview contract smoke, CI smoke workflow, PyInstaller onedir packaging
path, packaged app quickstart, and release hygiene decisions.

This release is for research and backtesting only. Backtested performance does
not guarantee future results. This is not investment advice and does not place
live trades.

## Highlights

- Desktop startup smoke tests cover imports, offscreen window construction, and
  subprocess launch with `QSL_EXIT_AFTER_MS`.
- Sample data workflow smoke covers sample CSV import, backtest structured
  output, and markdown report generation.
- Archive import preview contract smoke covers the current preview schema and
  acceptance behavior.
- Windows GitHub Actions CI smoke workflow runs the focused 16-test suite on
  `master` push and pull request events.
- `scripts/build_package.ps1` builds a PyInstaller `--onedir` Windows package
  and runs a packaged executable launch smoke.
- Packaged app quickstart documents build, launch, sample data location,
  troubleshooting, and current limits.
- Release hygiene ignores generated build outputs and local agent-loop hold
  artifacts.

## Verification

Packaged build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1
```

Observed result:

```text
Build succeeded.
Packaged exe launch smoke passed with exit code 0.
Onedir size was about 386 MB in the latest local verification.
```

Smoke tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_data_page_wiring.py tests/test_quality_checker.py tests/test_candlestick_chart.py tests/test_archive_import_preview_contract_acceptance.py -q
```

Observed result:

```text
98 passed
```

## Known Limits

- Windows only.
- No installer, code signing, or auto-update.
- Large PyInstaller onedir package (~395 MB on disk, 122.8 MiB zip).
- CI does not build the package yet.
- No screenshot or visual regression coverage.
- Full manual packaged workflow should still be exercised by an evaluator.
- Sample data smoke test produces limited trades (sample files are small).
- Not a `v1.0` or public production release.

## Local Release Artifact

```text
release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip
    Size: 128,770,261 bytes / 122.8 MiB
    Status: gitignored, not pushed
    Tag: v0.3.0-dev (local only)
```

## Disclaimer

This software is for research and backtesting purposes only.
Backtested performance does not guarantee future results.
Not financial advice. No live trading.
