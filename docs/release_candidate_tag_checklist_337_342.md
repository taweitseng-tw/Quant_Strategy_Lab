# Release Candidate Tag Checklist - Tasks 337-342

> Pre-tag checklist. This document does not create a git tag.
> Generated: 2026-06-10

## Recommended Tag

Recommended tag name:

```text
v0.3.0-dev
```

Use this as a developer-oriented packaged release candidate. Do not tag this as
`v1.0` or as a public production release. The project is still Windows-only,
large, unsigned, and intended for research/backtesting.

## Required Pre-Tag Commands

Run the packaged build and launch smoke:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1
```

Run the current smoke tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q
```

Check diffs and status:

```powershell
git diff --check
git status --short
git check-ignore AGENT_LOOP_README.md scripts/agent_loop.ps1 tools/agent_loop.py
```

Remove generated package outputs before committing or tagging:

```powershell
Remove-Item -Recurse -Force -LiteralPath dist, build -ErrorAction SilentlyContinue
Remove-Item -Force -LiteralPath QuantStrategyLab.spec -ErrorAction SilentlyContinue
```

## Observed Results

| Check | Observed result |
|---|---|
| Package build script | Build succeeded. |
| Packaged launch smoke | PASS, exit code 0. |
| Onedir size | About 386 MB in the latest local run. |
| Smoke tests | 16 passed. |
| Diff check | No diff-check errors; CRLF warnings only. |
| Hold artifact ignore check | `AGENT_LOOP_README.md`, `scripts/agent_loop.ps1`, and `tools/agent_loop.py` are ignored. |
| Final status target | Clean after generated artifacts are removed and checklist docs are committed. |

## Release Notes Draft

```markdown
## v0.3.0-dev

Developer-oriented packaged release candidate for Quant Strategy Lab.

This is research and backtesting software only. Backtested performance does not
guarantee future results. This is not investment advice and does not place live
trades.

### Highlights

- Windows PyInstaller onedir package build script.
- Packaged executable launch smoke verified with exit code 0.
- Desktop startup smoke tests.
- Sample data import, backtest, and report smoke coverage.
- Archive import preview contract smoke coverage.
- Windows GitHub Actions smoke workflow.
- Packaged app quickstart.
- Release hygiene for generated build outputs and local hold artifacts.

### Known limits

- Windows only.
- No installer, code signing, or auto-update.
- Large onedir package, about 386 MB in local verification.
- CI does not build the package yet.
- Not a production or public v1.0 release.
```

## Tag Command for Later Use

Do not run this command in this task. Use it only after Codex/user approval:

```powershell
git tag -a v0.3.0-dev -m "v0.3.0-dev developer packaged release candidate"
```

Push only after the local tag is approved:

```powershell
git push origin v0.3.0-dev
```

## Remaining Non-Blocking Risks

1. No installer or code signing.
2. CI smoke does not build the PyInstaller package.
3. No screenshot or visual regression coverage.
4. Full manual packaged workflow should still be exercised by an evaluator.

## Decision

If this checklist is committed and `git status --short` is clean, Codex may
create the `v0.3.0-dev` tag in the next explicitly approved task.
