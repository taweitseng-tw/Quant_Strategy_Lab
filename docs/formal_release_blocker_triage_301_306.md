# Formal Release Blocker Triage - Tasks 301-306

> Triage document. This does not claim formal desktop release readiness.
> Generated: 2026-06-10

## Summary

Developer-alpha evidence is strong enough for an internal evaluator pass, but
formal desktop release is still blocked. The remaining blockers are practical
release-readiness gaps, not architecture blockers.

## Must Fix Before Formal Desktop Release

| Blocker | Current state | Required next action |
|---|---|---|
| Packaging path is not accepted | Users still need a Python environment and source checkout. No executable, installer, or documented install path has been accepted. | Run a packaging path spike and choose PyInstaller, Nuitka, or pip entrypoint packaging for the first formal desktop build. |
| End-user quickstart is missing | Existing docs are mostly developer and agent workflow documents. A non-agent user does not yet have a concise install, launch, sample-data, and troubleshooting guide. | Add a short user quickstart after the packaging path is chosen. |
| Release hygiene is not clean | Local hold artifacts remain untracked by decision. That is acceptable for developer-alpha, but formal release still needs a clean release checklist that explicitly excludes or removes local-only artifacts. | Create a release hygiene checklist and verify the intended release tree from a clean clone or clean checkout. |

## Should Fix After First Formal Release

| Gap | Current state | Rationale |
|---|---|---|
| UI regression automation | Current proof is subprocess/offscreen smoke plus walkthrough evidence. | Manual walkthrough is acceptable for the first formal desktop release if packaging and quickstart are clear. |
| Multi-platform CI | CI is Windows-only. | Windows is the primary target. Linux/macOS can follow after the Windows release path is stable. |
| Wider test scheduling | CI currently runs the focused 16-test smoke set. | Full suite can be scheduled or added later once runtime and flakiness are measured. |

## Evidence Already Sufficient

| Evidence | Source | Status |
|---|---|---|
| Desktop startup smoke | `tests/test_app_startup_smoke.py` | Sufficient for developer-alpha startup confidence. |
| Sample data workflow smoke | `tests/test_sample_data_workflow_smoke.py` | Sufficient for developer-alpha workflow confidence. |
| Archive preview contract smoke | `tests/test_archive_import_preview_contract_acceptance.py` | Sufficient for current archive preview contract confidence. |
| CI smoke workflow | `.github/workflows/ci.yml` | Sufficient as the first Windows CI smoke workflow design and implementation. |
| Hold artifact decision | `docs/hold_artifact_decision_277_282.md` | Sufficient for developer-alpha; formal release still needs a clean release checklist. |

## Verification Commands

Run the current local smoke set:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_startup_smoke.py tests/test_sample_data_workflow_smoke.py tests/test_archive_import_preview_contract_acceptance.py -q
```

Expected current result:

```text
16 passed
```

Check documentation diffs:

```powershell
git diff --check
git status --short
```

Expected current result:

```text
No diff-check errors. Only intended files should be staged.
```

## Formal Release Readiness Estimate

- Developer-alpha readiness: approximately 98%.
- Formal desktop release readiness: approximately 87%.
- Remaining high-quality rounds: approximately 3-5.

The next two highest-leverage release tasks are packaging path selection and a
user-facing quickstart. Release hygiene should be handled before final tagging.

## Recommended Next Task

Tasks 307-312 - Packaging Path Spike

Create `docs/packaging_path_spike_307_312.md` comparing:

1. PyInstaller executable.
2. Nuitka executable.
3. pip-installable entrypoint.

The spike should recommend one first-release path, list risks around PySide6
size and plugins, and provide the smallest local verification command. It should
not implement packaging yet unless explicitly assigned.
