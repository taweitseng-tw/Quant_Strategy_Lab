# Release Artifact Archive Plan - Tasks 355-360

> Archive plan for sharing the packaged Windows build output.
> No push, upload, zip archive, or build artifact was created in this task.
> Generated: 2026-06-10

## Problem

The local `v0.3.0-dev` tag captures source code and release notes, but the
packaged app is generated output. The PyInstaller onedir package is large and
must not be committed to git.

The latest verified build reported an onedir size of about 386 MB.

## Options

| Option | Summary | Pros | Cons |
|---|---|---|---|
| Keep local only | Keep the tag and rebuild package when needed. | Cleanest source control state; no upload risk. | Not shareable with evaluators who cannot build locally. |
| Manual local zip | Build locally and zip `dist/QuantStrategyLab/` into `release_artifacts/`. | Smallest shareable next step; no remote required. | Manual process; archive size must be measured after creation. |
| Configure remote and push tag later | Add a remote and push `v0.3.0-dev`. | Shares source checkpoint. | Does not by itself provide a packaged executable. |
| Future release artifact upload | CI or release workflow builds and uploads package. | Best long-term repeatability. | Requires remote, CI packaging, and release workflow work. |

## Recommendation

Use a manual local zip archive when an evaluator needs the packaged app.

Do not commit the archive. Store it under `release_artifacts/`, which is now
ignored by git.

Keep the current `v0.3.0-dev` tag local until the user chooses a remote or
sharing destination.

## Commands for Later Use

Build the package:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1
```

Create a local archive directory:

```powershell
New-Item -ItemType Directory -Force -Path release_artifacts | Out-Null
```

Create a zip archive:

```powershell
Compress-Archive -Path .\dist\QuantStrategyLab\* -DestinationPath .\release_artifacts\QuantStrategyLab-v0.3.0-dev-windows-onedir.zip -Force
```

Inspect the archive:

```powershell
Get-ChildItem .\release_artifacts\
```

These commands are documented for later use. They were not executed in this
task.

## Git Hygiene

| Path | Decision |
|---|---|
| `dist/` | Ignored generated build output. |
| `build/` | Ignored generated build output. |
| `*.exe` | Ignored generated binary output. |
| `*.spec` | Ignored generated PyInstaller spec for now. |
| `release_artifacts/` | Ignored local package archive output. |

## Verification

```powershell
git status --short
git remote -v
git diff --check
```

Expected:

```text
No push was executed.
No upload was executed.
No archive was created.
No generated build output was committed.
```

## Next Recommended Task

No additional local release-candidate task is required unless the user wants to
share the package. If sharing is needed, run the documented build and zip
commands manually, then send or upload the zip outside git.
