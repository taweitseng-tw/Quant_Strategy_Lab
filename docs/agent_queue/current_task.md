# Agent Queue - Current Task

> Codex writes this file. Anti-Gravity or DeepSeek reads it, executes only this scope, then writes a completion report under `docs/agent_reports/`.

## Status

Ready for assignment

## Assigned Agent

DeepSeek V4 Pro

## Current Task

Batch 059G-Impl + 059H-Design - Manifest JSON Serialization and Archive Builder Adapter Design.

## Context Level

Level 2 for 059G implementation, Level 3 for 059H design.

## Required Reading

Before doing anything, read:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`
7. `docs/context_brief.md`
8. `docs/archive_builder_input_contract_059F.md`
9. `docs/review_notes/2026-06-07_task-059e-impl_059f-design_csv-dataset-snapshot-and-archive-builder-contract_codex-review.md`
10. This task file

## Context

059E added a standalone deterministic CSV dataset snapshot writer. 059F defined ArchiveBuilder input boundaries. Codex accepted the batch but rejected the proposed full Builder + Exporter + zip next step as too broad.

The next batch must stay small: implement manifest JSON serialization and design the repository adapter contract only. Do not build end-to-end archive export yet.

## Scope

### Do

- Complete two sequential tasks:
  - Task 059G-Impl - Archive manifest JSON serialization
  - Task 059H-Design - ArchiveBuilder repository adapter contract
- For Task 059G:
  - Add JSON serialization/deserialization helpers for `ArchiveManifest`.
  - Preserve deterministic JSON key ordering and indentation.
  - Add folder-level helpers that can write `manifest.json` and read it back.
  - Add focused tests for round-trip serialization, deterministic bytes, and read/write from folder.
- For Task 059H:
  - Create `docs/archive_builder_repository_adapter_059H.md`.
  - Define an adapter/protocol boundary for future ArchiveBuilder repository reads.
  - Specify required methods, inputs, outputs, fake-test fixture shape, and failure behavior.
  - Recommend exactly one next two-task batch.
- Update:
  - `docs/changelog.md`
  - `docs/task_board.md`
- Write completion report:
  - `docs/agent_reports/2026-06-07_task-059g-impl_059h-design_manifest-json-serialization-and-builder-adapter-contract_deepseek.md`

### Do Not

- Do not implement ArchiveBuilder, ArchiveExporter, or ArchiveImporter.
- Do not wire archive export into repository, UI, services, or CLI.
- Do not write zip export logic.
- Do not change repository schema or migrations.
- Do not add runtime dependencies.
- Do not change existing engine behavior.
- Do not create, delete, move, retarget, or push any git tag.
- Do not run `git add`, `git commit`, `git reset`, or `git checkout`.

## Files Likely Involved

- `archive/manifest.py`
- `tests/test_archive_manifest_json.py`
- `docs/archive_builder_repository_adapter_059H.md`
- `docs/changelog.md`
- `docs/task_board.md`
- `docs/agent_reports/2026-06-07_task-059g-impl_059h-design_manifest-json-serialization-and-builder-adapter-contract_deepseek.md`

## Acceptance Criteria

1. `ArchiveManifest` can serialize to deterministic JSON text and deserialize back.
2. `manifest.json` folder write/read helpers exist and are tested.
3. Tests cover round trip, deterministic bytes, and folder read/write.
4. No ArchiveBuilder/Exporter/Importer is implemented.
5. No repository, UI, schema, dependency, or engine changes are made.
6. Repository adapter design exists and recommends exactly one next two-task batch.
7. Changelog, task board, and completion report are updated.
8. Focused tests, full suite, `git diff --check`, and agent status pass.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_archive_manifest_json.py tests/test_dataset_snapshot.py tests/test_archive_verifier.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
powershell -ExecutionPolicy Bypass -File scripts\agent_status.ps1
git status --short
```

Expected:

- Focused archive manifest, dataset snapshot, and verifier tests pass.
- Full suite passes.
- `git diff --check` passes.
- Agent status shows Batch 059G-Impl + 059H-Design completion report as latest report.
- `git status --short` shows only files within this task scope.

## After Completion

Stop and report:

1. Completed
2. Files changed
3. Verification result
4. Known issues
5. Recommended next two-task batch
