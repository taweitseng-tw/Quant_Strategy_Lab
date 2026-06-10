# Local Release Zip Checklist - Tasks 361-366

> Documentation-only checklist. No build or zip was executed in this task.
> Generated: 2026-06-10

## Goal

Document how to create a local zip archive for the `v0.3.0-dev` Windows onedir
package when the user wants to share it outside git.

## Build Command

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1
```

Expected successful output includes:

```text
SUCCESS: dist/QuantStrategyLab/QuantStrategyLab.exe
Total size: 386 MB
Launch smoke: PASS (exit code 0)
```

The exact size can vary slightly between machines and dependency versions.

## Zip Command

Create the ignored local archive directory:

```powershell
New-Item -ItemType Directory -Force -Path release_artifacts | Out-Null
```

Zip the onedir package:

```powershell
Compress-Archive -Path .\dist\QuantStrategyLab\* -DestinationPath .\release_artifacts\QuantStrategyLab-v0.3.0-dev-windows-onedir.zip -Force
```

## Verification Commands

Check the zip exists and record its actual size:

```powershell
Get-ChildItem .\release_artifacts\QuantStrategyLab-v0.3.0-dev-windows-onedir.zip
```

Check the tag object and target commit:

```powershell
git rev-parse v0.3.0-dev
git rev-list -n 1 v0.3.0-dev
```

Expected current values:

```text
Tag object: ed34d2b5373c3fb8417839b9f06b67e2f706cebe
Target commit: bd94e90bd82839f8e47d21bbda5dc80cc04c8003
```

Check source control hygiene:

```powershell
git status --short
```

Expected:

```text
No `dist/`, `build/`, `.zip`, `.exe`, or generated `.spec` files staged.
```

## Cleanup Commands

Remove generated build outputs after the zip is created:

```powershell
Remove-Item -Recurse -Force -LiteralPath dist, build -ErrorAction SilentlyContinue
Remove-Item -Force -LiteralPath QuantStrategyLab.spec -ErrorAction SilentlyContinue
```

Keep or move the zip as needed:

```text
release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip
```

`release_artifacts/` is ignored by git.

## Important Notes

- The commands in this checklist were not executed in this task.
- The zip size is not estimated here; measure the actual file after creation.
- Do not commit the zip or generated build outputs.
- Do not push the local `v0.3.0-dev` tag unless the user chooses a remote and
  approves publishing.
- This is a developer pre-release, not `v1.0` or production software.
