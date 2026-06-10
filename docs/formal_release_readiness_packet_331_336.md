# Formal Release Readiness Packet - Tasks 331-336

> Release readiness assessment after packaged build, build script, and
> packaged-app quickstart.
> Generated: 2026-06-10

## Decision

Developer-alpha readiness: PASS.

Packaged Windows app readiness: PASS for a release-candidate style evaluator
build.

Formal public desktop release: NOT PASS for a broad public release yet. The
current evidence supports a `v0.3.0-dev` or `v0.3.0-rc` style tag after the final
status check is clean, not a production-quality `v1.0` release.

## Current Evidence

| Area | Evidence | Status |
|---|---|---|
| Desktop startup | `tests/test_app_startup_smoke.py` | PASS |
| Sample data workflow | `tests/test_sample_data_workflow_smoke.py` | PASS |
| Archive preview contract | `tests/test_archive_import_preview_contract_acceptance.py` | PASS |
| Windows CI smoke workflow | `.github/workflows/ci.yml` | Present |
| PyInstaller onedir build | `scripts/build_package.ps1` | PASS locally |
| Packaged exe launch smoke | `QSL_EXIT_AFTER_MS=100`, `QT_QPA_PLATFORM=offscreen` | PASS locally |
| User quickstart | `docs/packaged_app_quickstart_325_330.md` | Present |
| Build artifact hygiene | `.gitignore` ignores `dist/`, `build/`, `*.exe`, and generated `*.spec` | Present |

## Verification Commands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_package.ps1
```

Observed result:

```text
Build succeeded.
Packaged exe launch smoke passed with exit code 0.
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q
```

Observed result:

```text
16 passed
```

```powershell
git diff --check
git status --short
```

Expected before tagging:

```text
No diff-check errors.
No unexpected tracked or untracked release files.
```

## Hold Artifact Decision

The following local automation artifacts are excluded from release scope:

| Path | Decision |
|---|---|
| `AGENT_LOOP_README.md` | Ignore for release status. Do not stage. |
| `scripts/agent_loop.ps1` | Ignore for release status. Do not stage. |
| `tools/agent_loop.py` | Ignore for release status. Do not stage. |

This task adds precise `.gitignore` rules for those paths. It does not commit
the hold artifacts themselves.

## Build Artifact Decision

| Artifact | Decision |
|---|---|
| `dist/` | Generated output. Do not commit. |
| `build/` | Generated output. Do not commit. |
| `*.exe` | Generated binary. Do not commit as source. |
| `*.spec` | Auto-generated for now. Do not commit until a reviewed spec is assigned. |

Generated PyInstaller outputs were removed after verification.

## Remaining Risks

1. The packaged exe launch smoke is verified, but a full packaged-app manual
   walkthrough is still recommended before a wider audience release.
2. The first package is Windows-only and large.
3. There is no installer, code signing, auto-update, or release publishing flow.
4. CI runs the smoke suite but does not yet build the package.

## Recommended Final Action

If the next `git status --short` is clean after this packet is committed, the
project is ready for a `v0.3.0-dev` or `v0.3.0-rc` release-candidate tag.

The smallest next task is:

Tasks 337-342 - Release Candidate Tag Checklist

The task should verify clean status, rerun smoke/build commands, choose the tag
name, and produce a short release note. It should not add new features.
