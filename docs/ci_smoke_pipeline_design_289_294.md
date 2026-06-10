# CI Smoke Pipeline Design - Tasks 289-294

> Design document. No workflow code was created in this task.
> Generated: 2026-06-10

## Goal

Define the smallest useful GitHub Actions smoke pipeline for Quant Strategy Lab.
The first CI workflow should prove that the repository installs on Windows,
the desktop entrypoint can start in offscreen mode, and the current sample-data
workflow contracts still pass.

This task is design-only. A later implementation task should create
`.github/workflows/ci.yml`.

## Baseline

- Python: 3.11, matching the project requirement `>=3.11`.
- Runner: `windows-latest`, because the desktop app is PySide6 based and the
  local developer path is Windows-first.
- Branches: start with the current repository branch convention, `master`.
- Install command:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

The project currently declares these runtime dependencies in `pyproject.toml`:
`PySide6`, `pandas`, `numpy`, `matplotlib`, `pyqtgraph`, `plotly`, and
`openpyxl`. The dev extra includes `pytest`.

## Initial Smoke Test Set

Run the same focused smoke set that has been used for developer-alpha evidence:

```powershell
python -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q
```

Expected current result: 16 tests pass.

This is intentionally not the full test suite. The initial workflow should be a
fast acceptance signal for startup, sample data workflow, and archive import
preview contracts. Broader suites can be added after this smoke workflow is
stable.

## PySide6 Offscreen Risk

The desktop startup subprocess smoke uses `QT_QPA_PLATFORM=offscreen` and an
exit timer. On Windows with PySide6 wheels this should work without an external
display server. If a runner lacks the required Qt platform plugin, the existing
test helper is expected to report a precise skip reason instead of producing an
ambiguous timeout.

CI review should treat unexpected failure, timeout, or import errors as blocking.
An explicit skip caused by unavailable offscreen support should be investigated
before expanding CI to additional platforms.

## Proposed Future Workflow Outline

```yaml
name: CI Smoke

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  smoke:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ["3.11"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e .[dev]

      - name: Run smoke tests
        run: python -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q
```

The implementation task should create the workflow file in a dedicated change,
then verify the exact command locally before relying on GitHub Actions output.

## Out of Scope

- Creating `.github/workflows/ci.yml` in this design task.
- Running or requiring the full test suite on every push.
- Adding Linux or macOS runners.
- Adding lint, type checking, coverage, packaging, or release publishing.
- Changing dependency pins or adding a lockfile.

## Acceptance Criteria for the Follow-up Implementation

1. `.github/workflows/ci.yml` exists and follows the Windows Python 3.11 smoke
   design above.
2. The workflow installs the project with `python -m pip install -e .[dev]`.
3. The workflow runs the combined 16-test smoke command.
4. No agent-loop hold artifacts are staged as part of CI implementation.
5. Documentation is updated only if the implementation materially changes this
   design.
