# Local Release Zip Evidence - Tasks 367-372

> Build and zip evidence. Zip is local only, ignored by git, and not pushed or
> uploaded.
> Generated: 2026-06-10

## Build Result

| Property | Value |
|---|---|
| Build command | `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1` |
| Build status | Success |
| Output directory | `dist/QuantStrategyLab/` |
| Reported onedir size | 386 MB |
| Launch smoke | PASS, exit code 0 |

## Zip Result

| Property | Value |
|---|---|
| Zip path | `release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip` |
| Zip size | 128,770,261 bytes |
| Zip size | 122.8 MiB |
| Gitignored | Yes, via `release_artifacts/` |
| Staged | No |
| Pushed or uploaded | No |

## Verification Commands

```powershell
Get-Item .\release_artifacts\QuantStrategyLab-v0.3.0-dev-windows-onedir.zip
git check-ignore .\release_artifacts\QuantStrategyLab-v0.3.0-dev-windows-onedir.zip
git status --short
```

Observed:

```text
Zip exists locally.
Zip is ignored by git.
No generated package artifact is staged.
```

## Cleanup State

Generated build folders were removed after zip creation:

```text
dist/ - removed
build/ - removed
QuantStrategyLab.spec - removed
```

The local zip remains available here:

```text
release_artifacts/QuantStrategyLab-v0.3.0-dev-windows-onedir.zip
```

## Notes

- The zip is outside source control and should stay that way.
- The zip was not pushed or uploaded.
- The local `v0.3.0-dev` tag remains local.
- This is a developer pre-release artifact, not a production release.
