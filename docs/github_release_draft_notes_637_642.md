# GitHub Release Draft Notes - Tasks 637-642

Date: 2026-06-12

## Decision

Draft ready. No GitHub Release was created or published in this task.

The `v0.4.0-dev` developer pre-release tag exists, points to the CI-passing
commit `1ef9657`, and the tag-triggered GitHub Actions run completed
successfully with a package artifact.

## Evidence Reviewed

| Item | Value |
|---|---|
| Repository | `taweitseng-tw/Quant_Strategy_Lab` |
| Tag | `v0.4.0-dev` |
| Tag target | `1ef9657 build: declare setuptools packages` |
| CI run | `27400889299` |
| CI result | Success |
| Smoke job | Success |
| Package job | Success |
| Artifact name | `QuantStrategyLab-windows-onedir` |
| Artifact size | `99,589,060` bytes |
| Artifact digest | `sha256:e2112c1c57dd915c7c6c88be46d66e344e8f7b31ba3a49903df1eed364bca9c9` |
| Artifact expiry | 2026-09-10 |

## Draft Release Title

```text
v0.4.0-dev - Developer Pre-release
```

## Draft Release Notes

```markdown
## Quant Strategy Lab v0.4.0-dev

Developer pre-release for local Windows desktop validation.

This is not a public 1.0 stable release. It is intended for controlled desktop
testing of the current local-first research workflow.

### Highlights

- Added background validation execution to reduce UI blocking during validation runs.
- Added boundary-only validation cancellation through the toolbar Stop action.
- Added stale-run guarding so a second validation run cannot start while one is active.
- Improved active dataset handling, sample data workflow, and desktop startup smoke coverage.
- Added English quickstart instructions to `README.md`.
- Added GitHub Actions smoke checks for Windows/Python 3.11.
- Added tag-triggered PyInstaller onedir packaging.

### Download

Download the GitHub Actions artifact from the successful `v0.4.0-dev` workflow run:

- Artifact: `QuantStrategyLab-windows-onedir`
- Workflow run: CI Smoke for tag `v0.4.0-dev`

After downloading, extract the artifact and run:

```powershell
dist\QuantStrategyLab\QuantStrategyLab.exe
```

If you are running from source instead:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
.\.venv\Scripts\python.exe app/main.py
```

### Quick Smoke Path

1. Launch the app.
2. Create or open a local project folder.
3. Import `sample_data/sample_txf.csv` or `sample_data/sample_ohlcv.csv`.
4. Run validation from the toolbar.
5. Inspect Results and Report pages.
6. Export a Markdown or HTML report.

### Verification

The tag-triggered GitHub Actions run completed successfully:

- `smoke (3.11)`: passed
- `package (3.11)`: passed
- Package artifact uploaded: `QuantStrategyLab-windows-onedir`

Local release-candidate checks also passed before tagging:

- Startup/sample workflow smoke tests
- PyInstaller onedir build
- Packaged launch smoke

### Known Risks and Limits

- Windows is the primary target.
- The executable is unsigned and may trigger Windows SmartScreen warnings.
- The package is PyInstaller onedir, not a single-file executable or MSI installer.
- The GitHub Actions artifact expires according to GitHub artifact retention.
- No broker API or live trading is included.
- This software is for research and backtesting only. Backtested performance does not guarantee future results.

### Tag

- Tag: `v0.4.0-dev`
- Commit: `1ef9657`
```

## Publish Boundary

Do not publish this GitHub Release unless the user explicitly approves.

Recommended next action:

```text
Ask the user whether Codex should create a draft GitHub Release for v0.4.0-dev using these notes.
```

## Verification

Commands run:

```powershell
git show --no-patch --format="%h %D%n%s" v0.4.0-dev
gh run view 27400889299 --repo taweitseng-tw/Quant_Strategy_Lab --json status,conclusion,jobs
gh api repos/taweitseng-tw/Quant_Strategy_Lab/actions/runs/27400889299/artifacts
gh release view v0.4.0-dev --repo taweitseng-tw/Quant_Strategy_Lab
```

Results:

- Tag `v0.4.0-dev` points to `1ef9657`.
- CI run `27400889299` completed successfully.
- Artifact `QuantStrategyLab-windows-onedir` exists.
- No GitHub Release exists yet for `v0.4.0-dev`.
