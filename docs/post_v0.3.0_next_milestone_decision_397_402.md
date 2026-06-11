# Post-v0.3.0-dev Next Milestone Decision - Tasks 397-402

> Planning artifact only. No code, binaries, upload, push, or tag operation was performed.
> Generated: 2026-06-11.

## Current State

`v0.3.0-dev` is accepted as a local Windows developer pre-release checkpoint.
The next phase should move back to product capability work instead of more release-document polishing.

## Option A - External Evaluator Distribution and Feedback Collection

### Goal

Share the local developer pre-release with a small evaluator group and collect structured feedback.

### Why Now

- The release zip, local tag, release notes, and evaluator-facing docs exist.
- Real evaluator feedback can reveal install, startup, import, and workflow issues that local smoke tests miss.

### Concrete Tasks

1. Create a structured evaluator feedback form or issue template.
2. Prepare a short evaluator handoff packet with run steps, known limits, and disclaimer.
3. Collect feedback on startup, OHLCV import, backtest workflow, validation workflow, and confusing UI.
4. Triage reported issues into blocker, important, and backlog buckets.

### Risks

- Requires manual distribution by the user.
- Feedback timing is not controllable.
- Feedback may be vague unless the form is structured.

### Verification

- At least one evaluator confirms launch plus import.
- Feedback is recorded in a structured doc or issue list.
- Top issues are prioritized with reproducible steps when available.

## Option B - Strategy Quality / Robustness Expansion

### Goal

Improve how the app rejects weak strategies and explains accepted/rejected candidates.

### Why Now

- The local developer pre-release is accepted.
- Data import, smoke workflow, and validation surfaces are stable enough to support deeper strategy-quality work.
- This directly advances the core product mission: eliminate weak curve-fit strategies and keep explainable candidates.

### Concrete Tasks

1. Add an implementation-ready design for elimination rule configuration.
2. Expose a focused set of elimination thresholds in the Validate page or service layer, depending on current architecture.
3. Add tests proving thresholds affect pass/fail decisions without changing default behavior.
4. Add a compact strategy quality evidence section to reports or validation summaries.
5. Keep all work behind existing service boundaries; UI must not own validation logic.

### Risks

- This may require Level 3 context because validation logic affects strategy acceptance.
- Scope can expand if the first task tries to redesign the full validation engine.
- UI wiring must not duplicate business logic.

### Verification

- Existing validation tests still pass.
- New focused tests prove threshold behavior and default backward compatibility.
- Report or summary output shows the reasons for rejection or acceptance.

## Option C - CI / Package Automation Hardening

### Goal

Reduce manual release work by automating package build and artifact handling.

### Why Now

- The current package path works locally but remains manual.
- Automation would reduce repeated release-checklist work for future versions.

### Concrete Tasks

1. Audit the current CI workflow and packaging script.
2. Design a tag-triggered Windows packaging workflow.
3. Add artifact upload for the generated zip.
4. Keep GitHub Release creation as optional until token permissions and release policy are confirmed.

### Risks

- CI packaging can be slow and fragile on Windows runners.
- Artifact size and runner disk limits need verification.
- Token and release permissions may block fully automated publishing.

### Verification

- CI smoke still passes.
- Packaging job produces an artifact in a controlled test run.
- No release is published unless explicitly approved.

## Recommendation

Choose **Option B - Strategy Quality / Robustness Expansion**.

Reasoning:

1. It best matches the product mission after the local developer pre-release is accepted.
2. It creates measurable user-facing capability instead of more release hygiene.
3. It can start with a bounded first task: elimination rule configuration design and wiring.
4. Option A can run in parallel manually, but should not block engineering progress.
5. Option C is valuable later, but it improves delivery mechanics more than product capability.

## Recommended Next Tasks

1. Tasks 403-408 - Elimination Rule Configuration Design and Contract
2. Tasks 409-414 - Elimination Rule Configuration Implementation
3. Tasks 415-420 - Strategy Quality Evidence Summary
4. Tasks 421-426 - Fitness Multi-Metric Weighting Design
5. Tasks 427-432 - Fitness Multi-Metric Weighting Implementation
6. Tasks 433-438 - Strategy Explainability Report Section

## Guardrails For The Next Milestone

- Use Level 3 context for validation behavior changes.
- Preserve service and engine boundaries.
- Keep defaults backward compatible unless explicitly approved.
- Add deterministic tests for every strategy acceptance or rejection rule.
- Do not present strategy output as financial advice.
